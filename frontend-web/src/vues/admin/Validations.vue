<script setup lang="ts">
// L'écran qui débloque toute la plateforme : sans validation, un vendeur ne
// publie rien et un livreur ne livre rien (D-02).
//
// **Ta remarque, L-7** : *« validation : tu n'as pas pensé aux autres pour que
// cette partie soit synchronisée »*. C'était vrai — décider changeait une
// ligne en base et s'arrêtait là. Chaque décision émet maintenant un
// événement : elle laisse une trace au journal d'audit et **prévient la
// personne concernée** avec le motif (D-62).
//
// Un refus et une suspension exigent un motif : recevoir une décision sans
// savoir quoi corriger est le meilleur moyen de faire redéposer dix fois le
// même dossier.
import { Bike, Check, ShieldCheck, Store, Truck, X } from '@lucide/vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import { computed, onMounted, ref } from 'vue'

import { espaces } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import Volet from '../../composants/Volet.vue'
import { useNotification } from '../../notifications'

type Candidat = {
  id: number
  nom_boutique?: string
  type_activite?: string
  mode_livraison?: string
  vehicule?: string
  siret?: string
  description?: string
  utilisateur: { prenom: string; nom: string; email: string; date_inscription?: string }
  [cle: string]: unknown
}

const notifier = useNotification()
const vendeurs = ref<Candidat[]>([])
const livreurs = ref<Candidat[]>([])
const chargement = ref(true)
const occupe = ref(false)
const onglet = ref('vendeurs')
const selection = ref<Candidat | null>(null)

const decision = ref<{
  candidat: Candidat
  genre: 'vendeurs' | 'livreurs'
  action: 'valider' | 'refuser'
} | null>(null)
const motif = ref('')

