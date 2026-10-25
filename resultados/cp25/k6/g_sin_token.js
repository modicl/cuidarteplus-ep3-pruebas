import http from 'k6/http';
import { check } from 'k6';
import { BASE, STATS } from './common.js';
export const options = {
  vus: 1, iterations: 20,
  thresholds: { 'http_req_duration{op:sin_token}': ['p(95)<300', 'max<300'] },
  summaryTrendStats: STATS,
};
export default function () {
  const r = http.get(`${BASE}/pacientes`, { tags: { op: 'sin_token' }, responseCallback: http.expectedStatuses(401) });
  check(r, { '401': (x) => x.status === 401 });
}
