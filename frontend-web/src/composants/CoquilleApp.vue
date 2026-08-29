<script setup lang="ts">
// La coquille commune aux cinq roles : sidebar retractable a gauche, navbar en
// haut, panneau retractable a droite (regles d'or 6 et 8).
//
// Une seule application, cinq peaux : seule la couleur d'accent change, portee
// par une variable CSS. Ecrire une coquille par role serait le debut de la
// divergence (design-system.md § 8).
import { Bell, ChevronsLeft, LogOut, PanelRight, Search, X } from '@lucide/vue'
import { computed, ref } from 'vue'

import { descriptionDuRole } from '../roles'
import { useAuthentification } from '../stores/authentification'
import LogoRivDinde from './LogoRivDinde.vue'

const session = useAuthentification()

const sidebarOuverte = ref(true)
const panneauOuvert = ref(false)
const entreeActive = ref(0)

const role = computed(() => descriptionDuRole(session.role))
const initiales = computed(() => {
  const u = session.utilisateur
  return u ? `${u.prenom[0] ?? ''}${u.nom[0] ?? ''}`.toUpperCase() : '?'
})
</script>

<template>
  <div
    class="flex min-h-screen w-full bg-atelier text-slate-900"
    :style="{ '--accent': role.accent, '--accent-doux': role.accentDoux }"
  >
    <!-- ── Sidebar ──────────────────────────────────────────────────── -->
    <aside
      class="flex shrink-0 flex-col bg-ardoise text-slate-300 transition-[width] duration-200"
      :class="sidebarOuverte ? 'w-[248px]' : 'w-[76px]'"
    >
      <div class="flex h-[68px] items-center gap-3 px-5">
        <LogoRivDinde :taille="34" />
        <span v-if="sidebarOuverte" class="font-semibold tracking-tight text-white">RivDinde</span>
      </div>

      <nav class="flex flex-1 flex-col gap-0.5 px-3">
        <button
          v-for="(entree, index) in role.navigation"
          :key="entree.libelle"
          type="button"
          :title="entree.libelle"
          class="group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-left
                 text-[13.5px] transition-colors duration-150"
          :class="
            index === entreeActive
              ? 'text-white'
              : 'text-slate-400 hover:bg-white/6 hover:text-slate-100'
          "
          :style="index === entreeActive ? { background: 'var(--accent)' } : undefined"
          @click="entreeActive = index"
        >
          <component :is="entree.icone" :size="18" class="shrink-0" />
          <span v-if="sidebarOuverte" class="truncate">{{ entree.libelle }}</span>
          <span
            v-if="sidebarOuverte && entree.prochainement"
            class="ml-auto rounded-full bg-white/10 px-1.5 py-0.5 text-[10px] text-slate-300"
          >
            bientot
          </span>
        </button>
      </nav>

      <button
        type="button"
        class="mx-3 mb-3 flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-[12.5px]
               text-slate-500 transition-colors duration-150 hover:bg-white/6 hover:text-slate-300"
        @click="sidebarOuverte = !sidebarOuverte"
      >
        <ChevronsLeft
          :size="17"
          class="transition-transform duration-200"
          :class="sidebarOuverte ? '' : 'rotate-180'"
        />
        <span v-if="sidebarOuverte">Replier le menu</span>
      </button>
    </aside>

    <!-- ── Colonne centrale ─────────────────────────────────────────── -->
    <div class="flex min-w-0 flex-1 flex-col">
      <header
        class="flex h-[68px] shrink-0 items-center justify-between gap-6 border-b
               border-slate-200 bg-white px-6"
      >
        <div class="min-w-0">
          <p class="text-[11px] font-bold tracking-[0.09em] uppercase" :style="{ color: role.accent }">
            {{ role.espace }}
          </p>
          <h1 class="truncate text-[17px] font-semibold tracking-tight">
            {{ role.navigation[entreeActive]?.libelle }}
          </h1>
        </div>

        <div class="flex items-center gap-2.5">
          <div class="relative hidden md:block">
            <Search :size="16" class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              placeholder="Rechercher…"
              class="w-56 rounded-xl border border-slate-200 bg-slate-50 py-2 pr-3 pl-9
                     text-[13.5px] transition-colors duration-150 focus:border-slate-300
                     focus:bg-white focus:outline-none"
            />
          </div>

          <button
            type="button"
            title="Notifications"
            class="relative flex h-9 w-9 items-center justify-center rounded-xl border
                   border-slate-200 text-slate-600 transition-colors duration-150
                   hover:bg-slate-50"
            @click="panneauOuvert = !panneauOuvert"
          >
            <Bell :size="17" />
          </button>

          <button
            type="button"
            title="Panneau lateral"
            class="hidden h-9 w-9 items-center justify-center rounded-xl border border-slate-200
                   text-slate-600 transition-colors duration-150 hover:bg-slate-50 lg:flex"
            @click="panneauOuvert = !panneauOuvert"
          >
            <PanelRight :size="17" />
          </button>

          <div class="ml-1 flex items-center gap-2.5 border-l border-slate-200 pl-3">
            <span
              class="flex h-9 w-9 items-center justify-center rounded-full text-[12.5px] font-bold"
              :style="{ background: role.accentDoux, color: role.accent }"
            >
              {{ initiales }}
            </span>
            <div class="hidden leading-tight sm:block">
              <b class="block text-[13px]">{{ session.utilisateur?.prenom }}</b>
              <span class="text-[11.5px] text-slate-500">{{ session.utilisateur?.email }}</span>
            </div>
            <button
              type="button"
              title="Se deconnecter"
              class="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500
                     transition-colors duration-150 hover:bg-red-50 hover:text-red-600"
              @click="session.deconnecter()"
            >
              <LogOut :size="17" />
            </button>
          </div>
        </div>
      </header>

      <main class="flex-1 overflow-x-hidden p-6">
        <slot />
      </main>
    </div>

    <!-- ── Panneau lateral droit ────────────────────────────────────── -->
    <Transition
      enter-active-class="transition-all duration-200"
      enter-from-class="opacity-0 translate-x-4"
      leave-active-class="transition-all duration-150"
      leave-to-class="opacity-0 translate-x-4"
    >
      <aside
        v-if="panneauOuvert"
        class="hidden w-[320px] shrink-0 border-l border-slate-200 bg-white p-5 lg:block"
      >
        <div class="flex items-center justify-between">
          <b class="text-[14px]">Notifications</b>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400
                   transition-colors hover:bg-slate-100"
            @click="panneauOuvert = false"
          >
            <X :size="16" />
          </button>
        </div>

        <div class="mt-16 flex flex-col items-center text-center">
          <span
            class="flex h-14 w-14 items-center justify-center rounded-2xl"
            :style="{ background: role.accentDoux, color: role.accent }"
          >
            <Bell :size="22" />
          </span>
          <b class="mt-4 text-[14px]">Aucune notification</b>
          <p class="mt-1 text-[13px] text-slate-500">
            Les changements de statut de vos commandes s'afficheront ici.
          </p>
        </div>
      </aside>
    </Transition>
  </div>
</template>
