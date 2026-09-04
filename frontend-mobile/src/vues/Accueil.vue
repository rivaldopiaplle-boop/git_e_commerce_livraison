<script setup lang="ts">
// L'accueil — refait au bloc O.
//
// **Ton reproche, O-1** : *« les onglets menus sont très peu remplis, surtout
// le premier onglet accueil et son équivalent »*. Il montrait trois tuiles :
// deux compteurs et un bouton vers le catalogue. Et **O-2** : *« tu ne t'es
// pas inspiré des vraies applications d'e-commerce et de livraison »*.
//
// Elles se ressemblent toutes, et pour de bonnes raisons. Dans l'ordre, elles
// répondent à quatre questions, et l'ordre compte :
//
//   1. **où suis-je livré ?** — c'est cette adresse qui décide des boutiques
//      Express visibles (D-09). Un catalogue qui change sans qu'on sache
//      pourquoi fait croire que l'application est cassée ;
//   2. **où en est ma commande ?** — la seule chose qu'on ouvre l'application
//      pour voir quand on a déjà commandé ;
//   3. **qu'est-ce que je cherche ?** — la recherche et les catégories ;
//   4. **qu'est-ce que je peux commander tout de suite ?** — ce qu'on a déjà
//      pris, puis ce qui se vend.
//
// Tout est cliquable (O-8) : chaque chiffre mène à sa liste, chaque pastille à
// sa recherche filtrée, chaque vignette à sa fiche. Un chiffre qu'on ne peut
// qu'admirer est un élément mort qui trompe l'œil (D-64).
import { IonBadge, IonIcon, IonSpinner, IonToggle } from '@ionic/vue'
import { ETAPES_SUIVI, LIBELLES_STATUT, euros, positionSuivi } from '@partage/metier'
import type { StatutCommande } from '@partage/types'
import {
  bagHandleOutline, bicycleOutline, chevronForward, cubeOutline, keyOutline,
  listOutline, locationOutline, navigateOutline, searchOutline, storefrontOutline,
  walletOutline,
} from 'ionicons/icons'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import VignetteProduit from '@/composants/VignetteProduit.vue'
import { useLivreur } from '@/magasins/livreur'
import { useSession } from '@/magasins/session'
import { useRafraichissement } from '@/rafraichissement'

type Produit = {
  id: number
  nom: string
  image?: string
  prix_centimes: number
  disponible?: boolean
  distance_km?: number | null
  boutique?: { nom: string; type_service?: string }
}

type Accueil = {
  role: string
  adresse?: { id: number; libelle: string; ville: string; code_postal: string } | null
  panier?: { articles: number; total_centimes: number; apercu: string[] }
  commande_en_cours?: {
    id: number
    numero_commande: string
    type_service: 'EXPRESS' | 'STANDARD'
    statut_actuel: StatutCommande
    montant_total_centimes: number
    boutiques: string[]
    code_confirmation: string
  } | null
  compteurs?: { en_cours: number; livrees: number; total_depense_centimes: number }
  categories?: { slug: string; nom: string; univers: string; nombre: number }[]
  boutiques_express?: {
    id: number; nom: string; ville: string; distance_km: number | null; type_service: string
  }[]
  a_commander_de_nouveau?: Produit[]
  populaires?: Produit[]
  // Livreur
  mode?: string
  statut_validation?: string
  disponibilite?: string
  aujourdhui?: { courses: number; gains_centimes: number; distance_km: number }
  course_en_cours?: {
    id: number
    client: string
    statut_livraison: string
    libelle_statut: string
    adresse?: { rue?: string; ville?: string } | null
    remuneration_centimes: number
  } | null
  disponibles?: number
  raison_indisponibilite?: string
}

const session = useSession()
const livreur = useLivreur()
const routeur = useRouter()

const donnees = ref<Accueil | null>(null)
const chargement = ref(true)

const estLivreur = computed(() => session.role === 'LIVREUR')
const express = computed(() => donnees.value?.mode === 'EXPRESS')
const disponible = computed(() => donnees.value?.disponibilite === 'DISPONIBLE')

