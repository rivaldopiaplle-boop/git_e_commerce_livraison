<script setup lang="ts">
// LA coquille, reprise **exactement** du modele de la maquette :
// sidebar claire de 210 px, navbar de 56 px, panneau droit de 300 px.
//
// Elle habille tout le site — catalogue public compris. Trois regles tenues
// ici, et rappelees parce qu'elles ont ete apprises a mes depens :
//   · aucun filtre dans la sidebar : ils vivent dans le contenu ;
//   · sidebar et navbar ne defilent jamais, seul le contenu defile ;
//   · une seule structure, du catalogue au tableau de bord.
import {
  Bell, ChevronsLeft, Lock, LogIn, LogOut, Search, ShoppingCart, UserRound,
} from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { espaces, type Notification } from '../api/espaces'

import BandeauLivrerA from './BandeauLivrerA.vue'
import LogoRivDinde from './LogoRivDinde.vue'
import PanneauActivite from './PanneauActivite.vue'
import PanneauLateral from './PanneauLateral.vue'
import { descriptionDuRole } from '../roles'
import { useAuthentification } from '../stores/authentification'
import { useCatalogue } from '../stores/catalogue'
import { usePanier } from '../stores/panier'

const session = useAuthentification()
const catalogue = useCatalogue()
const panier = usePanier()
const route = useRoute()
const routeur = useRouter()

const sidebarRepliee = ref(false)
const menuProfil = ref(false)

// La cloche existait sans jamais rien afficher. Elle se remplit a l'ouverture
// du menu plutot qu'au chargement de chaque page : une notification n'est pas
// une donnee critique, elle ne doit pas ralentir l'entree dans l'application.
const menuNotifications = ref(false)
const notifications = ref<Notification[]>([])
const nonLues = ref(0)
const notificationsChargees = ref(false)

async function ouvrirNotifications() {
  menuNotifications.value = !menuNotifications.value
  if (!menuNotifications.value || !session.estConnecte) return
  const donnees = await espaces.notifications.lire()
  notifications.value = donnees.notifications
  nonLues.value = donnees.non_lues
  notificationsChargees.value = true
  if (donnees.non_lues) {
    await espaces.notifications.marquerLues()
    nonLues.value = 0
  }
}

watch(
  () => session.estConnecte,
  async (connecte) => {
    if (!connecte) {
      notifications.value = []
      nonLues.value = 0
      notificationsChargees.value = false
      return
    }
    nonLues.value = (await espaces.notifications.lire()).non_lues
  },
  { immediate: true },
)

const role = computed(() => descriptionDuRole(session.role, session.sousRole))
const surLeCatalogue = computed(() => route.name === 'vitrine')

const initiale = computed(() => session.utilisateur?.prenom?.[0]?.toUpperCase() ?? '?')
const entreeActive = computed(() =>
  role.value.navigation.findIndex((entree) => entree.route === route.name),
)
const titre = computed(
  () => role.value.navigation[entreeActive.value]?.libelle ?? role.value.espace,
)

// La recherche pilote le catalogue. Depuis un autre ecran, chercher y ramene.
const recherche = ref(catalogue.recherche)
watch(recherche, (valeur) => {
  if (!surLeCatalogue.value) routeur.push({ name: 'vitrine' })
  catalogue.chercher(valeur)
})
watch(
  () => catalogue.recherche,
  (valeur) => {
    if (valeur !== recherche.value) recherche.value = valeur
  },
)
</script>

