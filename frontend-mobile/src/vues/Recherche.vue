<script setup lang="ts">
// Le catalogue mobile.
//
// Grille verticale : c'est de la recherche active, on veut tout voir (D-69).
// Le bouton d'ajout est **visible en permanence** et large d'au moins 44 px —
// il n'y a pas de survol sur un téléphone pour révéler une action, et le pouce
// doit le retrouver sans réfléchir d'une carte à l'autre.
//
// **Refait au bloc O-1** : *« pas dense, pas assez de symboles, pas de popups,
// pas de panneau qui surgit en bas »*, et *« tout doit être caché les uns
// derrière les autres »*.
//
// Les trois filtres étaient à plat, en haut, en permanence : un tiers de la
// hauteur d'un téléphone consommé par des boutons qu'on touche une fois par
// visite. Et ils n'exposaient que le service — ni catégorie, ni boutique, ni
// tri, alors que le serveur rend tout cela dans ses facettes (D-35).
//
// Ils partent dans une **feuille du bas**, et l'en-tête se réduit à une ligne :
// la recherche, et un bouton qui dit combien de filtres sont actifs. Ce qui est
// gagné va aux produits, qui sont ce qu'on est venu voir.
import {
  IonBadge, IonButton, IonIcon, IonModal, IonSearchbar, IonSegment, IonSegmentButton,
  IonSpinner,
} from '@ionic/vue'
import type { Produit } from '@partage/types'
import { bagHandleOutline, closeOutline, optionsOutline } from 'ionicons/icons'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import VignetteProduit from '@/composants/VignetteProduit.vue'
import { usePanier } from '@/magasins/panier'
import { useSession } from '@/magasins/session'
import { useRafraichissement } from '@/rafraichissement'

type Facette = { slug: string; nom: string; univers: string; nombre: number }
type Univers = { nom: string; nombre: number; categories: Facette[] }
type FacetteBoutique = { id: number; nom: string; type_service: string; nombre: number }

const session = useSession()
const panier = usePanier()
const routeur = useRouter()

const route = useRoute()

const produits = ref<Produit[]>([])
const recherche = ref('')
const service = ref('')
// Les filtres arrivent aussi de l'accueil : taper une pastille de catégorie ou
// une boutique doit mener ICI, déjà filtré. Un lien qui ouvre une liste non
// filtrée oblige à refaire le geste (O-8).
const categorie = ref(String(route.query.categorie ?? ''))
const boutique = ref(String(route.query.boutique ?? ''))
const dispoSeule = ref(false)
const chargement = ref(false)
const panneau = ref(false)

const univers = ref<Univers[]>([])
const boutiques = ref<FacetteBoutique[]>([])

/** Combien de filtres sont actifs : le bouton le dit, sinon on ne sait plus
 *  pourquoi la liste est courte. */
/** Les catégories à plat, pour retrouver le nom d'une catégorie retenue. */
const categories = computed<Facette[]>(() =>
  univers.value.flatMap((groupe) => groupe.categories),
)

const actifs = computed(() =>
  [service.value, categorie.value, boutique.value, dispoSeule.value ? '1' : '']
    .filter(Boolean).length,
)

async function charger() {
  chargement.value = true
  try {
    const parametres = new URLSearchParams()
    if (recherche.value.trim()) parametres.set('recherche', recherche.value.trim())
    if (service.value) parametres.set('type_service', service.value)
    if (categorie.value) parametres.set('categorie', categorie.value)
    if (boutique.value) parametres.set('boutique', boutique.value)
    if (dispoSeule.value) parametres.set('disponible', '1')
    const suffixe = parametres.toString() ? `?${parametres}` : ''

    // `appelerComplet` rend le corps ENTIER — `data` et `meta`. Les facettes
    // voyagent dans `meta` (D-35), et deux appels pour la même adresse
    // doubleraient le travail du serveur à chaque frappe.
    //
    // Elles décrivent ce qui reste après le filtrage géographique : les
    // catégories proposées ne sont donc jamais vides, et un filtre ne mène
    // jamais à « aucun résultat ».
    const reponse = await session.client.appelerComplet<{
      data: Produit[]
      meta?: { facettes?: { univers?: Univers[]; boutiques?: FacetteBoutique[] } }
    }>(`/produits${suffixe}`)
    produits.value = reponse.data
    univers.value = reponse.meta?.facettes?.univers ?? []
    boutiques.value = reponse.meta?.facettes?.boutiques ?? []
  } finally {
    chargement.value = false
  }
}