async function charger() {
  try {
    donnees.value = await session.client.get<Accueil>('/moi/accueil')
  } catch {
    // Un accueil vide vaut mieux qu'un écran en erreur : les onglets du bas
    // restent, et tout le reste de l'application marche.
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger, { periodique: true })

const bascule = ref(false)
async function changerDisponibilite() {
  bascule.value = true
  try {
    await livreur.basculerDisponibilite()
    await charger()
  } finally {
    bascule.value = false
  }
}

/** La frise du suivi, réduite à « où on en est sur combien ». */
const suivi = computed(() => {
  const commande = donnees.value?.commande_en_cours
  if (!commande) return null
  const etapes = ETAPES_SUIVI[commande.type_service] ?? []
  return {
    position: positionSuivi(commande.type_service, commande.statut_actuel),
    total: etapes.length,
    etapes,
  }
})

/** Les explications de « rien à prendre », les mêmes que l'écran À proximité. */
const RAISONS: Record<string, string> = {
  course_en_cours: 'Vous avez déjà une course en route.',
  hors_ligne: 'Rendez-vous disponible pour en recevoir.',
  mauvais_mode: 'Votre travail, ce sont les tournées.',
  hors_rayon: 'Rien dans votre rayon pour l’instant.',
  aucune: 'Rien n’attend de livreur pour l’instant.',
}
</script>

<template>
  <Ecran
    :titre="estLivreur ? 'Aujourd’hui' : `Bonjour ${session.utilisateur?.prenom ?? ''}`"
    :sous-titre="estLivreur
      ? `Livreur · ${express ? 'Express' : 'Standard'}`
      : 'Espace client'"
    :rafraichir="charger"
  >
    <div v-if="chargement && !donnees" class="centre"><IonSpinner /></div>

    <!-- ══ Le livreur ═══════════════════════════════════════════════════ -->
    <template v-else-if="estLivreur">
      <div
        v-if="donnees?.statut_validation && donnees.statut_validation !== 'VALIDE'"
        class="bandeau-attente"
      >
        <b>Votre compte attend une validation</b>
        <span>
          Un administrateur doit vérifier vos pièces avant que des courses vous
          soient proposées.
        </span>
      </div>

      <!-- Se rendre disponible est LA première action de la journée. -->
      <div class="carte-mobile disponibilite">
        <div>
          <b>{{ disponible ? 'Vous êtes disponible' : 'Vous êtes hors ligne' }}</b>
          <span class="sous-titre">
            {{ disponible
              ? 'Vous recevez les courses proches de vous.'
              : 'Aucune course ne vous sera proposée.' }}
          </span>
        </div>
        <IonToggle
          :checked="disponible"
          :disabled="bascule"
          @ion-change="changerDisponibilite"
        />
      </div>

      <!-- La journée, et pas seulement le cumul de toujours : c'est ce qu'un
           livreur regarde le matin et le soir. -->
      <span class="titre-section">Votre journée</span>
      <div class="grille">
        <button type="button" class="tuile" @click="routeur.push('/historique')">
          <IonIcon :icon="listOutline" />
          <b>{{ donnees?.aujourdhui?.courses ?? 0 }}</b>
          <span>livraisons faites</span>
        </button>
        <button type="button" class="tuile" @click="routeur.push('/gains')">
          <IonIcon :icon="walletOutline" />
          <b>{{ euros(donnees?.aujourdhui?.gains_centimes ?? 0) }}</b>
          <span>gagnés aujourd’hui</span>
        </button>
        <button
          type="button"
          class="tuile large"
          @click="routeur.push(express ? '/proximite' : '/tournee')"
        >
          <IonIcon :icon="express ? bicycleOutline : listOutline" />
          <b v-if="express">{{ donnees?.disponibles ?? 0 }} course(s) à prendre</b>
          <b v-else>{{ livreur.tournee?.nombre_arrets ?? 0 }} arrêts dans votre tournée</b>
          <span>
            {{ express
              ? (donnees?.disponibles
                ? 'Les plus proches de vous d’abord'
                : RAISONS[donnees?.raison_indisponibilite ?? 'aucune'])
              : 'Préparée par l’entrepôt, dans l’ordre' }}
          </span>
        </button>
      </div>

      <!-- Ce qui se passe MAINTENANT, en grand et cliquable -->
      <template v-if="donnees?.course_en_cours">
        <span class="titre-section">Votre course en cours</span>
        <button
          type="button"
          class="carte-mobile ligne-action"
          @click="routeur.push(express ? '/courses' : '/arret')"
        >
          <span class="detail">
            <b>{{ donnees.course_en_cours.client }}</b>
            <span class="sous-titre">
              {{ donnees.course_en_cours.adresse?.rue }},
              {{ donnees.course_en_cours.adresse?.ville }}
            </span>
            <IonBadge class="badge">{{ donnees.course_en_cours.libelle_statut }}</IonBadge>
          </span>
          <span class="fin">
            <b>{{ euros(donnees.course_en_cours.remuneration_centimes) }}</b>
            <IonIcon :icon="chevronForward" />
          </span>
        </button>
      </template>

      <button type="button" class="carte-mobile ligne-action"
              @click="routeur.push('/gains')">
        <span class="detail">
          <b>Mes gains</b>
          <span class="sous-titre">Détail par course, et ce qu’un litige bloque</span>
        </span>
        <IonIcon :icon="chevronForward" />
      </button>
    </template>

    <!-- ══ Le client ════════════════════════════════════════════════════ -->
    <template v-else>
      <!-- 1. Où l'on est livré, et la recherche : les deux premiers gestes -->
      <button type="button" class="adresse-barre" @click="routeur.push('/adresses')">
        <IonIcon :icon="locationOutline" />
        <span class="min">
          <span class="etiquette">Livrer à</span>
          <b>{{ donnees?.adresse
            ? `${donnees.adresse.libelle} · ${donnees.adresse.ville}`
            : 'Ajouter une adresse' }}</b>
        </span>
        <IonIcon :icon="chevronForward" />
      </button>

      <button type="button" class="recherche-fausse" @click="routeur.push('/recherche')">
        <IonIcon :icon="searchOutline" />
        <span>Un plat, un produit, une boutique…</span>
      </button>

      <!-- 2. Où en est ma commande : la raison n°1 d'ouvrir l'application -->
      <template v-if="donnees?.commande_en_cours">
        <span class="titre-section">Votre commande en cours</span>
        <button type="button" class="carte-mobile suivi" @click="routeur.push('/commandes')">
          <span class="haut">
            <b>{{ donnees.commande_en_cours.numero_commande }}</b>
            <IonBadge>{{ LIBELLES_STATUT[donnees.commande_en_cours.statut_actuel] }}</IonBadge>
          </span>
          <span class="sous-titre">{{ donnees.commande_en_cours.boutiques.join(' · ') }}</span>

          <span v-if="suivi" class="jauge">
            <span
              v-for="(etape, index) in suivi.etapes"
              :key="etape"
              :class="index <= suivi.position ? 'faite' : ''"
            />
          </span>

          <!-- Le code que le livreur demandera à la porte. Il était généré et
               n'apparaissait NULLE PART côté client (O-5). -->
          <span v-if="donnees.commande_en_cours.code_confirmation" class="code">
            <IonIcon :icon="keyOutline" />
            <span>
              <b>{{ donnees.commande_en_cours.code_confirmation }}</b>
              code à donner au livreur
            </span>
          </span>
        </button>
      </template>

      <!-- Reprendre son panier là où on l'a laissé -->
      <button
        v-if="donnees?.panier?.articles"
        type="button"
        class="carte-mobile ligne-action panier"
        @click="routeur.push('/panier')"
      >
        <span class="detail">
          <b>{{ donnees.panier.articles }} article(s) dans votre panier</b>
          <span class="sous-titre">{{ donnees.panier.apercu.join(', ') }}</span>
        </span>
        <span class="fin">
          <b>{{ euros(donnees.panier.total_centimes) }}</b>
          <IonIcon :icon="chevronForward" />
        </span>
      </button>

      <!-- 3. Ce que je cherche : les catégories, en pastilles défilantes -->
      <template v-if="donnees?.categories?.length">
        <span class="titre-section">Par envie</span>
        <div class="bande">
          <button
            v-for="categorie in donnees.categories"
            :key="categorie.slug"
            type="button"
            class="puce"
            @click="routeur.push({ path: '/recherche', query: { categorie: categorie.slug } })"
          >
            {{ categorie.nom }}
            <span class="compteur">{{ categorie.nombre }}</span>
          </button>
        </div>
      </template>

      <!-- Les boutiques Express qui livrent VRAIMENT chez soi -->
      <template v-if="donnees?.boutiques_express?.length">
        <span class="titre-section">
          Express près de chez vous
          <button type="button" class="lien" @click="routeur.push('/boutiques')">Tout voir</button>
        </span>
        <div class="bande">
          <button
            v-for="boutique in donnees.boutiques_express"
            :key="boutique.id"
            type="button"
            class="carte-boutique"
            @click="routeur.push({ path: '/recherche', query: { boutique: boutique.id } })"
          >
            <span class="rond"><IonIcon :icon="storefrontOutline" /></span>
            <b>{{ boutique.nom }}</b>
            <span class="sous-titre">
              <IonIcon :icon="bicycleOutline" />
              {{ boutique.distance_km != null ? `${boutique.distance_km} km` : boutique.ville }}
            </span>
          </button>
        </div>
      </template>

      <!-- 4. Ce que je peux commander tout de suite -->
      <template v-if="donnees?.a_commander_de_nouveau?.length">
        <span class="titre-section">Commander à nouveau</span>
        <div class="bande">
          <VignetteProduit
            v-for="produit in donnees.a_commander_de_nouveau"
            :key="produit.id"
            :produit="produit"
          />
        </div>
      </template>

      <template v-if="donnees?.populaires?.length">
        <span class="titre-section">
          Les plus demandés
          <button type="button" class="lien" @click="routeur.push('/recherche')">Tout voir</button>
        </span>
        <div class="grille-produits">
          <VignetteProduit
            v-for="produit in donnees.populaires"
            :key="produit.id"
            :produit="produit"
            forme="tuile"
          />
        </div>
      </template>

      <!-- Les compteurs en bas : utiles, mais ce n'est pas ce qu'on vient
           chercher. Ils restent cliquables. -->
      <span class="titre-section">Votre historique</span>
      <div class="grille">
        <button type="button" class="tuile" @click="routeur.push('/commandes')">
          <IonIcon :icon="cubeOutline" />
          <b>{{ donnees?.compteurs?.en_cours ?? 0 }}</b>
          <span>en cours</span>
        </button>
        <button type="button" class="tuile" @click="routeur.push('/commandes')">
          <IonIcon :icon="navigateOutline" />
          <b>{{ donnees?.compteurs?.livrees ?? 0 }}</b>
          <span>livrées</span>
        </button>
        <button type="button" class="tuile large" @click="routeur.push('/commandes')">
          <IonIcon :icon="bagHandleOutline" />
          <b>{{ euros(donnees?.compteurs?.total_depense_centimes ?? 0) }}</b>
          <span>dépensés depuis votre inscription</span>
        </button>
      </div>
    </template>
  </Ecran>
</template>

<style scoped>
.centre {
  display: grid;
  place-items: center;
  padding: 48px 0;
}
.titre-section {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin: 18px 2px 8px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--rd-encre-douce);
}
.lien {
  border: 0;
  background: none;
  padding: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: none;
  color: var(--accent);
}

