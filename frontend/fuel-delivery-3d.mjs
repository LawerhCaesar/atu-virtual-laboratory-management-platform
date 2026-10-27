import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

// Generic teaching geometry; the solver remains the sole source of numerical results.
export function createFuelScene(container, baseline) {
  for (const key of ['length_m','width_m','height_m','wheelbase_m','wheel_radius_m','front_track_m','rear_track_m','front_overhang_m','rear_overhang_m']) {
    if (!Number.isFinite(baseline?.[key]) || baseline[key] <= 0) throw new Error('Vehicle baseline dimensions are unavailable');
  }
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, powerPreference: 'low-power'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.append(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, .1, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false; controls.enablePan = false; controls.minDistance = 3; controls.maxDistance = 18;
  controls.maxPolarAngle = Math.PI * .7; controls.target.set(0, .5, 0);
  let mode = 'vehicle';
  const home = () => { if(mode==='vehicle') {camera.position.set(6.4, 3.5, 7.4); controls.target.set(0, .72, 0);} else {camera.position.set(7.4, 5.1, 9.4); controls.target.set(0, .5, 0);} controls.update(); draw(); };
  scene.add(new THREE.HemisphereLight(0xd8e9ff, 0x263142, 2.2));
  const key = new THREE.DirectionalLight(0xffffff, 3.2); key.position.set(2, 8, 7); scene.add(key);
  const rim = new THREE.DirectionalLight(0x80b7ff, 2); rim.position.set(-6, 3, -5); scene.add(rim);
  const metal = new THREE.MeshStandardMaterial({color: 0x9ba9b6, metalness: .8, roughness: .31});
  const dark = new THREE.MeshStandardMaterial({color: 0x273b51, metalness: .65, roughness: .4});
  const rubber = new THREE.MeshStandardMaterial({color: 0x111c2a, metalness: .1, roughness: .68});
  const gold = new THREE.MeshStandardMaterial({color: 0xe6b85d, metalness: .55, roughness: .35, emissive: 0x452000, emissiveIntensity: .35});
  const glass = new THREE.MeshStandardMaterial({color: 0x779cb7, metalness: .15, roughness: .15, transparent: true, opacity: .24, depthWrite: false, side: THREE.DoubleSide});
  const sprayMaterial = new THREE.MeshBasicMaterial({color: 0xf2bb5f, transparent: true, opacity: .2, depthWrite: false, side: THREE.DoubleSide});
  const detailGroup = new THREE.Group(), vehicleGroup = new THREE.Group(); scene.add(detailGroup, vehicleGroup);
  const add = (geometry, material, x, y, z, parent = detailGroup) => { const mesh = new THREE.Mesh(geometry, material); mesh.position.set(x, y, z); parent.add(mesh); return mesh; };
  const box = (w,h,d,mat,x,y,z,parent) => add(new THREE.BoxGeometry(w,h,d),mat,x,y,z,parent);
  const cylinder = (r1,r2,h,mat,x,y,z,parent) => add(new THREE.CylinderGeometry(r1,r2,h,32),mat,x,y,z,parent);
  const pipe = (points, radius, mat) => { const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p))); return add(new THREE.TubeGeometry(curve, 64, radius, 12, false),mat,0,0,0); };
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
  const railCore = cylinder(.045,.045,3.15,gold,.15,1.55,0); railCore.rotation.z = Math.PI/2;
  for (const x of [-.9,.1,1.1]) { const cap=cylinder(.28,.28,.12,dark,x,1.55,0); cap.rotation.z=Math.PI/2; }
  for (const x of [-.75,1.45]) { cylinder(.09,.09,.32,metal,x,1.24,0); box(.27,.10,.45,dark,x,1.02,0); }
  const injector = new THREE.Group(); injector.position.set(.55,0,0); detailGroup.add(injector);
  cylinder(.19,.23,.5,dark,0,1.18,0,injector); cylinder(.14,.19,.63,metal,0,.67,0,injector);
  cylinder(.11,.14,.22,gold,0,.25,0,injector); const needle=cylinder(.035,.035,.52,gold,0,.55,0,injector);
  for(const y of [.48,.78,1.05]) cylinder(.20,.20,.035,rubber,0,y,0,injector);
  box(.36,.19,.35,rubber,0,1.22,.32,injector);
  const chamber = new THREE.Group(); chamber.position.set(.55,0,0); detailGroup.add(chamber);
  cylinder(.72,.72,1.75,glass,0,-.57,0,chamber);
  const piston=cylinder(.65,.65,.22,metal,0,-1.1,0,chamber);
  cylinder(.73,.73,.12,dark,0,.32,0,chamber); cylinder(.73,.73,.12,dark,0,-1.36,0,chamber);
  for(const angle of [0,Math.PI/2,Math.PI,3*Math.PI/2]) {const x=.56*Math.cos(angle),z=.56*Math.sin(angle);cylinder(.07,.07,.08,metal,x,.42,z,chamber);}
  for(const y of [-1.28,-1.05,-.82]) { const ring=cylinder(.68,.68,.025,dark,0,y,0,chamber); ring.material=metal; }
  const spray = add(new THREE.ConeGeometry(.48,1.05,32,1,true),sprayMaterial,0,-.3,0,chamber);
  // Small droplets move along the feed line at a deliberately slowed teaching pace.
  const droplets = Array.from({length: 6}, () => add(new THREE.SphereGeometry(.075,12,12),gold,0,0,0));
  const path = new THREE.CatmullRomCurve3([[-2.82,.5,0],[-2.8,1.25,0],[-2.1,1.55,0],[-1.3,1.55,0],[.5,1.55,0]].map(p=>new THREE.Vector3(...p)));
  // Dimensions are project baselines in metres. Silhouette and internal layout are generic.
  const L=baseline.length_m, W=baseline.width_m, H=baseline.height_m, R=baseline.wheel_radius_m, WB=baseline.wheelbase_m;
  const body = new THREE.Shape();
  body.moveTo(-L/2,.39); body.lineTo(-L/2+.12,.8); body.quadraticCurveTo(-L*.44,1.08,-L*.29,1.16);
  body.quadraticCurveTo(-L*.18,H,L*.01,H); body.lineTo(L*.20,H); body.quadraticCurveTo(L*.30,H-.03,L*.36,1.17);
  body.quadraticCurveTo(L*.46,1.04,L/2-.05,.92); body.lineTo(L/2,.4); body.closePath();
  const bodyMaterial=new THREE.MeshStandardMaterial({color:0x6c9ab8,metalness:.42,roughness:.3,transparent:true,opacity:.19,depthWrite:false,side:THREE.DoubleSide});
  const vehicleBody=add(new THREE.ExtrudeGeometry(body,{depth:W,bevelEnabled:false,curveSegments:20}),bodyMaterial,0,0,-W/2,vehicleGroup);
  const outline=new THREE.LineSegments(new THREE.EdgesGeometry(vehicleBody.geometry,25),new THREE.LineBasicMaterial({color:0xabcde0,transparent:true,opacity:.42})); outline.position.z=-W/2;vehicleGroup.add(outline);
  const frame=box(L*.87,.12,W*.72,dark,0,.48,0,vehicleGroup);
  const windowMat=new THREE.MeshStandardMaterial({color:0x92bed5,metalness:.2,roughness:.25,transparent:true,opacity:.28,depthWrite:false,side:THREE.DoubleSide});
  const windowShape=new THREE.Shape(); windowShape.moveTo(-L*.27,1.15);windowShape.quadraticCurveTo(-L*.17,H-.08,-L*.02,H-.1);windowShape.lineTo(L*.17,H-.1);windowShape.quadraticCurveTo(L*.25,H-.1,L*.30,1.15);windowShape.closePath();
  for(const z of [-W/2-.005,W/2+.005]) add(new THREE.ShapeGeometry(windowShape,20),windowMat,0,0,z,vehicleGroup);
  const wheelMat=new THREE.MeshStandardMaterial({color:0x151d27,roughness:.82}), hubMat=new THREE.MeshStandardMaterial({color:0xa6b3be,metalness:.8,roughness:.28});
  const axleMidpoint=(baseline.rear_overhang_m-baseline.front_overhang_m)/2;
  for(const [x,track] of [[axleMidpoint-WB/2,baseline.rear_track_m],[axleMidpoint+WB/2,baseline.front_track_m]]) for(const side of [-1,1]) {
    const wheel=cylinder(R,R,.22,wheelMat,x,R,side*track/2,vehicleGroup); wheel.rotation.x=Math.PI/2;
    const hub=cylinder(R*.56,R*.56,.235,hubMat,x,R,side*track/2,vehicleGroup);hub.rotation.x=Math.PI/2;
    const centre=cylinder(R*.14,R*.14,.25,dark,x,R,side*track/2,vehicleGroup);centre.rotation.x=Math.PI/2;
    for(let k=0;k<5;k++){const angle=k*Math.PI*2/5; const spoke=box(R*.62,.035,.025,dark,x+Math.cos(angle)*R*.27,R+Math.sin(angle)*R*.27,side*(track/2+.125),vehicleGroup);spoke.rotation.z=angle;}
  }
  // System positions are illustrative, not the manufacturer's installation.
  box(.76,.26,.58,dark,-L*.28,.58,0,vehicleGroup); box(.53,.10,.4,gold,-L*.28,.69,0,vehicleGroup);
  box(.84,.42,.68,metal,L*.27,.79,0,vehicleGroup);box(.76,.12,.62,dark,L*.27,1.06,0,vehicleGroup);
  const engineRail=cylinder(.045,.045,.70,gold,L*.27,1.16,0,vehicleGroup);engineRail.rotation.z=Math.PI/2;
  const vehiclePath = new THREE.CatmullRomCurve3([[-L*.28,.75,0],[-L*.18,.64,0],[0,.64,0],[L*.22,.85,0],[L*.27,1.16,0]].map(p=>new THREE.Vector3(...p)));
  add(new THREE.TubeGeometry(vehiclePath,64,.025,10,false),gold,0,0,0,vehicleGroup);
  const vehicleDroplets=Array.from({length:5},()=>add(new THREE.SphereGeometry(.045,12,12),gold,0,0,0,vehicleGroup));
  const floor=box(L+1.2,.08,W+1.0,dark,0,-.05,0,vehicleGroup);floor.material=new THREE.MeshStandardMaterial({color:0x172a40,metalness:.35,roughness:.65});
  let current = {outputs:{fuelFlowGps:0, injectorPulseWidthMs:0, injectorDutyCyclePct:0}, running:false, motion:false, phase:0};
  let visible = true;
  function resize() { const w=container.clientWidth, h=container.clientHeight; if (!w || !h) return; renderer.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix(); draw(); }
  function draw() { if (visible && container.clientWidth && container.clientHeight) renderer.render(scene,camera); }
  function update(snapshot) {
    current = snapshot; const o=snapshot.outputs; const duty=Math.max(0,Math.min(100,o.injectorDutyCyclePct))/100;
    const deadFraction = o.injectorPulseWidthMs > 0 ? Math.min(1, Math.max(0, o.injectorDeadTimeMs / o.injectorPulseWidthMs)) : 1;
    const opening = snapshot.running && snapshot.motion && snapshot.phase >= duty * deadFraction && snapshot.phase < duty;
    needle.position.y = opening ? .60 : .55;
    spray.visible = !!opening; sprayMaterial.opacity = .15 + Math.min(o.fuelFlowGps/8,.35);
    spray.scale.x = spray.scale.z = .55 + Math.min(o.injectorPulseWidthMs/20,.65);
    droplets.forEach((drop,index) => { drop.position.copy(path.getPointAt((snapshot.phase + index/droplets.length)%1)); drop.visible = snapshot.running && snapshot.motion; });
    vehicleDroplets.forEach((drop,index)=>{drop.position.copy(vehiclePath.getPointAt((snapshot.phase+index/vehicleDroplets.length)%1));drop.visible=snapshot.running&&snapshot.motion;});
    // Piston is static: the provided fuel model has no crank-angle output.
    piston.position.y = -1.1; draw();
  }
  function focus(component) { const targets={source:[-3,-.15,0],rail:[.1,1.55,0],injector:[.55,.75,0],cylinder:[.55,-.5,0]}; const p=targets[component]; if (!p) return; controls.target.set(...p); controls.update(); draw(); }
  controls.addEventListener('change',draw);
  const observer = new ResizeObserver(resize); observer.observe(container);
  renderer.domElement.addEventListener('webglcontextlost', event => { event.preventDefault(); container.dispatchEvent(new Event('fuel3dunavailable')); });
  function setMode(value) { mode=value==='detail'?'detail':'vehicle'; detailGroup.visible=mode==='detail'; vehicleGroup.visible=mode==='vehicle'; home(); }
  function zoom(factor) { const offset=camera.position.clone().sub(controls.target); const distance=THREE.MathUtils.clamp(offset.length()*factor,controls.minDistance,controls.maxDistance); camera.position.copy(controls.target).add(offset.setLength(distance)); controls.update(); draw(); }
  resize(); setMode('vehicle');
  return {update, focus, setMode, zoom, reset:home, setVisible(value) {visible=value; if(value) resize();}, dispose() {observer.disconnect(); controls.dispose(); renderer.dispose(); renderer.domElement.remove();}};
}
