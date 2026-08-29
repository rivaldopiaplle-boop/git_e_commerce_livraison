<script setup lang="ts">
import LogoRivDinde from './LogoRivDinde.vue'

const colonnes = [
  { titre: 'Commander', liens: ['Catalogue', 'Boutiques Express', 'Boutiques Standard'] },
  { titre: 'Rejoindre', liens: ['Devenir vendeur', 'Devenir livreur', 'Ouvrir un entrepot'] },
  { titre: 'La plateforme', liens: ['Comment ca marche', 'Frais de livraison', 'Nous contacter'] },
]
</script>

<template>
  <footer class="mt-20 border-t border-encre-3 bg-encre-2/40">
    <div class="mx-auto grid max-w-[1240px] gap-10 px-5 py-14 sm:grid-cols-2 lg:grid-cols-4">
      <div>
        <LogoRivDinde :taille="40" />
        <p class="mt-4 text-[13.5px] leading-relaxed text-[#b49a8c]">
          Commander, livrer, suivre. Deux rythmes de livraison, une seule
          plateforme.
        </p>
      </div>

      <div v-for="colonne in colonnes" :key="colonne.titre">
        <b class="text-[12px] tracking-[0.09em] text-marque uppercase">{{ colonne.titre }}</b>
        <ul class="mt-4 flex flex-col gap-2.5">
          <li v-for="lien in colonne.liens" :key="lien">
            <span class="text-[13.5px] text-[#b49a8c]">{{ lien }}</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="border-t border-encre-3 px-5 py-5">
      <p class="mx-auto max-w-[1240px] text-[12px] text-[#7c6459]">
        Projet de demonstration — aucune commande reelle, aucun paiement reel.
        Les photos proviennent de banques d'images sous licence libre.
      </p>
    </div>
  </footer>
</template>
