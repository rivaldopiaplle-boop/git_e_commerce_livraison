<script setup lang="ts">
// Le catalogue du vendeur — **et son stock** (D-79).
//
// **Ta remarque, L-3** : *« Mon catalogue et Stock se marchent sur les pieds,
// si tu organises bien on peut fusionner »*, et *« deux fois le bouton
// corriger le stock »*. Tu as raison : ce sont deux vues du même objet, et les
// séparer obligeait à porter deux boutons pour la même action.
//
// Un seul écran, cinq onglets, et **un seul** bouton de correction de stock
// par ligne. Rien n'est perdu au passage (D-97) : les états de vente, les
// alertes de stock, la popup de correction avec son motif obligatoire et
// l'historique complet sont tous là — ils ont juste changé de place.
import {
  ArrowDownRight, ArrowUpRight, Boxes, Check, Eye, EyeOff, History, ImageOff,
  Package, PackageX, Pencil, Plus, RotateCcw,
} from '@lucide/vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { computed, ref } from 'vue'

import { useRafraichissement } from '../../rafraichissement'
import { EchecApi } from '../../api/client'
import { vendeur, type Mouvement, type ProduitCatalogue } from '../../api/vendeur'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import FicheContextuelle from '../../composants/FicheContextuelle.vue'
import { useNotification } from '../../notifications'
import { useAuthentification } from '../../stores/authentification'

type Ligne = ProduitCatalogue & { [cle: string]: unknown }
type LigneJournal = Mouvement & { produit: string; [cle: string]: unknown }

const notifier = useNotification()
const session = useAuthentification()

const produits = ref<Ligne[]>([])
const chargement = ref(true)
const onglet = ref('en-vente')
const selection = ref<Ligne | null>(null)
// L'oeil ouvre une popup par-dessus la liste (M-1) : le panneau de droite,
// lui, reste le contexte permanent de la ligne active.
const apercu = ref(false)
const mouvementsProduit = ref<Mouvement[]>([])
const occupe = ref(false)

const journal = ref<LigneJournal[]>([])
const journalCharge = ref(false)

// La correction de stock : une seule popup, un seul chemin (D-49).
const ajuste = ref<Ligne | null>(null)
const saisie = ref({ quantite: 0, type: 'AJUSTEMENT', motif: '' })
const erreurPopup = ref('')

// Retirer de la vente est réversible, mais ça retire un produit du catalogue
// public : on confirme, et on explique (D-60, D-61).
const aRetirer = ref<Ligne | null>(null)

const MOTIFS = [
  'Inventaire', 'Casse', 'Erreur de saisie', 'Périmé', 'Vol ou perte',
  'Rupture constatée en boutique',
]
const TYPES = [
  { valeur: 'AJUSTEMENT', libelle: 'Ajustement manuel', motifRequis: true },
  { valeur: 'REAPPRO', libelle: 'Réapprovisionnement', motifRequis: false },
  { valeur: 'RETOUR', libelle: 'Retour client', motifRequis: false },
]

// Le personnel corrige le stock mais ne publie ni ne retire un produit : ce
// sont des décisions commerciales (D-04). Le serveur le vérifie aussi.
const estVendeur = computed(() => session.role === 'VENDEUR')

