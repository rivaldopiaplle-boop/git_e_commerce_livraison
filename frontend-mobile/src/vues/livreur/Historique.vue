<script setup lang="ts">
// L'historique des livraisons, tous statuts confondus.
//
// Les échecs y figurent au même titre que les réussites : un livreur doit
// pouvoir montrer qu'il est passé deux fois avant qu'un colis reparte.
//
// **Refait au bloc O-5** : *« l'historique est déplié, laid, non cliquable »*.
// Il l'était. Chaque course occupait une carte pleine largeur avec son badge,
// et rien ne s'ouvrait — un journal de bord qu'on ne peut pas consulter n'est
// pas un journal, c'est une liste de noms.
//
// Trois corrections, dans l'ordre où le reproche les nomme :
//
//   · **groupé par jour**, avec le total gagné en tête de journée. C'est
//     l'unité dans laquelle un livreur pense : « qu'est-ce que j'ai fait
//     mardi ? » ;
//   · **une ligne par course**, dense, et non une carte ;
//   · **chaque ligne s'ouvre** sur le détail : l'adresse, les tentatives, et
//     surtout **le calcul de la rémunération** — « ça sort d'où » était l'autre
//     moitié de ta remarque.
import {
  IonBadge, IonIcon, IonModal, IonSegment, IonSegmentButton,
} from '@ionic/vue'
import type { Livraison } from '@partage/types'
import { euros, jour, tonDuStatut } from '@partage/metier'
import {
  bicycleOutline, chevronForward, locationOutline, receiptOutline, walletOutline,
} from 'ionicons/icons'
import { computed, ref } from 'vue'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'
import { useRafraichissement } from '@/rafraichissement'

const livreur = useLivreur()
const filtre = ref('toutes')
const ouverte = ref<Livraison | null>(null)

useRafraichissement(() => livreur.charger())

const TONS: Record<string, string> = {
  succes: 'success', erreur: 'danger', cours: 'primary', attente: 'warning', neutre: 'medium',
}

const visibles = computed(() => {
  const toutes = [...livreur.terminees, ...livreur.enCours]
  if (filtre.value === 'livrees') {
    return toutes.filter((c) => c.statut_livraison === 'LIVREE')
  }
  if (filtre.value === 'echecs') {
    return toutes.filter((c) => c.statut_livraison === 'ECHOUEE')
  }
  return toutes
})

/**
 * Groupé par jour, le plus récent d'abord, avec le total de la journée.
 *
 * Un livreur ne cherche pas « la course numéro 47 » : il cherche sa journée de
 * mardi. Le total en tête répond à la question suivante avant qu'on la pose.
 */
const journees = computed(() => {
  const par: Record<string, { jour: string; courses: Livraison[]; total: number }> = {}
  for (const course of visibles.value) {
    const date = (course.date_reelle ?? course.date_estimee ?? '').slice(0, 10) || 'sans date'
    const entree = par[date] ?? (par[date] = { jour: date, courses: [], total: 0 })
    entree.courses.push(course)
    if (course.statut_livraison === 'LIVREE') {
      entree.total += course.remuneration_livreur_centimes
    }
  }
  return Object.values(par).sort((a, b) => b.jour.localeCompare(a.jour))
})
</script>

