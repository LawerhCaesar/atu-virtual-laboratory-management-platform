import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

// Generic teaching geometry; the solver remains the sole source of numerical results.
export function createFuelScene(container) {
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, powerPreference: 'low-power'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.append(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, .1, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false; controls.enablePan = false; controls.minDistance = 6; controls.maxDistance = 18;
  controls.maxPolarAngle = Math.PI * .7; controls.target.set(0, .5, 0);
  const home = () => { camera.position.set(7.4, 5.1, 9.4); controls.target.set(0, .5, 0); controls.update(); draw(); };
  scene.add(new THREE.HemisphereLight(0xd8e9ff, 0x263142, 2.2));
  const key = new THREE.DirectionalLight(0xffffff, 3.2); key.position.set(2, 8, 7); scene.add(key);
  const rim = new THREE.DirectionalLight(0x80b7ff, 2); rim.position.set(-6, 3, -5); scene.add(rim);
  const metal = new THREE.MeshStandardMaterial({color: 0x9ba9b6, metalness: .8, roughness: .31});
  const dark = new THREE.MeshStandardMaterial({color: 0x273b51, metalness: .65, roughness: .4});
  const rubber = new THREE.MeshStandardMaterial({color: 0x111c2a, metalness: .1, roughness: .68});
  const gold = new THREE.MeshStandardMaterial({color: 0xe6b85d, metalness: .55, roughness: .35, emissive: 0x452000, emissiveIntensity: .35});
  const glass = new THREE.MeshStandardMaterial({color: 0x779cb7, metalness: .15, roughness: .15, transparent: true, opacity: .24, depthWrite: false, side: THREE.DoubleSide});
  const sprayMaterial = new THREE.MeshBasicMaterial({color: 0xf2bb5f, transparent: true, opacity: .2, depthWrite: false, side: THREE.DoubleSide});
  const add = (geometry, material, x, y, z, parent = scene) => { const mesh = new THREE.Mesh(geometry, material); mesh.position.set(x, y, z); parent.add(mesh); return mesh; };
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
  const injector = new THREE.Group(); injector.position.set(.55,0,0); scene.add(injector);
  cylinder(.19,.23,.5,dark,0,1.18,0,injector); cylinder(.14,.19,.63,metal,0,.67,0,injector);
  cylinder(.11,.14,.22,gold,0,.25,0,injector); const needle=cylinder(.035,.035,.52,gold,0,.55,0,injector);
  for(const y of [.48,.78,1.05]) cylinder(.20,.20,.035,rubber,0,y,0,injector);
  box(.36,.19,.35,rubber,0,1.22,.32,injector);
  const chamber = new THREE.Group(); chamber.position.set(.55,0,0); scene.add(chamber);
  cylinder(.72,.72,1.75,glass,0,-.57,0,chamber);
  const piston=cylinder(.65,.65,.22,metal,0,-1.1,0,chamber);
  cylinder(.73,.73,.12,dark,0,.32,0,chamber); cylinder(.73,.73,.12,dark,0,-1.36,0,chamber);
  for(const angle of [0,Math.PI/2,Math.PI,3*Math.PI/2]) {const x=.56*Math.cos(angle),z=.56*Math.sin(angle);cylinder(.07,.07,.08,metal,x,.42,z,chamber);}
  for(const y of [-1.28,-1.05,-.82]) { const ring=cylinder(.68,.68,.025,dark,0,y,0,chamber); ring.material=metal; }
  const spray = add(new THREE.ConeGeometry(.48,1.05,32,1,true),sprayMaterial,0,-.3,0,chamber);
  // Small droplets move along the feed line at a deliberately slowed teaching pace.
  const droplets = Array.from({length: 6}, () => add(new THREE.SphereGeometry(.075,12,12),gold,0,0,0));
  const path = new THREE.CatmullRomCurve3([[-2.82,.5,0],[-2.8,1.25,0],[-2.1,1.55,0],[-1.3,1.55,0],[.5,1.55,0]].map(p=>new THREE.Vector3(...p)));
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
    // Piston is static: the provided fuel model has no crank-angle output.
    piston.position.y = -1.1; draw();
  }
  function focus(component) { const targets={source:[-3,-.15,0],rail:[.1,1.55,0],injector:[.55,.75,0],cylinder:[.55,-.5,0]}; const p=targets[component]; if (!p) return; controls.target.set(...p); controls.update(); draw(); }
  controls.addEventListener('change',draw);
  const observer = new ResizeObserver(resize); observer.observe(container);
  renderer.domElement.addEventListener('webglcontextlost', event => { event.preventDefault(); container.dispatchEvent(new Event('fuel3dunavailable')); });
  resize(); home();
  return {update, focus, reset:home, setVisible(value) {visible=value; if(value) resize();}, dispose() {observer.disconnect(); controls.dispose(); renderer.dispose(); renderer.domElement.remove();}};
}
