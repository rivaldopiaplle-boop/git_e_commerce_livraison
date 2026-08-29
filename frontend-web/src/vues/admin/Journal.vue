<script setup lang="ts">
// Le journal d'audit.
//
// On ne consigne pas des lignes de log techniques mais **les changements de
// statut**, parce que ce sont eux qu'on relit quand un client conteste. « Qui
// a fait passer cette commande en livree, et quand ? » est la seule question
// que cet ecran doit savoir trancher.
import { ArrowRight, ScrollText, Search } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Trace } from '../../api/espaces'
import Squelette from '../../composants/Squelette.vue'

const traces = ref<Trace[]>([])
const chargement = ref(true)
const recherche = ref('')

onMounted(async () => {
  try {
    traces.value = await espaces.admin.journal()
  } finally {
    chargement.value = false
  }
})

const visibles = computed(() => {
  const texte = recherche.value.trim().toLowerCase()
  if (!texte) return traces.value
  return traces.value.filter((trace) =>
    `${trace.type_objet} ${trace.id_objet} ${trace.statut_apres} ${trace.par} ${trace.commentaire}`
      .toLowerCase()
      .includes(texte),
  )
})

const lisible = (statut: string) => statut.toLowerCase().replace(/_/g, ' ')
const quand = (date: string) =>
  new Date(date).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit',
  })
</script>

<template>
  <div class="mx-auto max-w-[940px] animate-[apparition_0.2s_ease-out]">
    <p class="bandeau bandeau-info mb-4">
      <ScrollText :size="15" class="mt-px shrink-0" />
      Aucun statut ne change en silence : chaque passage laisse une trace datee, avec son
      auteur et, le cas echeant, le motif invoque.
    </p>

    <div class="mb-4 flex items-center gap-2 rounded-full bg-papier px-3.5 py-2 ring-1
                ring-trait">
      <Search :size="14" class="text-encre-douce" />
      <input
        v-model="recherche"
        type="search"
        placeholder="Statut, auteur, numero d objet…"
        class="w-full bg-transparent text-[12.5px] focus:outline-none"
      />
    </div>

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 8" :key="n" hauteur="40px" />
    </div>

    <div v-else-if="!visibles.length" class="carte">
      <div class="vide">
        <ScrollText :size="30" class="text-trait" />
        <b class="vide-titre">Aucune trace ne correspond</b>
      </div>
    </div>

    <div v-else class="carte">
      <h3 class="carte-titre">
        <span>{{ visibles.length }} evenement(s)</span>
        <span class="text-[11px] font-semibold text-encre-douce">du plus recent au plus ancien</span>
      </h3>
      <div v-for="trace in visibles" :key="trace.id" class="ligne">
        <span class="w-28 shrink-0 text-[11.5px] text-encre-douce">{{ quand(trace.date) }}</span>
        <span class="badge badge-neutre w-[92px] justify-center">
          {{ lisible(trace.type_objet) }} {{ trace.id_objet }}
        </span>
        <span class="flex min-w-0 flex-1 items-center gap-2">
          <span v-if="trace.statut_avant" class="truncate text-encre-douce">
            {{ lisible(trace.statut_avant) }}
          </span>
          <ArrowRight :size="12" class="shrink-0 text-encre-douce" />
          <b class="truncate">{{ lisible(trace.statut_apres) }}</b>
        </span>
        <span v-if="trace.commentaire" class="hidden max-w-[220px] truncate text-encre-douce
                                              lg:block">
          « {{ trace.commentaire }} »
        </span>
        <span class="w-40 shrink-0 truncate text-right text-[11.5px] text-encre-douce">
          {{ trace.par }}
        </span>
      </div>
    </div>
  </div>
</template>