function reinitialiser() {
  service.value = ''
  categorie.value = ''
  boutique.value = ''
  dispoSeule.value = false
}

useRafraichissement(charger)
// On attend que la frappe se calme : une requête par lettre saturerait le
// réseau d'un téléphone en 4G.
let minuteur: ReturnType<typeof setTimeout>
watch([recherche, service, categorie, boutique, dispoSeule], () => {
  clearTimeout(minuteur)
  minuteur = setTimeout(charger, 300)
})

const nombre = computed(() => panier.contenu.nombre_articles)
</script>

<template>
  <Ecran titre="Catalogue" sous-titre="Espace client" :rafraichir="charger">
    <template #actions>
      <IonButton fill="clear" @click="routeur.push('/panier')">
        <IonIcon slot="icon-only" :icon="bagHandleOutline" style="color: #fff" />
        <IonBadge v-if="nombre" color="light" class="pastille">{{ nombre }}</IonBadge>
      </IonButton>
    </template>

    <!-- Une seule ligne en haut : la recherche, et l'accès aux filtres. Ce
         qui est gagné va aux produits, qui sont ce qu'on vient voir (O-1). -->
    <div class="barre">
      <IonSearchbar
        v-model="recherche"
        placeholder="Un burger, un casque…"
        :debounce="0"
        class="recherche"
      />
      <button type="button" class="bouton-filtres" :class="actifs ? 'actif' : ''"
              @click="panneau = true">
        <IonIcon :icon="optionsOutline" />
        <span v-if="actifs" class="compteur">{{ actifs }}</span>
      </button>
    </div>

    <!-- Les filtres retenus, en pastilles : sans elles, on ne sait plus
         pourquoi la liste est si courte. Chacune se retire d'un appui. -->
    <div v-if="actifs" class="retenus">
      <button v-if="service" type="button" class="retenu" @click="service = ''">
        {{ service === 'EXPRESS' ? 'Express' : 'Standard' }} <IonIcon :icon="closeOutline" />
      </button>
      <button v-if="categorie" type="button" class="retenu" @click="categorie = ''">
        {{ categories.find((c) => c.slug === categorie)?.nom ?? categorie }}
        <IonIcon :icon="closeOutline" />
      </button>
      <button v-if="boutique" type="button" class="retenu" @click="boutique = ''">
        {{ boutiques.find((b) => String(b.id) === boutique)?.nom ?? 'Boutique' }}
        <IonIcon :icon="closeOutline" />
      </button>
      <button v-if="dispoSeule" type="button" class="retenu" @click="dispoSeule = false">
        En stock <IonIcon :icon="closeOutline" />
      </button>
    </div>

    <div v-if="chargement" class="chargement"><IonSpinner name="dots" /></div>

    <div v-else class="grille">
      <!-- La MEME vignette que l'accueil : un produit ne doit pas avoir l'air
           différent selon l'écran où on le croise (O-1). -->
      <VignetteProduit
        v-for="produit in produits"
        :key="produit.id"
        :produit="produit"
        forme="tuile"
      />
    </div>

    <!-- Le panneau qui surgit du bas (O-1). Les filtres du serveur, tous :
         catégories et boutiques viennent des facettes, donc ils ne proposent
         jamais un choix qui ne rendrait rien (D-35). -->
    <IonModal :is-open="panneau" :initial-breakpoint="0.75" :breakpoints="[0, 0.75, 1]"
              @did-dismiss="panneau = false">
      <div class="feuille">
        <span class="poignee-titre">
          <b class="titre">Filtrer</b>
          <button v-if="actifs" type="button" class="lien" @click="reinitialiser">
            Tout effacer
          </button>
        </span>

        <span class="etiquette">Mode de livraison</span>
        <IonSegment v-model="service">
          <IonSegmentButton value="">Tout</IonSegmentButton>
          <IonSegmentButton value="EXPRESS">Express</IonSegmentButton>
          <IonSegmentButton value="STANDARD">Standard</IonSegmentButton>
        </IonSegment>

        <!-- Groupées par univers : sept catégories à plat ne disent rien,
             « Restauration » et « High-tech » se lisent d'un coup d'œil. -->
        <template v-for="groupe in univers" :key="groupe.nom">
          <span class="etiquette">{{ groupe.nom }} · {{ groupe.nombre }}</span>
          <div class="puces">
            <button
              v-for="facette in groupe.categories"
              :key="facette.slug"
              type="button"
              class="puce"
              :class="categorie === facette.slug ? 'active' : ''"
              @click="categorie = categorie === facette.slug ? '' : facette.slug"
            >
              {{ facette.nom }} <span class="nombre">{{ facette.nombre }}</span>
            </button>
          </div>
        </template>

        <span class="etiquette">Boutique</span>
        <div class="puces">
          <button
            v-for="facette in boutiques"
            :key="facette.id"
            type="button"
            class="puce"
            :class="boutique === String(facette.id) ? 'active' : ''"
            @click="boutique = boutique === String(facette.id) ? '' : String(facette.id)"
          >
            {{ facette.nom }} <span class="nombre">{{ facette.nombre }}</span>
          </button>
        </div>

        <label class="bascule">
          <input v-model="dispoSeule" type="checkbox" />
          <span>
            <b>Seulement ce qui est en stock</b>
            Un produit en rupture reste visible au catalogue, avec son bouton d'alerte.
          </span>
        </label>

        <IonButton expand="block" @click="panneau = false">
          Voir {{ produits.length }} résultat{{ produits.length > 1 ? 's' : '' }}
        </IonButton>
      </div>
    </IonModal>

    <div v-if="!chargement && !produits.length" class="etat-vide">
      <b>Aucun produit ne livre chez vous</b>
      <span>
        Les boutiques Express trop lointaines n'apparaissent jamais ici : mieux vaut un
        catalogue court qu'une promesse intenable.
      </span>
    </div>
  </Ecran>
