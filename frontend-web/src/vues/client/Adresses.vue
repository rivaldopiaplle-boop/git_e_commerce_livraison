<script setup lang="ts">
// Le carnet d'adresses du client.
//
// C'était la dernière des quatre listes encore faites à la main. Trois choses
// changent, et deux étaient des défauts :
//
//   · elle passe sur `Liste.vue` avec ses boutons-symboles, comme toutes les
//     autres listes du projet ;
//   · **on pouvait retirer une adresse d'un seul clic**, sans confirmation.
//     Une adresse effacée par erreur se ressaisit en entier, et rien ne la
//     rattrape. Une popup demande maintenant confirmation ;
//   · **on ne pouvait pas modifier une adresse**, seulement l'effacer et la
//     retaper. L'API savait déjà le faire, l'écran ne s'en servait pas.
//
// L'adresse principale n'est pas un détail de confort : c'est elle qui décide
// quelles boutiques Express apparaissent au catalogue (D-09).
import { AlertTriangle, Check, MapPin, Pencil, Plus, Star, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { espaces, type Adresse } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Popup from '../../composants/Popup.vue'
import Volet from '../../composants/Volet.vue'
import { useNotification } from '../../notifications'

type Ligne = Adresse & { [cle: string]: unknown }

const VIDE = {
  libelle: 'Domicile', rue: '', complement: '', code_postal: '', ville: '',
  instructions_livraison: '',
}

const notifier = useNotification()
const adresses = ref<Ligne[]>([])
const chargement = ref(true)
const erreur = ref('')
const occupe = ref(false)
const selection = ref<Ligne | null>(null)

/** La même popup sert à créer et à corriger : c'est le même formulaire. */
const formulaire = ref<{ ouvert: boolean; id: number | null }>({ ouvert: false, id: null })
const saisie = ref({ ...VIDE })
const retrait = ref<Ligne | null>(null)

async function charger() {
  chargement.value = true
  try {
    adresses.value = (await espaces.client.adresses()) as Ligne[]
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const principale = computed(() => adresses.value.find((a) => a.est_principale) ?? null)

const colonnes: Colonne<Ligne>[] = [
  { cle: 'libelle', titre: 'Adresse', champTri: 'libelle' },
  { cle: 'ville', titre: 'Ville', champTri: 'ville', masquerSous: 'sm' },
  { cle: 'consignes', titre: 'Consignes de livraison', masquerSous: 'md' },
  { cle: 'principale', titre: 'Catalogue', largeur: 130, aligne: 'centre' },
]

async function agir(action: Promise<Adresse[]>, reussite?: string) {
  erreur.value = ''
  occupe.value = true
  try {
    adresses.value = (await action) as Ligne[]
    if (reussite) notifier.succes(reussite)
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : "L'action a échoué."
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
}

/** Une correction et une creation ne promettent pas la meme chose : on le dit. */
const explicationFormulaire = computed(() =>
  formulaire.value.id
    ? 'La correction vaut pour vos prochaines commandes. Celles déjà passées gardent '
      + 'l’adresse telle qu’elle était le jour de la livraison.'
    : 'Elle rejoint votre carnet. La première adresse enregistrée devient '
      + 'automatiquement l’adresse principale.',
)

function ouvrirCreation() {
  formulaire.value = { ouvert: true, id: null }
  saisie.value = { ...VIDE }
  erreur.value = ''
}

function ouvrirCorrection(adresse: Ligne) {
  formulaire.value = { ouvert: true, id: adresse.id }
  saisie.value = {
    libelle: adresse.libelle,
    rue: adresse.rue,
    complement: adresse.complement,
    code_postal: adresse.code_postal,
    ville: adresse.ville,
    instructions_livraison: adresse.instructions_livraison,
  }
  erreur.value = ''
}

async function enregistrer() {
  const correction = formulaire.value.id !== null
  await agir(
    correction
      ? espaces.client.modifierAdresse(formulaire.value.id!, saisie.value)
      : espaces.client.ajouterAdresse(saisie.value),
    correction ? 'Adresse corrigée.' : 'Adresse ajoutée à votre carnet.',
  )
  if (!erreur.value) formulaire.value = { ouvert: false, id: null }
}

async function retirer() {
  if (!retrait.value) return
  await agir(espaces.client.retirerAdresse(retrait.value.id), 'Adresse retirée du carnet.')
  if (!erreur.value) {
    if (selection.value?.id === retrait.value.id) selection.value = null
    retrait.value = null
  }
}
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <div class="mb-4 flex items-start justify-between gap-3">
      <p class="text-[12.5px] text-encre-douce">
        L'adresse principale sert à filtrer le catalogue Express : seules les boutiques
        qui livrent chez vous y apparaissent.
      </p>
      <button type="button" class="bouton-accent shrink-0" @click="ouvrirCreation">
        <Plus :size="15" />
        Nouvelle adresse
      </button>
    </div>

    <p v-if="erreur" class="bandeau bandeau-erreur mb-3">
      <AlertTriangle :size="15" class="mt-px shrink-0" /> {{ erreur }}
    </p>

    <Liste
      :colonnes="colonnes"
      :lignes="adresses"
      :cle-ligne="(adresse) => adresse.id"
      :chargement="chargement"
      :recherche="(a) => `${a.libelle} ${a.rue} ${a.code_postal} ${a.ville}`"
      :active="(a) => selection?.id === a.id"
      @ligne-cliquee="(a) => (selection = selection?.id === a.id ? null : a)"
      placeholder="Libellé, rue, ville, code postal…"
    >
      <template #col-libelle="{ ligne }">
        <span class="flex min-w-0 items-center gap-2.5">
          <span
            class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
            :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
          >
            <MapPin :size="15" />
          </span>
          <span class="min-w-0">
            <b class="block truncate">{{ ligne.libelle || 'Adresse' }}</b>
            <span class="block truncate text-[11.2px] text-encre-douce">
              {{ ligne.rue }}<template v-if="ligne.complement">, {{ ligne.complement }}</template>
            </span>
          </span>
        </span>
      </template>

      <template #col-ville="{ ligne }">
        <span class="text-encre-douce">{{ ligne.code_postal }} {{ ligne.ville }}</span>
      </template>

      <template #col-consignes="{ ligne }">
        <span v-if="ligne.instructions_livraison" class="truncate text-encre-douce">
          « {{ ligne.instructions_livraison }} »
        </span>
        <span v-else class="text-trait">—</span>
      </template>

      <template #col-principale="{ ligne }">
        <span v-if="ligne.est_principale" class="badge badge-ok">
          <Star :size="10" /> principale
        </span>
        <span v-else class="text-[11.5px] text-encre-douce">—</span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          :titre="ligne.est_principale
            ? 'C’est déjà votre adresse principale'
            : 'Filtrer le catalogue sur cette adresse'"
          :icone="Star"
          :ton="ligne.est_principale ? 'accent' : 'neutre'"
          :desactive="ligne.est_principale || occupe"
          @click="agir(
            espaces.client.modifierAdresse(ligne.id, { est_principale: true }),
            'Le catalogue Express suit désormais cette adresse.',
          )"
        />
        <ActionLigne titre="Corriger cette adresse" :icone="Pencil"
                     @click="ouvrirCorrection(ligne)" />
        <ActionLigne
          titre="Retirer du carnet"
          :icone="Trash2"
          ton="danger"
          :desactive="occupe"
          @click="retrait = ligne"
        />
      </template>

      <template #vide>
        <div class="vide">
          <MapPin :size="30" class="text-trait" />
          <b class="vide-titre">Aucune adresse enregistrée</b>
          <p class="vide-texte">
            Ajoutez-en une : le catalogue vous montrera alors les boutiques Express qui
            livrent réellement chez vous, au lieu de toutes les autres.
          </p>
          <button type="button" class="bouton-accent mt-4" @click="ouvrirCreation">
            <Plus :size="15" /> Ajouter une adresse
          </button>
        </div>
      </template>
    </Liste>

    <Volet :titre="selection?.libelle || 'Mon carnet'">
      <div class="flex flex-col gap-4 p-4 text-[12.5px]">
        <template v-if="selection">
          <div class="kpi">
            <div class="kpi-nombre">{{ selection.code_postal }}</div>
            <div class="kpi-libelle">{{ selection.ville }}</div>
          </div>
          <p class="leading-relaxed">
            {{ selection.rue }}<template v-if="selection.complement">,
            {{ selection.complement }}</template><br />
            {{ selection.code_postal }} {{ selection.ville }}
          </p>
          <p v-if="selection.instructions_livraison" class="text-encre-douce">
            <span class="etiquette">Consignes pour le livreur</span><br />
            « {{ selection.instructions_livraison }} »
          </p>
          <p v-if="selection.est_principale" class="bandeau bandeau-info">
            <Star :size="15" class="mt-px shrink-0" />
            Le catalogue Express est filtré sur cette adresse : les boutiques qui ne
            livrent pas ici ne vous sont pas montrées.
          </p>
          <button type="button" class="bouton-neutre" @click="ouvrirCorrection(selection)">
            <Pencil :size="15" /> Corriger
          </button>
        </template>

        <template v-else>
          <div class="kpi">
            <div class="kpi-nombre">{{ adresses.length }}</div>
            <div class="kpi-libelle">Adresse(s) enregistrée(s)</div>
          </div>
          <p class="leading-relaxed text-encre-douce">
            <template v-if="principale">
              Votre catalogue Express est filtré sur
              <b class="text-encre">{{ principale.libelle }}</b>, à
              {{ principale.ville }}.
            </template>
            <template v-else>
              Aucune adresse principale : le catalogue vous montre toutes les boutiques,
              y compris celles qui ne livrent pas chez vous.
            </template>
          </p>
        </template>
      </div>
    </Volet>

    <!-- Créer ou corriger : le même formulaire -->
    <Popup
      v-if="formulaire.ouvert"
      :titre="formulaire.id ? 'Corriger cette adresse' : 'Ajouter une adresse'"
      :explication="explicationFormulaire"
      @fermer="formulaire = { ouvert: false, id: null }"
    >
      <form class="flex flex-col gap-3" @submit.prevent="enregistrer">
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Libellé</span>
          <input v-model="saisie.libelle" class="champ-clair" placeholder="Domicile, Bureau…" />
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Rue</span>
          <input v-model="saisie.rue" class="champ-clair" required />
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Complément</span>
          <input v-model="saisie.complement" class="champ-clair"
                 placeholder="Bâtiment, étage, code…" />
        </label>
        <div class="flex gap-3">
          <label class="flex w-32 flex-col gap-1.5">
            <span class="etiquette">Code postal</span>
            <input v-model="saisie.code_postal" class="champ-clair" required />
          </label>
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="etiquette">Ville</span>
            <input v-model="saisie.ville" class="champ-clair" required />
          </label>
        </div>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Instructions pour le livreur</span>
          <input v-model="saisie.instructions_livraison" class="champ-clair"
                 placeholder="Code portail, étage, laisser chez le gardien…" />
        </label>
      </form>

      <template #actions>
        <button
          type="button"
          class="bouton-neutre !py-2"
          @click="formulaire = { ouvert: false, id: null }"
        >
          Annuler
        </button>
        <button type="button" class="bouton-accent !py-2" :disabled="occupe"
                @click="enregistrer">
          <Check :size="15" /> Enregistrer
        </button>
      </template>
    </Popup>

    <!-- Retirer : on demande, parce qu'une adresse effacée se ressaisit en entier -->
    <Popup
      v-if="retrait"
      :titre="`Retirer « ${retrait.libelle || 'cette adresse'} » ?`"
      explication="Vos commandes passées gardent l'adresse à laquelle elles ont été
                   livrées. Seul votre carnet change."
      @fermer="retrait = null"
    >
      <p class="text-[12.5px] leading-relaxed">
        {{ retrait.rue }}<br />{{ retrait.code_postal }} {{ retrait.ville }}
      </p>
      <p v-if="retrait.est_principale" class="bandeau mt-3">
        <AlertTriangle :size="15" class="mt-px shrink-0" />
        C'est votre adresse principale. Sans elle, le catalogue Express ne saura plus
        quelles boutiques livrent chez vous.
      </p>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="retrait = null">
          Garder
        </button>
        <button type="button" class="bouton-accent !py-2" :disabled="occupe" @click="retirer">
          <Trash2 :size="15" /> Retirer du carnet
        </button>
      </template>
    </Popup>
  </div>
</template>
