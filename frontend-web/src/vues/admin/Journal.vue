<script setup lang="ts">
// Le journal d'audit.
//
// On ne consigne pas des lignes de log techniques mais **les changements de
// statut**, parce que ce sont eux qu'on relit quand un client conteste. « Qui
// a fait passer cette commande en livrée, et quand ? » est la seule question
// que cet écran doit savoir trancher.
import { ArrowRight, Eye, ScrollText } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { espaces, type Trace } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Volet from '../../composants/Volet.vue'

type Ligne = Trace & { [cle: string]: unknown }

const traces = ref<Ligne[]>([])
const chargement = ref(true)
const selection = ref<Ligne | null>(null)

onMounted(async () => {
  try {
    traces.value = (await espaces.admin.journal()) as Ligne[]
  } finally {
    chargement.value = false
  }
})

const colonnes: Colonne<Ligne>[] = [
  { cle: 'date', titre: 'Quand', largeur: 130,
    tri: (a, b) => a.date.localeCompare(b.date) },
  { cle: 'objet', titre: 'Objet', largeur: 130, aligne: 'centre' },
  { cle: 'transition', titre: 'Changement' },
  { cle: 'commentaire', titre: 'Motif', masquerSous: 'lg' },
  { cle: 'auteur', titre: 'Par', largeur: 170, aligne: 'droite', masquerSous: 'md' },
]

const lisible = (statut: string) => statut.toLowerCase().replace(/_/g, ' ')
const quand = (date: string) =>
  new Date(date).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit',
  })
</script>

<template>
  <div class="mx-auto max-w-[1040px] animate-[apparition_0.2s_ease-out]">
    <p class="bandeau bandeau-info mb-4">
      <ScrollText :size="15" class="mt-px shrink-0" />
      Aucun statut ne change en silence : chaque passage laisse une trace datée, avec son
      auteur et, le cas échéant, le motif invoqué.
    </p>

    <Liste
      :colonnes="colonnes"
      :lignes="traces"
      :cle-ligne="(trace) => trace.id"
      :chargement="chargement"
      :recherche="(t) => `${t.type_objet} ${t.id_objet} ${t.statut_apres} ${t.par} ${t.commentaire}`"
      placeholder="Statut, auteur, numéro d'objet…"
      :par-page="20"
    >
      <template #col-date="{ ligne }">
        <span class="text-encre-douce">{{ quand(ligne.date) }}</span>
      </template>
      <template #col-objet="{ ligne }">
        <span class="badge badge-neutre">
          {{ lisible(ligne.type_objet) }} {{ ligne.id_objet }}
        </span>
      </template>
      <template #col-transition="{ ligne }">
        <span class="flex min-w-0 items-center gap-2">
          <span v-if="ligne.statut_avant" class="truncate text-encre-douce">
            {{ lisible(ligne.statut_avant) }}
          </span>
          <ArrowRight :size="12" class="shrink-0 text-encre-douce" />
          <b class="truncate">{{ lisible(ligne.statut_apres) }}</b>
        </span>
      </template>
      <template #col-commentaire="{ ligne }">
        <span class="min-w-0 truncate text-encre-douce">
          {{ ligne.commentaire ? `« ${ligne.commentaire} »` : '—' }}
        </span>
      </template>
      <template #col-auteur="{ ligne }">
        <span class="min-w-0 truncate text-[11.5px] text-encre-douce">{{ ligne.par }}</span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter cette trace"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
      </template>

      <template #vide>
        <div class="vide">
          <ScrollText :size="30" class="text-trait" />
          <b class="vide-titre">Aucune trace ne correspond</b>
        </div>
      </template>
    </Liste>

    <Volet v-if="selection" :titre="`${lisible(selection.type_objet)} n° ${selection.id_objet}`">
      <dl class="flex flex-col gap-2 text-[12px]">
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Quand</dt>
          <dd class="font-semibold">{{ quand(selection.date) }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Avant</dt>
          <dd class="font-semibold">{{ lisible(selection.statut_avant) || '—' }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Après</dt>
          <dd class="font-semibold">{{ lisible(selection.statut_apres) }}</dd>
        </div>
        <div>
          <dt class="text-encre-douce">Par</dt>
          <dd class="font-semibold break-all">{{ selection.par }}</dd>
        </div>
        <div v-if="selection.commentaire">
          <dt class="text-encre-douce">Motif invoqué</dt>
          <dd class="leading-relaxed">« {{ selection.commentaire }} »</dd>
        </div>
      </dl>
    </Volet>
  </div>
</template>