/* ── Adresse et recherche ───────────────────────────────────────────── */
.adresse-barre {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 12px;
  margin-bottom: 10px;
  border: 1px solid var(--rd-trait);
  border-radius: 12px;
  background: #fff;
  text-align: left;
}
.adresse-barre > ion-icon {
  font-size: 18px;
  color: var(--accent);
  flex-shrink: 0;
}
.adresse-barre .min {
  flex: 1;
  min-width: 0;
}
.adresse-barre .etiquette {
  display: block;
  font-size: 9.5px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--rd-encre-douce);
}
.adresse-barre b {
  display: block;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.recherche-fausse {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 11px 14px;
  border: 0;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 1px 3px rgb(15 20 32 / 0.08);
  color: var(--rd-encre-douce);
  font-size: 13px;
  text-align: left;
}
.recherche-fausse ion-icon {
  font-size: 17px;
}

/* ── Le suivi ───────────────────────────────────────────────────────── */
.suivi {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%;
  text-align: left;
}
.suivi .haut {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.suivi .haut b {
  font-size: 13.5px;
}
.jauge {
  display: flex;
  gap: 4px;
  margin-top: 6px;
}
.jauge span {
  flex: 1;
  height: 4px;
  border-radius: 99px;
  background: var(--rd-trait);
}
.jauge span.faite {
  background: var(--accent);
}
.code {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--accent-doux);
  font-size: 11px;
  color: var(--rd-encre-douce);
}
.code ion-icon {
  font-size: 16px;
  color: var(--accent);
}
.code b {
  display: block;
  font-size: 17px;
  letter-spacing: 0.22em;
  color: var(--accent);
}

/* ── Lignes cliquables ──────────────────────────────────────────────── */
.ligne-action {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  text-align: left;
}
.ligne-action .detail {
  flex: 1;
  min-width: 0;
}
.ligne-action .detail b {
  display: block;
  font-size: 13px;
}
.ligne-action .fin {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.ligne-action .fin b {
  font-size: 14px;
  color: var(--accent);
}
.ligne-action ion-icon {
  color: var(--rd-encre-douce);
  font-size: 16px;
}
.panier {
  border-left: 3px solid var(--accent);
}
.badge {
  margin-top: 6px;
}

/* ── Bandes horizontales ────────────────────────────────────────────── */
.bande {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-bottom: 2px;
  /* Les bandes débordent volontairement de la marge du contenu : c'est ce qui
     dit « ça continue à droite » sans flèche ni point. */
  margin: 0 -14px;
  padding-left: 14px;
  padding-right: 14px;
}
.bande::-webkit-scrollbar {
  display: none;
}
.puce {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--rd-trait);
  border-radius: 999px;
  background: #fff;
  font-size: 12.5px;
  font-weight: 600;
}
.puce .compteur {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--accent);
}
.carte-boutique {
  flex: 0 0 130px;
  width: 130px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 12px;
  border: 1px solid var(--rd-trait);
  border-radius: 14px;
  background: #fff;
  text-align: left;
}
.carte-boutique .rond {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--accent-doux);
  color: var(--accent);
  font-size: 18px;
  margin-bottom: 4px;
}
.carte-boutique b {
  font-size: 12.5px;
  line-height: 1.25;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.carte-boutique .sous-titre {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10.5px;
}
.grille-produits {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* ── Tuiles ─────────────────────────────────────────────────────────── */
.disponibilite {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.disponibilite b {
  display: block;
  font-size: 13.5px;
}
.bandeau-attente {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 11px 13px;
  margin-bottom: 10px;
  border-radius: 12px;
  background: #fff6ea;
  border: 1px solid #ffe2b3;
  color: #7a4a06;
  font-size: 11.5px;
  line-height: 1.55;
}
.grille {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.tuile {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 13px;
  border: 1px solid var(--rd-trait);
  border-radius: 14px;
  background: #fff;
  text-align: left;
}
.tuile.large {
  grid-column: 1 / -1;
}
.tuile ion-icon {
  font-size: 18px;
  color: var(--accent);
  margin-bottom: 3px;
}
.tuile b {
  font-size: 17px;
  font-weight: 800;
}
.tuile span {
  font-size: 11px;
  color: var(--rd-encre-douce);
  line-height: 1.4;
}
</style>
