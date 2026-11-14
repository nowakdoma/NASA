// Validates web/public/data/* against ../contracts/*.schema.json (JSON Schema 2020-12).
// Semantic cross-file checks live in `python -m engine.validate`.
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import Ajv2020 from 'ajv/dist/2020.js';

const here = dirname(fileURLToPath(import.meta.url));
const contracts = resolve(here, '../../contracts');
const data = resolve(here, '../public/data');
const read = (p) => JSON.parse(readFileSync(p, 'utf8'));

const ajv = new Ajv2020({ allErrors: true, strict: false });
let failed = false;
for (const [file, schema] of [
  ['fields.geojson', 'fields.schema.json'],
  ['strategies.json', 'strategies.schema.json'],
]) {
  const validate = ajv.compile(read(resolve(contracts, schema)));
  if (validate(read(resolve(data, file)))) {
    console.log(`OK   public/data/${file}`);
  } else {
    failed = true;
    console.log(`FAIL public/data/${file}`);
    for (const e of validate.errors.slice(0, 20)) console.log(`  - ${e.instancePath} ${e.message}`);
  }
}
process.exit(failed ? 1 : 0);
