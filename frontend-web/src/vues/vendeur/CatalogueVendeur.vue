<script setup lang="ts">
// Le catalogue du vendeur : l'écran où il passe ses journées.
//
// Il passe par la liste commune du projet — recherche, tri, pagination, état
// vide rédigé — et ses boutons-symboles font vraiment leur travail : consulter
// la fiche publique, modifier, déclarer une rupture, retirer de la vente et
// **remettre en vente**, ce qui manquait.
import {
  Eye, EyeOff, ImageOff, Package, PackageX, Pencil, Plus, RotateCcw,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { useNotification } from '../../notifications'
import { vendeur, type ProduitCatalogue } from '../../api/vendeur'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import Volet from '../../composants/Volet.vue'

type Ligne = ProduitCatalogue & { [cle: string]: unknown }

const notifier = useNotification()
const produits = ref<Ligne[]>([])
const chargement = ref(true)
const onglet = ref('en-vente')
const selection = ref<Ligne | null>(null)

const enRupture = ref<Ligne | null>(null)
const motifRupture = ref('Rupture constatée en boutique')
const occupe = ref(false)

async function charger() {
  chargement.value = true
  try {
    produits.value = (await vendeur.mesProduits()) as Ligne[]
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const enVente = computed(() => produits.value.filter((p) => p.est_visible))
const retires = computed(() => produits.value.filter((p) => !p.est_visible))
const ruptures = computed(() => enVente.value.filter((p) => p.est_en_rupture))

const visibles = computed(() =>
  onglet.value === 'retires' ? retires.value
    : onglet.value === 'ruptures' ? ruptures.value
      : enVente.value,
)

const colonnes: Colonne<Ligne>[] = [
  { cle: 'produit', titre: 'Produit', champTri: 'nom' },
  { cle: 'prix', titre: 'Prix', largeur: 100, aligne: 'droite',
    champTri: 'prix_centimes' },
  { cle: 'stock', titre: 'Stock', largeur: 90, aligne: 'droite', masquerSous: 'sm',
    champTri: 'stock_disponible' },
  { cle: 'etat', titre: 'État', largeur: 104, aligne: 'centre' },
]

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const etat = (produit: Ligne) =>
  !produit.est_visible ? { classe: 'badge-neutre', libelle: 'retiré' }
    : produit.est_en_rupture ? { classe: 'badge-erreur', libelle: 'rupture' }
      : produit.stock_disponible <= produit.seuil_alerte
        ? { classe: 'badge-attente', libelle: 'stock bas' }
        : { classe: 'badge-ok', libelle: 'en vente' }

async function agir(action: Promise<unknown>, reussite?: string) {
  occupe.value = true
  try {
    await action
    await charger()
    if (selection.value) {
      selection.value = produits.value.find((p) => p.id === selection.value!.id) ?? null
    }
    if (reussite) notifier.succes(reussite)
  } catch (echec) {
    notifier.echec(echec instanceof EchecApi ? echec.erreur.message : "L'action a échoué.")
  } finally {
    occupe.value = false
  }
}

async function declarerRupture() {
  if (!enRupture.value) return
  const produit = enRupture.value
  enRupture.value = null
  await agir(
    vendeur.stock.definir(produit.id, 0, 'AJUSTEMENT', motifRupture.value),
    `« ${produit.nom} » est declare en rupture.`,
  )
  motifRupture.value = 'Rupture constatée en boutique'
}
</script>

<template>
  <div class="mx-auto max-w-[1100px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'en-vente', libelle: 'En vente', compteur: enVente.length },
        { cle: 'ruptures', libelle: 'En rupture', compteur: ruptures.length },
        { cle: 'retires', libelle: 'Retirés de la vente', compteur: retires.length },
      ]"
    />

    <Liste
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(produit) => produit.id"
      :chargement="chargement"
      :recherche="(p) => `${p.nom} ${p.categorie?.nom ?? ''}`"
      :active="(p) => selection?.id === p.id"
      @ligne-cliquee="(p) => (selection = selection?.id === p.id ? null : p)"
      placeholder="Nom de produit, catégorie…"
    >
      <template #outils>
        <RouterLink :to="{ name: 'vendeur-nouveau' }" class="bouton-accent !py-2">
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
              <template v-if="!ligne.nombre_photos"> · aucune photo</template>
            </span>
          </span>
        </span>
      </template>

      <template #col-prix="{ ligne }">
        <b>{{ euros(ligne.prix_centimes) }}</b>
      </template>
      <template #col-stock="{ ligne }">
        <span class="text-encre-douce">{{ ligne.stock_disponible }}</span>
      </template>
      <template #col-etat="{ ligne }">
        <span class="badge" :class="etat(ligne).classe">{{ etat(ligne).libelle }}</span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter ce produit"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
        <ActionLigne
          titre="Modifier ce produit"
          :icone="Pencil"
          :vers="{ name: 'vendeur-produit', params: { id: ligne.id } }"
        />
        <ActionLigne
          v-if="ligne.est_visible && !ligne.est_en_rupture"
          titre="Déclarer une rupture de stock"
          :icone="PackageX"
          :desactive="occupe"
          @click="enRupture = ligne"
        />
        <ActionLigne
          v-if="ligne.est_visible"
          titre="Retirer de la vente"
          :icone="EyeOff"
          ton="danger"
          :desactive="occupe"
          @click="agir(vendeur.masquer(ligne.id), `« ${ligne.nom} » est retire de la vente.`)"
        />
        <ActionLigne
          v-else
          titre="Remettre en vente"
          :icone="RotateCcw"
          ton="accent"
          :desactive="occupe"
          @click="agir(vendeur.remettreEnVente(ligne.id), `« ${ligne.nom} » est de nouveau en vente.`)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <span
            v-if="!produits.length"
            class="flex h-14 w-14 items-center justify-center rounded-lg"
            :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
          >
            <Package :size="24" />
          </span>
          <Package v-else :size="30" class="text-trait" />
          <b class="vide-titre">
            {{
              !produits.length ? 'Votre catalogue est vide'
              : onglet === 'ruptures' ? 'Aucune rupture — tout est disponible'
              : onglet === 'retires' ? 'Aucun produit retiré de la vente'
              : 'Aucun produit ne correspond'
            }}
          </b>
          <p v-if="!produits.length" class="vide-texte">
            Ajoutez votre premier produit : un nom, un prix, une photo. Il apparaîtra
            aussitôt au catalogue de vos clients.
          </p>
          <RouterLink
            v-if="!produits.length"
            :to="{ name: 'vendeur-nouveau' }"
            class="bouton-accent mt-4"
          >
            <Plus :size="15" /> Ajouter un produit
          </RouterLink>
        </div>
      </template>
    </Liste>

    <!-- Le produit sélectionné, dans le volet -->
    <Volet v-if="selection" :titre="selection.nom">
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
          <dt class="text-encre-douce">Stock</dt>
          <dd class="font-semibold">{{ selection.stock_disponible }}</dd>
        </div>
        <div v-if="selection.stock_reserve" class="flex justify-between gap-2">
          <dt class="text-encre-douce">Réservé par un paiement</dt>
          <dd class="font-semibold">{{ selection.stock_reserve }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Seuil d'alerte</dt>
          <dd class="font-semibold">{{ selection.seuil_alerte }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Photos</dt>
          <dd class="font-semibold">{{ selection.nombre_photos }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">État</dt>
          <dd><span class="badge" :class="etat(selection).classe">{{ etat(selection).libelle }}</span></dd>
        </div>
      </dl>

      <div class="mt-4 flex flex-col gap-2">
        <RouterLink
          :to="{ name: 'vendeur-produit', params: { id: selection.id } }"
          class="bouton-accent w-full"
        >
          <Pencil :size="15" /> Modifier la fiche
        </RouterLink>
        <RouterLink
          v-if="selection.est_visible"
          :to="{ name: 'produit', params: { id: selection.id } }"
          class="bouton-neutre w-full"
        >
          <Eye :size="15" /> Voir la fiche publique
        </RouterLink>
      </div>
    </Volet>

    <!-- La popup de la maquette : une action courte, un motif obligatoire -->
    <Popup
      v-if="enRupture"
      titre="Déclarer une rupture de stock"
      :explication="`Le stock de « ${enRupture.nom} » passe à zéro. Le produit reste au catalogue,
                     son bouton d'achat est gelé et vos clients peuvent demander à être prévenus
                     de son retour. Le mouvement est tracé dans l'historique.`"
      @fermer="enRupture = null"
    >
      <label class="flex flex-col gap-1.5">
        <span class="etiquette">Motif</span>
        <input v-model="motifRupture" class="champ-clair" required />
      </label>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="enRupture = null">
          Annuler
        </button>
        <button
          type="button"
          class="bouton-accent !py-2"
          :disabled="occupe || !motifRupture.trim()"
          @click="declarerRupture"
        >
          <PackageX :size="15" />
          Déclarer la rupture
        </button>
      </template>
    </Popup>
  </div>
</template>
