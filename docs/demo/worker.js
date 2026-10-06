// Module Web Worker (Pyodide 314 does not support classic workers): runs the repository's Python (pymoo NSGA-II / SPEA2) inside Pyodide so the page stays responsive.
// Protocol (worker -> page): {type:'status', text}, {type:'ready'}, {type:'progress', gen, total},
//                            {type:'result', json, seconds}, {type:'error', message}
// Protocol (page -> worker): {type:'run', user, algo, seed, popSize, nGen}

const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs';

let py = null;
let totalGen = 50;

const send = (msg) => self.postMessage(msg);

// pymoo's verbose=True prints one table row per generation ("    22 |  2200 | ..."); that is the progress signal.
function onStdout(line) {
  const m = /^\s*(\d+)\s*\|\s*\d+\s*\|/.exec(line);
  if (m) send({ type: 'progress', gen: Number(m[1]), total: totalGen });
}

async function init() {
  send({ type: 'status', text: 'Loading the Python runtime…' });
  py = await loadPyodide({ indexURL: PYODIDE_URL, stdout: onStdout, stderr: () => {} });
  send({ type: 'status', text: 'Loading numpy and scipy…' });
  await py.loadPackage(['numpy', 'scipy']);
  send({ type: 'status', text: 'Unpacking pymoo and the project code…' });
  const buf = await (await fetch('pybundle.zip')).arrayBuffer();
  py.unpackArchive(buf, 'zip', { extractDir: '/app' });
  py.runPython(`
import sys
sys.path.insert(0, '/app')
from pymoo.config import Config
Config.warnings['not_compiled'] = False   # silence pymoo's "no compiled modules" notice; results are identical
import runner
from src.database import get_user_dri
get_user_dri(1)                            # builds the SQLite database from data/*.csv on first use
`);
  send({ type: 'ready' });
}

function run({ user, algo, seed, popSize, nGen }) {
  totalGen = nGen;
  const t0 = performance.now();
  py.globals.set('_args', py.toPy([user, algo, seed, popSize, nGen]));
  const json = py.runPython('runner.run(*_args)');
  send({ type: 'result', json, seconds: (performance.now() - t0) / 1000 });
}

self.onmessage = (e) => {
  if (e.data.type !== 'run') return;
  try {
    run(e.data);
  } catch (err) {
    send({ type: 'error', message: String(err && err.message ? err.message : err) });
  }
};

init().catch((err) => send({ type: 'error', fatal: true, message: String(err && err.message ? err.message : err) }));
