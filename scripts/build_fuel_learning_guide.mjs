import fs from 'node:fs';
import {FIELDS} from '../static/js/fuel-delivery/model.mjs';
import {INPUT_HELP,OUTPUT_HELP,LESSONS} from '../static/js/fuel-delivery/learning.mjs';
fs.writeFileSync(new URL('./fuel-learning-content.json',import.meta.url),JSON.stringify({fields:FIELDS,help:INPUT_HELP,outputs:OUTPUT_HELP,lessons:LESSONS},null,2));
