import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CutawayClock, cylinderPose } from "../static/js/engine-live-data/kinematics.mjs";

// The renderer consumes snapshots; it never writes to the engineering model.
export function createCutaway(root, initial, onFailure) {
  const $ = id => root.querySelector(`#${id}`);
  const host = $("cutaway-viewport");
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setClearColor(0xeef3fa);
  const canvas = renderer.domElement;
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", "Interactive generic four-cylinder engine cutaway. Silver pistons, gold connecting rods, blue crankshaft, green intake and orange exhaust valves.");
  canvas.setAttribute("aria-describedby", "cutaway-description cutaway-status");
  host.replaceChildren(canvas);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
  const controls = new OrbitControls(camera, canvas);
  controls.target.set(0, 0.9, 0);
  controls.minDistance = 4; controls.maxDistance = 15;
  controls.enablePan = false;
  controls.maxPolarAngle = Math.PI * 0.85;
  function resetCamera() { camera.position.set(4.8, 3.7, 6.8); controls.update(); }
  resetCamera();
  scene.add(new THREE.HemisphereLight(0xffffff, 0x526784, 2.5));
  const light = new THREE.DirectionalLight(0xffffff, 3);
  light.position.set(-3, 6, 5); scene.add(light);
  const materials = [];
  function material(color, properties = {}) {
    const result = new THREE.MeshStandardMaterial({ color, metalness: .35, roughness: .4, ...properties });
    materials.push(result); return result;
  }
  const silver = material(0xb7c5d3), gold = material(0xdba54d), blue = material(0x2857b5);
  const green = material(0x23775c), orange = material(0xb65a23), dark = material(0x435467);
  const casingMat = material(0x83abc9, { transparent: true, opacity: .1, depthWrite: false });
  const casing = new THREE.Group(); scene.add(casing);
  function mesh(geometry, mat, parent = scene, position = [0, 0, 0]) {
    const node = new THREE.Mesh(geometry, mat); node.position.set(...position); parent.add(node); return node;
  }
  function cylinder(radius, length, mat, parent, position) {
    return mesh(new THREE.CylinderGeometry(radius, radius, length, 24), mat, parent, position);
  }
  const shaft = cylinder(.095, 4.9, blue); shaft.rotation.z = Math.PI / 2;
  const base = mesh(new THREE.BoxGeometry(5.1, .15, 1.8), dark, scene, [0, -.55, 0]);
  base.material = dark;
  const cylinders = [];
  const cylinderList = $("cutaway-cylinders"); cylinderList.replaceChildren();
  const up = new THREE.Vector3(0, 1, 0);
  for (let index = 0; index < 4; index++) {
    const x = (index - 1.5) * 1.1;
    const piston = cylinder(.35, .25, silver, scene, [x, 1.61, 0]);
    for (const y of [-.075, .075]) {
      const ring = mesh(new THREE.TorusGeometry(.352, .014, 6, 32), dark, piston, [0, y, 0]);
      ring.rotation.x = Math.PI / 2;
    }
    const rod = cylinder(.065, 1, gold);
    const pin = cylinder(.105, .5, gold); pin.rotation.z = Math.PI / 2;
    const arms = [];
    for (const side of [-1, 1]) {
      const web = cylinder(.37, .075, blue, scene, [x + side * .28, 0, 0]);
      web.rotation.z = Math.PI / 2;
      arms.push(mesh(new THREE.BoxGeometry(.12, 1, .1), blue, scene, [x + side * .22, 0, 0]));
    }
    mesh(new THREE.BoxGeometry(.94, 1.6, .98), casingMat, casing, [x, 1.25, 0]);
    for (const z of [-.48, .48]) mesh(new THREE.BoxGeometry(.95, .09, .07), silver, casing, [x, 2.03, z]);
    const intake = new THREE.Group(), exhaust = new THREE.Group();
    scene.add(intake, exhaust);
    intake.position.set(x, 2.05, -.2); exhaust.position.set(x, 2.05, .2);
    for (const [group, mat] of [[intake, green], [exhaust, orange]]) {
      cylinder(.12, .04, mat, group);
      cylinder(.025, .4, mat, group, [0, .2, 0]);
    }
    const sparkMat = material(0x596779, { emissive: 0xffd27a, emissiveIntensity: 0 });
    const spark = mesh(new THREE.SphereGeometry(.075, 12, 12), sparkMat, scene, [x, 1.94, 0]);
    const injectorMat = material(0x775020, { emissive: 0xeab84d, emissiveIntensity: 0 });
    const injector = mesh(new THREE.ConeGeometry(.085, .25, 16), injectorMat, scene, [x, 1.9, -.5]);
    injector.rotation.x = -.5;
    const text = document.createElement("li");
    const title = document.createElement("strong"); title.textContent = `Cylinder ${index + 1}`;
    const stroke = document.createElement("span"); text.append(title, stroke); cylinderList.append(text);
    const tag = document.createElement("span"); tag.className = "cutaway-tag"; tag.textContent = `C${index + 1}`;
    tag.setAttribute("aria-hidden", "true"); host.append(tag);
    cylinders.push({ x, piston, rod, pin, arms, intake, exhaust, spark, injector, stroke, tag });
  }
  // Separate command markers, not a mechanical fan/pump speed model.
  const fanMat = material(0x536273), coolantMat = material(0x2857b5);
  const fan = new THREE.Group(); fan.position.set(2.9, 1.15, 0); scene.add(fan);
  mesh(new THREE.TorusGeometry(.35, .025, 8, 32), dark, fan);
  for (let blade = 0; blade < 4; blade++) {
    const group = new THREE.Group(); group.rotation.z = blade * Math.PI / 2; fan.add(group);
    mesh(new THREE.BoxGeometry(.13, .28, .04), fanMat, group, [0, .17, 0]);
  }
  const coolant = mesh(new THREE.TorusGeometry(.24, .055, 10, 32), coolantMat, scene, [-2.75, 1.25, 0]);
  const grid = new THREE.GridHelper(8, 16, 0xa6b6ca, 0xdce4ed); grid.position.y = -.64; scene.add(grid);

  const signals = [
    ["state", "Engine state"], ["rpm", "Input engine speed"], ["playback", "Visual playback"],
    ["injection", "Injection command"], ["spark", "Ignition command"], ["coolant", "Control temperature"],
    ["fan", "Fan duty command"], ["pump", "Virtual electric-pump duty"],
    ["fuel", "Fuel-pump command"], ["starter", "Starter command"],
  ];
  const values = {};
  $("cutaway-signals").replaceChildren();
  for (const [key, title] of signals) {
    const div = document.createElement("div"), dt = document.createElement("dt"), dd = document.createElement("dd");
    dt.textContent = title; dd.dataset.cutawaySignal = key;
    div.append(dt, dd); $("cutaway-signals").append(div); values[key] = dd;
  }
  const clock = new CutawayClock();
  clock.scale = Number($("cutaway-speed").value);
  casing.visible = $("cutaway-casing").checked;
  let result = initial, running = false, angle = 0, previous = 0, frameId, dirty = true, disposed = false;
  const abort = new AbortController();
  const animate = $("cutaway-animate");
  if (!animate.dataset.initialised) {
    animate.checked = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    animate.dataset.initialised = "true";
  }
  const listen = (id, event, callback) => $(id).addEventListener(event, callback, { signal: abort.signal });
  listen("cutaway-speed", "change", () => { clock.scale = Number($("cutaway-speed").value); sync(result, running); });
  listen("cutaway-animate", "change", () => { angle = clock.angle; dirty = true; sync(result, running); });
  listen("cutaway-casing", "change", () => { casing.visible = $("cutaway-casing").checked; dirty = true; });
  listen("cutaway-left", "click", () => { camera.position.applyAxisAngle(up, -.25); controls.update(); dirty = true; });
  listen("cutaway-right", "click", () => { camera.position.applyAxisAngle(up, .25); controls.update(); dirty = true; });
  const zoom = factor => { camera.position.sub(controls.target).multiplyScalar(factor).add(controls.target); controls.update(); dirty = true; };
  listen("cutaway-in", "click", () => zoom(.85));
  listen("cutaway-out", "click", () => zoom(1.15));
  listen("cutaway-camera", "click", () => { resetCamera(); dirty = true; });
  controls.addEventListener("change", () => { dirty = true; });
  const resize = new ResizeObserver(() => {
    const width = Math.max(1, host.clientWidth), height = Math.max(1, host.clientHeight);
    renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix(); dirty = true;
  });
  resize.observe(host);
  function sync(snapshot, isRunning) {
    result = snapshot; running = isRunning;
    const { inputs: i, outputs: o } = result;
    const content = {
      state: o.EngineStateLabel, rpm: `${i.EngineSpeed.toFixed(0)} rpm`,
      playback: `${clock.scale}× · ${animate.checked ? (running ? "following simulation" : "paused") : "motion disabled"}`,
      injection: `${o.InjectionEnable ? "ON" : "OFF"} · ${o.InjectorPW.toFixed(4)} ms`,
      spark: `${o.IgnitionEnable ? "ON" : "OFF"} · ${o.IgnitionTiming.toFixed(2)}° BTDC`,
      coolant: `${o.ControlTemperature.toFixed(2)} °C`, fan: `${o.FanDuty.toFixed(2)} %`,
      pump: `${o.WaterPumpDuty.toFixed(2)} %`, fuel: o.FuelPumpState ? "ON" : "OFF", starter: o.StarterState ? "ON" : "OFF",
    };
    for (const [key, value] of Object.entries(content)) values[key].textContent = value;
    if (!running) angle = clock.angle;
    dirty = true;
  }
  function draw() {
    const { outputs: o } = result;
    for (const [index, c] of cylinders.entries()) {
      const pose = cylinderPose(index + 1, angle, o);
      c.piston.position.y = pose.piston;
      const from = new THREE.Vector3(c.x, pose.pinY, pose.pinZ);
      const to = new THREE.Vector3(c.x, pose.piston, 0);
      c.rod.position.copy(from).add(to).multiplyScalar(.5);
      c.rod.scale.y = from.distanceTo(to);
      c.rod.quaternion.setFromUnitVectors(up, to.clone().sub(from).normalize());
      c.pin.position.copy(from);
      const crankVector = new THREE.Vector3(0, pose.pinY, pose.pinZ);
      for (const [armIndex, arm] of c.arms.entries()) {
        arm.position.set(c.x + (armIndex ? .22 : -.22), pose.pinY / 2, pose.pinZ / 2);
        arm.scale.y = crankVector.length(); arm.quaternion.setFromUnitVectors(up, crankVector.clone().normalize());
      }
      c.intake.position.y = 2.05 - (pose.intake ? .12 : 0);
      c.exhaust.position.y = 2.05 - (pose.exhaust ? .12 : 0);
      c.spark.material.emissiveIntensity = pose.spark ? 2 : 0;
      c.injector.material.emissiveIntensity = o.InjectionEnable ? Math.min(o.InjectorPW / 5, 1.5) : 0;
      const label = `${pose.stroke} · ${pose.cycle.toFixed(0)}°${pose.spark ? " · spark" : ""}`;
      if (c.stroke.textContent !== label) c.stroke.textContent = label;
      const point = new THREE.Vector3(c.x, 2.65, 0).project(camera);
      c.tag.style.left = `${(point.x + 1) * 50}%`; c.tag.style.top = `${(1 - point.y) * 50}%`;
    }
    fanMat.color.set(o.FanDuty > 0 ? 0x2857b5 : 0x536273);
    fan.scale.setScalar(.85 + o.FanDuty / 100 * .15);
    coolantMat.color.setHSL(.6 * (1 - Math.min(1, Math.max(0, (o.ControlTemperature + 20) / 155))), .7, .4);
    coolant.rotation.z = 0; // Colour is a temperature marker, not fluid flow.
    host.dataset.phase = angle.toFixed(4);
    renderer.render(scene, camera);
    dirty = false;
  }
  function frame(time) {
    if (disposed) return;
    const dt = Math.min(.1, Math.max(0, (time - previous) / 1000)); previous = time;
    if (running && animate.checked) { angle += (clock.angle - angle) * Math.min(1, dt * 25); dirty = true; }
    if (dirty && !document.hidden) draw();
    frameId = requestAnimationFrame(frame);
  }
  function dispose() {
    if (disposed) return;
    disposed = true; cancelAnimationFrame(frameId); abort.abort(); resize.disconnect(); controls.dispose();
    scene.traverse(object => { if (object.geometry) object.geometry.dispose(); });
    for (const mat of materials) mat.dispose();
    grid.material.dispose(); renderer.dispose(); renderer.forceContextLoss(); host.replaceChildren();
  }
  canvas.addEventListener("webglcontextlost", event => {
    event.preventDefault(); if (!disposed) { dispose(); onFailure(); }
  }, { signal: abort.signal });
  sync(initial, false);
  frameId = requestAnimationFrame(frame);
  return {
    sync,
    advance(snapshot, dt) { if (animate.checked) clock.advance(snapshot, dt); },
    reset() { clock.reset(); angle = 0; dirty = true; },
    dispose,
  };
}
