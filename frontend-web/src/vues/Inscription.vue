<script setup lang="ts">
// L'inscription valide desormais AVANT d'envoyer, avec vee-validate + zod
// (D-26). Elle validait a la main : un mot de passe trop court se decouvrait
// apres l'aller-retour reseau, ce qui est exactement ce qui fait abandonner
// une creation de compte.
import { ArrowLeft, Bike, KeyRound, Mail, Store, User, UserPlus } from '@lucide/vue'
import { useForm } from 'vee-validate'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { EchecApi } from '../api/client'
import { accueilDuRole } from '../routeur'
import ChampTexte from '../composants/ChampTexte.vue'
import LogoRivDinde from '../composants/LogoRivDinde.vue'
import PanneauMarque from '../composants/PanneauMarque.vue'
import { useAuthentification } from '../stores/authentification'
import { schemaBoutique, schemaInscription } from '../validation'

type Profil = 'client' | 'vendeur' | 'livreur'

const session = useAuthentification()
const routeur = useRouter()
const route = useRoute()

// La page « rejoindre » arrive ici avec ?profil=vendeur : le formulaire est
// deja sur le bon onglet, personne n'a a le rechercher.
const profilDemande = route.query.profil as Profil | undefined
const profil = ref<Profil>(
  profilDemande && ['client', 'vendeur', 'livreur'].includes(profilDemande)
    ? profilDemande
    : 'client',
)
const PROFILS: { cle: Profil; libelle: string; icone: typeof User }[] = [
  { cle: 'client', libelle: 'Client', icone: User },
  { cle: 'vendeur', libelle: 'Vendeur', icone: Store },
  { cle: 'livreur', libelle: 'Livreur', icone: Bike },
]

// Le vendeur a un champ de plus, obligatoire : le schema suit le profil
// choisi. Un seul schema avec un champ « parfois requis » serait plus court a
// ecrire et impossible a lire six mois plus tard.
const schema = computed(() =>
  profil.value === 'vendeur' ? schemaBoutique : schemaInscription,
)

const { handleSubmit, errors, values, setFieldError, resetForm } = useForm({
  validationSchema: schema,
  initialValues: { prenom: '', nom: '', email: '', mot_de_passe: '', nom_boutique: '' },
})

// Les listes deroulantes n'ont pas de regle a verifier : elles partent d'une
// liste fermee, et un `v-model` ordinaire suffit.
const choixVendeur = ref({ type_activite: 'EXPRESS' })
const choixLivreur = ref({ mode_livraison: 'EXPRESS', vehicule: 'VELO' })

const erreur = ref('')

// Changer de profil efface le message d'erreur du profil precedent : le lire
// encore apres avoir change d'onglet n'a aucun sens.
watch(profil, () => {
  erreur.value = ''
})

// Dit avant l'envoi, pas apres : un vendeur doit savoir qu'il sera verifie
// avant de pouvoir travailler (D-02).
const avertissement = computed(() =>
  profil.value === 'client'
    ? ''
    : 'Votre compte sera cree, puis verifie par un administrateur avant activation.',
)

// `handleSubmit` ne se declenche QUE si le schema passe. Il n'y a donc plus de
// verification manuelle a oublier, et le formulaire ne part jamais incomplet.
const valider = handleSubmit(async (saisie) => {
  erreur.value = ''
  const commun = {
    email: saisie.email,
    mot_de_passe: saisie.mot_de_passe,
    nom: saisie.nom,
    prenom: saisie.prenom,
  }
  const specifique =
    profil.value === 'vendeur'
      ? { nom_boutique: saisie.nom_boutique, ...choixVendeur.value }
      : profil.value === 'livreur'
        ? { ...choixLivreur.value }
        : {}

  try {
    await session.inscrire(profil.value, { ...commun, ...specifique })
    await routeur.push({
      name: session.enAttenteDeValidation ? 'en-attente' : accueilDuRole(session.role),
    })
  } catch (echec) {
    if (echec instanceof EchecApi) {
      erreur.value = echec.erreur.message
      // Le serveur sait des choses que le navigateur ignore — « cette adresse
      // est deja prise ». On pose son message SUR le champ concerne plutot que
      // dans un bandeau general, ou il faudrait deviner quoi corriger.
      for (const [champ, messages] of Object.entries(echec.erreur.details ?? {})) {
        if (Array.isArray(messages) && messages.length) {
          setFieldError(champ as never, messages[0])
        }
      }
    } else {
      erreur.value = "L'inscription n'a pas abouti."
    }
  }
})

