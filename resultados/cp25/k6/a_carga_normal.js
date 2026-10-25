import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter } from 'k6/metrics';
import { data, BASE, auth, login, thresholdsFor, STATS } from './common.js';
const created = new Counter('examenes_creados');
const deleted = new Counter('examenes_eliminados');
export const options = {
  vus: Number(__ENV.VUS || 20), duration: __ENV.DUR || '3m',
  thresholds: thresholdsFor(['post', 'get', 'put', 'delete'], 300),
  summaryTrendStats: STATS,
};
export function setup() { return data.accounts.filter((a) => a.role === 'adm').map((a) => login(a.user)); }
export default function (tokens) {
  const t = tokens[(__VU - 1) % tokens.length];
  const p = http.post(`${BASE}/examenes`, JSON.stringify({ tipo_examen_medico_id: 1, paciente_id: 1, diagnosis: 'carga A' }), Object.assign(auth(t), { tags: { op: 'post' } }));
  check(p, { 'POST 201': (r) => r.status === 201 });
  if (p.status !== 201) return;
  created.add(1);
  const id = p.json('id');
  const g = http.get(`${BASE}/examenes/${id}`, Object.assign(auth(t), { tags: { op: 'get' } }));
  check(g, { 'GET 200': (r) => r.status === 200 });
  const u = http.put(`${BASE}/examenes/${id}`, JSON.stringify({ diagnosis: 'carga A editado' }), Object.assign(auth(t), { tags: { op: 'put' } }));
  check(u, { 'PUT 200': (r) => r.status === 200 });
  const d = http.del(`${BASE}/examenes/${id}`, null, Object.assign(auth(t), { tags: { op: 'delete' } }));
  check(d, { 'DELETE 200': (r) => r.status === 200 });
  if (d.status === 200) deleted.add(1);
  sleep(0.5);
}
