import fs from 'node:fs';import {createRequire} from 'node:module';import {HELP,LEGEND_HELP,LESSONS,CSV_HELP} from '../static/js/edward/learning.mjs';
const require=createRequire(import.meta.url),E=require('../static/js/edward/Edward_BEV_Virtual_Platform.js');
fs.writeFileSync(new URL('./motor-learning-content.json',import.meta.url),JSON.stringify({help:HELP,legends:LEGEND_HELP,lessons:LESSONS,columns:CSV_HELP,fields:E.FIELD_GROUPS,labels:E.LABELS,defaults:E.DEFAULTS},null,2));
