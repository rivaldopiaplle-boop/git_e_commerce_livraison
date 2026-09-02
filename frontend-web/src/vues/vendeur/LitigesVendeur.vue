<script setup lang="ts">
// Les litiges vus par la boutique — D-94.
//
// Cet écran n'existait pas, et son absence était le trou le plus grave de la
// procédure : un client pouvait ouvrir un litige, un administrateur pouvait le
// trancher, et **le vendeur n'avait aucun moyen de donner sa version**. Une
// place de marché qui condamne sans entendre est une place de marché qu'on
// quitte.
//
// L'ordre de la liste n'est pas décoratif : ce qui attend une réponse passe
// devant. Quelqu'un qui a quarante-huit heures pour répondre n'a que faire des
// dossiers déjà clos.
import { AlertTriangle, Clock, Eye, MessageSquare, Scale } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { espaces, type Litige } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Popup from '../../composants/Popup.vue'
import FicheContextuelle from '../../composants/FicheContextuelle.vue'
import { useNotification } from '../../notifications'

type Ligne = Litige & { [cle: string]: unknown }

const { succes, echec: prevenir } = useNotification()

const litiges = ref<Ligne[]>([])
const chargement = ref(true)
const selection = ref<Ligne | null>(null)
// L'oeil ouvre une popup par-dessus la liste (M-1) : le panneau de droite,
// lui, reste le contexte permanent de la ligne active.
const apercu = ref(false)

const reponseA = ref<Ligne | null>(null)
const texte = ref('')
const envoi = ref(false)
const erreur = ref('')

async function charger() {
  chargement.value = true
  try {
    litiges.value = (await espaces.vendeur.litiges()) as Ligne[]
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

/** Ce qui attend vraiment quelque chose de la boutique. */
const aRepondre = computed(() =>
  litiges.value.filter((d) => !d.date_reponse_vendeur && !['RESOLU', 'REJETE'].includes(d.statut)),
)

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
const quandEtHeure = (date: string | null) =>
  date ? new Date(date).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  }) : '—'

/** Combien d'heures reste-t-il, arrondies à l'heure. */
function heuresRestantes(dossier: Ligne) {
  if (!dossier.date_limite_reponse) return 0
  const reste = new Date(dossier.date_limite_reponse).getTime() - Date.now()
  return Math.max(0, Math.round(reste / 3_600_000))
}

const BADGES: Record<string, string> = {
  OUVERT: 'badge-erreur',
  EN_COURS: 'badge-attente',
  RESOLU: 'badge-ok',
  REJETE: 'badge-neutre',
}

/**
 * L'oeil : on consulte, on ne selectionne pas seulement.
 *
 * Il ouvre la popup ET marque la ligne active, pour que le panneau de
 * droite montre la meme chose une fois la popup refermee.
 */
function consulter(ligne: Ligne) {
  selection.value = ligne
  apercu.value = true
}

const colonnes: Colonne<Ligne>[] = [
  { cle: 'dossier', titre: 'Dossier', champTri: 'id' },
  { cle: 'client', titre: 'Client', champTri: 'client' },
  { cle: 'montant', titre: 'Montant', champTri: 'montant_commande_centimes', aligne: 'droite' },
  { cle: 'echeance', titre: 'Votre réponse' },
  { cle: 'statut', titre: 'Statut', champTri: 'statut' },
]

function ouvrirReponse(dossier: Ligne) {
  reponseA.value = dossier
  texte.value = ''
  erreur.value = ''
}

