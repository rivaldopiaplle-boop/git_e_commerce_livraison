// La déclaration d'une colonne de `Liste.vue`.
//
// Dans un fichier à part et non dans le `<script setup>` : un type exporté
// depuis un SFC n'est pas toujours vu comme un vrai type par les écrans qui
// l'importent, et un type qui redevient `any` en silence ne protège de rien.
export type Colonne<L> = {
  /** Identifie la colonne et nomme son emplacement de rendu : `col-<clé>`. */
  cle: string
  titre: string
  /** Largeur fixe, en pixels. Sans elle, la colonne prend la place restante. */
  largeur?: number
  aligne?: 'gauche' | 'droite' | 'centre'

  /** La **propriété de la ligne** sur laquelle trier. Sa présence rend
   *  l'en-tête cliquable.
   *
   *  C'est une propriété et non un comparateur, parce que c'est ainsi que le
   *  DataTable de PrimeVue trie. Une première version passait un comparateur
   *  via `sortFunction` : cette option n'existe pas dans PrimeVue 5, elle
   *  partait dans le DOM comme un attribut inerte, et le tri ne faisait
   *  **rien** sans que rien ne le signale. Le type interdit désormais de
   *  refaire l'erreur.
   */
  champTri?: keyof L & string
  /** Masquée sous cette largeur d'écran, pour rester lisible en étroit. */
  masquerSous?: 'sm' | 'md' | 'lg' | 'xl'
}
