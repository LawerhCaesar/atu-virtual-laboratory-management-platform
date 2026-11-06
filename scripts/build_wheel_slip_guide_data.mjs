import fs from 'node:fs';
import {FIELDS} from '../static/js/wheel-slip/model.mjs';
import {HELP,SECTIONS,SIGNALS} from '../static/js/wheel-slip/learning.mjs';
fs.writeFileSync('static/js/wheel-slip/learning-guide.json',JSON.stringify({title:'Wheel-Slip Control Using ABS and TCS',sections:SECTIONS,parameters:[...FIELDS.map(([key,title,unit,def])=>({key,title,unit,default:def,help:HELP[key]})),{title:'ABS enabled',unit:'on/off',default:true,help:HELP.absEnabled},{title:'TCS enabled',unit:'on/off',default:true,help:HELP.tcsEnabled}],signals:SIGNALS,credits:[]},null,2));
