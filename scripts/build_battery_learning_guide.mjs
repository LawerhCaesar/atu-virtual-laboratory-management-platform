import fs from 'node:fs';import {HELP,CHANNELS,LESSONS} from '../static/js/battery-energy/learning.mjs';import {defaults} from '../static/js/battery-energy/controller.mjs';
fs.writeFileSync(new URL('./battery-learning-content.json',import.meta.url),JSON.stringify({help:HELP,channels:CHANNELS,lessons:LESSONS,defaults:defaults()},null,2));
