// Wheel-Slip ABS/TCS, specification-derived educational model. SI units internally.
export const MODEL_VERSION = "1.0.0-spec";
export const FIELDS = [
  ["durationS", "Simulation duration", "s", 12, 2, 60, 1, "Length of the simulated scenario."],
  ["brakeStepTimeS", "Brake step time", "s", 1, 0, 60, .1, "Time when brake demand changes."],
  ["brakeBefore", "Brake demand before step", "ratio", 0, 0, 1, .05, "Initial fraction of maximum brake torque."],
  ["brakeAfter", "Brake demand after step", "ratio", 1, 0, 1, .05, "Fraction of maximum brake torque after the step."],
  ["throttleStepTimeS", "Throttle step time", "s", 1, 0, 60, .1, "Time when throttle demand changes."],
  ["throttleBefore", "Throttle demand before step", "ratio", 0, 0, 1, .05, "Initial fraction of maximum drive torque."],
  ["throttleAfter", "Throttle demand after step", "ratio", 0, 0, 1, .05, "Fraction of maximum drive torque after the step."],
  ["roadMu", "Road friction coefficient", "ratio", .35, .05, 1.2, .05, "Scales the available tyre-road friction."],
  ["initialSpeedKph", "Initial vehicle speed", "km/h", 80, 0, 160, 5, "Vehicle and wheel start at this speed without slip."],
  ["vehicleMassKg", "Vehicle mass", "kg", 1500, 500, 3500, 50, "Sets longitudinal inertia and equal tyre loading."],
  ["wheelRadiusM", "Effective wheel radius", "m", .31, .15, .5, .01, "Converts angular speed into wheel peripheral speed."],
  ["wheelInertiaKgm2", "Wheel rotational inertia", "kg·m²", 1.2, .05, 5, .05, "Resistance of the represented wheel to angular acceleration."],
  ["maxBrakeTorqueNm", "Maximum brake torque per wheel", "N·m", 1800, 0, 5000, 100, "Maximum brake torque requested on the represented wheel."],
  ["maxDriveTorqueNm", "Maximum drive torque per wheel", "N·m", 1200, 0, 5000, 100, "Maximum drive torque requested on the represented wheel."],
];
export const DEFAULTS = Object.freeze({...Object.fromEntries(FIELDS.map(([key,,,value]) => [key,value])), timeStepS:.001, absEnabled:true, tcsEnabled:true});
const launch = {brakeAfter:0, throttleAfter:1, initialSpeedKph:5, roadMu:.25};
export const PRESETS = Object.freeze({
  "ABS emergency braking": {...DEFAULTS},
  "Braking without ABS": {...DEFAULTS, absEnabled:false},
  "TCS low-friction launch": {...DEFAULTS, ...launch},
  "Launch without TCS": {...DEFAULTS, ...launch, tcsEnabled:false},
});
const clamp=(x,lo,hi)=>Math.min(hi,Math.max(lo,x));
export function validateConfig(config) {
  const errors={};
  for (const [key,label,unit,,min,max] of FIELDS) {
    const value=config[key];
    if (typeof value!=="number" || !Number.isFinite(value) || value<min || value>max)
      errors[key]=`${label} must be between ${min} and ${max} ${unit}.`;
  }
  for (const key of ["brakeStepTimeS","throttleStepTimeS"]) if (Number.isFinite(config[key]) && config[key]>config.durationS) errors[key]="Step time cannot exceed the simulation duration.";
  if (config.timeStepS!==.001) errors.timeStepS="The reference integration step is fixed at 0.001 s.";
  if (Number.isFinite(config.durationS) && Math.abs(config.durationS*1000-Math.round(config.durationS*1000))>1e-7) errors.durationS="Duration must be a whole number of 0.001 s steps.";
  for (const key of ["absEnabled","tcsEnabled"]) if(typeof config[key]!=="boolean") errors[key]="Choose on or off.";
  return errors;
}
/** Fixed 1 ms Euler model from the supplied task. The source SLX was not provided. */
export function simulate(config) {
  const errors=validateConfig(config);
  if (Object.keys(errors).length) throw new Error(Object.values(errors).join(" "));
  const c={...config}, dt=.001, m=Math.max(c.vehicleMassKg,100), R=Math.max(c.wheelRadiusM,.05), J=Math.max(c.wheelInertiaKgm2,.05), mu=clamp(c.roadMu,.05,1.2), load=m*9.81/4;
  let V=Math.max(c.initialSpeedKph/3.6,0), omega=V/R, brakeTorque=0, driveTorque=0, distance=0, wheelAngleRad=0, absMode=0, tcsMode=0;
  const samples=[], warnings=[], metrics={finalDistanceM:0,stoppingTimeS:null,stoppingDistanceM:null,peakBrakeSlip:0,peakDriveSlip:0,peakAbsTyreForceN:0,absActiveTimeS:0,tcsActiveTimeS:0,finalVehicleSpeedKph:0,finalWheelSpeedKph:0};
  const slip=()=>{const s=(V-R*omega)/Math.max(Math.abs(V),Math.abs(R*omega),.5);return [s,Math.max(s,0),Math.max(-s,0)];};
  const record=(t,force)=>{const [,bs,ds]=slip(), mode=absMode>0?absMode:tcsMode>0?-tcsMode:0;
    const row={timeS:t,vehicleSpeedKph:V*3.6,wheelPeripheralSpeedKph:omega*R*3.6,brakeSlip:bs,driveSlip:ds,brakeTorqueNm:brakeTorque,driveTorqueNm:driveTorque,tyreForceN:force,controllerMode:mode,absActive:absMode>0,tcsActive:tcsMode>0,distanceM:distance,wheelAngleRad};
    if(Object.values(row).some(v=>typeof v==="number"&&!Number.isFinite(v)))throw new Error("The model produced a non-finite value.");
    samples.push(row); metrics.peakBrakeSlip=Math.max(metrics.peakBrakeSlip,bs); metrics.peakDriveSlip=Math.max(metrics.peakDriveSlip,ds); metrics.peakAbsTyreForceN=Math.max(metrics.peakAbsTyreForceN,Math.abs(force));
    if(metrics.stoppingTimeS===null && row.vehicleSpeedKph<=.1) {metrics.stoppingTimeS=t;metrics.stoppingDistanceM=distance;}
  };
  record(0,0);
  const steps=Math.round(c.durationS/dt);
  for(let i=0;i<steps;i++) {
    const t=i*dt, brake=clamp(t<c.brakeStepTimeS?c.brakeBefore:c.brakeAfter,0,1);
    let throttle=clamp(t<c.throttleStepTimeS?c.throttleBefore:c.throttleAfter,0,1);
    if(brake>.01) throttle=0;
    const reqBrake=brake*Math.max(c.maxBrakeTorqueNm,0), reqDrive=throttle*Math.max(c.maxDriveTorqueNm,0);
    const [signed,bs,ds]=slip();
    if(c.absEnabled&&brake>.001&&V>1) {
      if(bs>.20){absMode=3;brakeTorque-=45000*dt;} else if(bs<.12){absMode=1;brakeTorque+=24000*dt;} else absMode=2;
    } else {absMode=0;brakeTorque=reqBrake;}
    brakeTorque=clamp(brakeTorque,0,reqBrake);
    if(c.tcsEnabled&&throttle>.001&&brake<.001) {
      if(ds>.18){tcsMode=3;driveTorque-=35000*dt;} else if(ds<.10){tcsMode=1;driveTorque+=18000*dt;} else tcsMode=2;
    } else {tcsMode=0;driveTorque=reqDrive;}
    driveTorque=clamp(driveTorque,0,reqDrive);
    const s=Math.min(Math.abs(signed),1.5), shape=clamp((1.28*(1-Math.exp(-23.99*s))-.52*s)/1.10,0,1);
    const force=s<1e-6?0:-Math.sign(signed)*mu*load*shape;
    let resistance=.015*m*9.81+.5*1.225*.65*V*V;
    if(V<.05&&force<=0)resistance=0;
    const acceleration=(4*force-resistance)/m, angular=(driveTorque-brakeTorque-force*R)/J;
    V=Math.max(V+dt*acceleration,0); omega=Math.max(omega+dt*angular,0);
    if(V<.02&&brake>.10){V=0;omega=0;brakeTorque=0;}
    distance+=dt*V; wheelAngleRad+=dt*omega;
    if(absMode>0)metrics.absActiveTimeS+=dt;
    if(tcsMode>0)metrics.tcsActiveTimeS+=dt;
    record((i+1)*dt,force);
  }
  const last=samples.at(-1); metrics.finalDistanceM=distance; metrics.finalVehicleSpeedKph=last.vehicleSpeedKph; metrics.finalWheelSpeedKph=last.wheelPeripheralSpeedKph;
  warnings.push("The written reference uses wheel acceleration (drive torque − brake torque − tyre force × radius); this sign convention has not been validated against the missing Simulink model or a physical vehicle.");
  if(c.brakeAfter>.01 && c.throttleAfter>.001 || c.brakeBefore>.01 && c.throttleBefore>.001) warnings.push("Brake demand takes priority over throttle when brake exceeds 0.01.");
  return {config:c,samples,metrics,warnings,modelVersion:MODEL_VERSION};
}
