<script setup lang="ts">
// La facture imprimable — D-78.
//
// Elle s'imprime par le navigateur, avec `window.print()` et une feuille de
// style dediee. Aucune bibliotheque de PDF, aucun travail serveur : le
// navigateur propose lui-meme « Enregistrer au format PDF », et le resultat
// suit la langue et le format de papier de la personne qui imprime.
//
// La regle d'impression est en une phrase : **tout ce qui sert a naviguer
// disparait.** Une facture imprimee avec un bouton « Imprimer » dessus est le
// genre de detail qui trahit un travail bacle.
import { AlertTriangle, ArrowLeft, Printer } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { EchecApi } from '../../api/client'
import { paiements, type Facture } from '../../api/paiements'
import Squelette from '../../composants/Squelette.vue'

const route = useRoute()
const facture = ref<Facture | null>(null)
const chargement = ref(true)
const erreur = ref('')

onMounted(async () => {
  try {
    facture.value = await paiements.facture(Number(route.params.id))
  } catch (souci) {
    erreur.value = souci instanceof EchecApi ? souci.erreur.message : 'Facture introuvable.'
  } finally {
    chargement.value = false
  }
})

const euros = (centimes: number | null) =>
  ((centimes ?? 0) / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

/** Le navigateur sait deja imprimer et enregistrer en PDF : on ne refait pas son travail. */
const imprimer = () => window.print()

const jour = (valeur: string) =>
  new Date(valeur).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'long', year: 'numeric',
  })
</script>

<template>
  <div class="mx-auto max-w-[720px] animate-[apparition_0.2s_ease-out]">
    <div class="sans-impression flex items-center justify-between gap-3">
      <RouterLink :to="{ name: 'mes-commandes' }" class="bouton-neutre">
        <ArrowLeft :size="15" />
        Mes commandes
      </RouterLink>
      <button type="button" class="bouton-accent" :disabled="!facture" @click="imprimer">
        <Printer :size="15" />
        Imprimer
      </button>
    </div>

    <div v-if="chargement" class="mt-4"><Squelette hauteur="380px" /></div>

    <p v-else-if="erreur" class="bandeau bandeau-erreur mt-4">
      <AlertTriangle :size="15" class="mt-px shrink-0" />
      {{ erreur }}
    </p>

    <article v-else-if="facture" class="carte mt-4 p-8 feuille">
      <header class="flex items-start justify-between gap-6 border-b border-trait pb-5">
        <div>
          <b class="text-[19px] tracking-tight">RivDinde</b>
          <p class="mt-1 text-[11.5px] text-encre-douce">
            Place de marche et livraison<br />Lyon, France
          </p>
        </div>
        <div class="text-right">
          <b class="text-[15px]">Facture {{ facture.numero_facture ?? '—' }}</b>
          <p class="mt-1 text-[11.5px] text-encre-douce">
            Commande {{ facture.numero_commande }}<br />
            {{ jour(facture.date) }}
          </p>
        </div>
      </header>

      <p class="mt-5 text-[12px] text-encre-douce">
        <span class="etiquette">Livree a</span><br />
        {{ facture.adresse }}
      </p>

      <table class="mt-5 w-full text-[12.5px]">
        <thead>
          <tr class="border-b border-trait text-left text-[11px] text-encre-douce">
            <th class="pb-2 font-semibold">Article</th>
            <th class="pb-2 font-semibold">Boutique</th>
            <th class="pb-2 text-right font-semibold">Qte</th>
            <th class="pb-2 text-right font-semibold">Prix</th>
            <th class="pb-2 text-right font-semibold">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(ligne, index) in facture.lignes"
            :key="index"
            class="border-b border-trait-doux"
          >
            <td class="py-2">{{ ligne.nom }}</td>
            <td class="py-2 text-encre-douce">{{ ligne.boutique }}</td>
            <td class="py-2 text-right">{{ ligne.quantite }}</td>
            <td class="py-2 text-right">{{ euros(ligne.prix_unitaire_centimes) }}</td>
            <td class="py-2 text-right">{{ euros(ligne.sous_total_centimes) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="mt-5 flex justify-end">
        <dl class="w-[260px] text-[12.5px]">
          <div class="flex justify-between py-1">
            <dt class="text-encre-douce">Articles</dt>
            <dd>{{ euros(facture.montant_produits_centimes) }}</dd>
          </div>
          <div class="flex justify-between py-1">
            <dt class="text-encre-douce">Livraison</dt>
            <dd>
              {{ facture.montant_livraison_centimes
                ? euros(facture.montant_livraison_centimes) : 'offerte' }}
            </dd>
          </div>
          <div class="flex justify-between py-1">
            <dt class="text-encre-douce">Dont TVA {{ Math.round(facture.taux_tva * 100) }} %</dt>
            <dd>
              {{ euros(facture.montant_total_centimes - (facture.montant_ht_centimes ?? 0)) }}
            </dd>
          </div>
          <div class="mt-1 flex justify-between border-t border-trait pt-2 text-[15px]">
            <dt><b>Total TTC</b></dt>
            <dd><b>{{ euros(facture.montant_total_centimes) }}</b></dd>
          </div>
        </dl>
      </div>

      <p class="mt-6 border-t border-trait pt-4 text-[10.5px] text-encre-douce">
        Document emis par RivDinde pour le compte des vendeurs listes ci-dessus.
        Paiement en mode simulation : aucun montant n&rsquo;a ete debite.
      </p>
    </article>
  </div>
</template>
