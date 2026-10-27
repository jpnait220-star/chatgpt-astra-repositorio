import { createHandler } from '../lib/handler.mjs';
import { productionStore } from '../lib/store.mjs';
let store;
try { store = productionStore(); } catch { store = null; }
export default createHandler(store);