<template>
  <Ecran titre="Historique" sous-titre="Livreur" :rafraichir="livreur.charger">
    <IonSegment v-model="filtre" class="filtre">
      <IonSegmentButton value="toutes">Toutes</IonSegmentButton>
      <IonSegmentButton value="livrees">Livrées</IonSegmentButton>
      <IonSegmentButton value="echecs">Échecs</IonSegmentButton>
    </IonSegment>

    <template v-for="journee in journees" :key="journee.jour">
      <div class="entete-jour">
        <b>{{ journee.jour === 'sans date' ? 'Sans date' : jour(journee.jour) }}</b>
        <span v-if="journee.total">{{ euros(journee.total) }}</span>
      </div>

      <div class="groupe">
        <!-- Chaque ligne s'ouvre : c'est la moitié du reproche O-5,
             « non cliquable ». -->
        <button
          v-for="course in journee.courses"
          :key="course.id"
          type="button"
          class="ligne"
          @click="ouverte = course"
        >
          <span class="min">
            <b>{{ course.client }}</b>
            <span class="sous-titre">
              {{ course.numero_commande }}
              <template v-if="course.distance_km"> · {{ course.distance_km }} km</template>
              <template v-if="course.nombre_tentatives > 1">
                · {{ course.nombre_tentatives }} tentatives
              </template>
            </span>
          </span>
          <span class="droite">
            <IonBadge :color="TONS[tonDuStatut(course.statut_livraison)]">
              {{ course.libelle_statut }}
            </IonBadge>
            <b v-if="course.statut_livraison === 'LIVREE'">
              {{ euros(course.remuneration_livreur_centimes) }}
            </b>
          </span>
          <IonIcon :icon="chevronForward" class="chevron" />
        </button>
      </div>
    </template>

    <div v-if="!visibles.length" class="etat-vide">
      <IonIcon :icon="receiptOutline" class="grande-icone" />
      <b>Rien à cet état</b>
      <span>Vos livraisons passées apparaîtront ici.</span>
    </div>

    <!-- Le détail, et surtout le CALCUL : « la distance et le prix pour vous
         ne sont pas vraiment calculés, ça sort de nulle part » (O-5). -->
    <IonModal :is-open="!!ouverte" @did-dismiss="ouverte = null">
      <div v-if="ouverte" class="feuille">
        <b class="titre">{{ ouverte.client }}</b>
        <span class="sous-titre">{{ ouverte.numero_commande }}</span>

        <div class="bloc">
          <IonIcon :icon="locationOutline" />
          <span>
            {{ ouverte.adresse?.rue }}<br />
            {{ ouverte.adresse?.code_postal }} {{ ouverte.adresse?.ville }}
          </span>
        </div>

        <div class="bloc">
          <IonIcon :icon="bicycleOutline" />
          <span>
            {{ ouverte.distance_km ? `${ouverte.distance_km} km parcourus`
              : 'Distance non calculée' }}
            <template v-if="ouverte.nombre_tentatives > 1">
              · {{ ouverte.nombre_tentatives }} passages
            </template>
          </span>
        </div>

        <div class="bloc calcul">
          <IonIcon :icon="walletOutline" />
          <span>
            <b>{{ euros(ouverte.remuneration_livreur_centimes) }}</b>
            {{ ouverte.calcul_remuneration }}
          </span>
        </div>

        <p class="mention">
          Un gain est acquis à la confirmation de livraison, et suspendu si un
          litige est ouvert sur la commande — jamais versé puis repris.
        </p>
      </div>
    </IonModal>
  </Ecran>
</template>

<style scoped>
.filtre {
  margin-bottom: 12px;
}
.entete-jour {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin: 14px 2px 6px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--rd-encre-douce);
}
.entete-jour span {
  color: var(--accent);
  letter-spacing: 0;
  font-size: 12px;
}
.groupe {
  border: 1px solid var(--rd-trait);
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}
.ligne {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: 0;
  border-top: 1px solid var(--rd-trait-doux);
  background: none;
  text-align: left;
}
.ligne:first-child {
  border-top: 0;
}
.ligne .min {
  flex: 1;
  min-width: 0;
}
.ligne .min b {
  display: block;
  font-size: 13px;
}
.droite {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
  flex-shrink: 0;
}
.droite b {
  font-size: 12.5px;
  color: var(--accent);
}
.chevron {
  font-size: 14px;
  color: var(--rd-trait);
  flex-shrink: 0;
}
.feuille {
  padding: 20px 16px calc(20px + var(--rd-marge-basse, 12px));
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.feuille .titre {
  font-size: 18px;
}
.bloc {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--rd-atelier, #f4f5f8);
  font-size: 12.5px;
  line-height: 1.6;
}
.bloc ion-icon {
  font-size: 17px;
  color: var(--accent);
  flex-shrink: 0;
}
.bloc.calcul b {
  display: block;
  font-size: 17px;
  color: var(--accent);
}
.mention {
  margin: 0;
  font-size: 11px;
  line-height: 1.6;
  color: var(--rd-encre-douce);
}
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
</style>
