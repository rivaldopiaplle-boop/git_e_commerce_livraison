<script setup lang="ts" generic="T extends Record<string, unknown>">
// LA liste du projet. Toutes les listes de tous les rôles passent par ici.
//
// Elle repose désormais sur le **DataTable de PrimeVue**, comme le projet
// banque repose sur le DataGrid de MUI. D-26 l'imposait depuis le début :
// PrimeVue est là « pour ne pas redessiner à la main les tableaux, fenêtres,
// tiroirs et notifications que la règle d'or n°6 impose ». Je l'avais
// redessiné à la main — d'où une liste qui ne ressemblait à rien de connu.
//
// Ce qu'on gagne à ne pas réinventer : tri, pagination, filtre global,
// redimensionnement, navigation au clavier, rôles ARIA, et un rendu cohérent
// avec le reste des composants.
//
// L'interface publique n'a pas changé : les écrans déclarent leurs colonnes,
// remplissent les emplacements `col-<clé>`, `actions`, `outils` et `vide`.
// **Nouveau** : la ligne entière est cliquable — c'était le reproche « ce
// n'est pas cliquable, c'est bizarre ».
import { Search } from '@lucide/vue'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import { computed, ref } from 'vue'

import type { Colonne } from './liste'

const props = withDefaults(
  defineProps<{
    colonnes: Colonne<T>[]
    lignes: T[]
    cleLigne: (ligne: T) => string | number
    /** Le texte dans lequel la recherche cherche. Absente, pas de recherche. */
    recherche?: (ligne: T) => string
    placeholder?: string
    chargement?: boolean
    parPage?: number
    /** La ligne mise en avant, pour que la sélection se voie. */
    active?: (ligne: T) => boolean
  }>(),
  { parPage: 12, placeholder: 'Rechercher…' },
)

// Cliquer la ligne fait la même chose que son bouton « consulter » : c'est
// le geste naturel, et l'absence de réaction au clic donnait une impression
// d'écran mort.
const emission = defineEmits<{ 'ligne-cliquee': [T] }>()

const requete = ref('')

const filtrees = computed(() => {
  const texte = requete.value.trim().toLowerCase()
  if (!props.recherche || !texte) return props.lignes
  return props.lignes.filter((ligne) => props.recherche!(ligne).toLowerCase().includes(texte))
})

const ALIGNEMENTS: Record<string, string> = {
  droite: 'text-right justify-end',
  centre: 'text-center justify-center',
  gauche: 'text-left',
}
const MASQUES: Record<string, string> = {
  sm: 'hidden sm:table-cell',
  md: 'hidden md:table-cell',
  lg: 'hidden lg:table-cell',
  xl: 'hidden xl:table-cell',
}

function classeColonne(colonne: Colonne<T>) {
  return [
    colonne.masquerSous ? MASQUES[colonne.masquerSous] : '',
    ALIGNEMENTS[colonne.aligne ?? 'gauche'],
  ]
}
function styleColonne(colonne: Colonne<T>) {
  return colonne.largeur ? { width: `${colonne.largeur}px` } : undefined
}
</script>

<template>
  <div class="carte">
    <!-- Barre d'outils : recherche à gauche, actions de l'écran à droite -->
    <div
      v-if="recherche || $slots.outils"
      class="flex flex-wrap items-center justify-between gap-3 border-b border-trait-doux px-4 py-3"
    >
      <IconField v-if="recherche">
        <InputIcon>
          <Search :size="14" class="text-encre-douce" />
        </InputIcon>
        <InputText
          v-model="requete"
          type="search"
          :placeholder="placeholder"
          size="small"
          class="w-64"
        />
      </IconField>
      <span v-else />
      <span class="flex items-center gap-2">
        <slot name="outils" />
      </span>
    </div>

    <DataTable
      :value="filtrees"
      :data-key="undefined"
      :loading="chargement"
      :paginator="filtrees.length > parPage"
      :rows="parPage"
      removable-sort
      scrollable
      size="small"
      :row-class="(ligne) => (active?.(ligne as T) ? 'ligne-active' : '')"
      current-page-report-template="{first}–{last} sur {totalRecords}"
      paginator-template="PrevPageLink CurrentPageReport NextPageLink"
      @row-click="(evenement) => emission('ligne-cliquee', evenement.data as T)"
    >
      <Column
        v-for="colonne in colonnes"
        :key="colonne.cle"
        :field="colonne.champTri ?? colonne.cle"
        :header="colonne.titre"
        :sortable="!!colonne.champTri"
        :class="classeColonne(colonne)"
        :header-class="classeColonne(colonne)"
        :style="styleColonne(colonne)"
      >
        <template #body="{ data }">
          <slot :name="`col-${colonne.cle}`" :ligne="data as T" />
        </template>
      </Column>

      <!-- Les boutons-symboles : consulter et gérer, sans quitter la liste -->
      <Column
        v-if="$slots.actions"
        header="Actions"
        :style="{ width: '132px' }"
        class="text-right"
        header-class="text-right"
        frozen
        align-frozen="right"
      >
        <template #body="{ data }">
          <!-- `.stop` : cliquer un bouton d'action ne doit pas AUSSI
               déclencher le clic de la ligne. -->
          <span class="flex justify-end gap-1.5" @click.stop>
            <slot name="actions" :ligne="data as T" />
          </span>
        </template>
      </Column>

      <!-- État vide : rédigé, jamais un tableau muet (règle d'or n°2) -->
      <template #empty>
        <slot name="vide">
          <div class="vide">
            <b class="vide-titre">Aucun résultat</b>
            <p v-if="requete" class="vide-texte">Rien ne correspond à « {{ requete }} ».</p>
          </div>
        </slot>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
/* La liste vit dans une carte : elle n'a pas besoin de sa propre bordure. */
:deep(.p-datatable-table) {
  font-size: 12.5px;
}
:deep(.p-datatable-thead > tr > th) {
  background: transparent;
  border-color: var(--color-trait-doux);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-encre-douce);
}
:deep(.p-datatable-tbody > tr) {
  cursor: pointer;
  transition: background-color 0.12s ease;
}
:deep(.p-datatable-tbody > tr > td) {
  border-color: var(--color-trait-doux);
}
:deep(.p-datatable-tbody > tr:hover) {
  background: var(--color-atelier);
}
/* La ligne sélectionnée porte l'accent du rôle, en filet à gauche. */
:deep(.p-datatable-tbody > tr.ligne-active) {
  background: var(--accent-doux);
  box-shadow: inset 3px 0 0 0 var(--accent);
}
:deep(.p-datatable-paginator-bottom) {
  border-color: var(--color-trait-doux);
  font-size: 11.5px;
}
</style>
