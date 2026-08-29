<script setup lang="ts">
// Les onglets soulignes de la maquette. « Navigation a onglets » figure
// explicitement dans les regles d'or : le contenu d'un tableau de bord se
// range en onglets, pas en une seule colonne interminable.
defineProps<{ onglets: { cle: string; libelle: string; compteur?: number }[] }>()
const actif = defineModel<string>({ required: true })
</script>

<template>
  <div class="mb-4 flex gap-1 border-b border-trait">
    <button
      v-for="onglet in onglets"
      :key="onglet.cle"
      type="button"
      class="mr-4 border-b-2 px-1 py-2.5 text-[13px] font-semibold transition-colors
             duration-150"
      :class="
        actif === onglet.cle
          ? 'text-[color:var(--accent)]'
          : 'border-transparent text-encre-douce hover:text-encre'
      "
      :style="actif === onglet.cle ? { borderColor: 'var(--accent)' } : undefined"
      @click="actif = onglet.cle"
    >
      {{ onglet.libelle }}
      <span
        v-if="onglet.compteur !== undefined"
        class="ml-1.5 rounded-full bg-atelier px-1.5 py-0.5 text-[10.5px] font-bold"
      >
        {{ onglet.compteur }}
      </span>
    </button>
  </div>
</template>
