<script setup lang="ts">
// Le symbole de la marque, en SVG : net a 16 pixels comme a 400, aucun fichier
// image a charger, et recolorable par role (design-system.md § 2).
// Reference : plan-organisation/04-maquettes/identite-visuelle.html
withDefaults(defineProps<{ taille?: number; couleur?: string }>(), {
  taille: 40,
})
</script>

<template>
  <svg
    :width="taille"
    :height="taille"
    viewBox="0 0 100 96"
    role="img"
    aria-label="Colibri"
  >
    <defs v-if="!couleur">
      <linearGradient :id="`t${taille}`" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#7ff0dd" /><stop offset="1" stop-color="#14b8a6" />
      </linearGradient>
      <linearGradient :id="`g${taille}`" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#0f9b8e" /><stop offset="1" stop-color="#0b5d55" />
      </linearGradient>
      <linearGradient :id="`d${taille}`" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#0d7d72" /><stop offset="1" stop-color="#073d38" />
      </linearGradient>
      <linearGradient :id="`a${taille}`" x1="0" y1="1" x2="1" y2="0">
        <stop offset="0" stop-color="#2dd4bf" /><stop offset="1" stop-color="#a7f3e4" />
      </linearGradient>
    </defs>

    <!-- Version couleur de marque : un degrade par face, une seule lumiere. -->
    <g v-if="!couleur" transform="translate(0,2)">
      <path d="M50 18 L80 35 L50 52 L20 35 Z" :fill="`url(#t${taille})`" />
      <path d="M20 35 L50 52 L50 82 L20 65 Z" :fill="`url(#g${taille})`" />
      <path d="M80 35 L50 52 L50 82 L80 65 Z" :fill="`url(#d${taille})`" />
      <path
        d="M50 18 L80 35 L50 52 L20 35 Z"
        fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="1.1"
      />
      <path d="M35 26.5 L50 35 L35 43.5 L20 35 Z" fill="#fff" fill-opacity=".16" />
      <path d="M50 17 C76 1 97 7 95 25 C87 16 71 13 50 17 Z" :fill="`url(#a${taille})`" />
      <path d="M54 12 C70 3 82 5 83 14 C75 10 65 10 54 12 Z" fill="#fff" fill-opacity=".55" />
    </g>

    <!-- Version teintee : une seule couleur, trois opacites. C'est ce qui
         produit les cinq variantes de role sans dessiner cinq fichiers. -->
    <g v-else transform="translate(0,2)" :fill="couleur">
      <path d="M50 18 L80 35 L50 52 L20 35 Z" opacity=".95" />
      <path d="M20 35 L50 52 L50 82 L20 65 Z" opacity=".62" />
      <path d="M80 35 L50 52 L50 82 L80 65 Z" opacity=".38" />
      <path d="M50 17 C76 1 97 7 95 25 C87 16 71 13 50 17 Z" opacity=".85" />
    </g>
  </svg>
</template>
