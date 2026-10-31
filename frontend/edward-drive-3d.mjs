import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
export function createDriveScene(host){
 const renderer=new T.WebGLRenderer({antialias:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;host.append(renderer.domElement);
 const scene=new T.Scene();scene.background=new T.Color('#102338');const generator=new T.PMREMGenerator(renderer),room=new RoomEnvironment(),env=generator.fromScene(room,.04);scene.environment=env.texture;room.dispose();generator.dispose();
 scene.add(new T.HemisphereLight(0xcfe9ff,0x203341,2));const light=new T.DirectionalLight(0xffffff,3);light.position.set(4,6,4);scene.add(light);
 const camera=new T.PerspectiveCamera(38,1,.1,60),controls=new OrbitControls(camera,renderer.domElement);controls.enablePan=false;controls.minDistance=2.3;controls.maxDistance=16;controls.maxPolarAngle=Math.PI*.7;
 const mat=(color,metalness=.65,roughness=.3)=>new T.MeshStandardMaterial({color,metalness,roughness});const alu=mat(0xb6c4d1,.85,.28),dark=mat(0x244255),rubber=mat(0x111b25,.05,.8),copper=mat(0xbc7547,.8,.27),orange=mat(0xe69a39,.25),red=mat(0xbd4d52,.4),blue=mat(0x4aa7b6,.4);
 const add=(geometry,material,x,y,z,parent=scene)=>{const mesh=new T.Mesh(geometry,material);mesh.position.set(x,y,z);parent.add(mesh);return mesh;};
 const box=(w,h,d,m,x,y,z,p)=>add(new T.BoxGeometry(w,h,d),m,x,y,z,p);
 const cyl=(r,h,m,x,y,z,p)=>{const v=add(new T.CylinderGeometry(r,r,h,48),m,x,y,z,p);v.rotation.z=Math.PI/2;return v;};
 const pipe=(points,m,r=.035)=>add(new T.TubeGeometry(new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p))),48,r,8,false),m,0,0,0);
 box(8,.12,4,dark,0,-.45,0);box(1.8,.4,1.3,alu,-2.8,.1,0);box(1.65,.05,1.16,dark,-2.8,.33,0);
 for(let i=0;i<6;i++){box(.2,.08,.9,blue,-3.4+i*.24,.38,0);}
 box(.9,.36,1.1,dark,-1.1,.1,0);for(const z of [-.28,.28]){const c=add(new T.CylinderGeometry(.18,.18,.5,32),alu,-1.1,.5,z);box(.08,.06,.12,dark,-1.1,.78,z);}
 box(.8,.22,1.15,alu,.1,.2,0);for(let i=0;i<12;i++)box(.025,.12,1.1,dark,-.24+i*.06,.37,0);
 pipe([[-1.9,.15,.4],[-1.7,.3,.6],[-1.35,.3,.6]],orange);pipe([[-.7,.2,.4],[-.5,.35,.55],[-.3,.25,.4]],orange);
 const motorX=1.35;
 // Open metal sleeve, visible copper stator slots and a shaft-driven magnetic rotor.
 const shell=add(new T.CylinderGeometry(.66,.66,1.35,64,1,true,.45,Math.PI*1.4),alu,motorX,.3,0);shell.rotation.z=Math.PI/2;
 for(const x of [motorX-.68,motorX+.68]){const ring=add(new T.TorusGeometry(.6,.055,12,64),dark,x,.3,0);ring.rotation.y=Math.PI/2;}
 for(let n=0;n<18;n++){const a=n*Math.PI*2/18;const winding=box(1.16,.13,.14,copper,motorX,.3+Math.cos(a)*.5,Math.sin(a)*.5);winding.rotation.x=a;}
 const rotor=new T.Group();rotor.position.set(motorX,.3,0);scene.add(rotor);cyl(.31,1.2,dark,0,0,0,rotor);
 for(let n=0;n<8;n++){const a=n*Math.PI/4;const magnet=box(1.05,.1,.13,n%2?blue:red,0,Math.cos(a)*.33,Math.sin(a)*.33,rotor);magnet.rotation.x=a;}
 cyl(.085,3.15,alu,1.65,.3,0);box(.56,.7,.75,dark,2.55,.15,0);const gear=new T.Group();gear.position.set(2.55,.3,0);scene.add(gear);
 const gearFace=cyl(.4,.12,alu,0,0,0,gear);for(let n=0;n<18;n++){const a=n*Math.PI/9;const tooth=box(.15,.1,.1,alu,0,Math.cos(a)*.42,Math.sin(a)*.42,gear);tooth.rotation.x=a;}
 const wheels=[];for(const z of [-1.35,1.35]){const wheel=new T.Group();wheel.position.set(2.7,.05,z);scene.add(wheel);const tyre=add(new T.CylinderGeometry(.45,.45,.24,48),rubber,0,0,0,wheel);tyre.rotation.x=Math.PI/2;const hub=add(new T.CylinderGeometry(.29,.29,.26,32),alu,0,0,0,wheel);hub.rotation.x=Math.PI/2;for(let n=0;n<5;n++){const a=n*Math.PI*2/5;const spoke=box(.48,.04,.28,dark,0,0,0,wheel);spoke.rotation.z=a;}wheels.push(wheel);}
 const axle=add(new T.CylinderGeometry(.07,.07,2.7,24),alu,2.7,.05,0);axle.rotation.x=Math.PI/2;
 for(const [z,m] of [[-.22,red],[0,blue],[.22,orange]])pipe([[.4,.3,z],[.65,.6,z],[.8,.65,z]],m,.025);
 let visible=true,lastAngle=0;
 const draw=()=>{if(visible&&host.clientWidth&&host.clientHeight)renderer.render(scene,camera);};
 const resize=()=>{if(!host.clientWidth||!host.clientHeight)return;renderer.setSize(host.clientWidth,host.clientHeight,false);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();draw();};
 function focus(mode){if(mode==='motor'){controls.target.set(1.35,.3,0);camera.position.set(3.7,2.5,3.2);}else{controls.target.set(0,.1,0);camera.position.set(6,4.5,8);}controls.update();draw();}
 controls.addEventListener('change',draw);const observer=new ResizeObserver(resize);observer.observe(host);renderer.domElement.setAttribute('aria-label','3D battery, DC link, inverter, motor cutaway, reduction and wheels');renderer.domElement.setAttribute('role','img');
 focus('drive');resize();return{update(row,config,reduced){lastAngle=reduced?0:row?.motor_states_4||0;rotor.rotation.x=lastAngle;gear.rotation.x=-lastAngle/config.gear;for(const wheel of wheels)wheel.rotation.z=lastAngle/config.gear;draw();},focus,setVisible(v){visible=v;if(v)resize();},destroy(){observer.disconnect();controls.dispose();scene.traverse(o=>{o.geometry?.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material])m?.dispose();});env.dispose();renderer.dispose();renderer.domElement.remove();}};
}