async function repondre() {
  if (!reponseA.value) return
  envoi.value = true
  erreur.value = ''
  try {
    await espaces.vendeur.repondreLitige(reponseA.value.id, texte.value)
    succes('Votre version est enregistrée',
           'Un administrateur tranchera avec les deux versions sous les yeux.')
    reponseA.value = null
    selection.value = null
    await charger()
  } catch (souci) {
    erreur.value = souci instanceof EchecApi ? souci.erreur.message : 'Envoi impossible.'
    prevenir('Réponse refusée', erreur.value)
  } finally {
    envoi.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <h2 class="text-[21px] font-semibold tracking-tight">Litiges</h2>

    <!-- Ce qui presse, en haut : le délai court, et il court pour vous -->
    <p v-if="aRepondre.length" class="bandeau mt-3">
      <Clock :size="15" class="mt-px shrink-0" />
      <span>
        <b>{{ aRepondre.length }} dossier{{ aRepondre.length > 1 ? 's' : '' }}
        attend{{ aRepondre.length > 1 ? 'ent' : '' }} votre version.</b>
        Sans réponse de votre part dans le délai, l'administrateur tranchera avec les
        seuls éléments du client — et cela figurera au dossier.
      </span>
    </p>

    <Liste
      class="mt-3"
      :colonnes="colonnes"
      :lignes="litiges"
      :cle-ligne="(dossier) => dossier.id"
      :chargement="chargement"
      :recherche="(d) => `${d.id} ${d.client} ${d.commande} ${d.libelle_motif}`"
      :active="(d) => selection?.id === d.id"
      @ligne-cliquee="(d) => (selection = selection?.id === d.id ? null : d)"
      placeholder="Numéro de dossier, client, commande…"
    >
      <template #col-dossier="{ ligne }">
        <span class="flex min-w-0 items-center gap-2">
          <AlertTriangle
            :size="14"
            class="shrink-0"
            :class="ligne.statut === 'OUVERT' ? 'text-alerte' : 'text-encre-douce'"
          />
          <span class="min-w-0">
            <b class="block truncate">N° {{ ligne.id }} — {{ ligne.libelle_motif }}</b>
            <span class="text-[11.2px] text-encre-douce">{{ ligne.commande }}</span>
          </span>
        </span>
      </template>

      <template #col-client="{ ligne }">
        <span class="min-w-0 truncate text-encre-douce">{{ ligne.client }}</span>
      </template>

      <template #col-montant="{ ligne }">
        <b>{{ euros(ligne.montant_commande_centimes) }}</b>
      </template>

      <template #col-echeance="{ ligne }">
        <span v-if="ligne.date_reponse_vendeur" class="badge badge-ok">Version donnée</span>
        <span v-else-if="ligne.delai_expire" class="badge badge-erreur">Délai dépassé</span>
        <span v-else-if="['RESOLU', 'REJETE'].includes(ligne.statut)" class="badge badge-neutre">
          Sans objet
        </span>
        <span v-else class="badge badge-attente">
          {{ heuresRestantes(ligne) }} h restantes
        </span>
      </template>

      <template #col-statut="{ ligne }">
        <span class="badge" :class="BADGES[ligne.statut] ?? 'badge-neutre'">
          {{ ligne.libelle_statut }}
        </span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter le dossier"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="consulter(ligne)"
        />
        <ActionLigne
          :titre="ligne.date_reponse_vendeur
            ? 'Vous avez déjà donné votre version'
            : ligne.delai_expire
              ? 'Le délai de 48 heures est passé'
              : 'Donner votre version des faits'"
          :icone="MessageSquare"
          ton="accent"
          :desactive="!!ligne.date_reponse_vendeur || ligne.delai_expire
            || ['RESOLU', 'REJETE'].includes(ligne.statut)"
          @click="ouvrirReponse(ligne)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Scale :size="30" class="text-trait" />
          <b class="vide-titre">Aucun litige sur vos commandes</b>
          <p class="vide-texte">
            C'est la meilleure nouvelle de cet écran : vos livraisons arrivent comme
            promis.
          </p>
        </div>
      </template>
    </Liste>

    <FicheContextuelle
      v-if="selection"
      :titre="`Litige n° ${selection.id}`"
      :apercu-ouvert="apercu"
      @fermer-apercu="apercu = false"
    >
      <div class="flex flex-col gap-4 p-4 text-[12.5px]">
        <div class="kpi">
          <div class="kpi-nombre">{{ euros(selection.montant_commande_centimes) }}</div>
          <div class="kpi-libelle">Commande {{ selection.commande }}</div>
        </div>

        <section class="carte">
          <h4 class="carte-titre"><span>Ce que dit le client</span></h4>
          <p class="px-4 py-3 leading-relaxed">« {{ selection.description }} »</p>
        </section>

        <section v-if="selection.reponse_vendeur" class="carte">
          <h4 class="carte-titre"><span>Votre version</span></h4>
          <p class="px-4 py-3 leading-relaxed">« {{ selection.reponse_vendeur }} »</p>
        </section>

        <section v-if="selection.resolution" class="carte">
          <h4 class="carte-titre"><span>Décision rendue</span></h4>
          <p class="px-4 py-3 leading-relaxed">{{ selection.resolution }}</p>
          <p
            v-if="selection.montant_rembourse_centimes"
            class="border-t border-trait-doux px-4 py-2.5 text-avis"
          >
            {{ euros(selection.montant_rembourse_centimes) }} remboursés au client.
          </p>
        </section>

        <p
          v-if="!selection.date_reponse_vendeur && !selection.delai_expire
            && !['RESOLU', 'REJETE'].includes(selection.statut)"
          class="text-[11.5px] text-encre-douce"
        >
          Réponse attendue avant le {{ quandEtHeure(selection.date_limite_reponse) }}.
        </p>

        <button
          v-if="!selection.date_reponse_vendeur && !selection.delai_expire
            && !['RESOLU', 'REJETE'].includes(selection.statut)"
          type="button"
          class="bouton-accent"
          @click="ouvrirReponse(selection)"
        >
          <MessageSquare :size="15" />
          Donner ma version
        </button>
      </div>
    </FicheContextuelle>

    <Popup
      v-if="reponseA"
      :titre="`Répondre au litige n° ${reponseA.id}`"
      explication="Le client et l'administrateur liront votre version. Vous ne répondez
                   qu'une fois : ce n'est pas une messagerie, c'est une pièce au dossier."
      @fermer="reponseA = null"
    >
      <div class="flex flex-col gap-4">
        <section class="carte">
          <h4 class="carte-titre"><span>Ce qui vous est reproché</span></h4>
          <p class="px-4 py-3 text-[12.5px] leading-relaxed">
            <b class="block">{{ reponseA.libelle_motif }}</b>
            « {{ reponseA.description }} »
          </p>
        </section>

        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Votre version des faits</span>
          <textarea
            v-model="texte"
            rows="5"
            class="champ-clair"
            placeholder="Ce qui s'est réellement passé, et les éléments dont vous disposez."
          />
        </label>

        <p v-if="erreur" class="bandeau bandeau-erreur">
          <AlertTriangle :size="15" class="mt-px shrink-0" />
          {{ erreur }}
        </p>
      </div>

      <template #actions>
        <button type="button" class="bouton-neutre" @click="reponseA = null">Annuler</button>
        <button
          type="button"
          class="bouton-accent"
          :disabled="envoi || texte.trim().length < 20"
          @click="repondre"
        >
          <MessageSquare :size="15" />
          {{ envoi ? 'Envoi…' : 'Envoyer ma version' }}
        </button>
      </template>
    </Popup>
  </div>
</template>
