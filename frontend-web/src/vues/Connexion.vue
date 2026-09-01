<script setup lang="ts">
// L'ecran de connexion. Clair, comme toute l'application : il etait ecrit en
// blanc sur un fond sombre qui avait disparu du theme, et il ne restait donc
// rien de lisible a l'ecran.
import { ArrowLeft, KeyRound, LogIn, Mail, ShieldAlert } from '@lucide/vue'
import { useForm } from 'vee-validate'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { EchecApi } from '../api/client'
import { accueilDuRole } from '../routeur'
import ChampTexte from '../composants/ChampTexte.vue'
import LogoRivDinde from '../composants/LogoRivDinde.vue'
import PanneauMarque from '../composants/PanneauMarque.vue'
import { useAuthentification } from '../stores/authentification'
import { schemaConnexion } from '../validation'

const session = useAuthentification()
const routeur = useRouter()

// vee-validate + zod (D-26). A la connexion, le schema ne verifie QUE la forme
// de l'adresse et la presence du mot de passe : reprocher sa longueur a
// quelqu'un qui essaie d'entrer avec un mot de passe existant est une facon de
// le perdre.
const { handleSubmit, resetForm } = useForm({
  validationSchema: schemaConnexion,
  initialValues: { email: '', mot_de_passe: '' },
})
const erreur = ref('')

// Les comptes de demonstration, cliquables : changer de role prend deux clics.
// C'est ce qui rend une demonstration a cinq roles tenable en dix minutes
// (regle d'or n°3).
const COMPTES = [
  { email: 'lea@exemple.fr', qui: 'Cliente', couleur: '#16a34a' },
  { email: 'karim@exemple.fr', qui: 'Vendeur', couleur: '#2563eb' },
  { email: 'nadia@exemple.fr', qui: 'Gestion', couleur: '#0d9488' },
  { email: 'rachid@exemple.fr', qui: 'Entrepot', couleur: '#0d9488' },
  { email: 'amine@exemple.fr', qui: 'Livreur', couleur: '#7c3aed' },
  { email: 'admin@rivdinde.local', qui: 'Admin', couleur: '#b91c1c' },
  { email: 'ines@exemple.fr', qui: 'En attente', couleur: '#93590a' },
]

function remplir(compte: (typeof COMPTES)[number]) {
  // `resetForm` plutot que deux `setFieldValue` : il remet aussi les champs a
  // l'etat « pas encore touche », donc aucune erreur d'un essai precedent ne
  // reste affichee sous un champ qu'on vient de remplir pour la personne.
  resetForm({ values: { email: compte.email, mot_de_passe: 'Demonstration!2026' } })
  erreur.value = ''
}

const valider = handleSubmit(async (saisie) => {
  erreur.value = ''
  try {
    await session.connecter(saisie.email, saisie.mot_de_passe)
    // Un client retourne au catalogue, ou il commande ; les autres roles
    // entrent dans leur espace de travail.
    await routeur.push({
      name: session.enAttenteDeValidation ? 'en-attente' : accueilDuRole(session.role),
    })
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Connexion impossible.'
  }
})

</script>

<template>
  <div class="flex min-h-screen w-full bg-atelier">
    <PanneauMarque />

    <main class="flex flex-1 items-center justify-center px-6 py-12">
      <form
        class="w-full max-w-[380px] animate-[apparition_0.2s_ease-out]"
        @submit.prevent="valider"
      >
        <RouterLink
          to="/"
          class="mb-6 inline-flex items-center gap-2 text-[13px] text-encre-douce
                 transition-colors duration-150 hover:text-marque-fonce"
        >
          <ArrowLeft :size="15" />
          Retour au catalogue
        </RouterLink>

        <div class="mb-6 lg:hidden">
          <LogoRivDinde variante="complet" :taille="76" />
        </div>

        <h2 class="text-[26px] font-semibold tracking-tight text-encre">Connexion</h2>
        <p class="mt-1 mb-7 text-[14px] text-encre-douce">
          Entrez vos identifiants pour retrouver votre espace.
        </p>

        <div class="flex flex-col gap-4">
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
            autocomplete="current-password"
          />
        </div>

        <p v-if="erreur" class="bandeau bandeau-erreur mt-4" role="alert">
          <ShieldAlert :size="16" class="mt-px shrink-0" />
          {{ erreur }}
        </p>

        <button type="submit" class="bouton-marque mt-6 w-full" :disabled="session.chargement">
          <LogIn :size="17" />
          {{ session.chargement ? 'Connexion…' : 'Se connecter' }}
        </button>

        <p class="mt-5 text-center text-[13.5px] text-encre-douce">
          Pas encore de compte ?
          <RouterLink to="/inscription" class="font-semibold text-marque-fonce hover:underline">
            En creer un
          </RouterLink>
        </p>

        <div class="mt-8 border-t border-trait pt-6">
          <p class="mb-3 text-center text-[11px] font-semibold tracking-wider text-encre-douce
                    uppercase">
            Comptes de demonstration
          </p>
          <div class="flex flex-wrap justify-center gap-2">
            <button
              v-for="compte in COMPTES"
              :key="compte.email"
              type="button"
              class="rounded-full border border-trait bg-papier px-3 py-1.5 text-[11.5px]
                     font-semibold transition-colors duration-150 hover:bg-atelier"
              :style="{ color: compte.couleur }"
              :title="compte.email"
              @click="remplir(compte)"
            >
              {{ compte.qui }}
            </button>
          </div>
        </div>
      </form>
    </main>
  </div>
</template>