async function charger() {
  chargement.value = true
  try {
    const donnees = await espaces.admin.validations()
    vendeurs.value = donnees.vendeurs as unknown as Candidat[]
    livreurs.value = donnees.livreurs as unknown as Candidat[]
    selection.value = vendeurs.value[0] ?? livreurs.value[0] ?? null
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

function ouvrir(candidat: Candidat, genre: 'vendeurs' | 'livreurs',
                action: 'valider' | 'refuser') {
  decision.value = { candidat, genre, action }
  motif.value = ''
}

async function trancher() {
  if (!decision.value) return
  const { candidat, genre, action } = decision.value
  occupe.value = true
  try {
    if (genre === 'vendeurs') {
      await espaces.admin.deciderVendeur(candidat.id, action, motif.value)
    } else {
      await espaces.admin.deciderLivreur(candidat.id, action, motif.value)
    }
    notifier.succes(
      action === 'valider'
        ? 'Compte validé : la personne est prévenue et peut travailler.'
        : 'Dossier refusé, avec votre motif.',
    )
    decision.value = null
    await charger()
  } catch (echec) {
    notifier.echec(echec)
  } finally {
    occupe.value = false
  }
}

const nom = (candidat: Candidat) =>
  `${candidat.utilisateur.prenom} ${candidat.utilisateur.nom}`.trim()

const colonnesVendeurs: Colonne<Candidat>[] = [
  { cle: 'boutique', titre: 'Boutique' },
  { cle: 'responsable', titre: 'Responsable', masquerSous: 'md' },
  { cle: 'service', titre: 'Service', largeur: 100, aligne: 'centre' },
]
const colonnesLivreurs: Colonne<Candidat>[] = [
  { cle: 'personne', titre: 'Candidat' },
  { cle: 'vehicule', titre: 'Véhicule', masquerSous: 'md' },
  { cle: 'mode', titre: 'Mode', largeur: 100, aligne: 'centre' },
]

const enAttente = computed(() => vendeurs.value.length + livreurs.value.length)
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <p v-if="!enAttente && !chargement" class="bandeau bandeau-info mb-4">
      <ShieldCheck :size="15" class="mt-px shrink-0" />
      Aucun dossier n'attend de décision. Les candidatures arrivent ici dès qu'un vendeur
      ou un livreur s'inscrit.
    </p>

    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'vendeurs', libelle: 'Boutiques', compteur: vendeurs.length },
        { cle: 'livreurs', libelle: 'Livreurs', compteur: livreurs.length },
      ]"
    />

    <Liste
      v-if="onglet === 'vendeurs'"
      :colonnes="colonnesVendeurs"
      :lignes="vendeurs"
      :cle-ligne="(candidat) => candidat.id"
      :chargement="chargement"
      :recherche="(c) => `${c.nom_boutique} ${nom(c)} ${c.utilisateur.email}`"
      :active="(c) => selection?.id === c.id"
      placeholder="Boutique, responsable, e-mail…"
      @ligne-cliquee="(c) => (selection = selection?.id === c.id ? null : c)"
    >
      <template #col-boutique="{ ligne }">
        <span class="flex min-w-0 items-center gap-3">
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
            :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
          >
            <Store :size="16" />
          </span>
          <span class="min-w-0">
            <b class="block truncate">{{ ligne.nom_boutique }}</b>
            <span class="text-[11.2px] text-encre-douce">{{ ligne.utilisateur.email }}</span>
          </span>
        </span>
      </template>
      <template #col-responsable="{ ligne }">
        <span class="min-w-0 truncate text-encre-douce">{{ nom(ligne) }}</span>
      </template>
      <template #col-service="{ ligne }">
        <Tag :value="(ligne.type_activite ?? '').toLowerCase()" severity="secondary" />
      </template>

      <template #actions="{ ligne }">
        <ActionLigne titre="Valider cette boutique" :icone="Check" ton="accent"
                     :desactive="occupe" @click="ouvrir(ligne, 'vendeurs', 'valider')" />
        <ActionLigne titre="Refuser ce dossier" :icone="X" ton="danger"
                     :desactive="occupe" @click="ouvrir(ligne, 'vendeurs', 'refuser')" />
      </template>

      <template #vide>
        <div class="vide">
          <Store :size="30" class="text-trait" />
          <b class="vide-titre">Aucune boutique en attente</b>
          <p class="vide-texte">
            Une boutique validée devient visible au catalogue ; refusée, elle reçoit votre
            motif et peut redéposer un dossier corrigé.
          </p>
        </div>
      </template>
    </Liste>

    <Liste
      v-else
      :colonnes="colonnesLivreurs"
      :lignes="livreurs"
      :cle-ligne="(candidat) => candidat.id"
      :chargement="chargement"
      :recherche="(c) => `${nom(c)} ${c.utilisateur.email} ${c.vehicule}`"
      :active="(c) => selection?.id === c.id"
      placeholder="Nom, e-mail, véhicule…"
      @ligne-cliquee="(c) => (selection = selection?.id === c.id ? null : c)"
    >
      <template #col-personne="{ ligne }">
        <span class="flex min-w-0 items-center gap-3">
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
            :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
          >
            <component :is="ligne.mode_livraison === 'EXPRESS' ? Bike : Truck" :size="16" />
          </span>
          <span class="min-w-0">
            <b class="block truncate">{{ nom(ligne) }}</b>
            <span class="text-[11.2px] text-encre-douce">{{ ligne.utilisateur.email }}</span>
          </span>
        </span>
      </template>
      <template #col-vehicule="{ ligne }">
        <span class="text-encre-douce">{{ ligne.vehicule }}</span>
      </template>
      <template #col-mode="{ ligne }">
        <Tag :value="(ligne.mode_livraison ?? '').toLowerCase()" severity="secondary" />
      </template>

      <template #actions="{ ligne }">
        <ActionLigne titre="Valider ce livreur" :icone="Check" ton="accent"
                     :desactive="occupe" @click="ouvrir(ligne, 'livreurs', 'valider')" />
        <ActionLigne titre="Refuser cette candidature" :icone="X" ton="danger"
                     :desactive="occupe" @click="ouvrir(ligne, 'livreurs', 'refuser')" />
      </template>

      <template #vide>
        <div class="vide">
          <Truck :size="30" class="text-trait" />
          <b class="vide-titre">Aucun livreur en attente</b>
          <p class="vide-texte">
            Un livreur Standard validé doit ensuite être rattaché à un entrepôt, sans quoi
            il ne recevra jamais de tournée.
          </p>
        </div>
      </template>
    </Liste>

    <Volet v-if="selection" :titre="selection.nom_boutique ?? nom(selection)">
      <dl class="flex flex-col gap-2.5 text-[12px]">
        <div>
          <dt class="text-encre-douce">Responsable</dt>
          <dd class="font-semibold">{{ nom(selection) }}</dd>
          <dd class="break-all text-encre-douce">{{ selection.utilisateur.email }}</dd>
        </div>
        <div v-if="selection.type_activite" class="flex justify-between gap-2">
          <dt class="text-encre-douce">Type d'activité</dt>
          <dd class="font-semibold">{{ selection.type_activite }}</dd>
        </div>
        <div v-if="selection.siret" class="flex justify-between gap-2">
          <dt class="text-encre-douce">SIRET</dt>
          <dd class="font-mono font-semibold">{{ selection.siret }}</dd>
        </div>
        <div v-if="selection.mode_livraison" class="flex justify-between gap-2">
          <dt class="text-encre-douce">Mode</dt>
          <dd class="font-semibold">{{ selection.mode_livraison }}</dd>
        </div>
        <div v-if="selection.vehicule" class="flex justify-between gap-2">
          <dt class="text-encre-douce">Véhicule</dt>
          <dd class="font-semibold">{{ selection.vehicule }}</dd>
        </div>
        <div v-if="selection.description">
          <dt class="text-encre-douce">Description</dt>
          <dd class="leading-relaxed">{{ selection.description }}</dd>
        </div>
      </dl>

      <div class="mt-4 flex flex-col gap-2">
        <Button
          label="Valider"
          size="small"
          :disabled="occupe"
          @click="ouvrir(selection, selection.nom_boutique ? 'vendeurs' : 'livreurs', 'valider')"
        />
        <Button
          label="Refuser"
          severity="danger"
          outlined
          size="small"
          :disabled="occupe"
          @click="ouvrir(selection, selection.nom_boutique ? 'vendeurs' : 'livreurs', 'refuser')"
        />
      </div>

      <p class="mt-3 text-[11px] leading-relaxed text-encre-douce">
        Votre décision est tracée au journal d'audit et envoyée à la personne concernée,
        avec votre motif.
      </p>
    </Volet>

    <!-- Un geste binaire, mais irréversible : popup courte (D-60) -->
    <Popup
      v-if="decision"
      :titre="decision.action === 'valider' ? 'Valider ce compte ?' : 'Refuser ce dossier ?'"
      :explication="decision.action === 'valider'
        ? `${decision.candidat.nom_boutique ?? nom(decision.candidat)} pourra travailler immédiatement, et sera prévenu. Un catalogue devient visible au public dès cet instant.`
        : `${decision.candidat.nom_boutique ?? nom(decision.candidat)} recevra votre motif et pourra redéposer un dossier corrigé. Sans motif, la personne ne saura pas quoi changer.`"
      @fermer="decision = null"
    >
      <label class="flex flex-col gap-1.5">
        <span class="etiquette">
          Motif
          <span v-if="decision.action === 'refuser'" class="text-alerte">obligatoire</span>
          <span v-else class="font-normal text-encre-douce">— facultatif</span>
        </span>
        <Textarea
          v-model="motif"
          rows="3"
          auto-resize
          :placeholder="decision.action === 'valider'
            ? 'SIRET vérifié, pièces conformes…'
            : 'SIRET non vérifiable, pièce d’identité illisible…'"
        />
      </label>

      <template #actions>
        <Button label="Annuler" severity="secondary" outlined size="small"
                @click="decision = null" />
        <Button
          :label="decision.action === 'valider' ? 'Valider le compte' : 'Refuser le dossier'"
          :severity="decision.action === 'valider' ? undefined : 'danger'"
          size="small"
          :disabled="occupe || (decision.action === 'refuser' && !motif.trim())"
          @click="trancher"
        />
      </template>
    </Popup>
  </div>
</template>
