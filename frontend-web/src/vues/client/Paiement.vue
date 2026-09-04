<script setup lang="ts">
// Le paiement — D-12, D-15, D-18.
//
// Cet ecran manquait, et son absence n'etait pas un detail cosmetique : les
// commandes creees restaient en attente de paiement pour toujours, en gardant
// leur stock reserve. Au bout de quelques essais, des produits parfaitement
// disponibles s'affichaient en rupture sans que personne ne comprenne
// pourquoi.
//
// Trois choix qui se voient a l'ecran :
//
//   1. **Il paie TOUTES ses commandes en attente**, pas seulement celles qu'il
//      vient de creer. Un panier multi-boutique donne plusieurs commandes
//      (D-10) mais le client, lui, ne veut payer qu'une fois — et s'il est
//      parti en cours de route, il retrouve exactement la meme page.
//   2. **Une carte est exigee, et la simulation reste annoncee** (O-5). Ta
//      remarque : *« payer est valide sans carte, pas de demande de carte meme
//      la premiere fois »*. Le formulaire est donc reel — cle de Luhn,
//      echeance, cryptogramme — mais il n'accepte QUE les cartes d'essai, et
//      il le dit. Un faux formulaire qui accepte tout serait impressionnant
//      trente secondes et malhonnete ensuite.
//   3. **Renoncer est un vrai bouton.** Sans lui, le stock resterait immobilise
//      le temps de la reservation alors que l'acheteur a deja quitte la page.
import {
  AlertTriangle, ArrowLeft, Check, CreditCard, Loader, Lock, Package, ShieldCheck,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { EchecApi } from '../../api/client'
import { commandes, type Commande } from '../../api/commandes'
import { paiements, type Carte } from '../../api/paiements'
import Cartes from '../../composants/Cartes.vue'
import Popup from '../../composants/Popup.vue'
import Squelette from '../../composants/Squelette.vue'
import { useNotification } from '../../notifications'
import { usePanier } from '../../stores/panier'

type Manquant = { produit: string; demande: number; disponible: number }

const routeur = useRouter()
const panier = usePanier()
const { succes, echec: prevenirEchec } = useNotification()

const aPayer = ref<Commande[]>([])
const references = ref<Record<number, string>>({})
const chargement = ref(true)
const enCours = ref(false)
const renoncement = ref(false)
const erreur = ref('')
const manquants = ref<Manquant[]>([])
const minutes = ref(10)

/**
 * La carte retenue, et la reconfirmation — O-5.
 *
 * *« L'argent est paye sans reconfirmation. »* C'etait vrai : un clic, et
 * c'etait debite. La popup dit ce qui va se passer, avec le montant ET la
 * carte : « Payer 24,90 EUR avec Visa 4242 ». Un bouton « Payer » qui ne dit
 * ni combien ni avec quoi n'est pas une confirmation.
 */
const carte = ref<Carte | null>(null)
const confirmation = ref(false)

function surCarteChoisie(choisie: Carte | null) {
  carte.value = choisie
  // Changer de carte rouvre les intentions : c'est elle qui est notee sur le
  // paiement, et un ecran qui garde l'ancienne mentirait sur ce qui a servi.
  if (choisie && !chargement.value) preparer()
}

const total = computed(() =>
  aPayer.value.reduce((somme, commande) => somme + commande.montant_total_centimes, 0),
)
const articles = computed(() =>
  aPayer.value.reduce(
    (somme, commande) =>
      somme
      + commande.sous_commandes.reduce(
        (compte, sous) => compte + sous.lignes.reduce((n, ligne) => n + ligne.quantite, 0),
        0,
      ),
    0,
  ),
)

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

/**
 * Ouvrir l'intention de chaque commande en attente.
 *
 * L'ouverture est ce qui verifie que le stock tient toujours : c'est ici, et
 * pas au moment de payer, qu'on apprend qu'un article est parti. Le client a
 * donc l'information AVANT de sortir sa carte.
 */
async function preparer() {
  erreur.value = ''
  manquants.value = []
  try {
    const toutes = await commandes.miennes()
    aPayer.value = toutes.filter((c) => c.statut_actuel === 'EN_ATTENTE_PAIEMENT')

    // Sans carte, on ne tente meme pas : le serveur refuserait, et un
    // bandeau rouge a l'ouverture de la page n'aide personne.
    if (!carte.value) {
      chargement.value = false
      return
    }

    for (const commande of aPayer.value) {
      try {
        const intention = await paiements.ouvrir(commande.id, carte.value.id)
        references.value[commande.id] = intention.reference
        minutes.value = intention.reservation_expire_dans_minutes
      } catch (souci) {
        if (souci instanceof EchecApi && souci.erreur.code === 'stock_insuffisant') {
          const details = souci.erreur.details as { produits?: Manquant[] } | undefined
          manquants.value = [...manquants.value, ...(details?.produits ?? [])]
          erreur.value = souci.erreur.message
        } else {
          throw souci
        }
      }
    }
  } catch (souci) {
    erreur.value = souci instanceof EchecApi ? souci.erreur.message : 'Paiement indisponible.'
  } finally {
    chargement.value = false
  }
}

onMounted(preparer)

/**
 * Payer.
 *
 * En simulation, c'est le navigateur qui demande au serveur de confirmer,
 * faute de fournisseur pour le faire. En production, Stripe appellerait le
 * serveur directement et ce bouton se contenterait d'attendre : la vue
 * changerait, pas le reste du code (D-12).
 */
async function payer() {
  confirmation.value = false
  enCours.value = true
  erreur.value = ''
  let payees = 0
  try {
    for (const commande of aPayer.value) {
      const reference = references.value[commande.id]
      if (!reference) continue
      const resultat = await paiements.confirmer(reference)
      if (resultat.statut === 'CAPTURE') payees += 1
      else erreur.value = `Le paiement de la commande ${commande.numero_commande} a ete refuse.`
    }

    if (payees > 0) {
      await panier.charger()
      succes(
        payees > 1 ? `${payees} commandes payees` : 'Commande payee',
        'Les boutiques ont ete prevenues, la preparation commence.',
      )
      routeur.push({ name: 'mes-commandes', query: { payees } })
    } else {
      prevenirEchec('Paiement refuse', 'Aucun montant n’a ete debite.')
      await preparer()
    }
  } catch (souci) {
    erreur.value = souci instanceof EchecApi ? souci.erreur.message : 'Paiement impossible.'
  } finally {
    enCours.value = false
  }
}

/** Renoncer : le stock repart a la vente tout de suite, pas dans dix minutes. */
async function renoncer() {
  renoncement.value = true
  try {
    for (const commande of aPayer.value) await paiements.abandonner(commande.id)
    succes('Paiement abandonne', 'Les articles sont rendus a la vente.')
    routeur.push({ name: 'mes-commandes' })
  } catch (souci) {
    erreur.value = souci instanceof EchecApi ? souci.erreur.message : 'Abandon impossible.'
  } finally {
    renoncement.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[760px] animate-[apparition_0.2s_ease-out]">
    <h2 class="text-[21px] font-semibold tracking-tight">Payer ma commande</h2>

    <div v-if="chargement" class="mt-5 flex flex-col gap-3">
      <Squelette hauteur="80px" />
      <Squelette hauteur="140px" />
    </div>

    <template v-else-if="aPayer.length">
      <p class="mt-1 text-[13.5px] text-encre-douce">
        {{ articles }} article{{ articles > 1 ? 's' : '' }} —
        {{ aPayer.length }} commande{{ aPayer.length > 1 ? 's' : '' }}
        <template v-if="aPayer.length > 1">, livrees separement, un seul paiement</template>
      </p>

      <!-- Ce qui bloque, nommement : le client doit savoir QUOI a manque -->
      <section v-if="manquants.length" class="carte mt-4 border-avis-trait">
        <h3 class="carte-titre bg-avis-voile">
          <span class="flex items-center gap-2 text-avis">
            <AlertTriangle :size="15" />
            Le stock a change pendant que vous prepariez votre commande
          </span>
        </h3>
        <div v-for="manque in manquants" :key="manque.produit" class="ligne">
          <span class="min-w-0 flex-1 truncate"><b>{{ manque.produit }}</b></span>
          <span class="badge badge-erreur">
            {{ manque.demande }} demande{{ manque.demande > 1 ? 's' : '' }},
            {{ manque.disponible }} restant{{ manque.disponible > 1 ? 's' : '' }}
          </span>
        </div>
        <p class="border-t border-trait-doux px-4 py-2.5 text-[11.5px] text-encre-douce">
          Retirez ces articles depuis votre panier, puis revenez : les autres commandes
          restent payables.
        </p>
      </section>

      <!-- Le detail, par commande -->
      <div class="mt-4 flex flex-col gap-3">
        <article v-for="commande in aPayer" :key="commande.id" class="carte">
          <h3 class="carte-titre">
            <span class="flex items-center gap-2">
              <Package :size="15" :style="{ color: 'var(--accent)' }" />
              {{ commande.numero_commande }}
              <span class="badge badge-neutre">
                {{ commande.type_service === 'EXPRESS' ? 'Express' : 'Standard' }}
              </span>
            </span>
            <b>{{ euros(commande.montant_total_centimes) }}</b>
          </h3>
          <div v-for="sous in commande.sous_commandes" :key="sous.id">
            <div v-for="ligne in sous.lignes" :key="ligne.id" class="ligne">
              <span class="min-w-0 flex-1 truncate">
                <b>{{ ligne.quantite }} x {{ ligne.nom_produit_capture }}</b>
                <span class="ml-2 text-[11.5px] text-encre-douce">{{ sous.boutique }}</span>
              </span>
              <span class="text-[12.5px]">{{ euros(ligne.sous_total_centimes) }}</span>
            </div>
          </div>
          <p class="flex justify-between border-t border-trait-doux px-4 py-2.5
                    text-[11.5px] text-encre-douce">
            <span>Livraison</span>
            <span>
              {{ commande.montant_livraison_centimes
                ? euros(commande.montant_livraison_centimes) : 'offerte' }}
            </span>
          </p>
        </article>
      </div>

      <p v-if="erreur && !manquants.length" class="bandeau bandeau-erreur mt-4">
        <AlertTriangle :size="15" class="mt-px shrink-0" />
        {{ erreur }}
      </p>

      <!-- Le carnet de cartes (O-5) -->
      <div class="mt-4">
        <Cartes @choisie="surCarteChoisie" />
      </div>

      <!-- La simulation, dite franchement -->
      <p class="bandeau bandeau-info mt-4">
        <ShieldCheck :size="15" class="mt-px shrink-0" />
        <span>
          <b>Paiement en mode simulation.</b>
          La carte est reellement verifiee — cle de Luhn, echeance, cryptogramme —
          mais aucun montant n&rsquo;est debite, et seules les cartes d&rsquo;essai
          sont acceptees. Le fournisseur reel est derriere la meme interface : le
          jour ou une cle existe, seul le fichier des services externes change.
        </span>
      </p>

      <div class="carte mt-4 flex flex-wrap items-center justify-between gap-4 p-5">
        <div>
          <p class="text-[12.5px] text-encre-douce">Total a payer</p>
          <b class="text-[26px]" :style="{ color: 'var(--accent)' }">{{ euros(total) }}</b>
          <p class="mt-1 flex items-center gap-1.5 text-[11.5px] text-encre-douce">
            <Lock :size="12" />
            Vos articles sont mis de cote pendant {{ minutes }} minutes.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <button
            type="button"
            class="bouton-neutre"
            :disabled="renoncement || enCours"
            @click="renoncer"
          >
            <ArrowLeft :size="15" />
            {{ renoncement ? 'Abandon…' : 'Renoncer' }}
          </button>
          <button
            type="button"
            class="bouton-accent !px-5 !py-3 !text-[14px]"
            :disabled="enCours || renoncement || !carte || !Object.keys(references).length"
            :title="carte ? `Payer avec ${carte.libelle}` : 'Ajoutez une carte'"
            @click="confirmation = true"
          >
            <component :is="enCours ? Loader : CreditCard" :size="17"
                       :class="enCours ? 'animate-spin' : ''" />
            {{ enCours ? 'Paiement…' : `Payer ${euros(total)}` }}
          </button>
        </div>
      </div>
    </template>

    <div v-else class="carte mt-5">
      <div class="vide">
        <Check :size="30" class="text-trait" />
        <b class="vide-titre">Rien a payer</b>
        <p class="vide-texte">
          Toutes vos commandes sont reglees. Leur suivi se trouve dans « Mes commandes ».
        </p>
        <RouterLink :to="{ name: 'mes-commandes' }" class="bouton-accent mt-4">
          Voir mes commandes
        </RouterLink>
      </div>
    </div>

    <!-- La reconfirmation (O-5). Elle dit le montant ET la carte : un bouton
         « Payer » qui ne dit ni combien ni avec quoi n'est pas une
         confirmation, c'est un raccourci. -->
    <Popup
      v-if="confirmation && carte"
      titre="Confirmer le paiement"
      :explication="`Le montant sera debite immediatement. Aucune carte n'est reellement
                     debitee : cette demonstration tourne en mode simulation.`"
      @fermer="confirmation = false"
    >
      <dl class="flex flex-col gap-2.5 text-[13px]">
        <div class="flex justify-between gap-3">
          <dt class="text-encre-douce">Montant</dt>
          <dd class="text-[17px] font-bold" :style="{ color: 'var(--accent)' }">
            {{ euros(total) }}
          </dd>
        </div>
        <div class="flex justify-between gap-3">
          <dt class="text-encre-douce">Carte</dt>
          <dd class="font-semibold">{{ carte.libelle }}</dd>
        </div>
        <div class="flex justify-between gap-3">
          <dt class="text-encre-douce">Commandes</dt>
          <dd class="font-semibold">
            {{ aPayer.length }} commande{{ aPayer.length > 1 ? 's' : '' }},
            livree{{ aPayer.length > 1 ? 's separement' : '' }}
          </dd>
        </div>
      </dl>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="confirmation = false">
          Revenir
        </button>
        <button type="button" class="bouton-accent !py-2" :disabled="enCours" @click="payer">
          <CreditCard :size="15" /> Payer {{ euros(total) }}
        </button>
      </template>
    </Popup>
  </div>
</template>
