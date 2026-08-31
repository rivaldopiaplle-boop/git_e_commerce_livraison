<script setup lang="ts">
// Mon profil — repris de `ProfilPage.tsx` du projet banque (D-76, D-77).
//
// Ce qui donne son sérieux à cet écran, et qui manquait : **l'identité est
// gelée**. Nom, prénom et date de naissance ne se changent que par une demande
// motivée, arbitrée par un administrateur. Les coordonnées, elles, se
// corrigent directement.
//
// Sur une place de marché, l'identité engage : un vendeur validé sur un nom ne
// doit pas pouvoir en changer seul après coup.
//
// « Profil » et « Paramètres » restent deux écrans distincts, comme chez
// banque : le profil dit QUI on est, les paramètres COMMENT l'application se
// comporte.
import { Clock, Lock, Mail, Pencil, Save, ShieldCheck, Phone } from '@lucide/vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { profil as api, type Profil } from '../api/espaces'
import Popup from '../composants/Popup.vue'
import Volet from '../composants/Volet.vue'
import { useNotification } from '../notifications'

const notifier = useNotification()
const routeur = useRouter()

const donnees = ref<Profil | null>(null)
const chargement = ref(true)
const occupe = ref(false)

const email = ref('')
const telephone = ref('')

const demande = ref(false)
const nouveauNom = ref('')
const nouveauPrenom = ref('')
const motif = ref('')

