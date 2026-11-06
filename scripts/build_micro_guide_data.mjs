import fs from 'node:fs';
import {FIELDS} from '../static/js/micro-hybrid/model.mjs';
import {HELP,SECTIONS,SIGNALS} from '../static/js/micro-hybrid/learning.mjs';
fs.writeFileSync('static/js/micro-hybrid/learning-guide.json',JSON.stringify({title:'12 V Micro-Hybrid Stop-Start',sections:SECTIONS,parameters:FIELDS.map(([key,title,unit,def])=>({key,title,unit,default:def,help:HELP[key]})),signals:SIGNALS,credits:[['Genesis GV70 12.3-inch cluster','Damian B Oh','https://commons.wikimedia.org/wiki/File:Genesis_GV70_JK1_SDS_I_Slate_Gray_Velvet_Burgundy_Two_Tone_(6).jpg','CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0/']]},null,2));
