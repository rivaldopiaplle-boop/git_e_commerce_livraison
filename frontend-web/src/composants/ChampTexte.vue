<script setup lang="ts">
// Le champ de formulaire de toute l'application : libellé, icône, message
// d'erreur, aide. L'écrire une fois évite que le troisième écran ait des
// champs légèrement différents des deux premiers.
//
// Il fonctionne de **deux façons**, et c'est délibéré :
//
//   · avec `nom`, il se branche sur `vee-validate` : la valeur, l'erreur et le
//     moment où elle s'affiche viennent du formulaire. C'est le mode à
//     préférer — l'erreur apparaît quand on quitte le champ, pas après un
//     aller-retour réseau ;
//   · sans `nom`, il reste un `v-model` ordinaire, pour les formulaires
//     courts d'une popup où monter un schéma coûterait plus qu'il ne rapporte.
//
// Deux modes plutôt qu'un seul parce que la migration se fait écran par écran :
// un composant qui casserait les quinze formulaires existants d'un coup n'est
// pas une amélioration.
import { useField } from 'vee-validate'
import { computed, type Component } from 'vue'

const proprietes = defineProps<{
  label: string
  /** Le nom du champ dans le schéma. Sa présence branche `vee-validate`. */
  nom?: string
  icone?: Component
  type?: string
  aide?: string
  /** Une erreur venue du serveur, qui prime sur celle du schéma. */
  erreur?: string
  autocomplete?: string
  requis?: boolean
  minlength?: number
}>()

const modele = defineModel<string>()

// `useField` doit être appelé au montage, sans condition : les crochets de Vue
// ne se déclarent pas dans un `if`. On l'appelle donc toujours, avec un nom de
// repli, et on ignore son résultat quand le champ n'est pas piloté.
const champ = useField<string>(() => proprietes.nom ?? '__hors_formulaire__')
const pilote = computed(() => Boolean(proprietes.nom))

const valeur = computed({
  get: () => (pilote.value ? (champ.value.value ?? '') : (modele.value ?? '')),
  set: (nouvelle: string) => {
    if (pilote.value) champ.value.value = nouvelle
    else modele.value = nouvelle
  },
})

// L'erreur du serveur prime : elle sait des choses que le navigateur ignore,
// comme « cette adresse e-mail est déjà prise ».
const messageErreur = computed(
  () => proprietes.erreur || (pilote.value ? champ.errorMessage.value : ''),
)

function quitterLeChamp() {
  if (pilote.value) champ.handleBlur()
}
</script>

<template>
  <label class="flex flex-col gap-1.5">
    <span class="text-[13px] font-semibold text-encre-douce">{{ label }}</span>

    <span class="relative flex items-center">
      <component
        :is="icone"
        v-if="icone"
        :size="17"
        class="pointer-events-none absolute left-3.5 text-encre-douce"
      />
      <input
        v-model="valeur"
        :type="type ?? 'text'"
        :required="requis"
        :minlength="minlength"
        :autocomplete="autocomplete"
        :aria-invalid="messageErreur ? 'true' : undefined"
        class="champ-clair"
        :class="[icone ? 'pl-10' : '', messageErreur ? 'champ-erreur' : '']"
        @blur="quitterLeChamp"
      />
    </span>

    <span v-if="messageErreur" class="text-[12px] font-semibold text-alerte">
      {{ messageErreur }}
    </span>
    <span v-else-if="aide" class="text-[11.5px] text-encre-douce">{{ aide }}</span>
  </label>
</template>
