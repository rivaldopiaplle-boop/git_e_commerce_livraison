<script setup lang="ts">
// Le détail d'une ligne de liste, à deux endroits, écrit une seule fois — M-1.
//
// **Ta remarque** : *« le symbole œil doit ouvrir une fenêtre popup »*. Il se
// contentait de sélectionner la ligne, ce que tu avais déjà jugé inutile au
// bloc L-2 : *« l'œil bouton pour consulter au lieu d'ouvrir une fenêtre popup
// sélectionne, ce qui ne sert à rien »*.
//
// Les deux endroits ne font pas double emploi, et c'est exactement le partage
// de [D-60](journal-decisions) :
//
//   · **le panneau de droite** est le contexte permanent. Il suit la ligne
//     active et reste là pendant qu'on travaille dans la liste ;
//   · **la popup** est le geste « je veux voir ça maintenant, sans perdre ma
//     place ». C'est ce qu'un œil promet, et c'est ce qu'il fait désormais.
//
// Le contenu est passé **une fois** par la vue appelante, dans le slot par
// défaut. Vue appelle la fonction de slot autant de fois qu'on l'écrit : le
// même détail se rend donc dans la popup et dans le panneau sans être écrit
// deux fois. Deux copies d'un même détail finissent toujours par diverger, et
// c'est celle qu'on ne regarde pas qui ment.
import Popup from './Popup.vue'
import Volet from './Volet.vue'

defineProps<{
  titre: string
  /** L'œil a été cliqué : la popup s'ouvre par-dessus, la liste reste dessous. */
  apercuOuvert?: boolean
  explication?: string
}>()

defineEmits<{ fermerApercu: [] }>()
</script>

<template>
  <Popup
    v-if="apercuOuvert"
    :titre="titre"
    :explication="explication"
    @fermer="$emit('fermerApercu')"
  >
    <slot />
    <template #actions>
      <!-- Les actions de la popup sont facultatives : un aperçu peut n'être
           qu'une lecture, et un pied de fenêtre vide est du bruit. -->
      <slot name="actions" />
    </template>
  </Popup>

  <Volet :titre="titre">
    <slot />
  </Volet>
</template>
