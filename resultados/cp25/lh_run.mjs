// Uso: node lh_run.mjs <url> <puerto> <repeticiones> <salida.json> <conservar_sesion 0|1>
import fs from 'fs';
import { createRequire } from 'module';
const require = createRequire('C:/Users/Villa/qa-lighthouse/');
const lighthouse = (await import('file:///C:/Users/Villa/qa-lighthouse/node_modules/lighthouse/core/index.js')).default;
const [url, port, reps, out, keep] = process.argv.slice(2);
const flags = {
  port: Number(port), output: 'json', logLevel: 'error', onlyCategories: ['performance'],
  formFactor: 'mobile',
  screenEmulation: { mobile: true, width: 412, height: 823, deviceScaleFactor: 1.75, disabled: false },
  throttlingMethod: 'devtools',
  throttling: { rttMs: 150, throughputKbps: 1638.4, requestLatencyMs: 562.5, downloadThroughputKbps: 1474.56, uploadThroughputKbps: 675, cpuSlowdownMultiplier: 4 },
  disableStorageReset: keep === '1',
};
const results = [];
for (let i = 1; i <= Number(reps); i++) {
  const r = await lighthouse(url, flags);
  const lhr = r.lhr;
  const m = lhr.audits['metrics'].details.items[0];
  results.push({ rep: i, finalUrl: lhr.finalDisplayedUrl || lhr.finalUrl, load_ms: m.observedLoad, lcp_ms: lhr.audits['largest-contentful-paint'].numericValue, fcp_ms: lhr.audits['first-contentful-paint'].numericValue, perf_score: lhr.categories.performance.score, runWarnings: lhr.runWarnings });
  console.log(`rep ${i}: finalUrl=${results.at(-1).finalUrl} load=${Math.round(m.observedLoad)} ms LCP=${Math.round(results.at(-1).lcp_ms)} ms FCP=${Math.round(results.at(-1).fcp_ms)} ms score=${results.at(-1).perf_score}`);
}
fs.writeFileSync(out, JSON.stringify({ url, lighthouse: lhr_version(), flags, results }, null, 1));
function lhr_version() { return JSON.parse(fs.readFileSync('C:/Users/Villa/qa-lighthouse/node_modules/lighthouse/package.json', 'utf8')).version; }