async function charger() {
  chargement.value = true
  try {
    donnees.value = await api.lire()
    email.value = donnees.value.coordonnees.email
    telephone.value = donnees.value.coordonnees.telephone
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const modifie = computed(
  () =>
    donnees.value !== null
    && (email.value !== donnees.value.coordonnees.email
      || telephone.value !== donnees.value.coordonnees.telephone),
)

const enAttente = computed(
  () => (donnees.value?.demandes ?? []).filter((d) => d.statut === 'EN_ATTENTE'),
)

const initiales = computed(() => {
  const identite = donnees.value?.identite
  if (!identite) return '?'
  return `${identite.prenom.charAt(0)}${identite.nom.charAt(0)}`.toUpperCase()
})

const TONS: Record<string, 'success' | 'warn' | 'danger' | 'secondary'> = {
  ACCEPTEE: 'success',
  EN_ATTENTE: 'warn',
  REFUSEE: 'danger',
}

async function enregistrer() {
  occupe.value = true
  try {
    donnees.value = await api.modifierCoordonnees({
      email: email.value,
      telephone: telephone.value,
    })
    notifier.succes('Vos coordonnées sont à jour.')
  } catch (echec) {
    notifier.echec(echec)
  } finally {
    occupe.value = false
  }
}

function ouvrirDemande() {
  nouveauNom.value = donnees.value?.identite.nom ?? ''
  nouveauPrenom.value = donnees.value?.identite.prenom ?? ''
  motif.value = ''
  demande.value = true
}

async function envoyerDemande() {
  const champs: Record<string, string> = {}
  if (nouveauNom.value && nouveauNom.value !== donnees.value?.identite.nom) {
    champs.NOM = nouveauNom.value
  }
  if (nouveauPrenom.value && nouveauPrenom.value !== donnees.value?.identite.prenom) {
    champs.PRENOM = nouveauPrenom.value
  }
  if (!Object.keys(champs).length) {
    notifier.echec('Modifiez au moins un champ avant d’envoyer la demande.')
    return
  }

  occupe.value = true
  try {
    await api.demanderModification(champs, motif.value)
    demande.value = false
    await charger()
    notifier.succes('Votre demande part à l’administration. Vous serez prévenu de sa décision.')
  } catch (echec) {
    notifier.echec(echec)
  } finally {
    occupe.value = false
  }
}

const quand = (date: string | null) =>
  date ? new Date(date).toLocaleDateString('fr-FR') : '—'
</script>

<template>
  <div v-if="donnees" class="mx-auto max-w-[1000px] animate-[apparition_0.2s_ease-out]">
    <div class="grid gap-4 lg:grid-cols-[minmax(240px,300px)_1fr]">
      <!-- Qui je suis -->
      <aside class="flex flex-col gap-4">
        <div class="carte p-5 text-center">
          <span
            class="mx-auto flex h-16 w-16 items-center justify-center rounded-full text-[22px]
                   font-bold text-white"
            :style="{ background: 'var(--accent)' }"
          >
            {{ initiales }}
          </span>
          <b class="mt-3 block text-[17px]">
            {{ donnees.identite.prenom }} {{ donnees.identite.nom }}
          </b>
          <span class="text-[12.5px] text-encre-douce">{{ donnees.coordonnees.email }}</span>

          <div class="mt-3 flex justify-center gap-2">
            <Tag :value="donnees.identite.libelle_role" severity="info" />
            <Tag
              :value="donnees.identite.statut_compte.toLowerCase().replace(/_/g, ' ')"
              :severity="donnees.identite.statut_compte === 'ACTIF' ? 'success' : 'warn'"
            />
          </div>

          <dl class="mt-4 flex flex-col gap-2 border-t border-trait-doux pt-3 text-[12px]">
            <div class="flex justify-between gap-2">
              <dt class="text-encre-douce">Membre depuis</dt>
              <dd class="font-semibold">{{ quand(donnees.identite.date_inscription) }}</dd>
            </div>
          </dl>
        </div>

        <div class="carte p-5">
          <b class="flex items-center gap-2 text-[13px]">
            <ShieldCheck :size="15" /> Sécurité
          </b>
          <p class="mt-1.5 text-[12px] leading-relaxed text-encre-douce">
            Mot de passe, notifications et affichage se règlent dans les paramètres.
          </p>
          <Button
            label="Ouvrir les paramètres"
            severity="secondary"
            outlined
            size="small"
            class="mt-3 w-full"
            @click="routeur.push({ name: 'parametres' })"
          />
        </div>
      </aside>

      <!-- Ce qui se change, et ce qui se demande -->
      <div class="flex flex-col gap-4">
        <section class="carte">
          <h3 class="carte-titre">
            <span class="flex items-center gap-2">
              <Lock :size="14" /> Identité
              <span class="font-normal text-encre-douce">— champs gelés</span>
            </span>
            <Button
              label="Demander une correction"
              severity="secondary"
              outlined
              size="small"
              @click="ouvrirDemande"
            >
              <template #icon><Pencil :size="14" /></template>
            </Button>
          </h3>

          <div class="p-4">
            <Message v-if="enAttente.length" severity="warn" :closable="false" class="mb-4">
              {{ enAttente.length }} demande(s) en attente de décision. Les champs concernés
              seront mis à jour dès l'approbation.
            </Message>

            <div class="grid gap-3 sm:grid-cols-2">
              <div
                v-for="champ in [
                  { libelle: 'Prénom', valeur: donnees.identite.prenom },
                  { libelle: 'Nom', valeur: donnees.identite.nom },
                  { libelle: 'Rôle', valeur: donnees.identite.libelle_role,
                    aide: 'Attribué par l\'administration' },
                ]"
                :key="champ.libelle"
                class="rounded-lg border border-trait bg-atelier px-3.5 py-2.5"
              >
                <span class="etiquette flex items-center gap-1">
                  <Lock :size="10" /> {{ champ.libelle }}
                </span>
                <b class="mt-0.5 block text-[13.5px]">{{ champ.valeur }}</b>
                <span v-if="champ.aide" class="text-[11px] text-encre-douce">{{ champ.aide }}</span>
              </div>
            </div>

            <p class="mt-3 text-[11.5px] leading-relaxed text-encre-douce">
              Sur une place de marché, l'identité engage : une boutique est validée sur un nom.
              C'est pourquoi ces champs ne se modifient que par une demande validée.
            </p>
          </div>
        </section>

        <section class="carte">
          <h3 class="carte-titre">
            <span>Coordonnées <span class="font-normal text-encre-douce">— modifiables
              directement</span></span>
            <Button
              label="Enregistrer"
              size="small"
              :disabled="!modifie || occupe"
              @click="enregistrer"
            >
              <template #icon><Save :size="14" /></template>
            </Button>
          </h3>

          <div class="grid gap-3 p-4 sm:grid-cols-2">
            <label class="flex flex-col gap-1.5">
              <span class="etiquette flex items-center gap-1"><Mail :size="11" /> Adresse e-mail</span>
              <InputText v-model="email" size="small" />
              <span class="text-[11px] text-encre-douce">
                Elle sert à la connexion et aux notifications.
              </span>
            </label>
            <label class="flex flex-col gap-1.5">
              <span class="etiquette flex items-center gap-1"><Phone :size="11" /> Téléphone</span>
              <InputText v-model="telephone" size="small" placeholder="+33612345678" />
              <span class="text-[11px] text-encre-douce">
                Utilisé par le livreur, en numéro masqué.
              </span>
            </label>
          </div>
        </section>

        <section class="carte">
          <h3 class="carte-titre">
            <span class="flex items-center gap-2"><Clock :size="14" /> Mes demandes de correction</span>
          </h3>
          <div v-if="!donnees.demandes.length" class="vide">
            <b class="vide-titre">Aucune demande déposée</b>
            <p class="vide-texte">
              Une correction d'identité laisse une trace : c'est ce qui permet de la justifier
              plus tard.
            </p>
          </div>
          <div v-for="entree in donnees.demandes" :key="entree.id" class="ligne">
            <span class="min-w-0 flex-1">
              <b class="block truncate">
                {{ entree.champs.map((c) => c.libelle).join(', ') }}
              </b>
              <span class="text-[11.2px] text-encre-douce">
                {{ quand(entree.date_demande) }}
                <template v-if="entree.motif"> · « {{ entree.motif }} »</template>
              </span>
              <span
                v-if="entree.commentaire_decision"
                class="mt-0.5 block text-[11.2px] text-encre-douce"
              >
                Réponse : {{ entree.commentaire_decision }}
              </span>
            </span>
            <Tag :value="entree.libelle_statut" :severity="TONS[entree.statut] ?? 'secondary'" />
          </div>
        </section>
      </div>
    </div>

    <!-- Le volet garde l'état des demandes près de l'œil, comme chez banque -->
    <Volet titre="Mes demandes d'identité">
      <p class="text-[11.5px] leading-relaxed text-encre-douce">
        Nom, prénom et date de naissance étant gelés, chaque correction passe par une demande.
        Voici l'état des vôtres.
      </p>
      <div v-if="!donnees.demandes.length" class="vide !py-6">
        <b class="vide-titre">Aucune demande</b>
      </div>
      <ul v-else class="mt-3 flex flex-col gap-2">
        <li
          v-for="entree in donnees.demandes.slice(0, 5)"
          :key="entree.id"
          class="rounded-lg border border-trait bg-papier p-2.5 text-[11.5px]"
        >
          <Tag
            :value="entree.libelle_statut"
            :severity="TONS[entree.statut] ?? 'secondary'"
            class="!text-[10px]"
          />
          <span class="mt-1 block text-encre-douce">
            {{ entree.champs.map((c) => c.libelle).join(', ') }} — {{ quand(entree.date_demande) }}
          </span>
        </li>
      </ul>
    </Volet>

    <!-- La demande : formulaire court, donc popup (D-60) -->
    <Popup
      v-if="demande"
      titre="Demander une correction d'identité"
      explication="Un administrateur examinera votre demande. Expliquez pourquoi la
                   correction est nécessaire : sans motif, elle sera refusée."
      @fermer="demande = false"
    >
      <div class="flex flex-col gap-3">
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Prénom</span>
          <InputText v-model="nouveauPrenom" size="small" />
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Nom</span>
          <InputText v-model="nouveauNom" size="small" />
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Motif <span class="text-alerte">obligatoire</span></span>
          <Textarea
            v-model="motif"
            rows="3"
            auto-resize
            placeholder="Nom d'usage après mariage, faute de saisie à l'inscription…"
          />
        </label>
      </div>

      <template #actions>
        <Button label="Annuler" severity="secondary" outlined size="small"
                @click="demande = false" />
        <Button
          label="Envoyer la demande"
          size="small"
          :disabled="occupe || !motif.trim()"
          @click="envoyerDemande"
        />
      </template>
    </Popup>
  </div>

  <div v-else-if="chargement" class="mx-auto max-w-[1000px] p-6 text-[13px] text-encre-douce">
    Chargement du profil…
  </div>
</template>
