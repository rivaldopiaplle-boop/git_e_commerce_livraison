import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'

/**
 * Les règles de saisie du projet, écrites une fois — D-26.
 *
 * `vee-validate` + `zod` sont l'équivalent Vue de `react-hook-form` + `zod`
 * du projet banque. Ils étaient **déclarés dans `package.json` et utilisés
 * nulle part** : les formulaires validaient à la main, chacun à sa façon, et
 * découvraient la moitié des erreurs en revenant du serveur.
 *
 * Ce que ça change concrètement, et pourquoi ça valait le détour :
 *
 *   · **l'erreur s'affiche au moment où on quitte le champ**, pas après un
 *     aller-retour réseau. Découvrir « le mot de passe est trop court » après
 *     avoir cliqué « Créer mon compte » est ce qui fait abandonner ;
 *   · **une seule définition par règle.** Le mot de passe faisait dix
 *     caractères ici, huit là, et rien du tout dans le troisième formulaire ;
 *   · **le serveur reste seul juge.** Ces règles doublent les siennes pour le
 *     confort ; elles ne les remplacent pas. Une validation qui n'existe que
 *     dans le navigateur ne protège de rien.
 */

// ── Les briques, réutilisées d'un formulaire à l'autre ───────────────────

const texteRequis = (quoi: string, minimum = 2) =>
  z.string().trim().min(minimum, `${quoi} est obligatoire.`)

const courriel = z
  .string()
  .trim()
  .min(1, "L'adresse e-mail est obligatoire.")
  .email('Cette adresse e-mail ne ressemble pas à une adresse valide.')

/**
 * Le mot de passe.
 *
 * Dix caractères, et **on n'exige ni majuscule ni chiffre ni symbole**. Les
 * règles de composition poussent aux mots de passe du genre `Passe1234!`, que
 * les gens réutilisent partout ; la longueur protège mieux. C'est aussi ce que
 * recommandent l'ANSSI et le NIST depuis 2017. Django, côté serveur, refuse en
 * plus les mots de passe trop communs.
 */
const motDePasse = z
  .string()
  .min(10, 'Dix caractères au minimum : la longueur protège mieux que les symboles.')

const codePostal = z
  .string()
  .trim()
  .regex(/^\d{5}$/, 'Un code postal français fait cinq chiffres.')

// ── Les schémas, un par formulaire ───────────────────────────────────────

export const schemaConnexion = toTypedSchema(
  z.object({
    email: courriel,
    // À la connexion, on ne redit PAS la règle de longueur : le mot de passe
    // existe déjà, et reprocher sa forme à quelqu'un qui essaie d'entrer est
    // une façon de le perdre.
    mot_de_passe: z.string().min(1, 'Le mot de passe est obligatoire.'),
  }),
)

const compteCommun = {
  prenom: texteRequis('Le prénom'),
  nom: texteRequis('Le nom'),
  email: courriel,
  mot_de_passe: motDePasse,
}

/**
 * L'inscription d'un client ou d'un livreur.
 *
 * `nom_boutique` y figure en **facultatif** alors qu'il ne les concerne pas :
 * le formulaire d'inscription change de schéma quand on change d'onglet, et
 * deux schémas de formes différentes obligeraient l'écran à jongler avec deux
 * types. Un champ facultatif ignoré coûte moins cher qu'un `as never`.
 */
export const schemaInscription = toTypedSchema(
  z.object({ ...compteCommun, nom_boutique: z.string().trim().optional() }),
)

/** Le même, mais un vendeur DOIT nommer sa boutique. */
export const schemaBoutique = toTypedSchema(
  z.object({ ...compteCommun, nom_boutique: texteRequis('Le nom de la boutique') }),
)

export const schemaGestionnaire = toTypedSchema(
  z.object({
    prenom: texteRequis('Le prénom'),
    nom: texteRequis('Le nom'),
    email: courriel,
    mot_de_passe: motDePasse,
  }),
)

export const schemaAdresse = toTypedSchema(
  z.object({
    libelle: z.string().trim().optional(),
    rue: texteRequis('La rue', 4),
    complement: z.string().trim().optional(),
    code_postal: codePostal,
    ville: texteRequis('La ville'),
    instructions_livraison: z.string().trim().optional(),
  }),
)

/** Exporté pour les tests : une règle qu'on ne peut pas vérifier ne vaut rien. */
export const REGLES = { courriel, motDePasse, codePostal }