</template>

<style scoped>
.pastille {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 9px;
}
.barre {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.recherche {
  --background: #fff;
  --border-radius: 12px;
  padding: 0;
  flex: 1;
}
.bouton-filtres {
  position: relative;
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  border: 1px solid var(--rd-trait);
  border-radius: 12px;
  background: #fff;
  color: var(--ion-text-color);
  font-size: 19px;
}
.bouton-filtres.actif {
  border-color: var(--accent);
  color: var(--accent);
}
.bouton-filtres .compteur {
  position: absolute;
  top: -5px;
  right: -5px;
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  line-height: 17px;
}
.retenus {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.retenu {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border: 1px solid var(--accent);
  border-radius: 999px;
  background: var(--accent-doux);
  color: var(--accent);
  font-size: 11.5px;
  font-weight: 600;
}
.chargement {
  display: grid;
  place-items: center;
  padding: 40px;
}
.grille {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.feuille {
  padding: 18px 16px calc(20px + var(--rd-marge-basse, 12px));
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}
.poignee-titre {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}
.feuille .titre {
  font-size: 17px;
}
.lien {
  border: 0;
  background: none;
  padding: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
}
.etiquette {
  margin-top: 6px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--rd-encre-douce);
}
.puces {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.puce {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 12px;
  border: 1px solid var(--rd-trait);
  border-radius: 999px;
  background: #fff;
  font-size: 12px;
}
.puce.active {
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 700;
}
.puce .nombre {
  font-size: 10.5px;
  color: var(--rd-encre-douce);
}
.bascule {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-top: 1px solid var(--rd-trait-doux);
  font-size: 11.5px;
  line-height: 1.55;
  color: var(--rd-encre-douce);
}
.bascule b {
  display: block;
  font-size: 13px;
  color: var(--ion-text-color);
}
</style>