async function charger() {
  chargement.value = true
  try {
    produits.value = (await vendeur.mesProduits()) as Ligne[]
    if (selection.value) {
      selection.value = produits.value.find((p) => p.id === selection.value!.id) ?? null
    }
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger)

const enVente = computed(() => produits.value.filter((p) => p.est_visible))
const retires = computed(() => produits.value.filter((p) => !p.est_visible))
const ruptures = computed(() => enVente.value.filter((p) => p.est_en_rupture))
const aReapprovisionner = computed(() =>
  enVente.value.filter((p) => p.stock_disponible <= p.seuil_alerte),
)

const visibles = computed(() =>
  onglet.value === 'retires' ? retires.value
    : onglet.value === 'ruptures' ? ruptures.value
      : onglet.value === 'stock' ? aReapprovisionner.value
        : enVente.value,
)

const etat = (produit: Ligne) =>
  !produit.est_visible ? { ton: 'secondary' as const, libelle: 'retiré' }
    : produit.est_en_rupture ? { ton: 'danger' as const, libelle: 'rupture' }
      : produit.stock_disponible <= produit.seuil_alerte
        ? { ton: 'warn' as const, libelle: 'stock bas' }
        : { ton: 'success' as const, libelle: 'en vente' }

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const colonnes: Colonne<Ligne>[] = [
  { cle: 'produit', titre: 'Produit', champTri: 'nom' },
  { cle: 'prix', titre: 'Prix', largeur: 100, aligne: 'droite', champTri: 'prix_centimes' },
  { cle: 'stock', titre: 'Stock', largeur: 96, aligne: 'droite',
    champTri: 'stock_disponible' },
  { cle: 'etat', titre: 'État', largeur: 104, aligne: 'centre' },
]

const colonnesJournal: Colonne<LigneJournal>[] = [
  { cle: 'date', titre: 'Date', largeur: 130, champTri: 'date_mouvement' },
  { cle: 'produit', titre: 'Produit' },
  { cle: 'type', titre: 'Type', largeur: 150, masquerSous: 'md' },
  { cle: 'quantite', titre: 'Quantité', largeur: 92, aligne: 'droite' },
  { cle: 'apres', titre: 'Après', largeur: 70, aligne: 'droite' },
  { cle: 'motif', titre: 'Motif et auteur', masquerSous: 'lg' },
]

/**
 * L'oeil : on consulte, on ne selectionne pas seulement (M-1).
 *
 * Ici la consultation va CHERCHER l'historique des mouvements : c'est la
 * raison d'etre de l'ecran, et c'est pour cela qu'elle n'est pas la fonction
 * generique des autres listes.
 *
 * Elle ne bascule plus la selection : un oeil ouvre, il ne ferme pas. Refermer
 * en recliquant sur l'oeil etait invisible et surprenait a chaque fois.
 */
async function consulter(produit: Ligne) {
  selection.value = produit
  apercu.value = true
  mouvementsProduit.value = await vendeur.stock.mouvements(produit.id)
}

function ouvrirAjustement(produit: Ligne) {
  ajuste.value = produit
  saisie.value = { quantite: produit.stock_disponible, type: 'AJUSTEMENT', motif: '' }
  erreurPopup.value = ''
}

const typeCourant = computed(
  () => TYPES.find((type) => type.valeur === saisie.value.type) ?? TYPES[0],
)
const ecart = computed(() => saisie.value.quantite - (ajuste.value?.stock_disponible ?? 0))

async function appliquer() {
  if (!ajuste.value) return
  erreurPopup.value = ''
  occupe.value = true
  try {
    const resultat = await vendeur.stock.definir(
      ajuste.value.id, saisie.value.quantite, saisie.value.type, saisie.value.motif,
    )
    notifier.succes(
      resultat.stock_disponible === 0
        ? `« ${ajuste.value.nom} » est déclaré en rupture. Vos clients peuvent demander à être prévenus de son retour.`
        : `« ${ajuste.value.nom} » : stock à ${resultat.stock_disponible}.`,
    )
    ajuste.value = null
    journalCharge.value = false
    await charger()
    if (selection.value) {
      mouvementsProduit.value = await vendeur.stock.mouvements(selection.value.id)
    }
    if (onglet.value === 'journal') await chargerJournal()
  } catch (echec) {
    erreurPopup.value = echec instanceof EchecApi ? echec.erreur.message : 'Ajustement refusé.'
    notifier.echec(erreurPopup.value)
  } finally {
    occupe.value = false
  }
}

async function agir(action: Promise<unknown>, reussite: string) {
  occupe.value = true
  try {
    await action
    await charger()
    notifier.succes(reussite)
  } catch (echec) {
    notifier.echec(echec instanceof EchecApi ? echec.erreur.message : "L'action a échoué.")
  } finally {
    occupe.value = false
  }
}

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

const quand = (date: string) =>
  new Date(date).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit',
  })
</script>

