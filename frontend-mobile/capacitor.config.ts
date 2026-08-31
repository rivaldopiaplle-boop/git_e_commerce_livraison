import type { CapacitorConfig } from '@capacitor/cli'

// Capacitor emballe l'application web dans une application installable
// (D-20). Il ne réécrit rien : c'est le MÊME code Vue qui tourne dans le
// navigateur et dans l'application — c'est tout l'intérêt du choix.
const config: CapacitorConfig = {
  appId: 'fr.rivdinde.mobile',
  appName: 'RivDinde',
  webDir: 'dist',
  server: {
    // En développement, l'application installée charge le serveur Vite de la
    // machine plutôt qu'un paquet figé : on garde le rechargement à chaud sur
    // un vrai téléphone. À remplacer par l'IP locale de la machine.
    // url: 'http://192.168.1.10:5174',
    cleartext: true,
  },
  android: {
    // Une application de livraison sert dehors, souvent en plein soleil :
    // le thème clair est le bon défaut.
    backgroundColor: '#f4f5f8',
  },
}

export default config
