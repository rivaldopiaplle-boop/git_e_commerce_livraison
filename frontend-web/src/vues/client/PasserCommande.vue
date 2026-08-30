<script setup lang="ts">
// Le tunnel de commande.
//
// Il montre le decoupage AVANT de valider : un client doit savoir qu'il cree
// trois commandes livrees separement (D-10). Le decouvrir apres le paiement
// serait une mauvaise surprise.
//
// Ce que le bloc K a corrige, et qui rendait le bouton « passer commande »
// inutilisable : une SEULE ligne devenue indisponible bloquait tout le panier.
// L'apercu renvoyait 409, l'ecran affichait « votre panier est vide » alors
// que le panneau lateral montrait quinze articles, et rien ne disait quoi
// enlever. Une impasse pareille fait abandonner un achat.
import {
  AlertTriangle, ArrowRight, Bike, Check, MapPin, Package, ShieldCheck, Trash2,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { EchecApi } from '../../api/client'
import { commandes, type ApercuCommande } from '../../api/commandes'
import { espaces, type Adresse } from '../../api/espaces'
import Squelette from '../../composants/Squelette.vue'
import { useAuthentification } from '../../stores/authentification'
import { usePanier } from '../../stores/panier'

type LigneBloquante = {
  id_ligne: number
  nom: string
  quantite: number
  code: string
  message: string
  disponible?: number
}

const session = useAuthentification()
const panier = usePanier()
const routeur = useRouter()

const apercu = ref<ApercuCommande[]>([])
const bloquantes = ref<LigneBloquante[]>([])
const total = ref(0)
const chargement = ref(true)
const erreur = ref('')
const envoi = ref(false)
const nettoyage = ref(false)

const carnet = ref<Adresse[]>([])
const adresseChoisie = ref<number | 'nouvelle'>('nouvelle')
const adresse = ref({ rue: '', code_postal: '', ville: '', instructions_livraison: '' })

async function chargerApercu() {
  try {
    const donnees = await commandes.apercu()
    apercu.value = donnees.commandes
    total.value = donnees.total_centimes
    bloquantes.value = (donnees.lignes_bloquantes ?? []) as LigneBloquante[]
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Panier indisponible.'
  }
}

onMounted(async () => {
  await chargerApercu()
  if (session.estConnecte) {
    try {
      carnet.value = await espaces.client.adresses()
      const principale = carnet.value.find((a) => a.est_principale)
      if (principale) adresseChoisie.value = principale.id
    } catch {
      carnet.value = []
    }
  }
  chargement.value = false
})

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const adresseRemplie = computed(
  () => adresse.value.rue.trim() && adresse.value.ville.trim() && adresse.value.code_postal.trim(),
)
const peutValider = computed(
  () => apercu.value.length > 0
    && (adresseChoisie.value !== 'nouvelle' || adresseRemplie.value || carnet.value.length > 0),
)

async function retirerIndisponibles() {
  nettoyage.value = true
  erreur.value = ''
  try {
    await panier.nettoyer()
    bloquantes.value = []
    await chargerApercu()
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Nettoyage impossible.'
  } finally {
    nettoyage.value = false
  }
}

async function valider() {
  erreur.value = ''
  envoi.value = true
  try {
    const corps =
      adresseChoisie.value !== 'nouvelle'
        ? { id_adresse: adresseChoisie.value }
        : adresseRemplie.value
          ? { adresse: adresse.value }
          : {}
    const creees = await commandes.creer(corps)
    await panier.charger()
    routeur.push({ name: 'mes-commandes', query: { creees: creees.length } })
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Commande impossible.'
    // Le panier a peut-etre bouge entre l'apercu et la validation : on le
    // relit pour que le message et l'ecran racontent la meme chose.
    await chargerApercu()
  } finally {
    envoi.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[840px] animate-[apparition_0.2s_ease-out]">
    <h2 class="text-[21px] font-semibold tracking-tight">Valider ma commande</h2>

    <div v-if="chargement" class="mt-5 flex flex-col gap-3">
      <Squelette hauteur="90px" />
      <Squelette hauteur="90px" />
    </div>

    <template v-else>
      <!-- Ce qui bloque, nommement, avec la sortie de secours -->
      <section v-if="bloquantes.length" class="carte mt-4 border-avis-trait">
        <h3 class="carte-titre bg-avis-voile">
          <span class="flex items-center gap-2 text-avis">
            <AlertTriangle :size="15" />
            {{ bloquantes.length }} article{{ bloquantes.length > 1 ? 's' : '' }}
            ne {{ bloquantes.length > 1 ? 'peuvent' : 'peut' }} plus etre command{{
              bloquantes.length > 1 ? 'es' : 'e'
            }}
          </span>
          <button
            type="button"
            class="bouton-neutre !py-1.5 !text-[12px]"
            :disabled="nettoyage"
            @click="retirerIndisponibles"
          >
            <Trash2 :size="14" />
            {{ nettoyage ? 'Retrait…' : 'Les retirer et continuer' }}
          </button>
        </h3>
        <div v-for="ligne in bloquantes" :key="ligne.id_ligne" class="ligne">
          <span class="min-w-0 flex-1">
            <b class="block truncate">{{ ligne.nom }}</b>
            <span class="text-[11.2px] text-encre-douce">{{ ligne.message }}</span>
          </span>
          <span class="badge badge-erreur">{{ ligne.code.replace(/_/g, ' ') }}</span>
        </div>
        <p class="border-t border-trait-doux px-4 py-2.5 text-[11.5px] text-encre-douce">
          Le reste de votre panier est commandable : les articles ci-dessus ne sont pas
          comptes dans le total.
        </p>
      </section>

      <template v-if="apercu.length">
        <p class="mt-4 text-[13.5px] text-encre-douce">
          Votre panier donnera
          <b class="text-encre">
            {{ apercu.length }} commande{{ apercu.length > 1 ? 's' : '' }}
          </b>
          <template v-if="apercu.length > 1">
            , livrees separement — un seul paiement, plusieurs livraisons.
          </template>
        </p>

        <div class="mt-4 flex flex-col gap-3">
          <article v-for="(bloc, index) in apercu" :key="index" class="carte p-5">
            <div class="flex items-start justify-between gap-4">
              <div class="flex items-center gap-3">
                <span
                  class="flex h-10 w-10 items-center justify-center rounded-lg"
                  :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
                >
                  <component :is="bloc.type_service === 'EXPRESS' ? Bike : Package" :size="19" />
                </span>
                <div>
                  <b class="text-[14.5px]">
                    {{ bloc.type_service === 'EXPRESS' ? 'Livraison Express'
                                                       : 'Livraison Standard' }}
                  </b>
                  <p class="text-[12.5px] text-encre-douce">
                    {{ bloc.boutiques.join(' · ') }} — {{ bloc.articles }} article{{
                      bloc.articles > 1 ? 's' : ''
                    }}
                  </p>
                </div>
              </div>
              <div class="text-right">
                <b class="text-[15px]">
                  {{ euros(bloc.montant_produits_centimes + bloc.montant_livraison_centimes) }}
                </b>
                <p class="text-[12px] text-encre-douce">
                  dont
                  {{
                    bloc.montant_livraison_centimes
                      ? euros(bloc.montant_livraison_centimes) + ' de livraison'
                      : 'livraison offerte'
                  }}
                </p>
              </div>
            </div>
          </article>
        </div>

        <!-- Adresse : celle du carnet, ou une nouvelle -->
        <section class="carte mt-4 p-5">
          <b class="flex items-center gap-2 text-[14px]">
            <MapPin :size="16" :style="{ color: 'var(--accent)' }" />
            Adresse de livraison
          </b>

          <div v-if="carnet.length" class="mt-3 flex flex-col gap-2">
            <label
              v-for="entree in carnet"
              :key="entree.id"
              class="flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-[12.5px]
                     transition-colors"
              :class="adresseChoisie === entree.id ? 'border-[color:var(--accent)] bg-atelier'
                                                   : 'border-trait hover:bg-atelier'"
            >
              <input
                v-model="adresseChoisie"
                type="radio"
                :value="entree.id"
                class="mt-0.5"
                name="adresse"
              />
              <span>
                <b class="block">{{ entree.libelle || 'Adresse' }}</b>
                <span class="text-encre-douce">
                  {{ entree.rue }}, {{ entree.code_postal }} {{ entree.ville }}
                </span>
              </span>
            </label>
            <label
              class="flex cursor-pointer items-center gap-3 rounded-lg border p-3 text-[12.5px]
                     transition-colors"
              :class="adresseChoisie === 'nouvelle' ? 'border-[color:var(--accent)] bg-atelier'
                                                    : 'border-trait hover:bg-atelier'"
            >
              <input v-model="adresseChoisie" type="radio" value="nouvelle" name="adresse" />
              <b>Livrer a une autre adresse</b>
            </label>
          </div>

          <div v-if="adresseChoisie === 'nouvelle'" class="mt-4 flex flex-wrap gap-3">
            <label class="flex min-w-[240px] flex-1 flex-col gap-1.5">
              <span class="etiquette">Rue</span>
              <input v-model="adresse.rue" class="champ-clair" />
            </label>
            <label class="flex w-32 flex-col gap-1.5">
              <span class="etiquette">Code postal</span>
              <input v-model="adresse.code_postal" class="champ-clair" />
            </label>
            <label class="flex min-w-[160px] flex-1 flex-col gap-1.5">
              <span class="etiquette">Ville</span>
              <input v-model="adresse.ville" class="champ-clair" />
            </label>
            <label class="flex w-full flex-col gap-1.5">
              <span class="etiquette">Instructions (code, etage…)</span>
              <input v-model="adresse.instructions_livraison" class="champ-clair" />
            </label>
          </div>
        </section>

        <p v-if="erreur" class="bandeau bandeau-erreur mt-4">
          <AlertTriangle :size="15" class="mt-px shrink-0" />
          {{ erreur }}
        </p>

        <!-- Total et validation -->
        <div class="carte mt-4 flex flex-wrap items-center justify-between gap-4 p-5">
          <div>
            <p class="text-[12.5px] text-encre-douce">Total a payer</p>
            <b class="text-[26px]" :style="{ color: 'var(--accent)' }">{{ euros(total) }}</b>
          </div>

          <div class="flex flex-col items-end gap-2">
            <button
              v-if="session.estConnecte"
              type="button"
              class="bouton-accent !px-5 !py-3 !text-[14px]"
              :disabled="envoi || !peutValider"
              @click="valider"
            >
              <Check :size="17" />
              {{ envoi ? 'Validation…' : 'Valider ma commande' }}
            </button>

            <!-- Le panier suit le visiteur jusqu'au compte (D-34) : le lui
                 dire ici evite qu'il croie devoir tout recommencer. -->
            <RouterLink
              v-else
              :to="{ name: 'connexion', query: { suite: 'commande' } }"
              class="bouton-accent !px-5 !py-3 !text-[14px]"
            >
              Se connecter pour commander
              <ArrowRight :size="17" />
            </RouterLink>

            <p v-if="!session.estConnecte" class="text-[11.5px] text-encre-douce">
              Votre panier vous suit : il sera retrouve tel quel apres connexion.
            </p>
            <p v-else class="flex items-center gap-1.5 text-[11.5px] text-encre-douce">
              <ShieldCheck :size="13" />
              Le paiement Stripe arrive a la tranche suivante — la commande est creee
              sans debit.
            </p>
          </div>
        </div>
      </template>

      <div v-else-if="!bloquantes.length" class="carte mt-5">
        <div class="vide">
          <Package :size="30" class="text-trait" />
          <b class="vide-titre">Votre panier est vide</b>
          <p class="vide-texte">Ajoutez des articles au catalogue pour passer commande.</p>
          <RouterLink :to="{ name: 'vitrine' }" class="bouton-accent mt-4">
            Voir le catalogue
          </RouterLink>
        </div>
      </div>
    </template>
  </div>
</template>
