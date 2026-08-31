<script setup lang="ts">
// Les paramètres — repris de `ParametresPage.tsx` du projet banque (D-76).
//
// Écran distinct du profil, et c'est volontaire : le profil dit **qui on est**,
// les paramètres disent **comment l'application se comporte**. Les fusionner
// produit un écran fourre-tout que personne ne relit.
//
// Quatre sections, comme chez banque : sécurité, notifications, affichage,
// données.
import { Bell, Eye, KeyRound, Monitor, ShieldCheck, Trash2 } from '@lucide/vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Password from 'primevue/password'
import SelectButton from 'primevue/selectbutton'
import ToggleSwitch from 'primevue/toggleswitch'
import { onMounted, ref, watch } from 'vue'

import { profil as api, type Parametres } from '../api/espaces'
import Onglets from '../composants/Onglets.vue'
import Popup from '../composants/Popup.vue'
import Volet from '../composants/Volet.vue'
import { useNotification } from '../notifications'
import { useAuthentification } from '../stores/authentification'

const notifier = useNotification()
const session = useAuthentification()

const reglages = ref<Parametres | null>(null)
const chargement = ref(true)
const occupe = ref(false)
const onglet = ref('securite')

const ancien = ref('')
const nouveau = ref('')
const confirmation = ref('')

const deconnexionDemandee = ref(false)

const DENSITES = [
  { libelle: 'Normale', valeur: 'NORMALE' },
  { libelle: 'Compacte', valeur: 'COMPACTE' },
]

onMounted(async () => {
  try {
    reglages.value = await api.parametres()
  } finally {
    chargement.value = false
  }
})

/** Un réglage s'enregistre au moment où on le bascule.
 *
 *  Pas de bouton « Enregistrer » ici : un interrupteur qui ne fait rien tant
 *  qu'on n'a pas validé plus bas est le meilleur moyen de perdre un réglage.
 */
async function enregistrer(modification: Partial<Parametres>, libelle: string) {
  occupe.value = true
  try {
    reglages.value = await api.modifierParametres(modification)
    notifier.succes(libelle)
  } catch (echec) {
    notifier.echec(echec)
  } finally {
    occupe.value = false
  }
}

watch(
  () => reglages.value?.densite,
  (densite) => {
    if (densite) document.documentElement.dataset.densite = densite.toLowerCase()
  },
)

async function changerMotDePasse() {
  if (nouveau.value !== confirmation.value) {
    notifier.echec('Les deux mots de passe ne correspondent pas.')
    return
  }
  occupe.value = true
  try {
    await api.changerMotDePasse(ancien.value, nouveau.value)
    ancien.value = nouveau.value = confirmation.value = ''
    notifier.succes('Votre mot de passe est changé.')
  } catch (echec) {
    notifier.echec(echec)
  } finally {
    occupe.value = false
  }
}
</script>

