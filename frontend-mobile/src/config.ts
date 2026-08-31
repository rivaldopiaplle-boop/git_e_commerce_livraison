// L'adresse de l'API, et pourquoi elle ne peut pas être « localhost ».
//
// Une application installée sur un téléphone n'a AUCUN moyen de joindre le
// `localhost` de la machine de développement : `localhost`, pour elle, c'est
// le téléphone lui-même. C'est le premier piège du développement mobile, et
// il coûte une soirée à qui ne le sait pas.
//
// En développement on pointe donc l'IP locale de la machine ; en production,
// l'URL publique de l'API.
export const URL_API =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

/** Le mot de passe commun aux comptes de démonstration.
 *
 *  Il n'est pas secret : c'est un jeu de vitrine, et le proposer d'un bouton
 *  rend la démonstration tenable en dix minutes (règle d'or n°3).
 */
export const MOT_DE_PASSE_DEMO = 'Demonstration!2026'
