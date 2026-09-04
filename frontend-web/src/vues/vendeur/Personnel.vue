<script setup lang="ts">
// Le personnel de la boutique.
//
// Deux choses corrigées ici, et la seconde était un vrai trou :
//
//   · l'écran restait une pile de lignes faites à la main, alors que toutes
//     les autres listes du projet passent par `Liste.vue` avec ses
//     boutons-symboles. C'était l'une des quatre dernières ;
//   · **on créait des comptes sans jamais pouvoir en retirer un.** Un employé
//     qui partait gardait son accès aux commandes et au stock, indéfiniment.
//     On suspend plutôt qu'on supprime : les ajustements de stock qu'il a
//     signés doivent rester attribuables (D-13, D-95).
//
// La matrice des droits reste affichée en toutes lettres. C'est la première
// question d'un commerçant avant de créer un compte pour son employé, et y
// répondre dans l'interface évite un appel au support (D-04).
import {
  AlertTriangle, Check, Mail, Power, ShieldCheck, UserPlus, Users, X,
} from '@lucide/vue'
import { useForm } from 'vee-validate'
import { computed, ref } from 'vue'

import { useRafraichissement } from '../../rafraichissement'
import { api, EchecApi } from '../../api/client'
import { espaces, type MembrePersonnel } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import ChampTexte from '../../composants/ChampTexte.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Popup from '../../composants/Popup.vue'
import Volet from '../../composants/Volet.vue'
import { useNotification } from '../../notifications'
import { schemaGestionnaire } from '../../validation'

type Ligne = MembrePersonnel & {
  actif: boolean
  statut_compte: string
  derniere_connexion: string | null
  [cle: string]: unknown
}

const notifier = useNotification()
const personnel = ref<Ligne[]>([])
const acces = ref<{ libelle: string; autorise: boolean }[]>([])
const chargement = ref(true)
const selection = ref<Ligne | null>(null)

const creation = ref(false)
const occupe = ref(false)
const erreur = ref('')

const bascule = ref<Ligne | null>(null)
const motif = ref('')