<template>
  <div class="mx-auto max-w-[1100px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      :model-value="onglet"
      :onglets="[
        { cle: 'en-vente', libelle: 'En vente', compteur: enVente.length },
        { cle: 'stock', libelle: 'Stock et alertes', compteur: aReapprovisionner.length },
        { cle: 'ruptures', libelle: 'En rupture', compteur: ruptures.length },
        { cle: 'retires', libelle: 'Retirés', compteur: retires.length },
        { cle: 'journal', libelle: 'Historique' },
      ]"
      @update:model-value="changerOnglet"
    />

    <!-- ── L'historique du stock, tous produits confondus ────────────── -->
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
      <template #col-produit="{ ligne }"><b class="truncate">{{ ligne.produit }}</b></template>
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
            Chaque réapprovisionnement, vente ou correction apparaîtra ici, avec son motif
            et la personne qui l'a faite.
          </p>
        </div>
      </template>
    </Liste>

    <!-- ── Les produits ─────────────────────────────────────────────── -->
    <Liste
      v-else
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(produit) => produit.id"
      :chargement="chargement"
      :recherche="(p) => `${p.nom} ${p.categorie?.nom ?? ''}`"
      :active="(p) => selection?.id === p.id"
      placeholder="Nom de produit, catégorie…"
      @ligne-cliquee="consulter"
    >
      <template #outils>
        <RouterLink
          v-if="estVendeur"
          :to="{ name: 'vendeur-nouveau' }"
          class="bouton-accent !py-2"
        >
          <Plus :size="15" />
          Nouveau produit
        </RouterLink>
      </template>

      <template #col-produit="{ ligne }">
        <span class="flex min-w-0 items-center gap-3">
          <img
            v-if="ligne.image"
            :src="ligne.image"
            :alt="ligne.nom"
            class="h-9 w-9 shrink-0 rounded-lg object-cover"
            :class="ligne.est_visible ? '' : 'opacity-40 grayscale'"
          />
          <span
            v-else
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-atelier
                   text-encre-douce"
          >
            <ImageOff :size="14" />
          </span>
          <span class="min-w-0">
            <b class="block truncate">{{ ligne.nom }}</b>
            <span class="text-[11.2px] text-encre-douce">
              {{ ligne.categorie?.nom ?? 'Sans catégorie' }}
              · seuil {{ ligne.seuil_alerte }}
              <template v-if="ligne.stock_reserve">
                · {{ ligne.stock_reserve }} réservé(s)
              </template>
              <template v-if="!ligne.nombre_photos"> · aucune photo</template>
            </span>
          </span>
        </span>
      </template>

      <template #col-prix="{ ligne }"><b>{{ euros(ligne.prix_centimes) }}</b></template>
      <template #col-stock="{ ligne }">
        <b class="text-[15px]">{{ ligne.stock_disponible }}</b>
      </template>
      <template #col-etat="{ ligne }">
        <Tag :value="etat(ligne).libelle" :severity="etat(ligne).ton" />
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter ce produit et son historique"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="consulter(ligne)"
        />
        <!-- UN SEUL bouton de stock : la rupture se déclare dans la popup,
             où elle a sa place, plutôt que par un second bouton qui ouvre
             exactement la même chose. -->
        <ActionLigne
          titre="Corriger le stock"
          :icone="Boxes"
          :desactive="occupe"
          @click="ouvrirAjustement(ligne)"
        />
        <ActionLigne
          v-if="estVendeur"
          titre="Modifier la fiche produit"
          :icone="Pencil"
          :vers="{ name: 'vendeur-produit', params: { id: ligne.id } }"
        />
        <ActionLigne
          v-if="estVendeur && ligne.est_visible"
          titre="Retirer de la vente"
          :icone="EyeOff"
          ton="danger"
          :desactive="occupe"
          @click="aRetirer = ligne"
        />
        <ActionLigne
          v-else-if="estVendeur"
          titre="Remettre en vente"
          :icone="RotateCcw"
          ton="accent"
          :desactive="occupe"
          @click="agir(vendeur.remettreEnVente(ligne.id),
                       `« ${ligne.nom} » est de nouveau en vente.`)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Package :size="30" class="text-trait" />
          <b class="vide-titre">
            {{
              !produits.length ? 'Votre catalogue est vide'
              : onglet === 'stock' ? 'Rien à réapprovisionner'
              : onglet === 'ruptures' ? 'Aucune rupture — tout est disponible'
              : onglet === 'retires' ? 'Aucun produit retiré de la vente'
              : 'Aucun produit ne correspond'
            }}
          </b>
          <p class="vide-texte">
            {{
              !produits.length
                ? 'Ajoutez votre premier produit : un nom, un prix, une photo. Il apparaîtra aussitôt au catalogue de vos clients.'
                : 'Tout est au-dessus du seuil que vous avez fixé.'
            }}
          </p>
          <RouterLink
            v-if="!produits.length && estVendeur"
            :to="{ name: 'vendeur-nouveau' }"
            class="bouton-accent mt-4"
          >
            <Plus :size="15" /> Ajouter un produit
          </RouterLink>
        </div>
      </template>
    </Liste>

    <!-- Le produit consulté, avec son historique : dans le volet -->
    <FicheContextuelle
      v-if="selection"
      :titre="selection.nom"
      :apercu-ouvert="apercu"
      @fermer-apercu="apercu = false"
    >
      <img
        v-if="selection.image"
        :src="selection.image"
        :alt="selection.nom"
        class="aspect-4/3 w-full rounded-lg object-cover"
      />
      <dl class="mt-3 flex flex-col gap-2 text-[12px]">
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Prix</dt>
          <dd class="font-semibold">{{ euros(selection.prix_centimes) }}</dd>
        </div>
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
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Photos</dt>
          <dd class="font-semibold">{{ selection.nombre_photos }}</dd>
        </div>
      </dl>

      <div class="mt-3 flex flex-col gap-2">
        <Button label="Corriger le stock" size="small" @click="ouvrirAjustement(selection)" />
        <RouterLink
          v-if="estVendeur"
          :to="{ name: 'vendeur-produit', params: { id: selection.id } }"
          class="bouton-neutre w-full"
        >
          <Pencil :size="14" /> Modifier la fiche
        </RouterLink>
      </div>

      <b class="mt-4 block text-[11px] font-bold tracking-wider text-encre-douce uppercase">
        Derniers mouvements
      </b>
      <div v-if="!mouvementsProduit.length" class="vide !py-6">
        <b class="vide-titre">Aucun mouvement</b>
      </div>
      <ul v-else class="mt-2 flex flex-col gap-1.5">
        <li
          v-for="mouvement in mouvementsProduit.slice(0, 8)"
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
          <!-- QUI a fait le mouvement : c'est ce qui manquait pour que le
               vendeur et son personnel cessent de se marcher dessus (D-80). -->
          <span class="mt-0.5 block text-encre-douce">
            {{ quand(mouvement.date_mouvement) }} · par {{ mouvement.auteur }}
            <template v-if="mouvement.motif"> · {{ mouvement.motif }}</template>
          </span>
        </li>
      </ul>
    </FicheContextuelle>

    <!-- La popup de correction : « Nouvelle quantité » et un motif (D-49) -->
    <Popup
      v-if="ajuste"
      titre="Corriger le stock"
      :explication="`« ${ajuste.nom} » — le système en compte ${ajuste.stock_disponible}. Saisissez la quantité réellement présente : l'écart est calculé et tracé dans l'historique, jamais une modification silencieuse.`"
      @fermer="ajuste = null"
    >
      <div class="flex flex-col gap-3.5">
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Nouvelle quantité</span>
          <InputNumber
            v-model="saisie.quantite"
            :min="0"
            show-buttons
            button-layout="horizontal"
            size="small"
            input-class="text-center"
          />
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
          <Select
            v-model="saisie.type"
            :options="TYPES"
            option-label="libelle"
            option-value="valeur"
            size="small"
          />
        </label>

        <label class="flex flex-col gap-1.5">
          <span class="etiquette">
            Motif
            <span v-if="typeCourant.motifRequis" class="text-alerte">obligatoire</span>
          </span>
          <Select
            v-model="saisie.motif"
            :options="MOTIFS"
            editable
            size="small"
            placeholder="Casse, inventaire…"
          />
        </label>

        <p v-if="erreurPopup" class="bandeau bandeau-erreur">{{ erreurPopup }}</p>
      </div>

      <template #actions>
        <Button
          label="Mettre en rupture"
          severity="secondary"
          outlined
          size="small"
          class="mr-auto"
          @click="saisie.quantite = 0;
                  saisie.motif = saisie.motif || 'Rupture constatée en boutique'"
        >
          <template #icon><PackageX :size="14" /></template>
        </Button>
        <Button label="Annuler" severity="secondary" outlined size="small"
                @click="ajuste = null" />
        <Button
          label="Confirmer"
          size="small"
          :disabled="occupe || (typeCourant.motifRequis && !saisie.motif.trim())"
          @click="appliquer"
        >
          <template #icon><Check :size="14" /></template>
        </Button>
      </template>
    </Popup>

    <!-- Retirer de la vente : réversible, mais ça disparaît du catalogue -->
    <Popup
      v-if="aRetirer"
      titre="Retirer ce produit de la vente ?"
      :explication="`« ${aRetirer.nom} » disparaîtra du catalogue public. Rien n'est supprimé : les commandes passées le référencent toujours, et vous pouvez le remettre en vente à tout moment depuis l'onglet « Retirés ».`"
      @fermer="aRetirer = null"
    >
      <template #actions>
        <Button label="Annuler" severity="secondary" outlined size="small"
                @click="aRetirer = null" />
        <Button
          label="Retirer de la vente"
          severity="danger"
          size="small"
          :disabled="occupe"
          @click="agir(vendeur.masquer(aRetirer.id),
                       `« ${aRetirer.nom} » est retiré de la vente.`); aRetirer = null"
        />
      </template>
    </Popup>
  </div>
</template>
