import fs from 'node:fs';
import {VEHICLE_FIELDS,SCENARIO_FIELDS} from '../static/js/steering-response/model.mjs';
import {HELP,SECTIONS,SIGNALS} from '../static/js/steering-response/learning.mjs';
fs.writeFileSync('static/js/steering-response/learning-guide.json',JSON.stringify({title:'Vehicle Steering Response',sections:SECTIONS,parameters:[...SCENARIO_FIELDS,...VEHICLE_FIELDS].map(([key,title,unit,def])=>({key,title,unit,default:def,help:HELP[key]})).concat([{title:'Steering profile',unit:'pattern',default:'step',help:HELP.profile}]),signals:SIGNALS},null,2));
