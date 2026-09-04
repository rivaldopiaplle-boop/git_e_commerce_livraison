<script setup lang="ts">
// Le carnet de cartes, et la saisie d'une carte — O-5, D-150.
//
// **Ton reproche** : *« payer est validé sans carte, pas de demande de carte
// même la première fois, et après c'est enregistré »*, avec cette contrainte :
// *« que ça ne prenne pas beaucoup de temps »*.
//
// C'est ce qui décide de la forme de cet écran :
//
//   · **s'il y a déjà une carte, on ne montre pas de formulaire.** Une ligne
//     « Visa •••• 4242 » et un bouton. Le coût de saisie est payé une fois ;
//   · **le numéro se met en forme pendant la frappe** — « 4242 4242 4242 4242 »
//     plutôt que seize chiffres collés. On relit ce qu'on tape ;
//   · **l'échéance et le cryptogramme tiennent sur la même ligne**, parce que
//     c'est ainsi qu'ils sont imprimés sur la carte ;
//   · **l'erreur s'affiche sous le champ fautif.** « Erreur » en haut du
//     formulaire oblige à relire les quatre champs pour trouver lequel.
//
// Le numéro complet ne quitte jamais ce composant : il part une fois vers
// l'API, qui le remplace par un jeton et n'en garde que les quatre derniers
// chiffres.
import { AlertTriangle, CreditCard, Loader, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../api/client'
import { paiements, type Carte } from '../api/paiements'

const emet = defineEmits<{ (evenement: 'choisie', carte: Carte | null): void }>()

const cartes = ref<Carte[]>([])
const essais = ref<{ numero: string; marque: string; effet: string }[]>([])
const choisie = ref<number | null>(null)
const formulaire = ref(false)
const occupe = ref(false)
const chargement = ref(true)

const saisie = ref({ numero: '', expiration: '', cryptogramme: '' })
const erreurs = ref<Record<string, string>>({})

const carteRetenue = computed(() =>
  cartes.value.find((carte) => carte.id === choisie.value) ?? null,
)

async function charger() {
  try {
    const donnees = await paiements.cartes()
    cartes.value = donnees.cartes
    essais.value = donnees.cartes_d_essai
    choisie.value = (donnees.cartes.find((carte) => carte.par_defaut)
      ?? donnees.cartes[0])?.id ?? null
    // Sans carte, on ouvre le formulaire d'emblée : faire cliquer sur
    // « ajouter » quand il n'y a rien d'autre à faire est un clic de trop.
    formulaire.value = !donnees.cartes.length
    emet('choisie', carteRetenue.value)
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

/** « 4242 4242 4242 4242 » pendant la frappe : on relit ce qu'on tape. */
function formaterNumero(evenement: Event) {
  const champ = evenement.target as HTMLInputElement
  const chiffres = champ.value.replace(/\D/g, '').slice(0, 19)
  saisie.value.numero = chiffres.replace(/(.{4})/g, '$1 ').trim()
}

/** « 12/30 » : la barre s'ajoute toute seule, personne ne la tape. */
function formaterExpiration(evenement: Event) {
  const champ = evenement.target as HTMLInputElement
  const chiffres = champ.value.replace(/\D/g, '').slice(0, 4)
  saisie.value.expiration = chiffres.length > 2
    ? `${chiffres.slice(0, 2)}/${chiffres.slice(2)}`
    : chiffres
}

async function ajouter() {
  erreurs.value = {}
  occupe.value = true
  const [mois, annee] = saisie.value.expiration.split('/')
  try {
    const carte = await paiements.ajouterCarte({
      numero: saisie.value.numero.replace(/\s/g, ''),
      mois: mois ?? '',
      annee: annee ?? '',
      cryptogramme: saisie.value.cryptogramme,
    })
    saisie.value = { numero: '', expiration: '', cryptogramme: '' }
    formulaire.value = false
    await charger()
    choisir(carte.id)
  } catch (souci) {
    if (souci instanceof EchecApi) {
      const champ = (souci.erreur.details as { champ?: string })?.champ ?? 'numero'
      erreurs.value = { [champ]: souci.erreur.message }
    } else {
      erreurs.value = { numero: 'Carte refusée.' }
    }
  } finally {
    occupe.value = false
  }
}

function choisir(id: number) {
  choisie.value = id
  emet('choisie', carteRetenue.value)
}

async function retirer(carte: Carte) {
  occupe.value = true
  try {
    const donnees = await paiements.retirerCarte(carte.id)
    cartes.value = donnees.cartes
    choisie.value = donnees.cartes[0]?.id ?? null
    formulaire.value = !donnees.cartes.length
    emet('choisie', carteRetenue.value)
  } finally {
    occupe.value = false
  }
}

/** Remplir avec une carte d'essai : deux clics au lieu de seize chiffres. */
function remplirAvec(numero: string) {
  saisie.value = { numero: numero.replace(/(.{4})/g, '$1 ').trim(),
                   expiration: '12/30',
                   cryptogramme: numero.startsWith('37') ? '1234' : '123' }
}
</script>

<template>
  <section class="carte">
    <b class="mb-3 flex items-center gap-2 text-[13.5px]">
      <CreditCard :size="16" class="text-[color:var(--accent)]" />
      Moyen de paiement
    </b>

    <p v-if="chargement" class="text-[12.5px] text-encre-douce">Chargement…</p>

    <!-- Une carte enregistrée : une ligne, pas un formulaire (O-5). -->
    <div v-else-if="cartes.length" class="flex flex-col gap-2">
      <label
        v-for="carte in cartes"
        :key="carte.id"
        class="flex cursor-pointer items-center gap-3 rounded-lg border p-2.5 text-[13px]
               transition-colors"
        :class="choisie === carte.id ? 'border-[color:var(--accent)] bg-atelier'
                                     : 'border-trait hover:bg-atelier'"
      >
        <input
          type="radio"
          name="carte"
          :value="carte.id"
          :checked="choisie === carte.id"
          @change="choisir(carte.id)"
        />
        <span class="flex-1">
          <b>{{ carte.libelle }}</b>
          <span class="ml-2 text-[11.5px] text-encre-douce">
            expire {{ String(carte.mois_expiration).padStart(2, '0') }}/{{
              String(carte.annee_expiration).slice(-2) }}
          </span>
          <span v-if="carte.expiree" class="ml-2 text-[11.5px] font-bold text-[#9c2116]">
            expirée
          </span>
        </span>
        <button
          type="button"
          class="rounded-md p-1.5 text-encre-douce transition-colors hover:text-[#9c2116]"
          title="Retirer cette carte"
          :disabled="occupe"
          @click.prevent.stop="retirer(carte)"
        >
          <Trash2 :size="14" />
        </button>
      </label>

      <button
        v-if="!formulaire"
        type="button"
        class="bouton-neutre !py-2 self-start"
        @click="formulaire = true"
      >
        <Plus :size="14" /> Ajouter une carte
      </button>
    </div>

    <!-- Le formulaire : quatre champs, dans l'ordre où ils sont imprimés. -->
    <form v-if="formulaire" class="mt-3 flex flex-col gap-3" @submit.prevent="ajouter">
      <label class="flex flex-col gap-1.5">
        <span class="etiquette">Numéro de carte</span>
        <input
          :value="saisie.numero"
          class="champ-clair font-mono tracking-wider"
          inputmode="numeric"
          autocomplete="cc-number"
          placeholder="4242 4242 4242 4242"
          @input="formaterNumero"
        />
        <span v-if="erreurs.numero" class="text-[11.5px] text-[#9c2116]">
          {{ erreurs.numero }}
        </span>
      </label>

      <div class="flex gap-3">
        <label class="flex w-32 flex-col gap-1.5">
          <span class="etiquette">Expiration</span>
          <input
            :value="saisie.expiration"
            class="champ-clair font-mono"
            inputmode="numeric"
            autocomplete="cc-exp"
            placeholder="MM/AA"
            @input="formaterExpiration"
          />
        </label>
        <label class="flex w-32 flex-col gap-1.5">
          <span class="etiquette">Cryptogramme</span>
          <input
            v-model="saisie.cryptogramme"
            class="champ-clair font-mono"
            inputmode="numeric"
            autocomplete="cc-csc"
            maxlength="4"
            placeholder="123"
          />
        </label>
      </div>
      <span
        v-if="erreurs.expiration || erreurs.cryptogramme"
        class="text-[11.5px] text-[#9c2116]"
      >
        {{ erreurs.expiration || erreurs.cryptogramme }}
      </span>

      <!-- Les cartes d'essai sont OFFERTES, pas cachées dans une documentation :
           une démonstration qu'on ne sait pas essayer ne se démontre pas. -->
      <div v-if="essais.length" class="rounded-lg bg-atelier p-3">
        <p class="flex items-start gap-2 text-[11.5px] leading-relaxed text-encre-douce">
          <AlertTriangle :size="13" class="mt-px shrink-0" />
          <span>
            <b class="text-encre">N'entrez jamais votre vraie carte.</b>
            Cette démonstration n'accepte que les cartes d'essai ci-dessous, et
            refuse toutes les autres.
          </span>
        </p>
        <div class="mt-2 flex flex-wrap gap-2">
          <button
            v-for="essai in essais"
            :key="essai.numero"
            type="button"
            class="rounded-full border border-trait bg-papier px-2.5 py-1 font-mono
                   text-[11px] transition-colors hover:border-[color:var(--accent)]"
            :title="`Carte ${essai.marque} — ${essai.effet}`"
            @click="remplirAvec(essai.numero)"
          >
            {{ essai.numero.replace(/(.{4})/g, '$1 ').trim() }}
            <span class="text-encre-douce">· {{ essai.effet }}</span>
          </button>
        </div>
      </div>

      <div class="flex gap-2">
        <button type="submit" class="bouton-accent !py-2" :disabled="occupe">
          <Loader v-if="occupe" :size="14" class="animate-spin" />
          <Plus v-else :size="14" />
          Enregistrer la carte
        </button>
        <button
          v-if="cartes.length"
          type="button"
          class="bouton-neutre !py-2"
          @click="formulaire = false"
        >
          Annuler
        </button>
      </div>
    </form>
  </section>
</template>
