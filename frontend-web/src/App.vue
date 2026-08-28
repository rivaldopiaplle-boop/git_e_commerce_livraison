<script setup lang="ts">
import { onMounted, ref } from 'vue'

import LogoColibri from './composants/LogoColibri.vue'

// Tranche 0 : cet ecran ne fait qu'une chose, mais il la fait vraiment — il
// appelle l'API. Tant qu'il repond, toute la chaine est branchee : navigateur,
// Vite, CORS, Django, Postgres. C'est le test de sortie de la tranche.
type Sante = {
  statut: string
  version: string
  base_de_donnees: string
  environnement: string
}

const etat = ref<'chargement' | 'ok' | 'erreur'>('chargement')
const sante = ref<Sante | null>(null)
const message = ref('')

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

onMounted(async () => {
  try {
    const reponse = await fetch(`${API}/sante`)
    if (!reponse.ok) throw new Error(`L'API a repondu ${reponse.status}`)
    sante.value = await reponse.json()
    etat.value = 'ok'
  } catch (erreur) {
    // On dit ce qui s'est passe ET ce qu'on peut faire — jamais un code brut.
    message.value =
      erreur instanceof TypeError
        ? "L'API ne repond pas. Est-elle demarree ? Lance `python demarrer.py` a la racine."
        : String(erreur)
    etat.value = 'erreur'
  }
})
</script>

<template>
  <main>
    <LogoColibri :taille="96" />
    <h1>Colibri</h1>
    <p class="signature">commander, livrer, suivre</p>

    <div class="carte" :class="etat">
      <template v-if="etat === 'chargement'">
        <span class="pastille attente" />
        <span>Contact de l'API…</span>
      </template>

      <template v-else-if="etat === 'ok'">
        <span class="pastille ok" />
        <div>
          <b>API en ligne</b>
          <small>
            version {{ sante?.version }} · base {{ sante?.base_de_donnees }} ·
            {{ sante?.environnement }}
          </small>
        </div>
      </template>

      <template v-else>
        <span class="pastille erreur" />
        <div>
          <b>API injoignable</b>
          <small>{{ message }}</small>
        </div>
      </template>
    </div>

    <p class="pied">Tranche 0 — le squelette qui tourne.</p>
  </main>
</template>

<style scoped>
main {
  text-align: center;
  padding: 40px 24px;
}
h1 {
  margin: 18px 0 2px;
  font-size: 40px;
  letter-spacing: -0.03em;
  font-weight: 600;
}
.signature {
  margin: 0 0 32px;
  color: var(--marque-claire);
  font-size: 14px;
  letter-spacing: 0.08em;
}
.carte {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  text-align: left;
  padding: 16px 24px;
  border-radius: 14px;
  border: 1px solid #1e293b;
  background: rgba(15, 23, 42, 0.6);
  min-width: 340px;
}
.carte.ok { border-color: #0f766e; }
.carte.erreur { border-color: #7f1d1d; }
.carte b { display: block; font-size: 15px; }
.carte small { color: var(--sub); font-size: 12.5px; }
.pastille {
  width: 10px; height: 10px; border-radius: 50%; flex: none;
}
.pastille.ok { background: #14b8a6; box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.18); }
.pastille.erreur { background: #dc2626; box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.18); }
.pastille.attente { background: #f59e0b; animation: battement 1.1s ease-in-out infinite; }
@keyframes battement {
  50% { opacity: 0.25; }
}
.pied {
  margin-top: 36px;
  color: #475569;
  font-size: 12px;
}
</style>
