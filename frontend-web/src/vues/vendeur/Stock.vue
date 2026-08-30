<script setup lang="ts">
// L'écran de stock.
//
// La correction du stock est une **popup**, comme la maquette la décrit :
// « Nouvelle quantité » et un motif à choisir. On compte ce qu'il y a sur
// l'étagère, on ne calcule pas de tête l'écart avec ce que l'écran affiche.
// L'historique a son propre onglet, en tableau, tous produits confondus.
import {
  AlertTriangle, ArrowDownRight, ArrowUpRight, Boxes, Check, History, PackageX,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { useNotification } from '../../notifications'
import { vendeur, type Mouvement, type ProduitCatalogue } from '../../api/vendeur'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import Volet from '../../composants/Volet.vue'

type Ligne = ProduitCatalogue & { [cle: string]: unknown }
type LigneJournal = Mouvement & { produit: string; [cle: string]: unknown }

const notifier = useNotification()
const produits = ref<Ligne[]>([])
const chargement = ref(true)
const onglet = ref('tout')

const ajuste = ref<Ligne | null>(null)
const selection = ref<Ligne | null>(null)
const mouvementsProduit = ref<Mouvement[]>([])
const saisie = ref({ quantite: '0', type: 'AJUSTEMENT', motif: '' })
const erreur = ref('')
const occupe = ref(false)

const journal = ref<LigneJournal[]>([])
const journalCharge = ref(false)

// Les motifs de la maquette. Une liste fermée plutôt qu'un champ libre : six
// mois plus tard, « erreur » et « erreur de saisie » ne se regroupent plus.
const MOTIFS = [
  'Inventaire', 'Casse', 'Erreur de saisie', 'Périmé', 'Vol ou perte',
  'Rupture constatée en boutique',
]

const TYPES = [
  { valeur: 'AJUSTEMENT', libelle: 'Ajustement manuel', motifRequis: true },
  { valeur: 'REAPPRO', libelle: 'Réapprovisionnement', motifRequis: false },
  { valeur: 'RETOUR', libelle: 'Retour client', motifRequis: false },
]

async function charger() {
  chargement.value = true
  try {
    produits.value = (await vendeur.mesProduits()) as Ligne[]
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const aReapprovisionner = computed(() =>
  produits.value.filter((p) => p.est_visible && p.stock_disponible <= p.seuil_alerte),
)
const ruptures = computed(() => produits.value.filter((p) => p.est_visible && p.est_en_rupture))

const visibles = computed(() =>
  onglet.value === 'manquants' ? aReapprovisionner.value
    : onglet.value === 'ruptures' ? ruptures.value
      : produits.value,
)

const typeCourant = computed(
  () => TYPES.find((type) => type.valeur === saisie.value.type) ?? TYPES[0],
)
const ecart = computed(
  () => Number(saisie.value.quantite || 0) - (ajuste.value?.stock_disponible ?? 0),
)

function ouvrirAjustement(produit: Ligne) {
  ajuste.value = produit
  saisie.value = { quantite: String(produit.stock_disponible), type: 'AJUSTEMENT', motif: '' }
  erreur.value = ''
}

async function consulter(produit: Ligne) {
  if (selection.value?.id === produit.id) {
    selection.value = null
    return
  }
  selection.value = produit
  mouvementsProduit.value = await vendeur.stock.mouvements(produit.id)
}

async function appliquer() {
  if (!ajuste.value) return
  erreur.value = ''
  occupe.value = true
  try {
    const resultat = await vendeur.stock.definir(
      ajuste.value.id,
      Number(saisie.value.quantite),
      saisie.value.type,
      saisie.value.motif,
    )
    notifier.succes(`« ${ajuste.value.nom} » : stock à ${resultat.stock_disponible}.`)
    ajuste.value = null
    journalCharge.value = false
    await charger()
    if (selection.value) await consulter(selection.value)
    if (onglet.value === 'journal') await chargerJournal()
  } catch (echec) {
    // L'erreur reste AUSSI dans la popup : elle explique pourquoi le
    // formulaire qu'on a sous les yeux a ete refuse.
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Ajustement refusé.'
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
}

/** Le journal complet : tous les mouvements de la boutique. C'est ce qu'on
 *  ouvre quand un chiffre ne tombe pas juste. */
async function chargerJournal() {
  if (journalCharge.value) return
  const lots = await Promise.all(
    produits.value.map(async (produit) => {
      const mouvements = await vendeur.stock.mouvements(produit.id)
      return mouvements.map((mouvement) => ({ ...mouvement, produit: produit.nom }))
    }),
  )
  journal.value = lots
    .flat()
    .sort((a, b) => b.date_mouvement.localeCompare(a.date_mouvement))
    .slice(0, 150) as LigneJournal[]
  journalCharge.value = true
}

function changerOnglet(valeur: string) {
  onglet.value = valeur
  if (valeur === 'journal') chargerJournal()
}

const colonnes: Colonne<Ligne>[] = [
  { cle: 'produit', titre: 'Produit', champTri: 'nom' },
  { cle: 'seuil', titre: 'Seuil', largeur: 74, aligne: 'droite', masquerSous: 'md',
    champTri: 'seuil_alerte' },
  { cle: 'stock', titre: 'En stock', largeur: 90, aligne: 'droite',
    champTri: 'stock_disponible' },
  { cle: 'etat', titre: 'État', largeur: 100, aligne: 'centre' },
]

const colonnesJournal: Colonne<LigneJournal>[] = [
  { cle: 'date', titre: 'Date', largeur: 130, champTri: 'date_mouvement' },
  { cle: 'produit', titre: 'Produit' },
  { cle: 'type', titre: 'Type', largeur: 150, masquerSous: 'md' },
  { cle: 'quantite', titre: 'Quantité', largeur: 90, aligne: 'droite' },
  { cle: 'apres', titre: 'Après', largeur: 70, aligne: 'droite' },
  { cle: 'motif', titre: 'Motif', masquerSous: 'lg' },
]

const quand = (date: string) =>
  new Date(date).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit',
  })

const etat = (produit: Ligne) =>
  produit.est_en_rupture ? { classe: 'badge-erreur', libelle: 'rupture' }
    : produit.stock_disponible <= produit.seuil_alerte
      ? { classe: 'badge-attente', libelle: 'stock bas' }
      : { classe: 'badge-ok', libelle: 'ok' }
</script>

<template>
  <div class="mx-auto max-w-[1060px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      :model-value="onglet"
      :onglets="[
        { cle: 'tout', libelle: 'Tous les produits', compteur: produits.length },
        { cle: 'manquants', libelle: 'À réapprovisionner', compteur: aReapprovisionner.length },
        { cle: 'ruptures', libelle: 'En rupture', compteur: ruptures.length },
        { cle: 'journal', libelle: 'Historique' },
      ]"
      @update:model-value="changerOnglet"
    />

    <!-- L'historique, dans son propre onglet -->
    <Liste
      v-if="onglet === 'journal'"
      :colonnes="colonnesJournal"
      :lignes="journal"
      :cle-ligne="(mouvement) => mouvement.id"
      :chargement="!journalCharge"
      :recherche="(m) => `${m.produit} ${m.libelle_type} ${m.motif} ${m.auteur}`"
      placeholder="Produit, motif, auteur…"
      :par-page="15"
    >
      <template #col-date="{ ligne }">
        <span class="text-encre-douce">{{ quand(ligne.date_mouvement) }}</span>
      </template>
      <template #col-produit="{ ligne }">
        <b class="truncate">{{ ligne.produit }}</b>
      </template>
      <template #col-type="{ ligne }">{{ ligne.libelle_type }}</template>
      <template #col-quantite="{ ligne }">
        <b :class="ligne.quantite > 0 ? 'text-succes' : 'text-alerte'">
          <component
            :is="ligne.quantite > 0 ? ArrowUpRight : ArrowDownRight"
            :size="12"
            class="inline"
          />
          {{ ligne.quantite > 0 ? '+' : '' }}{{ ligne.quantite }}
        </b>
      </template>
      <template #col-apres="{ ligne }">{{ ligne.stock_apres }}</template>
      <template #col-motif="{ ligne }">
        <span class="min-w-0 truncate text-encre-douce">
          {{ ligne.motif || '—' }} · {{ ligne.auteur }}
        </span>
      </template>
      <template #vide>
        <div class="vide">
          <History :size="30" class="text-trait" />
          <b class="vide-titre">Aucun mouvement enregistré</b>
          <p class="vide-texte">
            Chaque réapprovisionnement, vente ou correction apparaîtra ici, avec son
            motif et son auteur.
          </p>
        </div>
      </template>
    </Liste>

    <!-- Les produits -->
    <template v-else>
      <p v-if="aReapprovisionner.length && onglet === 'tout'" class="bandeau mb-3">
        <AlertTriangle :size="15" class="mt-px shrink-0" />
        {{ aReapprovisionner.length }} produit(s) sous le seuil d'alerte — pensez à
        réapprovisionner ou à corriger le stock système.
      </p>

      <Liste
        :colonnes="colonnes"
        :lignes="visibles"
        :cle-ligne="(produit) => produit.id"
        :chargement="chargement"
        :recherche="(p) => p.nom"
        :active="(p) => selection?.id === p.id"
        @ligne-cliquee="consulter"
        placeholder="Filtrer par nom…"
      >
        <template #col-produit="{ ligne }">
          <span class="flex min-w-0 items-center gap-3">
            <img
              v-if="ligne.image"
              :src="ligne.image"
              :alt="ligne.nom"
              class="h-9 w-9 shrink-0 rounded-lg object-cover"
            />
            <span class="min-w-0">
              <b class="block truncate">{{ ligne.nom }}</b>
              <span class="text-[11.2px] text-encre-douce">
                <template v-if="ligne.stock_reserve">
                  {{ ligne.stock_reserve }} réservé(s) par un paiement en cours
                </template>
                <template v-else-if="!ligne.est_visible">retiré de la vente</template>
                <template v-else>{{ ligne.categorie?.nom ?? 'Sans catégorie' }}</template>
              </span>
            </span>
          </span>
        </template>
        <template #col-seuil="{ ligne }">
          <span class="text-encre-douce">{{ ligne.seuil_alerte }}</span>
        </template>
        <template #col-stock="{ ligne }">
          <b class="text-[15px]">{{ ligne.stock_disponible }}</b>
        </template>
        <template #col-etat="{ ligne }">
          <span class="badge" :class="etat(ligne).classe">{{ etat(ligne).libelle }}</span>
        </template>

        <template #actions="{ ligne }">
          <ActionLigne
            titre="Consulter l'historique de ce produit"
            :icone="History"
            :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
            @click="consulter(ligne)"
          />
          <ActionLigne
            titre="Corriger le stock"
            :icone="Boxes"
            @click="ouvrirAjustement(ligne)"
          />
          <ActionLigne
            titre="Mettre en rupture"
            :icone="PackageX"
            ton="danger"
            :desactive="ligne.est_en_rupture"
            @click="ouvrirAjustement(ligne); saisie.quantite = '0';
                    saisie.motif = 'Rupture constatée en boutique'"
          />
        </template>

        <template #vide>
          <div class="vide">
            <Boxes :size="30" class="text-trait" />
            <b class="vide-titre">
              {{
                onglet === 'manquants' ? 'Rien à réapprovisionner'
                : onglet === 'ruptures' ? 'Aucune rupture en cours'
                : 'Aucun produit'
              }}
            </b>
            <p class="vide-texte">
              {{
                onglet === 'tout'
                  ? 'Les produits de votre boutique apparaîtront ici avec leur stock.'
                  : 'Tout est au-dessus du seuil que vous avez fixé.'
              }}
            </p>
          </div>
        </template>
      </Liste>
    </template>

    <!-- L'historique du produit consulté, dans le volet -->
    <Volet v-if="selection" :titre="selection.nom">
      <dl class="flex flex-col gap-2 text-[12px]">
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">En stock</dt>
          <dd class="font-semibold">{{ selection.stock_disponible }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Commandable</dt>
          <dd class="font-semibold">{{ selection.stock_commandable }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Seuil d'alerte</dt>
          <dd class="font-semibold">{{ selection.seuil_alerte }}</dd>
        </div>
      </dl>

      <button type="button" class="bouton-accent mt-3 w-full" @click="ouvrirAjustement(selection)">
        <Boxes :size="15" /> Corriger le stock
      </button>

      <b class="mt-4 block text-[11px] font-bold tracking-wider text-encre-douce uppercase">
        Derniers mouvements
      </b>
      <div v-if="!mouvementsProduit.length" class="vide !py-6">
        <b class="vide-titre">Aucun mouvement</b>
      </div>
      <ul v-else class="mt-2 flex flex-col gap-1.5">
        <li
          v-for="mouvement in mouvementsProduit.slice(0, 10)"
          :key="mouvement.id"
          class="rounded-lg border border-trait bg-papier px-2.5 py-2 text-[11.5px]"
        >
          <span class="flex items-center justify-between gap-2">
            <b>{{ mouvement.libelle_type }}</b>
            <b :class="mouvement.quantite > 0 ? 'text-succes' : 'text-alerte'">
              {{ mouvement.quantite > 0 ? '+' : '' }}{{ mouvement.quantite }}
              → {{ mouvement.stock_apres }}
            </b>
          </span>
          <span class="mt-0.5 block text-encre-douce">
            {{ quand(mouvement.date_mouvement) }}
            <template v-if="mouvement.motif"> · {{ mouvement.motif }}</template>
          </span>
        </li>
      </ul>
    </Volet>

    <!-- La popup d'ajustement, telle que la maquette la décrit -->
    <Popup
      v-if="ajuste"
      titre="Corriger le stock"
      :explication="`« ${ajuste.nom} » — le système en compte ${ajuste.stock_disponible}.
                     Saisissez la quantité réellement présente : l'écart est calculé et
                     tracé dans l'historique, jamais une modification silencieuse.`"
      @fermer="ajuste = null"
    >
      <form class="flex flex-col gap-3.5" @submit.prevent="appliquer">
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Nouvelle quantité</span>
          <input v-model="saisie.quantite" type="number" min="0" required class="champ-clair" />
          <span
            v-if="ecart !== 0"
            class="text-[11.5px] font-semibold"
            :class="ecart > 0 ? 'text-succes' : 'text-alerte'"
          >
            {{ ecart > 0 ? '+' : '' }}{{ ecart }} par rapport au stock actuel
          </span>
        </label>

        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Type de mouvement</span>
          <select v-model="saisie.type" class="champ-clair">
            <option v-for="type in TYPES" :key="type.valeur" :value="type.valeur">
              {{ type.libelle }}
            </option>
          </select>
        </label>

        <label class="flex flex-col gap-1.5">
          <span class="etiquette">
            Motif
            <span v-if="typeCourant.motifRequis" class="text-alerte">obligatoire</span>
          </span>
          <input
            v-model="saisie.motif"
            list="motifs-stock"
            :required="typeCourant.motifRequis"
            placeholder="Casse, inventaire…"
            class="champ-clair"
          />
          <datalist id="motifs-stock">
            <option v-for="motif in MOTIFS" :key="motif" :value="motif" />
          </datalist>
        </label>

        <p v-if="erreur" class="bandeau bandeau-erreur">
          <AlertTriangle :size="15" class="mt-px shrink-0" />
          {{ erreur }}
        </p>
      </form>

      <template #actions>
        <button
          type="button"
          class="bouton-neutre mr-auto !py-2"
          title="Passer le stock à zéro"
          @click="saisie.quantite = '0'; saisie.motif = saisie.motif || 'Rupture constatée'"
        >
          <PackageX :size="15" />
          Mettre en rupture
        </button>
        <button type="button" class="bouton-neutre !py-2" @click="ajuste = null">Annuler</button>
        <button
          type="button"
          class="bouton-accent !py-2"
          :disabled="occupe || (typeCourant.motifRequis && !saisie.motif.trim())"
          @click="appliquer"
        >
          <Check :size="15" />
          Confirmer
        </button>
      </template>
    </Popup>
  </div>
</template>
