import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
export function createCorner(host){
 const renderer=new T.WebGLRenderer({antialias:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;host.append(renderer.domElement);
 const scene=new T.Scene();scene.background=new T.Color('#15232e');const pm=new T.PMREMGenerator(renderer),room=new RoomEnvironment(),env=pm.fromScene(room,.04);scene.environment=env.texture;room.dispose();pm.dispose();scene.add(new T.HemisphereLight(0xe2f0ff,0x24313a,1.7));const lamp=new T.DirectionalLight(0xfff0df,3.4);lamp.position.set(-3,5,4);scene.add(lamp);
 const camera=new T.PerspectiveCamera(37,1,.05,40),orbit=new OrbitControls(camera,renderer.domElement);orbit.enablePan=false;orbit.minDistance=2;orbit.maxDistance=9;orbit.maxPolarAngle=Math.PI*.49;
 const mat=(color,metalness=.8,roughness=.3)=>new T.MeshStandardMaterial({color,metalness,roughness});const steel=mat('#a8b6be',.95,.27),cast=mat('#74848c',.85,.42),dark=mat('#172027',.2,.7),rubber=mat('#10171b',.02,.9),caliperMat=mat('#424d57',.8,.32),copper=mat('#a46a3a',.8,.3),blue=mat('#42a7cd',.5,.35),amber=mat('#d49e53',.65,.35),teal=mat('#65b7a2',.5,.35);
 const group=(x,y,z,p=scene)=>{const g=new T.Group();g.position.set(x,y,z);p.add(g);return g;};
 const add=(geom,m,x=0,y=0,z=0,p=scene)=>{const o=new T.Mesh(geom,m);o.position.set(x,y,z);p.add(o);return o;};
 const box=(w,h,d,m,x,y,z,p)=>add(new RoundedBoxGeometry(w,h,d,2,Math.min(w,h,d)*.12),m,x,y,z,p);
 const cyl=(r,h,m,x,y,z,p,n=64)=>{const o=add(new T.CylinderGeometry(r,r,h,n),m,x,y,z,p);o.rotation.x=Math.PI/2;return o;};
 const ring=(r,t,m,x,y,z,p)=>add(new T.TorusGeometry(r,t,10,80),m,x,y,z,p);
 const tube=(points,r,m)=>add(new T.TubeGeometry(new T.CatmullRomCurve3(points.map(v=>new T.Vector3(...v))),40,r,8,false),m);
 const wheel=group(-.9,.94,0),fixed=group(-.9,.94,0);const profile=[[.61,-.18],[.75,-.21],[.87,-.14],[.9,0],[.87,.14],[.75,.21],[.61,.18]].map(([r,y])=>new T.Vector2(r,y));const tyre=add(new T.LatheGeometry(profile,96),rubber,0,0,-.17,wheel);tyre.rotation.x=Math.PI/2;
 for(const z of [-.3,-.17,-.04])ring(.895,.004,dark,0,0,z,wheel);
 for(let n=0;n<60;n++){const a=n*Math.PI/30;const tread=box(.04,.022,.14,rubber,Math.cos(a)*.894,Math.sin(a)*.894,-.17,wheel);tread.rotation.z=a;}
 ring(.625,.025,steel,0,0,.04,wheel);ring(.62,.02,steel,0,0,-.36,wheel);
 for(let n=0;n<10;n++){const a=n*Math.PI/5,s=box(.39,.04,.05,steel,Math.cos(a)*.44,Math.sin(a)*.44,.035,wheel);s.rotation.z=a;}
 // Ventilated annular disc, hub bolts and toothed encoder rotate together.
 const shape=new T.Shape();shape.absarc(0,0,.47,0,Math.PI*2,false);const hole=new T.Path();hole.absarc(0,0,.17,0,Math.PI*2,true);shape.holes.push(hole);for(const z of [.29,.37])add(new T.ExtrudeGeometry(shape,{depth:.025,bevelEnabled:false}),steel,0,0,z,wheel);
 for(let n=0;n<36;n++){const a=n*Math.PI/18;const vane=box(.25,.012,.07,cast,Math.cos(a)*.33,Math.sin(a)*.33,.345,wheel);vane.rotation.z=a;}
 for(const r of [.24,.33,.42])ring(r,.0009,cast,0,0,.398,wheel);cyl(.19,.17,cast,0,0,.34,wheel);for(let n=0;n<5;n++){const a=n*Math.PI*2/5;cyl(.025,.09,steel,Math.cos(a)*.12,Math.sin(a)*.12,.46,wheel,6);}
 ring(.24,.022,steel,0,0,-.43,wheel);for(let n=0;n<48;n++){const a=n*Math.PI/24;const tooth=box(.025,.035,.04,steel,Math.cos(a)*.25,Math.sin(a)*.25,-.43,wheel);tooth.rotation.z=a;}
 const sensor=box(.10,.15,.14,blue,-.20,.24,-.43,fixed);cyl(.09,.8,steel,0,0,-.63,fixed);box(.18,.4,.18,cast,0,0,-.4,fixed);
 box(.18,.36,.21,caliperMat,.44,.04,.35,fixed);box(.08,.31,.08,dark,.37,.04,.28,fixed);for(const y of [-.06,.13])cyl(.05,.06,cast,.46,y,.48,fixed);
 const block=box(.64,.37,.38,cast,1.0,1.0,0);box(.67,.16,.42,dark,1,1.29,0);const motor=group(1.55,1,0);cyl(.20,.48,steel,0,0,0,motor);cyl(.155,.05,dark,0,0,.26,motor);const spindle=group(0,0,.30,motor);for(let n=0;n<6;n++){const blade=box(.025,.25,.02,copper,0,0,0,spindle);blade.rotation.z=n*Math.PI/6;}
 for(let n=0;n<6;n++){const x=.78+(n%3)*.20,y=.87+Math.floor(n/3)*.19;cyl(.045,.05,steel,x,y,.23);}
 box(.22,.28,.24,mat('#d7d8c3',.1,.25),.66,1.58,0);box(.13,.04,.14,dark,.66,1.75,0);
 tube([[-.46,1.1,.36],[-.2,1.55,.24],[.15,1.18,.22],[.7,1.0,.24]],.018,dark);
 const pressure=tube([[-.46,1.1,.36],[-.2,1.55,.24],[.15,1.18,.22],[.7,1.0,.24]],.009,amber);
 const feedback=tube([[-1.1,1.18,-.43],[-1.4,1.7,-.5],[-.1,1.9,-.35],[.8,1.40,-.1]],.012,blue);
 const returnLine=tube([[.8,1.0,.27],[1.15,.65,.3],[1.60,.85,.3],[1.55,1.0,.3]],.012,teal);
 const road=add(new T.PlaneGeometry(20,20),mat('#263943',.05,.84));road.rotation.x=-Math.PI/2;road.material.color.set('#0d1820');road.material.envMapIntensity=.15;
 const patch=add(new T.PlaneGeometry(.62,.50),mat('#a3b6ae',.05,.6),-.9,.006,-.17);patch.rotation.x=-Math.PI/2;
 const forceArrow=new T.ArrowHelper(new T.Vector3(1,0,0),new T.Vector3(-.9,.10,.58),.7,0xe6b16b,.14,.08);forceArrow.visible=false;scene.add(forceArrow);
 const roadMarks=group(0,.014,0);for(let i=-5;i<6;i++)box(.55,.008,.025,steel,i*.6,.0,.7,roadMarks);
 const labels=[];for(const[text,point]of [['Wheel-speed sensor',[-1.1,1.18,-.43]],['Disc + fixed caliper',[-.46,.98,.48]],['Hydraulic valve block',[.85,1.5,0]],['Pump motor · cutaway',[1.65,.8,.3]]]){const e=document.createElement('span');e.className='ws-part-label';e.textContent=text;host.append(e);labels.push({e,point:new T.Vector3(...point)});}
 let mode='corner';function draw(){if(host.clientWidth&&host.clientHeight){renderer.render(scene,camera);for(const {e,point}of labels){const p=point.clone().project(camera);e.style.left=Math.max(8,Math.min(host.clientWidth-130,(p.x*.5+.5)*host.clientWidth))+'px';e.style.top=Math.max(8,Math.min(host.clientHeight-30,(-p.y*.5+.5)*host.clientHeight))+'px';e.hidden=p.z>1;}}}
 function focus(view){mode=view;host.dataset.camera=view;const target=view==='modulator'?new T.Vector3(1.08,1.22,0):view==='wheel'?new T.Vector3(-.9,1,0):new T.Vector3(.15,1.0,0);orbit.target.copy(target);camera.position.copy(target).add(view==='modulator'?new T.Vector3(1.3,1.1,2):view==='wheel'?new T.Vector3(1.3,1.1,2.5):new T.Vector3(3,2.3,5));camera.position.sub(target).multiplyScalar(Math.max(1,1.4/camera.aspect)).add(target);orbit.update();draw();}
 function resize(){if(!host.clientWidth||!host.clientHeight)return;renderer.setSize(host.clientWidth,host.clientHeight,false);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();focus(mode);}
 orbit.addEventListener('change',draw);const observer=new ResizeObserver(resize);observer.observe(host);renderer.domElement.setAttribute('role','img');renderer.domElement.setAttribute('aria-label','Representative Genesis-reference wheel corner: ventilated brake disc, caliper, wheel-speed encoder and sensor, ABS hydraulic block and return-pump motor');focus(mode);resize();
 return{focus,update(next,reduce=false){wheel.rotation.z=next&&!reduce?next.wheelAngleRad:0;spindle.rotation.z=next?.pumpIllustration&&!reduce?next.row.timeS*8:0;forceArrow.visible=!!next&&Math.abs(next.row.tyreForceN)>.1;if(next){forceArrow.setDirection(new T.Vector3(Math.sign(next.row.tyreForceN)||1,0,0));forceArrow.setLength(.15+.65*Math.min(1,Math.abs(next.row.tyreForceN)/(Math.max(.05,next.roadMu)*next.vehicleMassKg*9.81/4)),.12,.07);}
 roadMarks.position.x=next&&!reduce?-(next.row.distanceM%.6):0;caliperMat.emissive.set('#9a602a');caliperMat.emissiveIntensity=next?Math.max(0,next.brakeFraction)*.35:0;amber.emissive.set('#d49e53');amber.emissiveIntensity=next?next.brakeFraction*.4:0;teal.emissive.set('#65b7a2');teal.emissiveIntensity=next?.pumpIllustration?.7:0;patch.material.color.set(!next?'#6d818c':next.row.brakeSlip>.2||next.row.driveSlip>.18?'#b17c42':'#549888');host.dataset.valid=String(!!next);host.dataset.mode=next?String(next.mode):'none';host.dataset.pump=String(!!next?.pumpIllustration);host.dataset.wheelAngle=String(wheel.rotation.z);draw();},destroy(){observer.disconnect();orbit.dispose();scene.traverse(o=>{o.geometry?.dispose();});const mats=new Set();scene.traverse(o=>{if(o.material)mats.add(o.material);});mats.forEach(m=>m.dispose());env.dispose();renderer.dispose();renderer.domElement.remove();for(const{e}of labels)e.remove();}};
}