<template>
  <!-- h-screen + contenu qui defile : la sidebar et la navbar restent fixes. -->
  <div
    class="flex h-screen w-full overflow-hidden bg-atelier text-encre"
    :style="{ '--accent': role.accent, '--accent-doux': role.accentDoux }"
  >
    <!-- ── Sidebar ──────────────────────────────────────────────────── -->
    <aside
      class="barre-laterale flex shrink-0 flex-col border-r border-trait bg-panneau
             transition-[width] duration-200"
      :class="sidebarRepliee ? 'w-[64px]' : 'w-[210px]'"
    >
      <RouterLink
        :to="{ name: 'vitrine' }"
        class="flex items-center gap-2.5 overflow-hidden border-b border-trait-doux px-4 py-4
               whitespace-nowrap"
      >
        <LogoRivDinde :taille="24" />
        <span v-if="!sidebarRepliee" class="text-[13.5px] font-bold">RivDinde</span>
      </RouterLink>

      <nav class="flex flex-1 flex-col gap-0.5 overflow-hidden p-2.5">
        <component
          :is="entree.route ? 'RouterLink' : 'button'"
          v-for="(entree, index) in role.navigation"
          :key="entree.libelle"
          :to="entree.route ? { name: entree.route } : undefined"
          :type="entree.route ? undefined : 'button'"
          :disabled="entree.interdite || entree.prochainement"
          :title="
            entree.interdite
              ? entree.libelle + ' — reserve au proprietaire de la boutique'
              : entree.prochainement
                ? entree.libelle + ' — bientot'
                : entree.libelle
          "
          class="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px]
                 font-semibold whitespace-nowrap transition-colors duration-150"
          :class="
            index === entreeActive
              ? 'text-[color:var(--accent)]'
              : entree.interdite || entree.prochainement
                ? 'cursor-not-allowed text-encre-douce/40'
                : 'text-encre-douce hover:text-encre'
          "
          :style="
            index === entreeActive
              ? { background: 'var(--accent-doux)' }
              : undefined
          "
        >
          <component :is="entree.icone" :size="17" class="shrink-0" />
          <span v-if="!sidebarRepliee" class="truncate">{{ entree.libelle }}</span>
          <Lock v-if="entree.interdite && !sidebarRepliee" :size="12" class="ml-auto shrink-0" />
        </component>
      </nav>

      <div class="border-t border-trait-doux p-2.5">
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded-[9px] border border-dashed border-trait
                 px-2.5 py-2 text-[11.5px] font-semibold text-encre-douce transition-colors
                 hover:text-encre"
          @click="sidebarRepliee = !sidebarRepliee"
        >
          <ChevronsLeft
            :size="14"
            class="transition-transform duration-200"
            :class="sidebarRepliee ? 'rotate-180' : ''"
          />
          <span v-if="!sidebarRepliee">Reduire</span>
        </button>
      </div>
    </aside>

    <!-- ── Colonne centrale ─────────────────────────────────────────── -->
    <div class="flex min-w-0 flex-1 flex-col">
      <header
        class="barre-haute flex h-[56px] shrink-0 items-center justify-between gap-4
               border-b border-trait bg-papier px-[18px]"
      >
        <div class="min-w-0">
          <p
            class="text-[10px] font-bold tracking-[0.08em] uppercase"
            :style="{ color: role.accent }"
          >
            {{ role.espace }}
          </p>
          <h1 class="truncate text-[14px] font-bold">{{ titre }}</h1>
        </div>

        <div class="flex items-center gap-3.5">
          <BandeauLivrerA v-if="surLeCatalogue" clair class="hidden xl:block" />

          <div
            class="hidden items-center gap-2 rounded-full bg-atelier px-3.5 py-[7px] md:flex"
          >
            <Search :size="14" class="text-encre-douce" />
            <input
              v-model="recherche"
              type="search"
              placeholder="Rechercher…"
              class="w-[200px] bg-transparent text-[12.5px] text-encre placeholder:text-encre-douce
                     focus:outline-none"
            />
          </div>

          <button
            v-if="role.panneau === 'panier'"
            type="button"
            class="bouton-icone relative lg:hidden"
            title="Mon panier"
            @click="panier.ouvert = !panier.ouvert"
          >
            <ShoppingCart :size="17" />
            <span
              v-if="panier.nombreArticles"
              class="absolute top-1 right-1 h-[7px] w-[7px] rounded-full border-[1.5px]
                     border-white"
              :style="{ background: role.accent }"
            />
          </button>

          <div v-if="session.estConnecte" class="relative">
            <button
              type="button"
              class="bouton-icone relative"
              title="Notifications"
              @click="ouvrirNotifications"
            >
              <Bell :size="17" />
              <span
                v-if="nonLues"
                class="absolute top-1 right-1 h-[7px] w-[7px] rounded-full border-[1.5px]
                       border-white"
                :style="{ background: role.accent }"
              />
            </button>

            <Transition
              enter-active-class="transition duration-150"
              enter-from-class="opacity-0 -translate-y-1"
              leave-active-class="transition duration-100"
              leave-to-class="opacity-0"
            >
              <div
                v-if="menuNotifications"
                class="absolute top-full right-0 z-50 mt-2 w-[340px] overflow-hidden rounded-lg
                       border border-trait bg-papier shadow-lg"
              >
                <p class="border-b border-trait-doux px-4 py-2.5 text-[12.5px] font-bold">
                  Notifications
                </p>
                <div v-if="!notifications.length" class="vide !py-8">
                  <Bell :size="24" class="text-trait" />
                  <b class="vide-titre">Rien de nouveau</b>
                  <p class="vide-texte">
                    Les changements de statut de vos commandes s afficheront ici.
                  </p>
                </div>
                <div v-else class="max-h-[320px] overflow-auto">
                  <RouterLink
                    v-for="notification in notifications"
                    :key="notification.id"
                    :to="notification.lien || '/'"
                    class="ligne !text-[12px] hover:bg-atelier"
                    @click="menuNotifications = false"
                  >
                    <span
                      class="mt-1 h-[7px] w-[7px] shrink-0 rounded-full"
                      :style="{ background: notification.lue ? 'var(--color-trait)'
                                                             : role.accent }"
                    />
                    <span class="min-w-0 flex-1">
                      <b class="block truncate">{{ notification.titre }}</b>
                      <span class="text-encre-douce">{{ notification.contenu }}</span>
                    </span>
                  </RouterLink>
                </div>
              </div>
            </Transition>
          </div>

          <template v-if="session.estConnecte">
            <!-- Un menu profil, pas un bouton de deconnexion nu : c'est la ou
                 tout le monde va chercher son compte. -->
            <div class="relative">
              <button
                type="button"
                class="flex items-center gap-2.5 rounded-lg px-1.5 py-1 transition-colors
                       hover:bg-atelier"
                @click="menuProfil = !menuProfil"
              >
                <span
                  class="flex h-[30px] w-[30px] items-center justify-center rounded-full
                         text-[12px] font-bold text-white"
                  :style="{ background: role.accent }"
                >
                  {{ initiale }}
                </span>
                <span class="hidden leading-[1.25] sm:block">
                  <b class="block text-left text-[12.5px]">{{ session.utilisateur?.prenom }}</b>
                  <span class="text-[10.5px] text-encre-douce">{{ role.espace }}</span>
                </span>
              </button>

              <Transition
                enter-active-class="transition duration-150"
                enter-from-class="opacity-0 -translate-y-1"
                leave-active-class="transition duration-100"
                leave-to-class="opacity-0"
              >
                <div
                  v-if="menuProfil"
                  class="absolute top-full right-0 z-50 mt-2 w-56 rounded-lg border border-trait
                         bg-papier p-1.5 shadow-lg"
                >
                  <div class="border-b border-trait-doux px-3 py-2.5">
                    <b class="block text-[12.5px]">
                      {{ session.utilisateur?.prenom }} {{ session.utilisateur?.nom }}
                    </b>
                    <span class="text-[11px] text-encre-douce">
                      {{ session.utilisateur?.email }}
                    </span>
                  </div>
                  <RouterLink
                    :to="{ name: 'profil' }"
                    class="mt-1 flex items-center gap-2.5 rounded-md px-3 py-2 text-[12.5px]
                           text-encre-douce transition-colors hover:bg-atelier hover:text-encre"
                    @click="menuProfil = false"
                  >
                    <UserRound :size="15" /> Mon profil
                  </RouterLink>
                  <button
                    type="button"
                    class="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-left
                           text-[12.5px] text-encre-douce transition-colors hover:bg-[#fbe4e2]
                           hover:text-[#9c2116]"
                    @click="menuProfil = false; session.deconnecter()"
                  >
                    <LogOut :size="15" /> Se deconnecter
                  </button>
                </div>
              </Transition>
            </div>
          </template>

          <template v-else>
            <RouterLink :to="{ name: 'connexion' }" class="bouton-neutre !py-2 !text-[12.5px]">
              <LogIn :size="14" />
              <span class="hidden sm:block">Se connecter</span>
            </RouterLink>
            <RouterLink
              :to="{ name: 'inscription' }"
              class="bouton-accent hidden !py-2 !text-[12.5px] sm:inline-flex"
            >
              Creer un compte
            </RouterLink>
          </template>
        </div>
      </header>

      <!-- Le livreur travaille sur son telephone (D-40) : le lui dire vaut
           mieux que lui servir des ecrans web a moitie utiles. -->
      <p
        v-if="role.plateforme === 'mobile'"
        class="shrink-0 border-b border-[#e0d4f5] bg-[#f3edff] px-6 py-2.5 text-[12.5px]
               text-[#5b21b6]"
      >
        L espace livreur s utilise depuis l application mobile. Cet ecran web sert au suivi.
      </p>

      <main class="flex-1 overflow-auto px-6 py-5">
        <slot />
      </main>
    </div>

    <!-- ── Panneau droit, stable et retractable ─────────────────────── -->
    <!-- Le panier pour qui achete, l'activite pour qui travaille : un vendeur
         n'a pas de panier, et lui en afficher un ferait amateur. -->
    <PanneauLateral v-if="role.panneau === 'panier'" />
    <PanneauActivite v-else />
  </div>
</template>
