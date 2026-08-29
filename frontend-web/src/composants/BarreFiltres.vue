<script setup lang="ts">
// La colonne de filtres a gauche (regle d'or n°6 : sidebar retractable).
//
// Les compteurs viennent du serveur et decrivent CE QUI EST REELLEMENT
// VISIBLE : depuis Paris, « Plats » n'affiche plus 4 alors qu'aucun plat n'est
// livrable. C'est la correction du bug le plus trompeur du catalogue.
import { Bike, ChevronsLeft, Package, Store, Tag } from '@lucide/vue'
import { ref } from 'vue'

export type Univers = {
  nom: string
  nombre: number
  categories: { slug: string; nom: string; nombre: number }[]
}
export type BoutiqueFacette = { id: number; nom: string; type_service: string; nombre: number }

defineProps<{ univers: Univers[]; boutiques: BoutiqueFacette[]; total: number }>()

const categorie = defineModel<string | undefined>('categorie')
const boutique = defineModel<string | undefined>('boutique')
const service = defineModel<string | undefined>('service')

const repliee = ref(false)

const SERVICES = [
  { cle: undefined, libelle: 'Tous les services', icone: Store },
  { cle: 'EXPRESS', libelle: 'Express', icone: Bike },
  { cle: 'STANDARD', libelle: 'Standard', icone: Package },
]

function basculer<T>(actuel: T | undefined, valeur: T): T | undefined {
  return actuel === valeur ? undefined : valeur
}
</script>

<template>
  <aside
    class="shrink-0 transition-[width] duration-200"
    :class="repliee ? 'w-[52px]' : 'w-[240px]'"
  >
    <div class="sticky top-[84px]">
      <button
        type="button"
        class="mb-3 flex items-center gap-2 rounded-lg px-2 py-1.5 text-[12px] text-[#7c6459]
               transition-colors hover:text-marque-clair"
        @click="repliee = !repliee"
      >
        <ChevronsLeft
          :size="15"
          class="transition-transform duration-200"
          :class="repliee ? 'rotate-180' : ''"
        />
        <span v-if="!repliee">Replier les filtres</span>
      </button>

      <div v-if="!repliee" class="flex flex-col gap-6">
        <!-- Service -->
        <section>
          <b class="text-[11px] tracking-[0.09em] text-[#7c6459] uppercase">Service</b>
          <div class="mt-2.5 flex flex-col gap-1">
            <button
              v-for="option in SERVICES"
              :key="option.libelle"
              type="button"
              class="flex items-center gap-2.5 rounded-xl px-3 py-2 text-left text-[13px]
                     transition-colors duration-150"
              :class="
                service === option.cle
                  ? 'bg-marque/12 font-semibold text-marque'
                  : 'text-[#b49a8c] hover:bg-white/4'
              "
              @click="service = option.cle"
            >
              <component :is="option.icone" :size="15" />
              {{ option.libelle }}
            </button>
          </div>
        </section>

        <!-- Categories, groupees par univers -->
        <section v-for="groupe in univers" :key="groupe.nom">
          <b class="flex items-center justify-between text-[11px] tracking-[0.09em]
                    text-[#7c6459] uppercase">
            {{ groupe.nom }}
            <span class="text-[10px] normal-case">{{ groupe.nombre }}</span>
          </b>
          <div class="mt-2.5 flex flex-col gap-0.5">
            <button
              v-for="element in groupe.categories"
              :key="element.slug"
              type="button"
              class="flex items-center justify-between rounded-xl px-3 py-1.5 text-left
                     text-[13px] transition-colors duration-150"
              :class="
                categorie === element.slug
                  ? 'bg-marque/12 font-semibold text-marque'
                  : 'text-[#b49a8c] hover:bg-white/4'
              "
              @click="categorie = basculer(categorie, element.slug)"
            >
              <span class="flex items-center gap-2">
                <Tag :size="13" class="opacity-50" />
                {{ element.nom }}
              </span>
              <span class="text-[11px] opacity-60">{{ element.nombre }}</span>
            </button>
          </div>
        </section>

        <!-- Boutiques -->
        <section v-if="boutiques.length">
          <b class="text-[11px] tracking-[0.09em] text-[#7c6459] uppercase">Boutiques</b>
          <div class="mt-2.5 flex flex-col gap-0.5">
            <button
              v-for="element in boutiques"
              :key="element.id"
              type="button"
              class="flex items-center justify-between rounded-xl px-3 py-1.5 text-left
                     text-[13px] transition-colors duration-150"
              :class="
                boutique === String(element.id)
                  ? 'bg-marque/12 font-semibold text-marque'
                  : 'text-[#b49a8c] hover:bg-white/4'
              "
              @click="boutique = basculer(boutique, String(element.id))"
            >
              <span class="flex items-center gap-2 truncate">
                <component
                  :is="element.type_service === 'EXPRESS' ? Bike : Package"
                  :size="13"
                  class="opacity-50"
                />
                {{ element.nom }}
              </span>
              <span class="text-[11px] opacity-60">{{ element.nombre }}</span>
            </button>
          </div>
        </section>

        <button
          v-if="categorie || boutique || service"
          type="button"
          class="bouton-discret w-full !py-2 text-[12.5px]"
          @click="categorie = undefined; boutique = undefined; service = undefined"
        >
          Tout effacer
        </button>
      </div>
    </div>
  </aside>
</template>
