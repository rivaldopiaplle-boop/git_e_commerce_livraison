<script setup lang="ts">
// La vue d'ensemble — la même position pour les deux rôles, un contenu
// différent (D-89).
//
// Chaque chiffre est cliquable et mène à la liste correspondante, déjà
// filtrée : un chiffre isolé qu'on ne peut qu'admirer est un élément mort qui
// trompe l'œil (D-64).
import { IonBadge, IonIcon, IonToggle } from '@ionic/vue'
import { euros } from '@partage/metier'
import { bicycleOutline, listOutline, walletOutline } from 'ionicons/icons'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'
import { useSession } from '@/magasins/session'

const session = useSession()
const livreur = useLivreur()
const routeur = useRouter()

const estLivreur = computed(() => session.role === 'LIVREUR')
const express = computed(() => session.modeLivraison === 'EXPRESS')
const disponible = computed(() => livreur.disponibilite === 'DISPONIBLE')

const tableauClient = ref<Record<string, number>>({})

async function charger() {
  if (estLivreur.value) {
    await livreur.charger()
    return
  }
  try {
    tableauClient.value = await session.client.get('/moi/tableau-de-bord')
  } catch {
    tableauClient.value = {}
  }
}

onMounted(charger)

const bascule = ref(false)
async function changerDisponibilite() {
  bascule.value = true
  try {
    await livreur.basculerDisponibilite()
  } finally {
    bascule.value = false
  }
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
    <!-- ── Le livreur ─────────────────────────────────────────────── -->
    <template v-if="estLivreur">
      <!-- Se rendre disponible est LA première action de la journée : elle
           est en haut, et elle bascule d'un geste. -->
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

      <div class="grille">
        <button type="button" class="tuile" @click="routeur.push(express ? '/courses' : '/tournee')">
          <IonIcon :icon="express ? bicycleOutline : listOutline" />
          <b>{{ livreur.enCours.length }}</b>
          <span>{{ express ? 'course en cours' : 'arrêts à faire' }}</span>
        </button>
        <button type="button" class="tuile" @click="routeur.push('/historique')">
          <IonIcon :icon="listOutline" />
          <b>{{ livreur.gains.courses_terminees }}</b>
          <span>livraisons faites</span>
        </button>
        <button type="button" class="tuile large" @click="routeur.push('/gains')">
          <IonIcon :icon="walletOutline" />
          <b>{{ euros(livreur.gains.total_centimes) }}</b>
          <span>gains cumulés · {{ livreur.gains.distance_km.toFixed(1) }} km parcourus</span>
        </button>
      </div>

      <div v-if="livreur.courseActuelle" class="carte-mobile">
        <span class="etiquette">Course en cours</span>
        <b class="nom">{{ livreur.courseActuelle.client }}</b>
        <span class="sous-titre">
          {{ livreur.courseActuelle.adresse?.rue }}, {{ livreur.courseActuelle.adresse?.ville }}
        </span>
        <IonBadge class="badge">{{ livreur.courseActuelle.libelle_statut }}</IonBadge>
      </div>

      <div v-else-if="!livreur.chargement" class="etat-vide">
        <b>Aucune course en cours</b>
        <span>
          {{ disponible
            ? 'Regardez ce qui est disponible autour de vous.'
            : 'Rendez-vous disponible pour recevoir des courses.' }}
        </span>
      </div>
    </template>

    <!-- ── Le client ──────────────────────────────────────────────── -->
    <template v-else>
      <div class="grille">
        <button type="button" class="tuile" @click="routeur.push('/commandes')">
          <b>{{ tableauClient.en_cours ?? 0 }}</b>
          <span>commandes en cours</span>
        </button>
        <button type="button" class="tuile" @click="routeur.push('/commandes')">
          <b>{{ tableauClient.livrees ?? 0 }}</b>
          <span>commandes livrées</span>
        </button>
        <button type="button" class="tuile large" @click="routeur.push('/recherche')">
          <b>Parcourir le catalogue</b>
          <span>Ce qui livre chez vous, filtré par votre adresse</span>
        </button>
      </div>
    </template>
  </Ecran>
</template>

<style scoped>
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
.grille {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 12px;
}
.tuile {
  background: #fff;
  border: 1px solid var(--rd-trait-doux);
  border-radius: 14px;
  padding: 14px 12px;
  text-align: left;
  box-shadow: 0 2px 8px rgba(15, 20, 32, 0.05);
  /* Un retour tactile immédiat : sur mobile il n'y a pas de survol pour dire
     qu'un élément est cliquable. */
  transition: transform 0.12s ease;
}
.tuile:active {
  transform: scale(0.97);
}
.tuile.large {
  grid-column: span 2;
}
.tuile ion-icon {
  font-size: 18px;
  color: var(--accent);
}
.tuile b {
  display: block;
  font-size: 21px;
  font-weight: 800;
  margin-top: 4px;
}
.tuile.large b {
  font-size: 15px;
}
.tuile span {
  font-size: 11px;
  color: var(--rd-encre-douce);
  font-weight: 600;
}
.etiquette {
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--rd-encre-douce);
}
.nom {
  display: block;
  font-size: 15px;
  margin-top: 2px;
}
.badge {
  margin-top: 8px;
}
</style>
