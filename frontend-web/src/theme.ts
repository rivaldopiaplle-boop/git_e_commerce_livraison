// Le thème PrimeVue, calé sur les jetons de la maquette.
//
// D-26 impose **PrimeVue posé sur Tailwind**, et pour une raison précise :
// « pour ne pas redessiner à la main les tableaux, fenêtres, tiroirs et
// notifications que la règle d'or n°6 impose ». J'avais fait exactement le
// contraire — un tableau à la main, une fenêtre à la main, un tiroir à la
// main, des notifications à la main. C'est pour ça que rien ne ressemblait au
// projet banque, qui repose lui sur MUI.
//
// Le préréglage ci-dessous n'invente pas de couleurs : il branche les
// composants PrimeVue sur les jetons déjà définis dans `style.css`, et sur
// `--accent`, la couleur du rôle connecté (règle d'or n°8). Un tableau, une
// fenêtre et un toast prennent donc automatiquement le bleu du vendeur, le
// vert du client ou le rouge de l'admin.
import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'

export const themeRivDinde = definePreset(Aura, {
  semantic: {
    // La couleur primaire suit le rôle. `--accent` est posée par la coquille
    // sur l'élément racine, donc les composants la lisent sans rien savoir
    // du rôle connecté.
    primary: {
      50: 'color-mix(in srgb, var(--accent) 8%, white)',
      100: 'color-mix(in srgb, var(--accent) 16%, white)',
      200: 'color-mix(in srgb, var(--accent) 28%, white)',
      300: 'color-mix(in srgb, var(--accent) 44%, white)',
      400: 'color-mix(in srgb, var(--accent) 68%, white)',
      500: 'var(--accent)',
      600: 'color-mix(in srgb, var(--accent) 88%, black)',
      700: 'color-mix(in srgb, var(--accent) 76%, black)',
      800: 'color-mix(in srgb, var(--accent) 64%, black)',
      900: 'color-mix(in srgb, var(--accent) 52%, black)',
      950: 'color-mix(in srgb, var(--accent) 40%, black)',
    },
    focusRing: {
      width: '2px',
      style: 'solid',
      color: 'var(--accent)',
      offset: '2px',
    },
    colorScheme: {
      light: {
        surface: {
          0: '#ffffff',
          50: '#fbfbfd',
          100: '#f4f5f8',
          200: '#eef0f5',
          300: '#e4e7ee',
          400: '#cdd2dd',
          500: '#a8b0c0',
          600: '#5b6478',
          700: '#3f4759',
          800: '#252c3c',
          900: '#0f1420',
          950: '#080b12',
        },
        content: {
          background: '#ffffff',
          hoverBackground: '#f4f5f8',
          borderColor: '#e4e7ee',
          color: '#0f1420',
          hoverColor: '#0f1420',
        },
        text: {
          color: '#0f1420',
          hoverColor: '#0f1420',
          mutedColor: '#5b6478',
          hoverMutedColor: '#0f1420',
        },
        formField: {
          background: '#ffffff',
          borderColor: '#e4e7ee',
          hoverBorderColor: '#5b6478',
          focusBorderColor: 'var(--accent)',
          color: '#0f1420',
          placeholderColor: '#5b6478',
          paddingX: '0.875rem',
          paddingY: '0.625rem',
          borderRadius: '8px',
        },
        overlay: {
          modal: {
            background: '#ffffff',
            borderColor: '#e4e7ee',
            color: '#0f1420',
            shadow: '0 10px 30px -12px rgba(15, 20, 32, 0.4)',
          },
          popover: {
            background: '#ffffff',
            borderColor: '#e4e7ee',
            shadow: '0 10px 30px -12px rgba(15, 20, 32, 0.28)',
          },
        },
        mask: { background: 'rgba(10, 12, 18, 0.45)' },
      },
    },
  },
})

/** Les options passées à `application.use(PrimeVue, …)`.
 *
 *  `darkModeSelector` est neutralisé : la maquette est claire, et laisser
 *  PrimeVue basculer sur la préférence système ferait apparaître, chez
 *  quelqu'un en mode sombre, une moitié d'écran sombre et l'autre claire.
 */
export const optionsPrimeVue = {
  theme: {
    preset: themeRivDinde,
    options: {
      darkModeSelector: '.jamais-sombre',
      // Les classes utilitaires Tailwind doivent l'emporter sur celles de
      // PrimeVue : sans cette couche, un `!py-2` posé sur un bouton PrimeVue
      // ne s'applique pas.
      cssLayer: { name: 'primevue', order: 'theme, base, primevue, components, utilities' },
    },
  },
  locale: {
    startsWith: 'Commence par',
    contains: 'Contient',
    equals: 'Égal à',
    emptyMessage: 'Aucun résultat',
    emptySearchMessage: 'Aucun résultat',
    emptyFilterMessage: 'Aucun résultat',
    choose: 'Choisir',
    upload: 'Envoyer',
    cancel: 'Annuler',
    clear: 'Effacer',
    apply: 'Appliquer',
    dayNames: ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'],
    dayNamesShort: ['dim', 'lun', 'mar', 'mer', 'jeu', 'ven', 'sam'],
    dayNamesMin: ['D', 'L', 'M', 'M', 'J', 'V', 'S'],
    monthNames: [
      'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
      'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
    ],
    monthNamesShort: [
      'jan', 'fév', 'mar', 'avr', 'mai', 'juin',
      'juil', 'août', 'sep', 'oct', 'nov', 'déc',
    ],
    firstDayOfWeek: 1,
    dateFormat: 'dd/mm/yy',
    weekHeader: 'Sem',
    today: "Aujourd'hui",
  },
}