async function charger() {
  chargement.value = true
  try {
    const donnees = await espaces.vendeur.personnel()
    personnel.value = donnees.personnel as Ligne[]
    acces.value = donnees.acces
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger)

const actifs = computed(() => personnel.value.filter((membre) => membre.actif).length)

const quand = (date: string | null) =>
  date ? new Date(date).toLocaleDateString('fr-FR') : 'jamais connecté'

const colonnes: Colonne<Ligne>[] = [
  { cle: 'personne', titre: 'Employé' },
  // Ce qu'il a REELLEMENT fait (D-80) : le vendeur avait un employé et aucun
  // moyen de savoir ce qu'il faisait de ses journées.
  { cle: 'activite', titre: 'Son travail', masquerSous: 'sm' },
  { cle: 'connexion', titre: 'Dernière action', masquerSous: 'md' },
  { cle: 'statut', titre: 'Accès', largeur: 110, aligne: 'centre' },
]

/**
 * La saisie passe par `vee-validate` — N-2.
 *
 * Le formulaire validait à la main : un `minlength` sur le mot de passe, et le
 * reste découvert au retour du serveur. Une adresse e-mail déjà prise revenait
 * en bandeau rouge en haut de la popup, loin du champ fautif.
 *
 * Le schéma est celui de l'inscription : la règle de mot de passe a une seule
 * définition dans tout le projet, et elle ne peut plus diverger d'un écran à
 * l'autre.
 */
const { handleSubmit, resetForm, setFieldError } = useForm({
  validationSchema: schemaGestionnaire,
  initialValues: { prenom: '', nom: '', email: '', mot_de_passe: '' },
})

const creer = handleSubmit(async (saisie) => {
  erreur.value = ''
  occupe.value = true
  try {
    await espaces.vendeur.creerGestionnaire(saisie)
    notifier.succes(`Le compte de ${saisie.prenom} est créé.`)
    creation.value = false
    resetForm()
    await charger()
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Création refusée.'
    // Le message du serveur se pose SOUS le champ concerné quand on sait
    // lequel : « cette adresse est déjà prise » en haut de la popup oblige à
    // relire les quatre champs pour trouver lequel corriger.
    if (/e-?mail|adresse/i.test(erreur.value)) setFieldError('email', erreur.value)
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
})

/** Dire ce que l'action fait vraiment : suspendre n'est pas supprimer. */
const explicationBascule = computed(() =>
  bascule.value?.actif
    ? 'Le compte n’est pas supprimé : les ajustements de stock qu’il a signés doivent '
      + 'rester attribuables. La personne ne pourra simplement plus entrer.'
    : 'La personne pourra de nouveau préparer les commandes et ajuster le stock.',
)

function demanderBascule(membre: Ligne) {
  bascule.value = membre
  motif.value = ''
  erreur.value = ''
}

async function confirmerBascule() {
  if (!bascule.value) return
  occupe.value = true
  erreur.value = ''
  const suspendait = bascule.value.actif
  try {
    await api.post(`/vendeurs/personnel/${bascule.value.id}/basculer`, { motif: motif.value })
    notifier.succes(
      suspendait ? 'Accès suspendu' : 'Accès rétabli',
      suspendait
        ? 'La personne ne peut plus entrer, et son historique reste intact.'
        : 'La personne peut de nouveau préparer les commandes et ajuster le stock.',
    )
    bascule.value = null
    selection.value = null
    await charger()
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Action refusée.'
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <div class="mb-4 flex items-start justify-between gap-3">
      <p class="text-[12.5px] text-encre-douce">
        Vos employés préparent les commandes et corrigent le stock. Ils ne sont pas
        rattachés à la plateforme, mais à votre boutique.
      </p>
      <button type="button" class="bouton-accent shrink-0" @click="creation = true">
        <UserPlus :size="15" />
        Créer un compte
      </button>
    </div>

    <Liste
      :colonnes="colonnes"
      :lignes="personnel"
      :cle-ligne="(membre) => membre.id"
      :chargement="chargement"
      :recherche="(m) => `${m.utilisateur.prenom} ${m.utilisateur.nom} ${m.utilisateur.email}`"
      :active="(m) => selection?.id === m.id"
      @ligne-cliquee="(m) => (selection = selection?.id === m.id ? null : m)"
      placeholder="Nom, prénom, adresse e-mail…"
    >
      <template #col-personne="{ ligne }">
        <span class="flex min-w-0 items-center gap-2.5">
          <span
            class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[12px]
                   font-bold text-white"
            :style="{ background: ligne.actif ? 'var(--accent)' : 'var(--color-encre-douce)' }"
          >
            {{ ligne.utilisateur.prenom.charAt(0).toUpperCase() }}
          </span>
          <span class="min-w-0">
            <b class="block truncate">
              {{ ligne.utilisateur.prenom }} {{ ligne.utilisateur.nom }}
            </b>
            <span class="flex items-center gap-1 text-[11.2px] text-encre-douce">
              <Mail :size="11" /> {{ ligne.utilisateur.email }}
            </span>
          </span>
        </span>
      </template>

      <template #col-activite="{ ligne }">
        <span class="flex flex-wrap items-center gap-1.5">
          <span class="badge badge-cours">
            {{ ligne.commandes_preparees ?? 0 }} commande(s) préparée(s)
          </span>
          <span class="badge badge-neutre">
            {{ ligne.ajustements_stock ?? 0 }} ajustement(s)
          </span>
        </span>
      </template>

      <template #col-connexion="{ ligne }">
        <span class="text-encre-douce">
          {{ ligne.derniere_action ? quand(ligne.derniere_action) : 'aucune action' }}
        </span>
      </template>

      <template #col-statut="{ ligne }">
        <span class="badge" :class="ligne.actif ? 'badge-ok' : 'badge-neutre'">
          {{ ligne.actif ? 'Actif' : 'Suspendu' }}
        </span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Voir ce que cette personne peut faire"
          :icone="ShieldCheck"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
        <ActionLigne
          :titre="ligne.actif ? 'Suspendre son accès' : 'Rétablir son accès'"
          :icone="Power"
          :ton="ligne.actif ? 'danger' : 'accent'"
          @click="demanderBascule(ligne)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Users :size="30" class="text-trait" />
          <b class="vide-titre">Vous travaillez seul pour l'instant</b>
          <p class="vide-texte">
            Créez un compte pour un employé : il pourra préparer les commandes et corriger
            le stock, sans jamais voir vos prix d'achat ni votre chiffre d'affaires.
          </p>
          <button type="button" class="bouton-accent mt-4" @click="creation = true">
            <UserPlus :size="15" /> Créer un compte
          </button>
        </div>
      </template>
    </Liste>

    <!-- Ce que le personnel voit, et surtout ce qu'il ne voit pas -->
    <Volet :titre="selection
      ? `${selection.utilisateur.prenom} ${selection.utilisateur.nom}`
      : 'Droits du personnel'">
      <div class="flex flex-col gap-4 p-4 text-[12.5px]">
        <template v-if="selection">
          <div class="kpi">
            <div class="kpi-nombre">{{ selection.actif ? 'Actif' : 'Suspendu' }}</div>
            <div class="kpi-libelle">
              Dernière visite : {{ quand(selection.derniere_connexion) }}
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div class="kpi">
              <div class="kpi-nombre">{{ selection.commandes_preparees ?? 0 }}</div>
              <div class="kpi-libelle">Commandes préparées</div>
            </div>
            <div class="kpi">
              <div class="kpi-nombre">{{ selection.ajustements_stock ?? 0 }}</div>
              <div class="kpi-libelle">Ajustements de stock</div>
            </div>
          </div>
        </template>
        <div v-if="!selection" class="kpi">
          <div class="kpi-nombre">{{ actifs }} / {{ personnel.length }}</div>
          <div class="kpi-libelle">Comptes actifs</div>
        </div>

        <section class="carte">
          <h4 class="carte-titre"><span>Ce à quoi ils ont accès</span></h4>
          <div v-for="droit in acces" :key="droit.libelle" class="ligne">
            <component
              :is="droit.autorise ? Check : X"
              :size="15"
              class="shrink-0"
              :class="droit.autorise ? 'text-succes' : 'text-alerte'"
            />
            <span class="flex-1" :class="droit.autorise ? '' : 'text-encre-douce line-through'">
              {{ droit.libelle }}
            </span>
          </div>
          <p class="border-t border-trait-doux px-4 py-3 text-[11.5px] leading-relaxed
                    text-encre-douce">
            Ces limites sont vérifiées par le serveur, pas seulement masquées à l'écran :
            un employé qui appellerait l'adresse du chiffre d'affaires recevrait un refus.
          </p>
        </section>

        <button
          v-if="selection"
          type="button"
          :class="selection.actif ? 'bouton-neutre' : 'bouton-accent'"
          @click="demanderBascule(selection)"
        >
          <Power :size="15" />
          {{ selection.actif ? 'Suspendre son accès' : 'Rétablir son accès' }}
        </button>
      </div>
    </Volet>

    <!-- Créer un compte -->
    <Popup
      v-if="creation"
      titre="Créer un compte gestionnaire"
      explication="Ce compte appartient à votre boutique. Il n'a jamais accès au chiffre
                   d'affaires ni aux prix, et vous pouvez le suspendre à tout moment."
      @fermer="creation = false"
    >
      <form class="flex flex-col gap-3" @submit.prevent="creer">
        <div class="flex gap-3">
          <div class="flex-1"><ChampTexte nom="prenom" label="Prénom" /></div>
          <div class="flex-1"><ChampTexte nom="nom" label="Nom" /></div>
        </div>
        <ChampTexte nom="email" label="Adresse e-mail" type="email" :icone="Mail" />
        <!-- En clair, et c'est voulu : le vendeur doit pouvoir le lire pour le
             dicter à son employé. Ce n'est pas son mot de passe à lui. -->
        <ChampTexte
          nom="mot_de_passe"
          label="Mot de passe provisoire"
          aide="Dix caractères au minimum. Communiquez-le à votre employé, qui le changera."
        />

        <p v-if="erreur" class="bandeau bandeau-erreur">
          <AlertTriangle :size="15" class="mt-px shrink-0" /> {{ erreur }}
        </p>
      </form>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="creation = false">
          Annuler
        </button>
        <button type="button" class="bouton-accent !py-2" :disabled="occupe" @click="creer">
          <Check :size="15" /> Créer le compte
        </button>
      </template>
    </Popup>

    <!-- Suspendre ou rétablir -->
    <Popup
      v-if="bascule"
      :titre="bascule.actif
        ? `Suspendre l'accès de ${bascule.utilisateur.prenom}`
        : `Rétablir l'accès de ${bascule.utilisateur.prenom}`"
      :explication="explicationBascule"
      @fermer="bascule = null"
    >
      <label v-if="bascule.actif" class="flex flex-col gap-1.5">
        <span class="etiquette">Motif — la personne le lira</span>
        <textarea
          v-model="motif"
          rows="3"
          class="champ-clair"
          placeholder="Fin de contrat, congé prolongé, changement de poste…"
        />
      </label>

      <p v-if="erreur" class="bandeau bandeau-erreur mt-3">
        <AlertTriangle :size="15" class="mt-px shrink-0" /> {{ erreur }}
      </p>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="bascule = null">
          Annuler
        </button>
        <button
          type="button"
          class="bouton-accent !py-2"
          :disabled="occupe || (bascule.actif && !motif.trim())"
          @click="confirmerBascule"
        >
          <Power :size="15" />
          {{ bascule.actif ? 'Suspendre' : 'Rétablir' }}
        </button>
      </template>
    </Popup>
  </div>
</template>
