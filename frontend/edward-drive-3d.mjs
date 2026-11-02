import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
// Detailed generic PMSM e-axle. Angular kinematics come only from the reference sample.
export function createDriveScene(host){
 const renderer=new T.WebGLRenderer({antialias:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.03;renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;host.append(renderer.domElement);
 const scene=new T.Scene();scene.background=new T.Color(0x18222b);scene.fog=new T.Fog(0x18222b,12,27);const pm=new T.PMREMGenerator(renderer),room=new RoomEnvironment(),env=pm.fromScene(room,.04);scene.environment=env.texture;room.dispose();pm.dispose();
 scene.add(new T.HemisphereLight(0xe6f0ff,0x26313b,1.25));const key=new T.DirectionalLight(0xffffff,3.2);key.position.set(1,7,4);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-5,right:5,top:5,bottom:-5});key.shadow.bias=-.0003;scene.add(key);const rim=new T.DirectionalLight(0x9bc4e6,2.6);rim.position.set(-4,3,-4);scene.add(rim);
 const camera=new T.PerspectiveCamera(35,1,.05,45),orbit=new OrbitControls(camera,renderer.domElement);orbit.enablePan=false;orbit.minDistance=1.3;orbit.maxDistance=12;orbit.maxPolarAngle=Math.PI*.49;
 const mat=(color,metalness=.8,roughness=.3)=>new T.MeshStandardMaterial({color,metalness,roughness});const cast=mat(0x89979f,.9,.36),polished=mat(0xc4cbd0,.95,.19),steel=mat(0x67747b,.95,.25),graphite=mat(0x263139,.45,.42),rubber=mat(0x171c20,.03,.82),copper=mat(0xa96032,.88,.29),orange=mat(0xd87822,.2,.47),ceramic=mat(0xebe9de,.08,.5),rotorSteel=mat(0x3e4a50,.9,.24),magnet=mat(0x555b60,.75,.28);
 // Procedural micro-surface maps: cast alloy and rubber, generated locally.
 let seed=94721;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;},roughData=new Uint8Array(128*128*4),normalData=new Uint8Array(128*128*4);for(let i=0;i<128*128;i++){const v=185+Math.floor(random()*70);roughData.set([v,v,v,255],i*4);normalData.set([124+Math.floor(random()*8),124+Math.floor(random()*8),255,255],i*4);}const roughMap=new T.DataTexture(roughData,128,128),normalMap=new T.DataTexture(normalData,128,128);for(const texture of [roughMap,normalMap]){texture.wrapS=texture.wrapT=T.RepeatWrapping;texture.repeat.set(7,7);texture.generateMipmaps=true;texture.minFilter=T.LinearMipmapLinearFilter;texture.magFilter=T.LinearFilter;texture.needsUpdate=true;}cast.roughnessMap=roughMap;cast.normalMap=normalMap;cast.normalScale=new T.Vector2(.12,.12);rubber.roughnessMap=roughMap;
 const add=(g,m,x=0,y=0,z=0,parent=scene)=>{const mesh=new T.Mesh(g,m);mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh);return mesh;};
 const box=(w,h,d,m,x,y,z,p)=>add(new RoundedBoxGeometry(w,h,d,2,Math.min(w,h,d)*.12),m,x,y,z,p);
 const cyl=(r,d,m,x,y,z,p,segments=64)=>{const o=add(new T.CylinderGeometry(r,r,d,segments),m,x,y,z,p);o.rotation.x=Math.PI/2;return o;};
 const ring=(r,t,m,x,y,z,p,arc=Math.PI*2)=>add(new T.TorusGeometry(r,t,10,80,arc),m,x,y,z,p);
 const tube=(pts,m,r=.025)=>add(new T.TubeGeometry(new T.CatmullRomCurve3(pts.map(v=>new T.Vector3(...v))),40,r,10,false),m);
 const group=(x,y,z,p=scene)=>{const g=new T.Group();g.position.set(x,y,z);p.add(g);return g;};
 function bolts(radius,n,z,parent){for(let i=0;i<n;i++){const a=(i+.5)*Math.PI*2/n,x=Math.cos(a)*radius,y=Math.sin(a)*radius;cyl(.037,.035,steel,x,y,z,parent,6);ring(.04,.008,polished,x,y,z+.02,parent);}}
 function gear(radius,teeth,depth,parent){const shape=new T.Shape(),root=radius*.91;for(let i=0;i<teeth*4;i++){const a=i/(teeth*4)*Math.PI*2,r=i%4===1||i%4===2?radius:root;const x=Math.cos(a)*r,y=Math.sin(a)*r;i?shape.lineTo(x,y):shape.moveTo(x,y);}shape.closePath();const hole=new T.Path();hole.absarc(0,0,radius*.28,0,Math.PI*2,true);shape.holes.push(hole);const mesh=add(new T.ExtrudeGeometry(shape,{depth,bevelEnabled:true,bevelSegments:1,steps:1,bevelSize:.007,bevelThickness:.007}),steel,0,0,-depth/2,parent);cyl(radius*.3,depth*1.4,polished,0,0,0,parent);for(let n=0;n<6;n++){const a=n*Math.PI/3;cyl(radius*.07,depth*1.06,graphite,Math.cos(a)*radius*.62,Math.sin(a)*radius*.62,0,parent);}return mesh;}
 const mx=-.72,my=.88,motor=group(mx,my,0),exterior=group(0,0,0,motor),cutShell=group(0,0,0,motor);
 cyl(.64,1.22,cast,0,0,0,exterior);for(let n=0;n<30;n++){const a=n*Math.PI/15,b=box(.035,.07,1.08,cast,Math.cos(a)*.64,Math.sin(a)*.64,0,exterior);b.rotation.z=a-Math.PI/2;}
 for(const z of [-.65,.65]){cyl(.68,.085,cast,0,0,z,exterior);cyl(.29,.11,polished,0,0,z+.018,exterior);bolts(.57,12,z+Math.sign(z)*.06,exterior);}
 const shell=add(new T.CylinderGeometry(.64,.64,1.22,80,1,true,Math.PI*.05,Math.PI*1.1),cast,0,0,0,cutShell);shell.rotation.x=Math.PI/2;
 ring(.61,.037,polished,0,0,-.62,cutShell);ring(.61,.037,polished,0,0,.62,cutShell,Math.PI*1.1);cyl(.62,.065,cast,0,0,-.65,cutShell);bolts(.56,12,-.7,cutShell);
 const stator=group(0,0,0,motor);for(let n=0;n<36;n++){const a=n*Math.PI/18,x=Math.cos(a)*.49,y=Math.sin(a)*.49;const tooth=box(.1,.12,.91,steel,x,y,0,stator);tooth.rotation.z=a;const winding=box(.075,.085,1.03,copper,Math.cos(a)*.535,Math.sin(a)*.535,0,stator);winding.rotation.z=a;}
 for(const z of [-.51,.51])for(let n=0;n<18;n++){const a=n*Math.PI/9,coil=ring(.052,.022,copper,Math.cos(a)*.49,Math.sin(a)*.49,z,stator);coil.scale.y=1.4;}
 const rotor=group(0,0,0,motor);cyl(.348,1.02,rotorSteel,0,0,0,rotor);for(let n=0;n<8;n++){const a=n*Math.PI/4,m=box(.045,.1,.89,magnet,Math.cos(a)*.345,Math.sin(a)*.345,0,rotor);m.rotation.z=a;}
 for(const z of [-.49,.49]){cyl(.353,.026,polished,0,0,z,rotor);bolts(.235,6,z+.025,rotor);}cyl(.082,1.95,polished,0,0,0,rotor);for(const z of [-.72,.72]){ring(.127,.033,steel,0,0,z,motor);ring(.127,.011,polished,0,0,z+.035,motor);}
 cutShell.visible=false;
 // Integrated inverter/DC-link enclosure and realistic HV connectors.
 box(1.36,.26,.96,cast,mx,1.68,0);box(1.28,.055,.9,graphite,mx,1.84,0);for(let n=0;n<8;n++)box(.02,.08,.82,cast,mx-.54+n*.15,1.49,0);
 for(const x of [mx-.55,mx+.55])for(const z of [-.36,.36])cyl(.03,.04,polished,x,1.87,z,scene,6).rotation.x=0;
 for(const z of [-.22,.22]){box(.18,.13,.17,graphite,-1.4,1.67,z);box(.045,.08,.12,orange,-1.51,1.67,z);}
 const pack=group(-2.25,.28,-.15);box(.8,.28,1.5,cast,0,0,0,pack);box(.74,.025,1.44,graphite,0,.155,0,pack);for(let n=0;n<9;n++)box(.74,.022,.018,polished,0,-.08,-.6+n*.15,pack);
 for(const z of [-.22,.22])tube([[-1.84,.35,z],[-1.65,.42,z],[-1.62,1.35,z],[-1.43,1.67,z]],orange,.033);
 for(let n=0;n<3;n++){const z=-.2+n*.2;box(.12,.11,.13,ceramic,-.3,1.58,z);tube([[-.3,1.6,z],[-.08,1.44,z],[-.18,1.15,z],[-.34,1.1,z]],orange,.023);}
 // Two parallel-axis stages and a locked-straight-line differential representation.
 const gearCase=group(.25,.71,0),gearClosed=group(0,0,0,gearCase),gearOpen=group(0,0,0,gearCase);
 box(1.58,1.14,.67,cast,0,0,0,gearClosed);cyl(.57,.78,cast,.44,-.02,0,gearClosed);for(let n=0;n<10;n++){const a=n*Math.PI/5;cyl(.035,.07,steel,Math.cos(a)*.58+.23,Math.sin(a)*.5,.43,gearClosed,6);}
 box(1.58,1.14,.12,cast,0,0,-.39,gearOpen);for(const x of [-.58,.58])for(const y of [-.43,.43])cyl(.035,.07,steel,x,y,-.3,gearOpen,6);gearOpen.visible=false;
 const pinion=group(mx,my,.12);gear(.18,20,.15,pinion);const counter=group(-.15,.71,.12);gear(.42,46,.12,counter);const counterPinion=group(0,0,.17,counter);gear(.15,18,.12,counterPinion);const differential=group(.6,.67,.29);gear(.59,66,.16,differential);cyl(.2,.9,polished,0,0,0,differential);for(let n=0;n<6;n++){const a=n*Math.PI/3;cyl(.025,.05,steel,Math.cos(a)*.4,Math.sin(a)*.4,.13,differential,6);}
 const movingGears=[pinion,counter,differential];movingGears.forEach(g=>g.visible=false);
 const wheels=[],axles=[];
 for(const sign of [-1,1]){
  const z=sign*1.82,axle=group(.6,.67,0);cyl(.048,1.55,polished,0,0,sign*.95,axle);for(const center of [sign*.6,sign*1.42]){cyl(.1,.18,steel,0,0,center,axle);for(let n=0;n<6;n++)ring(.09+(n<3?n:5-n)*.012,.018,rubber,0,0,center+(n-2.5)*.03,axle);ring(.105,.01,polished,0,0,center-.11,axle);}axles.push(axle);
  const wheel=group(.6,.67,z);const profile=[[.42,-.155],[.51,-.16],[.61,-.13],[.65,-.08],[.658,0],[.65,.08],[.61,.13],[.51,.16],[.42,.155]].map(([r,z])=>new T.Vector2(r,z));const tyre=add(new T.LatheGeometry(profile,96),rubber,0,0,0,wheel);tyre.rotation.x=Math.PI/2;
  for(const offset of [-.06,0,.06])ring(.658,.003,graphite,0,0,offset,wheel);const tread=new T.InstancedMesh(new T.BoxGeometry(.033,.008,.21),graphite,80),dummy=new T.Object3D();for(let n=0;n<80;n++){const a=n*Math.PI/40;dummy.position.set(Math.cos(a)*.657,Math.sin(a)*.657,0);dummy.rotation.set(0,0,a+Math.PI/2);dummy.updateMatrix();tread.setMatrixAt(n,dummy.matrix);}wheel.add(tread);
  cyl(.42,.22,graphite,0,0,0,wheel);for(const side of [-1,1]){ring(.412,.017,polished,0,0,side*.12,wheel);for(let n=0;n<5;n++){const a=n*Math.PI*2/5;for(const branch of [-1,1]){const spoke=box(.37,.035,.055,polished,Math.cos(a)*.23,Math.sin(a)*.23,side*.1,wheel);spoke.rotation.z=a+branch*.14;}}}cyl(.115,.3,polished,0,0,0,wheel);bolts(.078,5,sign*.17,wheel);
  const brake=cyl(.31,.025,steel,0,0,-sign*.24,wheel);for(let n=0;n<18;n++){const a=n*Math.PI/9;cyl(.015,.03,graphite,Math.cos(a)*.25,Math.sin(a)*.25,-sign*.255,wheel);}box(.14,.29,.11,graphite,.9,.67,z-sign*.24);wheels.push(wheel);
 }
 // Machined mounting feet and a neutral studio floor give scale without a toy chassis.
 for(const x of [-1.1,.6])for(const z of [-.43,.43]){box(.19,.24,.18,cast,x,.22,z);cyl(.032,.035,steel,x,.35,z,scene,6).rotation.x=0;}
 const floor=add(new T.PlaneGeometry(60,60),mat(0x202b34,.15,.58),0,-.01,0);floor.rotation.x=-Math.PI/2;floor.castShadow=false;floor.receiveShadow=true;
 let visible=true,mode='drive',lastAngle=0;
 const draw=()=>{if(visible&&host.clientWidth&&host.clientHeight)renderer.render(scene,camera);};
 function resize(){if(!host.clientWidth||!host.clientHeight)return;renderer.setSize(host.clientWidth,host.clientHeight,false);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();draw();}
 function focus(view){mode=view;host.dataset.renderMode=mode;renderer.shadowMap.needsUpdate=true;const close=view!=='drive';exterior.visible=!close;cutShell.visible=close;gearClosed.visible=view!=='reduction';gearOpen.visible=view==='reduction';movingGears.forEach(g=>g.visible=view==='reduction');wheels.forEach(w=>w.visible=view==='drive');axles.forEach(w=>w.visible=view!=='motor');if(view==='motor'){orbit.target.set(mx,my,.12);camera.position.set(-2.3,2.05,2.7);}else if(view==='reduction'){orbit.target.set(.15,.77,.23);camera.position.set(1.5,1.8,3.15);}else{orbit.target.set(-.25,.75,0);camera.position.set(4,3.35,5.9);}orbit.update();draw();}
 orbit.addEventListener('change',draw);const observer=new ResizeObserver(resize);observer.observe(host);renderer.domElement.setAttribute('role','img');renderer.domElement.setAttribute('aria-label','Detailed electric axle with cast motor and inverter housings, reduction gears, CV half-shafts, disc brakes and tyres');focus('drive');resize();
 return{update(row,config,reduced){lastAngle=reduced?0:row?.motor_states_4||0;const ratio=config.gear,output=lastAngle/ratio;rotor.rotation.z=lastAngle;pinion.rotation.z=lastAngle;counter.rotation.z=-lastAngle/Math.sqrt(ratio);differential.rotation.z=output;wheels.forEach(w=>w.rotation.z=output);axles.forEach(a=>a.rotation.z=output);host.dataset.renderMotorAngle=String(lastAngle);host.dataset.renderWheelAngle=String(output);host.dataset.renderMode=mode;draw();},focus,setVisible(v){visible=v;if(v)resize();},destroy(){observer.disconnect();orbit.dispose();const materials=new Set();scene.traverse(o=>{o.geometry?.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material])if(m)materials.add(m);});materials.forEach(m=>m.dispose());roughMap.dispose();normalMap.dispose();env.dispose();renderer.dispose();renderer.domElement.remove();}};
}
