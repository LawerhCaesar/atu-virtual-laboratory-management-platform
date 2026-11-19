import * as T from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
export function createStand(host) {
  const renderer = new T.WebGLRenderer({
    antialias: true,
    powerPreference: "low-power",
  });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  renderer.outputColorSpace = T.SRGBColorSpace;
  renderer.toneMapping = T.ACESFilmicToneMapping;
  host.append(renderer.domElement);
  const scene = new T.Scene();
  scene.background = new T.Color(0x12283b);
  const g = new T.PMREMGenerator(renderer),
    room = new RoomEnvironment(),
    env = g.fromScene(room, 0.04);
  scene.environment = env.texture;
  room.dispose();
  g.dispose();
  scene.add(new T.HemisphereLight(0xd0e5ff, 0x28323b, 2));
  const light = new T.DirectionalLight(0xffffff, 3);
  light.position.set(4, 7, 3);
  scene.add(light);
  const camera = new T.PerspectiveCamera(38, 1, 0.1, 60),
    orbit = new OrbitControls(camera, renderer.domElement);
  orbit.enablePan = false;
  orbit.minDistance = 2;
  orbit.maxDistance = 14;
  const mat = (color, m = 0.6, r = 0.35) =>
      new T.MeshStandardMaterial({ color, metalness: m, roughness: r }),
    metal = mat(0xa6b7c3, 0.85, 0.28),
    dark = mat(0x243b50),
    rubber = mat(0x141e28, 0.05, 0.8),
    blue = mat(0x225b75),
    orange = mat(0xdc9b42, 0.4),
    red = mat(0xaf4e43),
    green = mat(0x3ca58c);
  const add = (geometry, material, x, y, z, parent = scene) => {
      const mesh = new T.Mesh(geometry, material);
      mesh.position.set(x, y, z);
      parent.add(mesh);
      return mesh;
    },
    box = (w, h, d, m, x, y, z, p) =>
      add(
        new RoundedBoxGeometry(w, h, d, 2, Math.min(w, h, d) * 0.09),
        m,
        x,
        y,
        z,
        p,
      ),
    cyl = (r, h, m, x, y, z, p) =>
      add(new T.CylinderGeometry(r, r, h, 48), m, x, y, z, p),
    pipe = (points, m, r = 0.03) =>
      add(
        new T.TubeGeometry(
          new T.CatmullRomCurve3(points.map((p) => new T.Vector3(...p))),
          48,
          r,
          10,
          false,
        ),
        m,
        0,
        0,
        0,
      );
  for (const z of [-0.7, 0.7]) {
    box(3.5, 0.12, 0.12, blue, 0, 0.15, z);
    for (const x of [-1.5, 1.5]) {
      const caster = cyl(0.13, 0.1, rubber, x, 0.03, z);
      caster.rotation.z = Math.PI / 2;
    }
  }
  for (const x of [-1.2, 1.2]) box(0.12, 1, 0.12, blue, x, 0.7, 0);
  box(2.3, 0.12, 1.4, blue, 0, 1.08, 0);
  const shellMaterial = metal.clone(),
    coverMaterial = dark.clone();
  box(1.25, 0.9, 0.85, shellMaterial, 0, 1.6, 0);
  box(1.34, 0.16, 0.92, coverMaterial, 0, 2.1, 0);
  for (let i = 0; i < 4; i++) {
    box(0.22, 0.08, 0.6, dark, -0.45 + i * 0.3, 2.22, 0);
    box(0.035, 0.6, 0.05, metal, -0.55 + i * 0.36, 1.6, 0.46);
  }
  box(1.1, 0.2, 0.8, dark, 0, 1.04, 0);
  for (let i = 0; i < 4; i++)
    pipe(
      [
        [-0.45 + i * 0.3, 1.86, -0.42],
        [-0.45 + i * 0.3, 1.6, -0.7],
        [0.6, 1.4, -0.72],
      ],
      metal,
      0.06,
    );
  const flywheel = new T.Group();
  flywheel.position.set(-0.78, 1.5, 0);
  scene.add(flywheel);
  const face = cyl(0.52, 0.12, metal, 0, 0, 0, flywheel);
  face.rotation.z = Math.PI / 2;
  for (let n = 0; n < 80; n++) {
    const a = (n * Math.PI) / 40,
      t = box(
        0.14,
        0.026,
        0.033,
        metal,
        0,
        Math.cos(a) * 0.53,
        Math.sin(a) * 0.53,
        flywheel,
      );
    t.rotation.x = a;
  }
  for (let n = 0; n < 6; n++) {
    const a = (n * Math.PI) / 3;
    cyl(
      0.06,
      0.13,
      dark,
      0,
      Math.cos(a) * 0.3,
      Math.sin(a) * 0.3,
      flywheel,
    ).rotation.z = Math.PI / 2;
  }
  const starter = cyl(0.15, 0.6, metal, -0.65, 1.05, 0.55);
  starter.rotation.z = Math.PI / 2;
  const solenoid = cyl(0.09, 0.3, dark, -0.65, 1.25, 0.55);
  solenoid.rotation.z = Math.PI / 2;
  const pinion = new T.Group();
  pinion.position.set(-0.9, 1.05, 0.45);
  scene.add(pinion);
  cyl(0.11, 0.13, orange, 0, 0, 0, pinion).rotation.z = Math.PI / 2;
  box(0.22, 1.2, 1.1, dark, 1.3, 1.58, 0);
  for (let i = 0; i < 12; i++)
    box(0.24, 0.025, 1, metal, 1.3, 1.1 + i * 0.08, 0);
  pipe(
    [
      [0.6, 1.8, 0.2],
      [1, 2, 0.3],
      [1.28, 1.96, 0.3],
    ],
    rubber,
    0.055,
  );
  pipe(
    [
      [1.28, 1.1, -0.3],
      [0.8, 0.9, -0.35],
      [0.5, 1.1, -0.35],
    ],
    rubber,
    0.055,
  );
  box(0.45, 0.6, 0.65, red, -1.4, 1.45, -0.3);
  cyl(0.09, 0.07, metal, -1.4, 1.79, -0.3);
  box(0.55, 0.38, 0.5, dark, -1.35, 0.5, 0.4);
  pipe(
    [
      [-1.35, 0.7, 0.4],
      [-1.4, 1, 0.6],
      [-0.7, 1.15, 0.55],
    ],
    red,
    0.025,
  );
  box(0.55, 0.8, 0.1, blue, 0, 1.75, 1.05);
  box(0.35, 0.2, 0.03, dark, 0, 1.93, 1.12);
  box(0.13, 0.15, 0.04, dark, -0.15, 1.62, 1.12);
  cyl(0.05, 0.035, green, 0.15, 1.64, 1.13).rotation.x = Math.PI / 2;
  // Cast housings, fasteners, intake runners and starter connections.
  const bronze = mat(0xb58a40, 0.8, 0.3),
    steel = mat(0x606b73, 0.8, 0.26);
  for (const x of [-0.48, -0.16, 0.16, 0.48]) {
    const bore = cyl(0.17, 0.56, metal, x, 1.55, 0.12);
    bore.rotation.x = Math.PI / 2;
    pipe(
      [
        [x, 1.91, 0.42],
        [x, 2, 0.7],
        [x, 1.72, 0.81],
        [x, 1.55, 0.65],
      ],
      rubber,
      0.085,
    );
    for (const z of [-0.37, 0.37]) {
      const bolt = cyl(0.034, 0.045, steel, x, 2.2, z);
      const washer = cyl(0.048, 0.015, metal, x, 2.18, z);
    }
  }
  for (const y of [1.25, 1.38, 1.51, 1.64, 1.77])
    box(1.28, 0.025, 0.92, metal, 0, y, 0);
  box(1.1, 0.12, 0.75, metal, 0, 1.15, 0);
  box(0.94, 0.18, 0.64, dark, 0, 0.98, 0);
  for (const x of [-0.9, -0.4]) {
    const cap = cyl(0.165, 0.055, steel, x, 1.05, 0.55);
    cap.rotation.z = Math.PI / 2;
  }
  for (let i = 0; i < 12; i++) {
    const a = (i * Math.PI) / 6,
      t = box(
        0.14,
        0.026,
        0.04,
        bronze,
        0,
        Math.cos(a) * 0.112,
        Math.sin(a) * 0.112,
        pinion,
      );
    t.rotation.x = a;
  }
  for (const x of [-0.82, -0.47]) {
    const band = cyl(0.153, 0.024, dark, x, 1.05, 0.55);
    band.rotation.z = Math.PI / 2;
  }
  const stud = cyl(0.035, 0.1, bronze, -0.52, 1.35, 0.55);
  pipe(
    [
      [-1.35, 0.7, 0.4],
      [-1.1, 0.7, 0.8],
      [-0.52, 1, 0.8],
      [-0.52, 1.37, 0.55],
    ],
    red,
    0.028,
  );
  box(0.12, 0.28, 0.45, metal, -0.94, 1.09, 0.54);
  const belt = cyl(0.29, 0.08, dark, 0.72, 1.45, 0);
  belt.rotation.z = Math.PI / 2;
  const hub = cyl(0.12, 0.095, metal, 0.72, 1.45, 0);
  hub.rotation.z = Math.PI / 2;
  const fan = new T.Group();
  fan.position.set(1.12, 1.6, 0);
  scene.add(fan);
  for (let n = 0; n < 7; n++) {
    const a = (n * Math.PI * 2) / 7;
    const blade = box(
      0.035,
      0.14,
      0.42,
      dark,
      0,
      Math.sin(a) * 0.24,
      Math.cos(a) * 0.24,
      fan,
    );
    blade.rotation.x = -a;
  }
  const fanHub = cyl(0.09, 0.16, metal, 1.12, 1.6, 0);
  fanHub.rotation.z = Math.PI / 2;
  for (const z of [-0.5, 0.5]) box(0.02, 1.12, 0.028, steel, 1.45, 1.58, z);
  const floor = add(
    new T.PlaneGeometry(12, 12),
    mat(0x132c3d, 0.1, 0.8),
    0,
    -0.12,
    0,
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  const grid = new T.GridHelper(10, 20, 0x345367, 0x1d3b4e);
  grid.position.y = -0.11;
  scene.add(grid);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFShadowMap;
  light.castShadow = true;
  light.shadow.mapSize.set(1024, 1024);
  light.shadow.camera.left = -4;
  light.shadow.camera.right = 4;
  light.shadow.camera.top = 4;
  light.shadow.camera.bottom = -4;
  scene.traverse((o) => {
    if (o.isMesh && o !== floor) o.castShadow = true;
  });
  const lamp = cyl(0.045, 0.03, orange, 0, 1.45, 1.13);
  lamp.rotation.x = Math.PI / 2;
  let angle = 0,
    last = 0,
    visible = true;
  function draw() {
    if (visible && host.clientWidth) renderer.render(scene, camera);
  }
  function resize() {
    if (!host.clientWidth || !host.clientHeight) return;
    renderer.setSize(host.clientWidth, host.clientHeight, false);
    camera.aspect = host.clientWidth / host.clientHeight;
    camera.updateProjectionMatrix();
    draw();
  }
  function focus(close = false) {
    orbit.target.set(close ? -0.8 : 0, close ? 1.27 : 1.35, close ? 0.3 : 0);
    camera.position.set(
      close ? -2.4 : -3.9,
      close ? 1.95 : 3.1,
      close ? 2.1 : 4.5,
    );
    orbit.update();
    host.dataset.camera = close ? "starter" : "whole";
    draw();
  }
  orbit.addEventListener("change", draw);
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  renderer.domElement.setAttribute("role", "img");
  renderer.domElement.setAttribute(
    "aria-label",
    "Virtual engine stand with starter, flywheel, radiator, tank and control panel",
  );
  focus();
  resize();
  return {
    focus,
    setTransparent(enabled) {
      for (const material of [shellMaterial, coverMaterial]) {
        material.transparent = enabled;
        material.opacity = enabled ? 0.22 : 1;
        material.depthWrite = !enabled;
      }
      host.dataset.transparent = String(enabled);
      draw();
    },
    update(r, reduced) {
      const t = r[0],
        dt = Math.max(0, Math.min(0.1, t - last));
      last = t;
      if (!reduced) {
        angle += ((r[8] * 2 * Math.PI) / 60) * dt;
        flywheel.rotation.x = angle;
        pinion.rotation.x = -angle * 5;
      }
      pinion.position.x = r[3] ? -0.83 : -1.02;
      lamp.material = r[3] ? orange : r[7] ? green : dark;
      draw();
    },
    setVisible(v) {
      visible = v;
      if (v) resize();
    },
    destroy() {
      observer.disconnect();
      orbit.dispose();
      scene.traverse((o) => {
        o.geometry?.dispose();
        o.material?.dispose();
      });
      env.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}
