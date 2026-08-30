// Ce que l'écran en cours pousse dans le panneau de droite.
//
// Repris de `useVolet` du projet banque : chaque page décide ce qu'elle met
// dans le volet, au lieu de laisser un panneau générique afficher la même
// chose partout. C'était la remarque du bloc K-1 : « le panneau droit des
// autres rôles n'a rien, pourquoi ? » — parce qu'aucun écran ne le nourrissait.
//
// Le contenu lui-même voyage par `<Teleport>` : le magasin ne retient que le
// titre et le fait qu'un écran contribue, ce qui suffit à savoir s'il faut
// afficher le repli (l'activité) ou non.
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useVolet = defineStore('volet', () => {
  const titre = ref<string | null>(null)
  const contributeurs = ref(0)

  function ouvrir(nouveauTitre: string) {
    titre.value = nouveauTitre
    contributeurs.value += 1
  }

  function fermer() {
    contributeurs.value = Math.max(0, contributeurs.value - 1)
    if (contributeurs.value === 0) titre.value = null
  }

  return { titre, contributeurs, ouvrir, fermer }
})