/** Rien de saisi : le bouton reste inutile tant que le formulaire est vide. */
const vide = computed(() => !values.email && !values.nom && !values.prenom)
</script>

<template>
  <div class="flex min-h-screen w-full bg-atelier">
    <PanneauMarque />

    <main class="flex flex-1 items-center justify-center px-6 py-12">
      <form class="w-full max-w-[440px] animate-[apparition_0.2s_ease-out]" @submit.prevent="valider">
        <RouterLink
          to="/"
          class="mb-6 inline-flex items-center gap-2 text-[13px] text-encre-douce
                 transition-colors duration-150 hover:text-marque-fonce"
        >
          <ArrowLeft :size="15" />
          Retour au catalogue
        </RouterLink>

        <div class="mb-6 lg:hidden">
          <LogoRivDinde :taille="52" />
        </div>

        <h2 class="text-[26px] font-semibold tracking-tight text-encre">Creer un compte</h2>
        <p class="mt-1 mb-6 text-[14px] text-encre-douce">Choisissez d'abord votre role.</p>

        <!-- Onglets : le choix du role change le formulaire, il doit donc etre
             visible en premier et non cache dans une liste deroulante. -->
        <div class="mb-5 flex gap-1 rounded-xl border border-trait bg-papier p-1.5">
          <button
            v-for="choix in PROFILS"
            :key="choix.cle"
            type="button"
            class="flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-[13.5px]
                   transition-all duration-150"
            :class="
              profil === choix.cle
                ? 'bg-marque font-bold text-encre'
                : 'text-encre-douce hover:bg-atelier'
            "
            @click="profil = choix.cle"
          >
            <component :is="choix.icone" :size="16" />
            {{ choix.libelle }}
          </button>
        </div>

        <p
          v-if="avertissement"
          class="bandeau mb-5"
        >
          {{ avertissement }}
        </p>

        <div class="flex flex-col gap-4">
          <div class="flex gap-3">
            <ChampTexte nom="prenom" label="Prénom" :icone="User" class="flex-1" />
            <ChampTexte nom="nom" label="Nom" class="flex-1" />
          </div>

          <ChampTexte
            nom="email"
            label="Adresse e-mail"
            type="email"
            :icone="Mail"
            autocomplete="email"
          />
          <ChampTexte
            nom="mot_de_passe"
            label="Mot de passe"
            type="password"
            :icone="KeyRound"
            autocomplete="new-password"
            aide="Dix caractères au minimum. La longueur protège mieux que les symboles."
          />

          <template v-if="profil === 'vendeur'">
            <ChampTexte nom="nom_boutique" label="Nom de la boutique" :icone="Store" />
            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-encre-douce">Type d'activite</span>
              <select v-model="choixVendeur.type_activite" class="champ-clair">
                <option value="EXPRESS">Express — restauration, livraison immediate</option>
                <option value="STANDARD">Standard — colis, passage par entrepot</option>
              </select>
            </label>
          </template>

          <template v-if="profil === 'livreur'">
            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-encre-douce">Mode de livraison</span>
              <select v-model="choixLivreur.mode_livraison" class="champ-clair">
                <option value="EXPRESS">Express — une course a la fois</option>
                <option value="STANDARD">Standard — tournees depuis un entrepot</option>
              </select>
            </label>
            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-encre-douce">Vehicule</span>
              <select v-model="choixLivreur.vehicule" class="champ-clair">
                <option value="VELO">Velo</option>
                <option value="SCOOTER">Scooter</option>
                <option value="VOITURE">Voiture</option>
                <option value="CAMIONNETTE">Camionnette</option>
              </select>
            </label>
          </template>
        </div>

        <p
          v-if="erreur"
          class="bandeau bandeau-erreur mt-4"
          role="alert"
        >
          {{ erreur }}
        </p>

        <button type="submit" class="bouton-marque mt-6 w-full" :disabled="session.chargement">
          <UserPlus :size="17" />
          {{ session.chargement ? 'Creation…' : 'Creer mon compte' }}
        </button>

        <p class="mt-5 text-center text-[13.5px] text-encre-douce">
          Deja inscrit ?
          <RouterLink to="/connexion" class="text-marque-fonce hover:underline">
            Se connecter
          </RouterLink>
        </p>
      </form>
    </main>
  </div>
</template>
