import * as THREE from 'three';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

// Generic teaching geometry; the solver remains the sole source of numerical results.
export function createFuelScene(container, baseline) {
  for (const key of ['length_m','width_m','height_m','wheelbase_m','wheel_radius_m','front_track_m','rear_track_m','front_overhang_m','rear_overhang_m']) {
    if (!Number.isFinite(baseline?.[key]) || baseline[key] <= 0) throw new Error('Vehicle baseline dimensions are unavailable');
  }
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, powerPreference: 'low-power'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
  container.append(renderer.domElement);
  const scene=new THREE.Scene();scene.background=new THREE.Color(0x102133);const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();const environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;room.dispose();pmrem.dispose();
  const camera = new THREE.PerspectiveCamera(38, 1, .1, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false; controls.enablePan = false; controls.minDistance = 3; controls.maxDistance = 18;
  controls.maxPolarAngle = Math.PI * .7; controls.target.set(0, .5, 0);
  let mode = 'vehicle';
  const home = () => { if(mode==='vehicle') {camera.position.set(5.2, 2.9, 6.0); controls.target.set(0, .72, 0);} else {camera.position.set(6.5, 3.8, 8.1); controls.target.set(0, .5, 0);} controls.update(); draw(); };
  scene.add(new THREE.HemisphereLight(0xd8e9ff, 0x263142, 2.2));
  const key = new THREE.DirectionalLight(0xffffff, 3.2); key.position.set(2, 8, 7); scene.add(key);key.castShadow=true;key.shadow.mapSize.set(1024,1024);Object.assign(key.shadow.camera,{left:-6,right:6,top:5,bottom:-5,near:.5,far:25});key.shadow.bias=-.001;key.shadow.normalBias=.03;
  const rim = new THREE.DirectionalLight(0x80b7ff, 2); rim.position.set(-6, 3, -5); scene.add(rim);
  const metal = new THREE.MeshStandardMaterial({color: 0x9ba9b6, metalness: .8, roughness: .31});
  const dark = new THREE.MeshStandardMaterial({color: 0x273b51, metalness: .65, roughness: .4});
  const rubber = new THREE.MeshStandardMaterial({color: 0x111c2a, metalness: .1, roughness: .68});
  const gold = new THREE.MeshStandardMaterial({color: 0xe6b85d, metalness: .55, roughness: .35, emissive: 0x452000, emissiveIntensity: .35});
  const glass = new THREE.MeshStandardMaterial({color: 0x779cb7, metalness: .15, roughness: .15, transparent: true, opacity: .24, depthWrite: false, side: THREE.DoubleSide});
  const sprayMaterial = new THREE.MeshBasicMaterial({color: 0xf2bb5f, transparent: true, opacity: .2, depthWrite: false, side: THREE.DoubleSide});
  const detailGroup = new THREE.Group(), vehicleGroup = new THREE.Group(); scene.add(detailGroup, vehicleGroup);
  const add = (geometry, material, x, y, z, parent = detailGroup) => { const mesh = new THREE.Mesh(geometry, material); mesh.position.set(x, y, z); parent.add(mesh);mesh.castShadow=!material.transparent;mesh.receiveShadow=true;return mesh; };
  const box = (w,h,d,mat,x,y,z,parent) => add(new THREE.BoxGeometry(w,h,d),mat,x,y,z,parent);
  const cylinder = (r1,r2,h,mat,x,y,z,parent) => add(new THREE.CylinderGeometry(r1,r2,h,32),mat,x,y,z,parent);
  const pipe = (points, radius, mat) => { const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p))); return add(new THREE.TubeGeometry(curve, 64, radius, 12, false),mat,0,0,0); };
  const copper=new THREE.MeshStandardMaterial({color:0xbc7349,metalness:.85,roughness:.25});
  const paint=new THREE.MeshPhysicalMaterial({color:0x456e85,metalness:.65,roughness:.25,clearcoat:1});
  const led=new THREE.MeshStandardMaterial({color:0xdaeeff,emissive:0x93bcda,emissiveIntensity:1.7});
  const redLED=new THREE.MeshStandardMaterial({color:0xba2033,emissive:0x680716,emissiveIntensity:1.3});
  const torus=(r,t,m,x,y,z,parent=detailGroup)=>add(new THREE.TorusGeometry(r,t,10,48),m,x,y,z,parent);
  const tags=[];
  function tag(text,x,y,z,parent=detailGroup){const c=document.createElement('canvas');c.width=512;c.height=96;const ctx=c.getContext('2d');ctx.fillStyle='#173247';ctx.fillRect(0,0,512,96);ctx.strokeStyle='#749bb2';ctx.lineWidth=3;ctx.strokeRect(2,2,508,92);ctx.fillStyle='#eef6ff';ctx.font='500 30px system-ui';ctx.textAlign='center';ctx.fillText(text,256,59);const texture=new THREE.CanvasTexture(c);texture.colorSpace=THREE.SRGBColorSpace;const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,transparent:true,depthTest:false}));sprite.position.set(x,y,z);sprite.scale.set(1.6,.3,1);parent.add(sprite);tags.push(sprite);}
  const base = box(8.2,.18,3.8,dark,0,-1.43,0); base.material = new THREE.MeshStandardMaterial({color:0x172a40,metalness:.6,roughness:.5});
  // Source tank and feed tube are symbolic; no tank level or pump dynamics are calculated.
  box(1.45,1.35,1.25,dark,-3,-.35,0); box(1.22,.75,1.27,gold,-3,-.62,0); box(1.1,.95,1.3,glass,-3,-.35,0);
  cylinder(.17,.17,.2,metal,-3,.42,0);
  for (const x of [-3.53,-2.47]) for (const z of [-.5,.5]) cylinder(.08,.08,.05,metal,x,.34,z);
  box(.95,.10,.06,metal,-3,.36,.66); box(.95,.10,.06,metal,-3,-.98,.66);
  pipe([[-2.82,.5,0],[-2.8,1.25,0],[-2.1,1.55,0],[-1.3,1.55,0]],.10,rubber);
  pipe([[-2.82,.5,0],[-2.8,1.25,0],[-2.1,1.55,0],[-1.3,1.55,0]],.035,gold);
  // The rail supplies a representative single injector and cylinder cutaway.
  const rail = cylinder(.22,.22,3.1,metal,.15,1.55,0); rail.rotation.z = Math.PI/2;
  for(const x of [-1.44,1.74]){const nut=add(new THREE.CylinderGeometry(.28,.28,.17,6),metal,x,1.55,0);nut.rotation.z=Math.PI/2;for(let k=0;k<5;k++){const ring=torus(.23,.012,dark,x+(k-2)*.028,1.55,0);ring.rotation.y=Math.PI/2;}}
  cylinder(.09,.09,.2,dark,-.55,1.85,0);box(.23,.17,.25,rubber,-.55,2,0);
  const railCore = cylinder(.045,.045,3.15,gold,.15,1.55,0); railCore.rotation.z = Math.PI/2;
  for (const x of [-.9,.1,1.1]) { const cap=cylinder(.28,.28,.12,dark,x,1.55,0); cap.rotation.z=Math.PI/2; }
  for (const x of [-.75,1.45]) { cylinder(.09,.09,.32,metal,x,1.24,0); box(.27,.10,.45,dark,x,1.02,0); }
  const injector = new THREE.Group(); injector.position.set(.55,0,0); detailGroup.add(injector);
  cylinder(.19,.23,.5,glass,0,1.18,0,injector); cylinder(.14,.19,.63,glass,0,.67,0,injector);
  cylinder(.11,.14,.22,gold,0,.25,0,injector); const needle=cylinder(.035,.035,.52,gold,0,.55,0,injector);
  add(new THREE.CylinderGeometry(.245,.245,.7,48,1,true,.6,Math.PI*1.35),metal,0,.83,0,injector);
  for(let k=0;k<14;k++){const ring=torus(.16,.016,copper,0,.9+k*.017,0,injector);ring.rotation.x=Math.PI/2;}
  const springPoints=Array.from({length:121},(_,i)=>new THREE.Vector3(.075*Math.cos(i/120*Math.PI*14),.43+i/120*.28,.075*Math.sin(i/120*Math.PI*14)));
  add(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(springPoints),120,.012,6,false),metal,0,0,0,injector);
  for(const y of [.48,.78,1.05]) cylinder(.20,.20,.035,rubber,0,y,0,injector);
  box(.36,.19,.35,rubber,0,1.22,.32,injector);
  const chamber = new THREE.Group(); chamber.position.set(.55,0,0); detailGroup.add(chamber);
  cylinder(.72,.72,1.75,glass,0,-.57,0,chamber);
  const piston=cylinder(.65,.65,.22,metal,0,-1.1,0,chamber);
  cylinder(.73,.73,.12,dark,0,.32,0,chamber); cylinder(.73,.73,.12,dark,0,-1.36,0,chamber);
  for(const angle of [0,Math.PI/2,Math.PI,3*Math.PI/2]) {const x=.56*Math.cos(angle),z=.56*Math.sin(angle);cylinder(.07,.07,.08,metal,x,.42,z,chamber);}
  for(const y of [-1.28,-1.05,-.82]) { const ring=cylinder(.68,.68,.025,dark,0,y,0,chamber); ring.material=metal; }
  const spray = add(new THREE.ConeGeometry(.48,1.05,32,1,true),sprayMaterial,0,-.3,0,chamber);
  const mist=Array.from({length:32},()=>add(new THREE.SphereGeometry(.018,6,6),gold,0,0,0,chamber));
  tag('01  FUEL SOURCE',-3,1.9,.1);tag('02  FUEL RAIL',.1,2.4,0);tag('03  INJECTOR',1.8,.85,.1);tag('04  CHAMBER',1.7,-.8,.1);
  // Small droplets move along the feed line at a deliberately slowed teaching pace.
  const droplets = Array.from({length: 6}, () => add(new THREE.SphereGeometry(.075,12,12),gold,0,0,0));
  const path = new THREE.CatmullRomCurve3([[-2.82,.5,0],[-2.8,1.25,0],[-2.1,1.55,0],[-1.3,1.55,0],[.5,1.55,0]].map(p=>new THREE.Vector3(...p)));
  // Dimensions are project baselines in metres. Silhouette and internal layout are generic.
  const L=baseline.length_m, W=baseline.width_m, H=baseline.height_m, R=baseline.wheel_radius_m, WB=baseline.wheelbase_m;
  const body = new THREE.Shape();
  body.moveTo(-L/2,.39); body.lineTo(-L/2+.12,.8); body.quadraticCurveTo(-L*.44,1.08,-L*.29,1.16);
  body.quadraticCurveTo(-L*.18,H,L*.01,H); body.lineTo(L*.20,H); body.quadraticCurveTo(L*.30,H-.03,L*.36,1.17);
  body.quadraticCurveTo(L*.46,1.04,L/2-.05,.92); body.lineTo(L/2,.4);const mid=(baseline.rear_overhang_m-baseline.front_overhang_m)/2,arch=R*1.12;for(const axle of [mid+WB/2,mid-WB/2]){body.lineTo(axle+arch,.4);body.absarc(axle,.4,arch,0,Math.PI,false);}body.lineTo(-L/2,.4);body.closePath();
  const bodyMaterial=new THREE.MeshStandardMaterial({color:0x6c9ab8,metalness:.42,roughness:.3,transparent:true,opacity:.34,depthWrite:false,side:THREE.DoubleSide});
  const vehicleBody=add(new THREE.ExtrudeGeometry(body,{depth:W,bevelEnabled:false,curveSegments:20}),bodyMaterial,0,0,-W/2,vehicleGroup);
  const outline=new THREE.LineSegments(new THREE.EdgesGeometry(vehicleBody.geometry,25),new THREE.LineBasicMaterial({color:0xabcde0,transparent:true,opacity:.42})); outline.position.z=-W/2;vehicleGroup.add(outline);
  box(.12,.4,W*.76,dark,L/2-.04,.68,0,vehicleGroup);
  for(let n=0;n<10;n++)box(.14,.015,W*.46,metal,L/2+.015,.53+n*.029,0,vehicleGroup);
  for(const side of [-1,1]){for(const y of [.92,.99])box(.06,.024,W*.19,led,L/2+.02,y,side*W*.34,vehicleGroup);box(.06,.1,W*.19,redLED,-L/2,.86,side*W*.33,vehicleGroup);box(.18,.11,.13,paint,L*.18,1.2,side*(W/2+.06),vehicleGroup);box(L*.77,.07,.06,dark,0,.43,side*W*.48,vehicleGroup);box(.43,.03,.028,metal,0,1.05,side*(W/2+.01),vehicleGroup);box(L*.3,.025,.025,metal,0,H-.06,side*W*.35,vehicleGroup);for(const x of [mid-WB/2,mid+WB/2])add(new THREE.TorusGeometry(R*1.12,.028,10,48,Math.PI),dark,x,.4,side*W*.505,vehicleGroup);}
  const frame=box(L*.87,.12,W*.72,dark,0,.48,0,vehicleGroup);
  const windowMat=new THREE.MeshStandardMaterial({color:0x92bed5,metalness:.2,roughness:.25,transparent:true,opacity:.28,depthWrite:false,side:THREE.DoubleSide});
  const windowShape=new THREE.Shape(); windowShape.moveTo(-L*.27,1.15);windowShape.quadraticCurveTo(-L*.17,H-.08,-L*.02,H-.1);windowShape.lineTo(L*.17,H-.1);windowShape.quadraticCurveTo(L*.25,H-.1,L*.30,1.15);windowShape.closePath();
  for(const z of [-W/2-.005,W/2+.005]) add(new THREE.ShapeGeometry(windowShape,20),windowMat,0,0,z,vehicleGroup);
  const wheelMat=new THREE.MeshStandardMaterial({color:0x151d27,roughness:.82}), hubMat=new THREE.MeshStandardMaterial({color:0xa6b3be,metalness:.8,roughness:.28});
  const axleMidpoint=(baseline.rear_overhang_m-baseline.front_overhang_m)/2;
  for(const [x,track] of [[axleMidpoint-WB/2,baseline.rear_track_m],[axleMidpoint+WB/2,baseline.front_track_m]]) for(const side of [-1,1]) {
    const wheel=cylinder(R,R,.22,wheelMat,x,R,side*track/2,vehicleGroup); wheel.rotation.x=Math.PI/2;
    const hub=cylinder(R*.56,R*.56,.235,hubMat,x,R,side*track/2,vehicleGroup);hub.rotation.x=Math.PI/2;
    const disc=cylinder(R*.68,R*.68,.026,metal,x,R,side*(track/2+.09),vehicleGroup);disc.rotation.x=Math.PI/2;box(.07,.19,.04,copper,x+R*.44,R,side*(track/2+.12),vehicleGroup);torus(R*.87,.012,dark,x,R,side*(track/2+.115),vehicleGroup);
    for(let t=0;t<28;t++){const a=t*Math.PI*2/28;const groove=box(.016,.022,.19,dark,x+Math.cos(a)*R,R+Math.sin(a)*R,side*track/2,vehicleGroup);groove.rotation.z=a-Math.PI/2;}
    const centre=cylinder(R*.14,R*.14,.25,dark,x,R,side*track/2,vehicleGroup);centre.rotation.x=Math.PI/2;
    for(let k=0;k<5;k++){const angle=k*Math.PI*2/5; const spoke=box(R*.62,.035,.025,dark,x+Math.cos(angle)*R*.27,R+Math.sin(angle)*R*.27,side*(track/2+.125),vehicleGroup);spoke.rotation.z=angle;}
  }
  // System positions are illustrative, not the manufacturer's installation.
  box(.76,.26,.58,dark,-L*.28,.58,0,vehicleGroup); box(.53,.10,.4,gold,-L*.28,.69,0,vehicleGroup);
  box(.84,.42,.68,metal,L*.27,.79,0,vehicleGroup);box(.76,.12,.62,dark,L*.27,1.06,0,vehicleGroup);
  const engineRail=cylinder(.045,.045,.70,gold,L*.27,1.16,0,vehicleGroup);engineRail.rotation.z=Math.PI/2;
  const vehiclePath = new THREE.CatmullRomCurve3([[-L*.28,.75,0],[-L*.18,.64,0],[0,.64,0],[L*.22,.85,0],[L*.27,1.16,0]].map(p=>new THREE.Vector3(...p)));
  add(new THREE.TubeGeometry(vehiclePath,64,.025,10,false),gold,0,0,0,vehicleGroup);
  tag('FUEL SOURCE',-L*.28,1.15,.6,vehicleGroup);tag('INJECTION SYSTEM',L*.27,1.8,0,vehicleGroup);
  const vehicleDroplets=Array.from({length:5},()=>add(new THREE.SphereGeometry(.045,12,12),gold,0,0,0,vehicleGroup));
  const floor=box(L+1.2,.08,W+1.0,dark,0,-.05,0,vehicleGroup);floor.material=new THREE.MeshStandardMaterial({color:0x172a40,metalness:.35,roughness:.65});
  let current = {outputs:{fuelFlowGps:0, injectorPulseWidthMs:0, injectorDutyCyclePct:0}, running:false, motion:false, phase:0};
  let visible = true;
  function resize() { const w=container.clientWidth, h=container.clientHeight; if (!w || !h) return; renderer.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix(); draw(); }
  function draw() { for(const sprite of tags){const d=camera.position.distanceTo(sprite.position);sprite.scale.set(d*.14,d*.026,1);} if (visible && container.clientWidth && container.clientHeight) renderer.render(scene,camera); }
  function update(snapshot) {
    current = snapshot; const o=snapshot.outputs; const duty=Math.max(0,Math.min(100,o.injectorDutyCyclePct))/100;
    const deadFraction = o.injectorPulseWidthMs > 0 ? Math.min(1, Math.max(0, o.injectorDeadTimeMs / o.injectorPulseWidthMs)) : 1;
    const opening = snapshot.running && snapshot.motion && snapshot.phase >= duty * deadFraction && snapshot.phase < duty;
    needle.position.y = opening ? .60 : .55;
    spray.visible = !!opening; sprayMaterial.opacity = .15 + Math.min(o.fuelFlowGps/8,.35);
    mist.forEach((drop,i)=>{const age=(snapshot.phase*3+i/32)%1,a=i*2.39996;drop.position.set(Math.cos(a)*age*.4,-.05-age*.88,Math.sin(a)*age*.4);drop.visible=!!opening;});
    spray.scale.x = spray.scale.z = .55 + Math.min(o.injectorPulseWidthMs/20,.65);
    droplets.forEach((drop,index) => { drop.position.copy(path.getPointAt((snapshot.phase + index/droplets.length)%1)); drop.visible = snapshot.running && snapshot.motion; });
    vehicleDroplets.forEach((drop,index)=>{drop.position.copy(vehiclePath.getPointAt((snapshot.phase+index/vehicleDroplets.length)%1));drop.visible=snapshot.running&&snapshot.motion;});
    // Piston is static: the provided fuel model has no crank-angle output.
    piston.position.y = -1.1; draw();
  }
  function focus(component) { const targets={source:[-3,-.15,0],rail:[.1,1.55,0],injector:[.55,.75,0],cylinder:[.55,-.5,0]}; const p=targets[component]; if (!p) return; controls.target.set(...p);const distance=component==='injector'?3.3:component==='cylinder'?3.8:component==='source'?4.0:5.0;camera.position.copy(controls.target).add(new THREE.Vector3(.55,.35,.8).normalize().multiplyScalar(distance));controls.update();draw(); }
  controls.addEventListener('change',draw);
  const observer = new ResizeObserver(resize); observer.observe(container);
  renderer.domElement.addEventListener('webglcontextlost', event => { event.preventDefault(); container.dispatchEvent(new Event('fuel3dunavailable')); });
  function setMode(value) { mode=value==='detail'?'detail':'vehicle'; detailGroup.visible=mode==='detail'; vehicleGroup.visible=mode==='vehicle';renderer.shadowMap.needsUpdate=true;home(); }
  function zoom(factor) { const offset=camera.position.clone().sub(controls.target); const distance=THREE.MathUtils.clamp(offset.length()*factor,controls.minDistance,controls.maxDistance); camera.position.copy(controls.target).add(offset.setLength(distance)); controls.update(); draw(); }
  resize(); setMode('vehicle');
  return {update, focus, setMode, zoom, reset:home, setVisible(value) {visible=value; if(value) resize();}, dispose() {observer.disconnect(); controls.dispose();scene.traverse(o=>{o.geometry?.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material]){m?.map?.dispose();m?.dispose();}});environment.dispose();renderer.dispose(); renderer.domElement.remove();}};
}
