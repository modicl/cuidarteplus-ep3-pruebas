import http from 'k6/http';
export const data = JSON.parse(open('/work/perf_data.json'));
export const BASE = __ENV.BASE || 'http://cuidarteplus-backend-ev:4000';
export const JSONH = { 'Content-Type': 'application/json' };
export function login(user, pass) {
  const r = http.post(`${BASE}/autenticacion/login`, JSON.stringify({ nombre_usuario: user, password: pass || data.password }), { headers: JSONH, tags: { op: 'login' } });
  return r.status === 200 ? r.json('token') : null;
}
export const auth = (t) => ({ headers: Object.assign({ Authorization: 'Bearer ' + t }, JSONH) });
export const authOnly = (t) => ({ headers: { Authorization: 'Bearer ' + t } });
export function thresholdsFor(ops, limit) {
  const th = { http_req_failed: ['rate==0'] };
  ops.forEach((o) => { th[`http_req_duration{op:${o}}`] = [`p(95)<${limit}`]; });
  return th;
}
export const STATS = ['avg', 'med', 'p(90)', 'p(95)', 'max'];
