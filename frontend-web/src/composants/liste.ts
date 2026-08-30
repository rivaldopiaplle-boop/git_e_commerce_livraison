// La déclaration d'une colonne de `Liste.vue`.
//
// Dans un fichier à part et non dans le `<script setup>` : un type exporté
// depuis un SFC n'est pas toujours vu comme un vrai type par les écrans qui
// l'importent, et un type qui redevient `any` en silence ne protège plus de
// rien — c'est exactement la classe d'erreur invisible que le bloc J a coûtée.
export type Colonne<L> = {
  cle: string
  titre: string
  /** Largeur fixe, en pixels. Sans elle, la colonne prend la place restante. */
  largeur?: number
  aligne?: 'gauche' | 'droite' | 'centre'
  /** Sa présence rend l'en-tête cliquable. */
  tri?: (a: L, b: L) => number
  /** Masquée sous cette largeur d'écran, pour rester lisible en étroit. */
  masquerSous?: 'sm' | 'md' | 'lg' | 'xl'
}
