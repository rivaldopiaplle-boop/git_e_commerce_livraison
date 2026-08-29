<script setup lang="ts">
// Les colis recus a l'entrepot, groupes par boutique deposante.
//
// C'est ainsi qu'ils arrivent physiquement : un vendeur Standard depose son
// lot du jour, pas un colis a la fois. Les grouper par commande obligerait le
// magasinier a faire dans sa tete le travail que l'ecran doit faire.
import { Building2, MapPin, Package, Warehouse } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { espaces, type Colis } from '../../api/espaces'
import Squelette from '../../composants/Squelette.vue'

const donnees = ref<Colis | null>(null)
const chargement = ref(true)

onMounted(async () => {
  try {
    donnees.value = await espaces.entrepot.colis()
  } finally {
    chargement.value = false
  }
})

const quand = (date: string | null) =>
  date
    ? new Date(date).toLocaleString('fr-FR', {
        day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
      })
    : '—'
</script>

<template>
  <div class="mx-auto max-w-[900px] animate-[apparition_0.2s_ease-out]">
    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 3" :key="n" hauteur="90px" />
    </div>

    <template v-else-if="donnees">
      <p class="bandeau bandeau-info mb-4">
        <Warehouse :size="15" class="mt-px shrink-0" />
        <span>
          <b>{{ donnees.entrepot?.nom ?? 'Entrepot' }}</b> — {{ donnees.total }} colis recu(s)
          de {{ donnees.groupes.length }} boutique(s). Un entrepot regroupe plusieurs
          vendeurs Standard : c'est ce qui rend une tournee possible.
        </span>
      </p>

      <div v-if="!donnees.groupes.length" class="carte">
        <div class="vide">
          <Package :size="30" class="text-trait" />
          <b class="vide-titre">Rien a receptionner</b>
          <p class="vide-texte">
            Aucun vendeur n a expedie de colis vers cet entrepot pour l instant. Les
            depots apparaitront ici des qu une boutique marquera une commande expediee.
          </p>
        </div>
      </div>

      <section v-for="groupe in donnees.groupes" :key="groupe.vendeur" class="carte mb-3">
        <h3 class="carte-titre">
          <span class="flex items-center gap-2">
            <Building2 :size="15" />
            {{ groupe.vendeur }}
            <span class="text-[11px] font-semibold text-encre-douce">{{ groupe.ville }}</span>
          </span>
          <span class="badge badge-cours">{{ groupe.colis.length }} colis</span>
        </h3>

        <div v-for="colis in groupe.colis" :key="colis.id" class="ligne">
          <Package :size="16" class="shrink-0 text-encre-douce" />
          <span class="min-w-0 flex-1">
            <b class="block truncate">{{ colis.numero_commande }}</b>
            <span class="flex items-center gap-1 text-[11.2px] text-encre-douce">
              <MapPin :size="11" /> {{ colis.destination }}
            </span>
          </span>
          <span class="text-encre-douce">{{ colis.articles }} article(s)</span>
          <span class="w-28 text-right text-[11.5px] text-encre-douce">
            recu le {{ quand(colis.date_expedition) }}
          </span>
        </div>
      </section>
    </template>
  </div>
</template>
