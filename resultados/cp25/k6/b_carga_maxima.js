import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter } from 'k6/metrics';
import { data, BASE, auth, login, thresholdsFor, STATS } from './common.js';
const created = new Counter('examenes_creados');
const STAGES = {
  B: [{ duration: '2m', target: 200 }, { duration: '5m', target: 200 }],
  F: [{ duration: '1m', target: 20 }, { duration: '2m', target: 200 }, { duration: '1m', target: 200 }, { duration: '2m', target: 400 }, { duration: '3m', target: 400 }, { duration: '1m', target: 20 }, { duration: '3m', target: 20 }],
};
export const options = {
  scenarios: { carga: { executor: 'ramping-vus', startVUs: 0, stages: STAGES[__ENV.PARTE || 'B'], gracefulRampDown: '30s', gracefulStop: '30s' } },
  thresholds: __ENV.PARTE === 'F' ? { http_req_failed: ['rate<1'] } : thresholdsFor(['login', 'get_paciente', 'get_examen', 'post'], 300),
  summaryTrendStats: STATS,
};
export default function () {
  const acc = data.accounts[(__VU - 1) % data.accounts.length];
  const t = login(acc.user);
  if (!t) { sleep(1); return; }
  const pid = acc.role === 'pac' ? acc.pacienteId : 1;
  const eid = acc.role === 'pac' ? acc.examenId : data.examen_ref;
  check(http.get(`${BASE}/pacientes/${pid}`, Object.assign(auth(t), { tags: { op: 'get_paciente' } })), { 'GET paciente 200': (r) => r.status === 200 });
  check(http.get(`${BASE}/examenes/${eid}`, Object.assign(auth(t), { tags: { op: 'get_examen' } })), { 'GET examen 200': (r) => r.status === 200 });
  if (acc.role === 'med') {
    const p = http.post(`${BASE}/examenes`, JSON.stringify({ tipo_examen_medico_id: 1, paciente_id: 1, diagnosis: 'carga B' }), Object.assign(auth(t), { tags: { op: 'post' } }));
    if (check(p, { 'POST 201': (r) => r.status === 201 })) created.add(1);
  }
  sleep(1);
}
