import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CutawayClock, cylinderPose, FIRING_ORDER } from "../static/js/engine-live-data/kinematics.mjs";

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
  const flywheel = new THREE.Group(); flywheel.position.set(-2.35, 0, 0); scene.add(flywheel);
  const rim = mesh(new THREE.TorusGeometry(.46, .06, 10, 40), silver, flywheel);
  rim.rotation.y = Math.PI / 2;
  for (let index = 0; index < 6; index++) {
    const spoke = mesh(new THREE.BoxGeometry(.07, .8, .05), gold, flywheel);
    spoke.rotation.x = index * Math.PI / 3;
  }
  const cams = [];
  for (const z of [-.2, .2]) {
    const cam = new THREE.Group(); cam.position.set(0, 2.48, z); scene.add(cam);
    const axle = cylinder(.045, 4.4, dark, cam); axle.rotation.z = Math.PI / 2;
    for (let index = 0; index < 4; index++) {
      const rotor = new THREE.Group(); rotor.position.x = (index - 1.5) * 1.1;
      rotor.rotation.x = -FIRING_ORDER.indexOf(index + 1) * Math.PI / 2 + (z < 0 ? Math.PI * .75 : Math.PI * 1.25);
      cam.add(rotor);
      const lobe = mesh(new THREE.SphereGeometry(.09, 12, 8), gold, rotor, [0, .05, 0]);
      lobe.scale.set(.6, 1.15, 1);
    }
    cams.push(cam);
  }
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
    const gasMat = material(0x326fbc, { transparent: true, opacity: .12, depthWrite: false, metalness: 0, roughness: 1 });
    const gas = cylinder(.31, 1, gasMat, scene, [x, 1.8, 0]);
    const intakeFlow = new THREE.Group(), exhaustFlow = new THREE.Group();
    scene.add(intakeFlow, exhaustFlow);
    for (const [flow, color, direction] of [[intakeFlow, 0x326fbc, -1], [exhaustFlow, 0x75808a, 1]]) {
      const curve = new THREE.CatmullRomCurve3([new THREE.Vector3(x, 2.05, direction * .18), new THREE.Vector3(x, 2.1, direction * .5), new THREE.Vector3(x, 2, direction * .85)]);
      mesh(new THREE.TubeGeometry(curve, 12, .06, 8, false), material(color, { transparent: true, opacity: .18, depthWrite: false }), scene);
      const beadMat = material(color, { metalness: 0 });
      for (let bead = 0; bead < 4; bead++) mesh(new THREE.SphereGeometry(.035, 8, 6), beadMat, flow);
    }
    const text = document.createElement("li");
    const title = document.createElement("strong"); title.textContent = `Cylinder ${index + 1}`;
    const stroke = document.createElement("span"); text.append(title, stroke); cylinderList.append(text);
    const tag = document.createElement("span"); tag.className = "cutaway-tag"; tag.textContent = `C${index + 1}`;
    tag.setAttribute("aria-hidden", "true"); host.append(tag);
    cylinders.push({ x, piston, rod, pin, arms, intake, exhaust, spark, injector, gas, intakeFlow, exhaustFlow, stroke, tag });
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
  const coolantFlow = new THREE.Group(); coolantFlow.position.copy(coolant.position); scene.add(coolantFlow);
  const flowMat = material(0x237d93, { metalness: 0 });
  for (let bead = 0; bead < 5; bead++) mesh(new THREE.SphereGeometry(.045, 8, 6), flowMat, coolantFlow);
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
  let result = initial, running = false, angle = 0, fanAngle = 0, pumpAngle = 0, frameId, dirty = true, disposed = false;
  let interpolation = { angle: 0, fan: 0, pump: 0, at: 0, target: 0, fanTarget: 0, pumpTarget: 0 };
  const abort = new AbortController();
  const animate = $("cutaway-animate");
  const effects = $("cutaway-effects");
  const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (!animate.dataset.initialised) {
    animate.checked = !motionPreference.matches;
    effects.checked = animate.checked;
    animate.dataset.initialised = "true";
  }
  const listen = (id, event, callback) => $(id).addEventListener(event, callback, { signal: abort.signal });
  motionPreference.addEventListener("change", event => {
    if (event.matches) { animate.checked = false; effects.checked = false; sync(result, running); }
  }, { signal: abort.signal });
  listen("cutaway-speed", "change", () => { clock.scale = Number($("cutaway-speed").value); sync(result, running); });
  listen("cutaway-animate", "change", () => { angle = clock.angle; dirty = true; sync(result, running); });
  listen("cutaway-effects", "change", () => { dirty = true; });
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
    if (i.EmergencyStop) {
      // Discard visual interpolation lag immediately: no post-stop coasting.
      clock.angle = angle; clock.fanAngle = fanAngle; clock.pumpAngle = pumpAngle;
    }
    if (clock.angle !== interpolation.target || clock.fanAngle !== interpolation.fanTarget || clock.pumpAngle !== interpolation.pumpTarget) {
      interpolation = { angle, fan: fanAngle, pump: pumpAngle, at: performance.now(), target: clock.angle, fanTarget: clock.fanAngle, pumpTarget: clock.pumpAngle };
    }
    if (!running) { angle = clock.angle; fanAngle = clock.fanAngle; pumpAngle = clock.pumpAngle; }
    dirty = true;
  }
  function draw() {
    const { inputs: i, outputs: o } = result;
    const moving = [2, 3].includes(o.EngineState) && !i.EmergencyStop;
    const slowCycle = i.EngineSpeed * clock.scale <= 300;
    flywheel.rotation.x = angle * Math.PI / 180;
    for (const cam of cams) cam.rotation.x = angle * Math.PI / 360;
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
      c.intake.position.y = 2.05 - pose.intakeLift * .12;
      c.exhaust.position.y = 2.05 - pose.exhaustLift * .12;
      // Avoid repeated bright flashes at high visual cycle frequencies.
      c.spark.material.emissiveIntensity = o.IgnitionEnable ? (slowCycle && pose.spark ? .8 : .18) : 0;
      c.injector.material.emissiveIntensity = o.InjectionEnable ? Math.min(o.InjectorPW / 5, 1.5) : 0;
      const top = 1.94, bottom = pose.piston + .13;
      c.gas.scale.y = Math.max(.04, top - bottom); c.gas.position.y = (top + bottom) / 2;
      c.gas.visible = effects.checked && moving;
      const colors = [0xbc673a, 0x75808a, 0x326fbc, 0xb88d35];
      const strokeIndex = Math.floor(pose.cycle / 180);
      const color = new THREE.Color(colors[strokeIndex]);
      if (slowCycle) {
        const blend = Math.min(1, (pose.cycle % 180) / 25);
        c.gas.material.color.set(colors[(strokeIndex + 3) % 4]).lerp(color, blend);
      } else c.gas.material.color.set(0x75808a);
      for (const [flow, active, direction] of [[c.intakeFlow, pose.intakeLift, -1], [c.exhaustFlow, pose.exhaustLift, 1]]) {
        flow.visible = effects.checked && moving && slowCycle && active > .05;
        for (const [bead, node] of flow.children.entries()) {
          const phase = ((pose.cycle % 180) / 180 * 2 + bead / 4) % 1;
          const distance = direction < 0 ? .85 - phase * .65 : .2 + phase * .65;
          node.position.set(c.x, 2.05, direction * distance);
        }
      }
      const label = `${pose.stroke} · ${pose.cycle.toFixed(0)}°${pose.spark ? " · spark" : ""}`;
      if (c.stroke.textContent !== label) c.stroke.textContent = label;
      const point = new THREE.Vector3(c.x, 2.65, 0).project(camera);
      c.tag.style.left = `${(point.x + 1) * 50}%`; c.tag.style.top = `${(1 - point.y) * 50}%`;
    }
    fanMat.color.set(o.FanDuty > 0 ? 0x2857b5 : 0x536273);
    fan.rotation.z = fanAngle * Math.PI / 180;
    coolantMat.color.setHSL(.6 * (1 - Math.min(1, Math.max(0, (o.ControlTemperature + 20) / 155))), .7, .4);
    coolant.rotation.z = 0; // Colour is a temperature marker, not fluid flow.
    coolantFlow.visible = effects.checked && o.WaterPumpDuty > 0 && !i.EmergencyStop;
    for (const [bead, node] of coolantFlow.children.entries()) {
      const a = pumpAngle * Math.PI / 180 + bead * Math.PI * 2 / 5;
      node.position.set(Math.cos(a) * .24, Math.sin(a) * .24, 0);
    }
    host.dataset.phase = angle.toFixed(4);
    host.dataset.fanPhase = fanAngle.toFixed(4);
    host.dataset.effects = effects.checked ? "on" : "off";
    renderer.render(scene, camera);
    dirty = false;
  }
  function frame(time) {
    if (disposed) return;
    if (running && animate.checked && !result.inputs.EmergencyStop) {
      const blend = Math.min(1, Math.max(0, (time - interpolation.at) / 200));
      angle = interpolation.angle + (interpolation.target - interpolation.angle) * blend;
      fanAngle = interpolation.fan + (interpolation.fanTarget - interpolation.fan) * blend;
      pumpAngle = interpolation.pump + (interpolation.pumpTarget - interpolation.pump) * blend;
      dirty = true;
    }
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
    reset() { clock.reset(); angle = 0; fanAngle = 0; pumpAngle = 0; interpolation = { angle: 0, fan: 0, pump: 0, at: 0, target: 0, fanTarget: 0, pumpTarget: 0 }; dirty = true; },
    dispose,
  };
}
