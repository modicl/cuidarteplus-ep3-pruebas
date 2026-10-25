import http from 'k6/http';
import { check } from 'k6';
import { data, BASE, auth, login, STATS } from './common.js';
export const options = {
  scenarios: {
    medico: { executor: 'shared-iterations', vus: 1, iterations: 50, exec: 'medico', startTime: '0s' },
    paciente: { executor: 'shared-iterations', vus: 1, iterations: 50, exec: 'paciente', startTime: '30s' },
  },
  thresholds: {
    'http_req_duration{op:vol_medico}': ['p(95)<300'],
    'http_req_duration{op:vol_paciente}': ['p(95)<300'],
    http_req_failed: ['rate==0'],
    'checks{check:200 examenes}': ['rate==1'],
  },
  summaryTrendStats: STATS,
};
export function setup() { return { med: login('qa_perf_med01'), pac: login('qa_perf_pac01') }; }
function go(t, op) {
  const r = http.get(`${BASE}/examenes/paciente/${data.paciente200}`, Object.assign(auth(t), { tags: { op: op } }));
  check(r, { '200 examenes': (x) => x.status === 200 && x.json().length === 200 }, { check: '200 examenes' });
}
export function medico(d) { go(d.med, 'vol_medico'); }
export function paciente(d) { go(d.pac, 'vol_paciente'); }
