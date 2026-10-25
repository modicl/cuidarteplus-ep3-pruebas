import http from 'k6/http';
import { check } from 'k6';
import { data, BASE, authOnly, login, STATS } from './common.js';
const pdf = open('/datos/resultado_examen.pdf', 'b');
export const options = {
  vus: 1, iterations: 10,
  thresholds: { 'http_req_duration{op:subida}': ['max<10000'], 'http_req_duration{op:descarga}': ['max<10000'], http_req_failed: ['rate==0'] },
  summaryTrendStats: STATS,
};
export function setup() { return { med: login('qa_medico1', 'Cuidarte#Med2026'), pac: login('paciente', 'Cuidarte#Pac2026') }; }
export default function (d) {
  const up = http.post(`${BASE}/documentos`, { examen_medico_id: String(data.examen_a3), paciente_id: '1', documento: http.file(pdf, 'resultado_examen.pdf', 'application/pdf') }, Object.assign(authOnly(d.med), { tags: { op: 'subida' } }));
  if (!check(up, { 'subida 201': (r) => r.status === 201 })) return;
  const id = up.json('documento.id');
  const dn = http.get(`${BASE}/documentos/${id}`, Object.assign(authOnly(d.pac), { tags: { op: 'descarga' }, responseType: 'binary' }));
  check(dn, { 'descarga 200 y 2 MB': (r) => r.status === 200 && r.body.byteLength === 2097152 });
}