<template>
  <div v-if="reglages" class="mx-auto max-w-[820px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'securite', libelle: 'Sécurité' },
        { cle: 'notifications', libelle: 'Notifications' },
        { cle: 'affichage', libelle: 'Affichage' },
        { cle: 'donnees', libelle: 'Mes données' },
      ]"
    />

    <!-- ── Sécurité ─────────────────────────────────────────────────── -->
    <template v-if="onglet === 'securite'">
      <section class="carte">
        <h3 class="carte-titre">
          <span class="flex items-center gap-2"><KeyRound :size="14" /> Mot de passe</span>
          <span class="text-[11px] font-semibold text-encre-douce">dix caractères minimum</span>
        </h3>
        <form class="grid gap-3 p-4 sm:grid-cols-2" @submit.prevent="changerMotDePasse">
          <label class="flex flex-col gap-1.5 sm:col-span-2">
            <span class="etiquette">Mot de passe actuel</span>
            <Password v-model="ancien" :feedback="false" toggle-mask input-class="w-full"
                      class="w-full" size="small" />
            <span class="text-[11px] text-encre-douce">
              On vous le demande parce qu'une session laissée ouverte suffirait sinon à
              prendre votre compte définitivement.
            </span>
          </label>
          <label class="flex flex-col gap-1.5">
            <span class="etiquette">Nouveau mot de passe</span>
            <Password v-model="nouveau" toggle-mask input-class="w-full" class="w-full"
                      size="small" prompt-label="Choisissez un mot de passe"
                      weak-label="Faible" medium-label="Moyen" strong-label="Solide" />
          </label>
          <label class="flex flex-col gap-1.5">
            <span class="etiquette">Confirmation</span>
            <Password v-model="confirmation" :feedback="false" toggle-mask
                      input-class="w-full" class="w-full" size="small" />
          </label>
          <div class="sm:col-span-2">
            <Button
              type="submit"
              label="Changer mon mot de passe"
              size="small"
              :disabled="occupe || !ancien || !nouveau"
            />
          </div>
        </form>
      </section>

      <section class="carte mt-4">
        <h3 class="carte-titre">
          <span class="flex items-center gap-2"><ShieldCheck :size="14" /> Session</span>
        </h3>
        <div class="p-4">
          <p class="text-[12.5px] text-encre-douce">
            Vous êtes connecté en tant que <b class="text-encre">{{ session.utilisateur?.email }}</b>.
            Se déconnecter vide aussi le panier de cette machine.
          </p>
          <Button
            label="Se déconnecter"
            severity="danger"
            outlined
            size="small"
            class="mt-3"
            @click="deconnexionDemandee = true"
          />
        </div>
      </section>
    </template>

    <!-- ── Notifications ────────────────────────────────────────────── -->
    <template v-else-if="onglet === 'notifications'">
      <section class="carte">
        <h3 class="carte-titre">
          <span class="flex items-center gap-2"><Bell :size="14" /> Comment être prévenu</span>
        </h3>

        <div class="ligne">
          <span class="min-w-0 flex-1">
            <b class="block">Dans l'application</b>
            <span class="text-[11.2px] text-encre-douce">
              Toujours actif : une information critique n'a jamais un canal unique.
            </span>
          </span>
          <ToggleSwitch :model-value="true" disabled />
        </div>

        <div class="ligne">
          <span class="min-w-0 flex-1">
            <b class="block">Par courriel</b>
            <span class="text-[11.2px] text-encre-douce">
              Changements de statut de commande, décisions vous concernant.
            </span>
          </span>
          <ToggleSwitch
            :model-value="reglages.notifications_email"
            :disabled="occupe"
            @update:model-value="(v) => enregistrer({ notifications_email: v },
              v ? 'Courriels activés.' : 'Courriels désactivés.')"
          />
        </div>

        <div class="ligne">
          <span class="min-w-0 flex-1">
            <b class="block">Notifications poussées</b>
            <span class="text-[11.2px] text-encre-douce">
              Sur l'application mobile, quand elle est installée.
            </span>
          </span>
          <ToggleSwitch
            :model-value="reglages.notifications_push"
            :disabled="occupe"
            @update:model-value="(v) => enregistrer({ notifications_push: v },
              v ? 'Notifications poussées activées.' : 'Notifications poussées désactivées.')"
          />
        </div>

        <div class="ligne">
          <span class="min-w-0 flex-1">
            <b class="block">Offres et nouveautés</b>
            <span class="text-[11.2px] text-encre-douce">
              Désactivé par défaut — on ne s'inscrit pas à la publicité sans le vouloir.
            </span>
          </span>
          <ToggleSwitch
            :model-value="reglages.courriels_promotionnels"
            :disabled="occupe"
            @update:model-value="(v) => enregistrer({ courriels_promotionnels: v },
              v ? 'Vous recevrez nos offres.' : 'Vous ne recevrez plus d’offres.')"
          />
        </div>
      </section>
    </template>

    <!-- ── Affichage ────────────────────────────────────────────────── -->
    <template v-else-if="onglet === 'affichage'">
      <section class="carte">
        <h3 class="carte-titre">
          <span class="flex items-center gap-2"><Monitor :size="14" /> Confort de lecture</span>
        </h3>

        <div class="ligne">
          <span class="min-w-0 flex-1">
            <b class="block">Densité des listes</b>
            <span class="text-[11.2px] text-encre-douce">
              Compacte affiche plus de lignes à l'écran, utile sur un poste de travail.
            </span>
          </span>
          <SelectButton
            :model-value="reglages.densite"
            :options="DENSITES"
            option-label="libelle"
            option-value="valeur"
            :allow-empty="false"
            size="small"
            @update:model-value="(v) => enregistrer({ densite: v }, 'Densité mise à jour.')"
          />
        </div>

        <div class="ligne">
          <span class="min-w-0 flex-1">
            <b class="flex items-center gap-1.5"><Eye :size="12" /> Masquer les montants</b>
            <span class="text-[11.2px] text-encre-douce">
              Remplace les sommes par des points. Pratique pour montrer son écran.
            </span>
          </span>
          <ToggleSwitch
            :model-value="reglages.masquer_montants"
            :disabled="occupe"
            @update:model-value="(v) => enregistrer({ masquer_montants: v },
              v ? 'Les montants sont masqués.' : 'Les montants sont visibles.')"
          />
        </div>

        <div class="ligne">
          <span class="min-w-0 flex-1">
            <b class="block">Couleur de l'interface</b>
            <span class="text-[11.2px] text-encre-douce">
              Elle suit votre rôle et ne se règle pas : c'est ce qui permet de savoir d'un
              coup d'œil dans quel espace on se trouve.
            </span>
          </span>
          <span
            class="h-6 w-10 rounded-md"
            :style="{ background: 'var(--accent)' }"
            aria-hidden="true"
          />
        </div>
      </section>
    </template>

    <!-- ── Mes données ──────────────────────────────────────────────── -->
    <template v-else>
      <section class="carte">
        <h3 class="carte-titre">
          <span>Ce que l'application conserve à votre sujet</span>
        </h3>
        <div class="p-4">
          <ul class="flex flex-col gap-2 text-[12.5px]">
            <li v-for="element in [
              'Votre identité et vos coordonnées',
              'Votre carnet d’adresses et les instructions de livraison',
              'Vos commandes, leurs statuts et leurs factures',
              'Vos avis et vos litiges',
              'Vos préférences de notification',
            ]" :key="element" class="flex gap-2">
              <span class="mt-1.5 h-[5px] w-[5px] shrink-0 rounded-full bg-encre-douce" />
              {{ element }}
            </li>
          </ul>

          <Message severity="info" :closable="false" class="mt-4">
            Rien n'est jamais effacé physiquement : un compte se suspend, une adresse se
            retire du carnet, un avis se masque. Vos commandes passées continuent d'exister
            — c'est ce qui permet de les justifier, y compris en votre faveur.
          </Message>

          <Button
            label="Demander la suppression de mon compte"
            severity="danger"
            outlined
            size="small"
            class="mt-4"
            @click="notifier.info(
              'La demande part à l’administration : un compte lié à des commandes ne peut pas être effacé sans arbitrage.',
              'Demande envoyée')"
          >
            <template #icon><Trash2 :size="14" /></template>
          </Button>
        </div>
      </section>
    </template>

    <Volet titre="Vos réglages">
      <p class="text-[11.5px] leading-relaxed text-encre-douce">
        Chaque réglage s'enregistre au moment où vous le basculez : il n'y a pas de bouton
        « Enregistrer » à ne pas oublier.
      </p>
      <dl class="mt-3 flex flex-col gap-2 text-[12px]">
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Courriels</dt>
          <dd class="font-semibold">{{ reglages.notifications_email ? 'Activés' : 'Coupés' }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Notifications poussées</dt>
          <dd class="font-semibold">{{ reglages.notifications_push ? 'Activées' : 'Coupées' }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Densité</dt>
          <dd class="font-semibold">{{ reglages.densite.toLowerCase() }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Montants</dt>
          <dd class="font-semibold">{{ reglages.masquer_montants ? 'Masqués' : 'Visibles' }}</dd>
        </div>
      </dl>
    </Volet>

    <!-- Une déconnexion est réversible, mais elle surprend : on confirme -->
    <Popup
      v-if="deconnexionDemandee"
      titre="Se déconnecter ?"
      explication="Votre panier n'est pas perdu : il est rattaché à votre compte et vous le
                   retrouverez à la prochaine connexion. Il cesse simplement d'être affiché
                   sur cette machine."
      @fermer="deconnexionDemandee = false"
    >
      <template #actions>
        <Button label="Rester connecté" severity="secondary" outlined size="small"
                @click="deconnexionDemandee = false" />
        <Button label="Se déconnecter" severity="danger" size="small"
                @click="session.deconnecter()" />
      </template>
    </Popup>
  </div>

  <div v-else-if="chargement" class="mx-auto max-w-[820px] p-6 text-[13px] text-encre-douce">
    Chargement des paramètres…
  </div>
</template>
