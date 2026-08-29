<script setup lang="ts">
// L'ecran de stock.
//
// Il presentait l'ajustement dans un formulaire deplie sous la ligne, avec
// une quantite a saisir sous la forme « +5 / -2 » et un historique tasse
// dessous. Deux erreurs :
//
//   · la maquette prevoit une POPUP pour cette action, avec « Nouvelle
//     quantite » et un motif a choisir. C'est ainsi qu'on fait un inventaire :
//     on compte ce qu'il y a sur l'etagere, on ne calcule pas de tete l'ecart
//     avec ce que l'ecran affiche ;
//   · l'historique n'a rien a faire coince entre deux lignes de liste. Il
//     part dans son propre onglet, en tableau, ou il se lit.
import {
  AlertTriangle, ArrowDownRight, ArrowUpRight, Boxes, Check, History, PackageX, Search,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { vendeur, type Mouvement, type ProduitCatalogue } from '../../api/vendeur'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import Squelette from '../../composants/Squelette.vue'

const produits = ref<ProduitCatalogue[]>([])
const chargement = ref(true)
const onglet = ref('tout')
const filtre = ref('')

const ajuste = ref<ProduitCatalogue | null>(null)
const saisie = ref({ quantite: '0', type: 'AJUSTEMENT', motif: '' })
const erreur = ref('')
const message = ref('')
const occupe = ref(false)

const journal = ref<(Mouvement & { produit: string })[]>([])
const journalCharge = ref(false)

// Les motifs de la maquette. Une liste fermee plutot qu'un champ libre : six
// mois plus tard, « erreur » et « erreur de saisie » ne se regroupent plus.
const MOTIFS = [
  'Inventaire',
  'Casse',
  'Erreur de saisie',
  'Perime',
  'Vol ou perte',
  'Rupture constatee en boutique',
]

const TYPES = [
  { valeur: 'AJUSTEMENT', libelle: 'Ajustement manuel', motifRequis: true },
  { valeur: 'REAPPRO', libelle: 'Reapprovisionnement', motifRequis: false },
  { valeur: 'RETOUR', libelle: 'Retour client', motifRequis: false },
]

async function charger() {
  chargement.value = true
  try {
    produits.value = await vendeur.mesProduits()
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const aReapprovisionner = computed(() =>
  produits.value.filter(
    (p) => p.est_visible && p.stock_disponible <= p.seuil_alerte,
  ),
)
const ruptures = computed(() => produits.value.filter((p) => p.est_visible && p.est_en_rupture))

const visibles = computed(() => {
  const base =
    onglet.value === 'manquants' ? aReapprovisionner.value
      : onglet.value === 'ruptures' ? ruptures.value
        : produits.value
  const recherche = filtre.value.trim().toLowerCase()
  return recherche ? base.filter((p) => p.nom.toLowerCase().includes(recherche)) : base
})

const typeCourant = computed(
  () => TYPES.find((type) => type.valeur === saisie.value.type) ?? TYPES[0],
)
const ecart = computed(
  () => Number(saisie.value.quantite || 0) - (ajuste.value?.stock_disponible ?? 0),
)

function ouvrir(produit: ProduitCatalogue) {
  ajuste.value = produit
  saisie.value = { quantite: String(produit.stock_disponible), type: 'AJUSTEMENT', motif: '' }
  erreur.value = ''
  message.value = ''
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
    message.value = `« ${ajuste.value.nom} » : stock a ${resultat.stock_disponible}.`
    ajuste.value = null
    journalCharge.value = false
    await charger()
    if (onglet.value === 'journal') await chargerJournal()
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Ajustement refuse.'
  } finally {
    occupe.value = false
  }
}

/** Le journal complet : tous les mouvements de la boutique, du plus recent
 *  au plus ancien. C'est ce qu'on ouvre quand un chiffre ne tombe pas juste. */
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
    .slice(0, 120)
  journalCharge.value = true
}

function changerOnglet(valeur: string) {
  onglet.value = valeur
  if (valeur === 'journal') chargerJournal()
}

const quand = (date: string) =>
  new Date(date).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
</script>

<template>
  <div class="mx-auto max-w-[1040px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      :model-value="onglet"
      :onglets="[
        { cle: 'tout', libelle: 'Tous les produits', compteur: produits.length },
        { cle: 'manquants', libelle: 'A reapprovisionner', compteur: aReapprovisionner.length },
        { cle: 'ruptures', libelle: 'En rupture', compteur: ruptures.length },
        { cle: 'journal', libelle: 'Historique' },
      ]"
      @update:model-value="changerOnglet"
    />

    <p v-if="message" class="bandeau bandeau-info mb-3">
      <Check :size="15" class="mt-px shrink-0" />
      {{ message }}
    </p>

    <!-- ── L'historique, dans son propre onglet ─────────────────────── -->
    <div v-if="onglet === 'journal'" class="carte">
      <h3 class="carte-titre">
        <span class="flex items-center gap-2"><History :size="15" /> Mouvements de stock</span>
        <span class="text-[11px] font-semibold text-encre-douce">
          les 120 derniers, toutes references confondues
        </span>
      </h3>

      <div v-if="!journalCharge" class="p-4">
        <Squelette v-for="n in 5" :key="n" hauteur="34px" />
      </div>

      <div v-else-if="!journal.length" class="vide">
        <History :size="30" class="text-trait" />
        <b class="vide-titre">Aucun mouvement enregistre</b>
        <p class="vide-texte">
          Chaque reapprovisionnement, vente ou correction apparaitra ici, avec son motif
          et son auteur.
        </p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-[12.5px]">
          <thead>
            <tr class="border-b border-trait-doux text-left text-[10.5px] font-bold
                       tracking-wider text-encre-douce uppercase">
              <th class="px-4 py-2.5">Date</th>
              <th class="px-4 py-2.5">Produit</th>
              <th class="px-4 py-2.5">Type</th>
              <th class="px-4 py-2.5 text-right">Quantite</th>
              <th class="px-4 py-2.5 text-right">Apres</th>
              <th class="px-4 py-2.5">Motif</th>
              <th class="px-4 py-2.5">Par</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="mouvement in journal"
              :key="mouvement.id"
              class="border-b border-trait-doux last:border-0 hover:bg-atelier"
            >
              <td class="px-4 py-2.5 whitespace-nowrap text-encre-douce">
                {{ quand(mouvement.date_mouvement) }}
              </td>
              <td class="px-4 py-2.5 font-semibold">{{ mouvement.produit }}</td>
              <td class="px-4 py-2.5">{{ mouvement.libelle_type }}</td>
              <td
                class="px-4 py-2.5 text-right font-bold whitespace-nowrap"
                :class="mouvement.quantite > 0 ? 'text-succes' : 'text-alerte'"
              >
                <component
                  :is="mouvement.quantite > 0 ? ArrowUpRight : ArrowDownRight"
                  :size="12"
                  class="inline"
                />
                {{ mouvement.quantite > 0 ? '+' : '' }}{{ mouvement.quantite }}
              </td>
              <td class="px-4 py-2.5 text-right">{{ mouvement.stock_apres }}</td>
              <td class="px-4 py-2.5 text-encre-douce">{{ mouvement.motif || '—' }}</td>
              <td class="px-4 py-2.5 text-encre-douce">{{ mouvement.auteur }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Les listes de produits ───────────────────────────────────── -->
    <template v-else>
      <div class="mb-4 flex items-center gap-2 rounded-full bg-papier px-3.5 py-2 ring-1
                  ring-trait">
        <Search :size="14" class="text-encre-douce" />
        <input
          v-model="filtre"
          type="search"
          placeholder="Filtrer par nom…"
          class="w-full bg-transparent text-[12.5px] focus:outline-none"
        />
      </div>

      <p v-if="aReapprovisionner.length && onglet === 'tout'" class="bandeau mb-3">
        <AlertTriangle :size="15" class="mt-px shrink-0" />
        {{ aReapprovisionner.length }} produit(s) sous le seuil d alerte — pensez a
        reapprovisionner ou a corriger le stock systeme.
      </p>

      <div v-if="chargement" class="flex flex-col gap-2">
        <Squelette v-for="n in 5" :key="n" hauteur="54px" />
      </div>

      <div v-else-if="!visibles.length" class="carte">
        <div class="vide">
          <Boxes :size="30" class="text-trait" />
          <b class="vide-titre">
            {{
              onglet === 'manquants' ? 'Rien a reapprovisionner'
              : onglet === 'ruptures' ? 'Aucune rupture en cours'
              : 'Aucun produit'
            }}
          </b>
          <p class="vide-texte">
            {{
              onglet === 'tout'
                ? 'Les produits de votre boutique apparaitront ici avec leur stock.'
                : 'Tout est au-dessus du seuil que vous avez fixe.'
            }}
          </p>
        </div>
      </div>

      <div v-else class="carte">
        <div v-for="produit in visibles" :key="produit.id" class="ligne">
          <img
            v-if="produit.image"
            :src="produit.image"
            :alt="produit.nom"
            class="h-10 w-10 shrink-0 rounded-lg object-cover"
          />
          <span class="min-w-0 flex-1">
            <b class="block truncate">{{ produit.nom }}</b>
            <span class="text-[11.2px] text-encre-douce">
              seuil d alerte a {{ produit.seuil_alerte }}
              <template v-if="produit.stock_reserve">
                · {{ produit.stock_reserve }} reserve(s) par un paiement en cours
              </template>
              <template v-if="!produit.est_visible"> · retire de la vente</template>
            </span>
          </span>

          <span class="w-16 shrink-0 text-right text-[16px] font-extrabold">
            {{ produit.stock_disponible }}
          </span>

          <span
            class="badge w-[92px] shrink-0 justify-center"
            :class="
              produit.est_en_rupture ? 'badge-erreur'
              : produit.stock_disponible <= produit.seuil_alerte ? 'badge-attente'
              : 'badge-ok'
            "
          >
            {{
              produit.est_en_rupture ? 'rupture'
              : produit.stock_disponible <= produit.seuil_alerte ? 'stock bas'
              : 'ok'
            }}
          </span>

          <button
            type="button"
            class="bouton-ligne"
            title="Corriger le stock"
            @click="ouvrir(produit)"
          >
            <Boxes :size="14" />
            <span class="sr-only">Corriger le stock de {{ produit.nom }}</span>
          </button>
        </div>
      </div>
    </template>

    <!-- ── La popup d'ajustement, telle que la maquette la decrit ───── -->
    <Popup
      v-if="ajuste"
      titre="Corriger le stock"
      :explication="`« ${ajuste.nom} » — le systeme en compte ${ajuste.stock_disponible}.
                     Saisissez la quantite reellement presente : l'ecart est calcule et
                     trace dans l'historique, jamais une modification silencieuse.`"
      @fermer="ajuste = null"
    >
      <form class="flex flex-col gap-3.5" @submit.prevent="appliquer">
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Nouvelle quantite</span>
          <input
            v-model="saisie.quantite"
            type="number"
            min="0"
            required
            class="champ-clair"
          />
          <span v-if="ecart !== 0" class="text-[11.5px] font-semibold"
                :class="ecart > 0 ? 'text-succes' : 'text-alerte'">
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
          class="bouton-neutre !py-2 mr-auto"
          title="Passer le stock a zero"
          @click="saisie.quantite = '0'; saisie.motif = saisie.motif || 'Rupture constatee'"
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
