/** Planar lateral-yaw bicycle model. State order: beta, r, psi, X, Y. */
/** @typedef {{speedKmh:number,baseMassKg:number,payloadKg:number,yawInertiaKgM2:number,cgToFrontM:number,cgToRearM:number,frontCorneringStiffnessNPerRad:number,rearCorneringStiffnessNPerRad:number,steeringRatio:number}} VehicleParameters */
/** @typedef {{profile:'step'|'sine'|'doublet',steeringAmplitudeDeg:number,stepTimeS:number,durationS:number,timeStepS:number,sineFrequencyHz:number,doubletHalfDurationS:number}} ScenarioParameters */
/** @typedef {{timeS:number,roadWheelAngleDeg:number,steeringWheelAngleDeg:number,yawRateDegPerS:number,sideslipDeg:number,lateralAccelerationMps2:number,lateralAccelerationG:number,turningRadiusM:number,headingDeg:number,xM:number,yM:number,frontLateralForceN:number,rearLateralForceN:number}} SimulationSample */
/** @typedef {{moduleId:string,moduleVersion:string,parameters:VehicleParameters,scenario:ScenarioParameters,outputVectorOrder:string[],samples:SimulationSample[],final:SimulationSample,platformVector:number[],warnings:string[],effective:{speedMps:number,totalMassKg:number,wheelbaseM:number},solver:{method:string,outputTimeStepS:number,internalSubsteps:number}} SimulationResult */
export const MODULE_ID='vehicle-steering-response', MODULE_VERSION='1.0.0';
export const LIMITS=Object.freeze({gravityMps2:9.81,radiusEpsilon:0.001,minimumSpeedMps:.5,minimumMassKg:100,maximumMassKg:50000,maximumSamples:120001,maximumIntegrationSteps:2000000});
export const VEHICLE_FIELDS=[
 ['speedKmh','Vehicle speed','km/h',60,0,160,5,'Operating condition','Constant longitudinal speed; values below 1.8 km/h use the reference minimum 0.5 m/s.'],
 ['baseMassKg','Base vehicle mass','kg',1500,0,3500,50,'Operating condition','Added to payload; the solver limits total mass to 100–50,000 kg.'],
 ['payloadKg','Payload','kg',0,0,1000,25,'Operating condition','Additional mass; inertia and axle geometry remain independent inputs.'],
 ['yawInertiaKgM2','Yaw moment of inertia','kg·m²',2500,100,8000,100,'Geometry and dynamics','Resistance to yaw acceleration; must be positive.'],
 ['cgToFrontM','CG to front axle','m',1.2,.1,3,.05,'Geometry and dynamics','Positive distance from centre of gravity to the front axle.'],
 ['cgToRearM','CG to rear axle','m',1.6,.1,3,.05,'Geometry and dynamics','Positive distance from centre of gravity to the rear axle; wheelbase is a + b.'],
 ['frontCorneringStiffnessNPerRad','Front axle cornering stiffness','N/rad',80000,10000,200000,5000,'Geometry and dynamics','Equivalent front-axle lateral force per radian of tyre slip; linear with no saturation.'],
 ['rearCorneringStiffnessNPerRad','Rear axle cornering stiffness','N/rad',80000,10000,200000,5000,'Geometry and dynamics','Equivalent rear-axle lateral force per radian of tyre slip; linear with no saturation.'],
 ['steeringRatio','Steering ratio','ratio',16,1,30,1,'Geometry and dynamics','Road-wheel angle multiplied by this ratio gives steering-wheel angle.'],
];
export const SCENARIO_FIELDS=[
 ['steeringAmplitudeDeg','Road-wheel steering amplitude','deg',1,-5,5,.1,'Steering scenario','Positive and negative steering are supported; keep angles small for the linear model.'],
 ['stepTimeS','Steering application time','s',1,0,10,.1,'Steering scenario','Within the simulation duration; input is zero before this time.'],
 ['durationS','Simulation duration','s',10,.1,60,1,'Steering scenario','Positive duration, subject to the displayed sample and numerical-work limits.'],
 ['timeStepS','Output time step','s',.01,.001,.05,.001,'Steering scenario','RK4 output interval, 0.001–0.05 s. Stiff cases use disclosed deterministic internal subdivisions.'],
 ['sineFrequencyHz','Sine frequency','Hz',.25,.01,2,.05,'Steering scenario','Frequency after application time; used for the sine profile only.'],
 ['doubletHalfDurationS','Doublet half duration','s',1,.05,5,.1,'Steering scenario','Positive then negative steering for this duration each; used for the doublet profile only.'],
];
export const DEFAULT_VEHICLE=Object.freeze(Object.fromEntries(VEHICLE_FIELDS.map(([key,,,value])=>[key,value])));
export const DEFAULT_SCENARIO=Object.freeze({profile:'step',...Object.fromEntries(SCENARIO_FIELDS.map(([key,,,value])=>[key,value]))});
export const OUTPUTS=[['yawRateDegPerS','Yaw rate','deg/s'],['sideslipDeg','Sideslip angle','deg'],['lateralAccelerationMps2','Lateral acceleration','m/s²'],['lateralAccelerationG','Lateral acceleration','g'],['turningRadiusM','Turning radius','m'],['headingDeg','Heading angle','deg'],['xM','X position','m'],['yM','Y position','m'],['frontLateralForceN','Front lateral force','N'],['rearLateralForceN','Rear lateral force','N'],['steeringWheelAngleDeg','Steering-wheel angle','deg']];
export const OUTPUT_VECTOR_ORDER=Object.freeze(OUTPUTS.map(([key])=>key));
export const platformVector=sample=>OUTPUT_VECTOR_ORDER.map(key=>sample[key]);
const DEG=Math.PI/180, RAD=180/Math.PI;
export function validateInputs(vehicle,scenario) {
 const errors={};
 for(const [key,label] of [...VEHICLE_FIELDS,...SCENARIO_FIELDS]) {const source=key in DEFAULT_VEHICLE?vehicle:scenario;if(!Number.isFinite(source[key])) errors[key]=`${label} must be a finite number.`;}
 for(const key of ['speedKmh','baseMassKg','payloadKg']) if(vehicle[key]<0)errors[key]='Must be non-negative.';
 for(const key of ['yawInertiaKgM2','cgToFrontM','cgToRearM','frontCorneringStiffnessNPerRad','rearCorneringStiffnessNPerRad','steeringRatio']) if(vehicle[key]<=0) errors[key]='Must be greater than zero.';
 if(scenario.durationS<=0)errors.durationS='Duration must be greater than zero.';
 if(scenario.timeStepS<.001||scenario.timeStepS>.05)errors.timeStepS='Time step must be 0.001–0.05 s.';
 if(scenario.stepTimeS<0||scenario.stepTimeS>scenario.durationS)errors.stepTimeS='Application time must be within the simulation duration.';
 if(!['step','sine','doublet'].includes(scenario.profile))errors.profile='Choose a supported steering profile.';
 if(scenario.sineFrequencyHz<=0)errors.sineFrequencyHz='Frequency must be positive.';
 if(scenario.doubletHalfDurationS<=0)errors.doubletHalfDurationS='Half duration must be positive.';
 if(Math.ceil(scenario.durationS/scenario.timeStepS)+1>LIMITS.maximumSamples)errors.durationS=`Choose duration and time step giving at most ${LIMITS.maximumSamples.toLocaleString()} samples.`;
 return errors;
}
export function steeringAtTime(t,s) {
 if(t<s.stepTimeS)return 0;
 if(s.profile==='sine')return s.steeringAmplitudeDeg*Math.sin(2*Math.PI*s.sineFrequencyHz*(t-s.stepTimeS));
 if(s.profile==='doublet')return t<s.stepTimeS+s.doubletHalfDurationS?s.steeringAmplitudeDeg:t<s.stepTimeS+2*s.doubletHalfDurationS?-s.steeringAmplitudeDeg:0;
 return s.steeringAmplitudeDeg;
}
function response(t,state,p,s) {
 const [beta,r,psi]=state, deltaDeg=steeringAtTime(t,s), alphaF=deltaDeg*DEG-beta-p.a*r/p.U, alphaR=-beta+p.b*r/p.U;
 const front=p.Cf*alphaF,rear=p.Cr*alphaR;
 return {front,rear,deltaDeg,derivative:[(front+rear)/(p.m*p.U)-r,(p.a*front-p.b*rear)/p.Iz,r,p.U*Math.cos(psi+beta),p.U*Math.sin(psi+beta)]};
}
const plus=(state,d,scale)=>state.map((v,i)=>v+d[i]*scale);
function rk4(t,state,dt,p,s) {
 const k1=response(t,state,p,s).derivative,k2=response(t+dt/2,plus(state,k1,dt/2),p,s).derivative,k3=response(t+dt/2,plus(state,k2,dt/2),p,s).derivative,k4=response(t+dt,plus(state,k3,dt),p,s).derivative;
 return state.map((v,i)=>v+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6);
}
function sampleFromState(timeS,state,p,s) {
 const [beta,r,psi,xM,yM]=state,{front,rear,deltaDeg}=response(timeS,state,p,s),ay=(front+rear)/p.m;
 return {timeS,roadWheelAngleDeg:deltaDeg,steeringWheelAngleDeg:deltaDeg*p.ratio,yawRateDegPerS:r*RAD,sideslipDeg:beta*RAD,lateralAccelerationMps2:ay,lateralAccelerationG:ay/LIMITS.gravityMps2,turningRadiusM:p.U/(Math.abs(r)+LIMITS.radiusEpsilon),headingDeg:psi*RAD,xM,yM,frontLateralForceN:front,rearLateralForceN:rear};
}
/** @param {VehicleParameters} vehicle @param {ScenarioParameters} scenario @returns {SimulationResult} */
export function simulateSteeringResponse(vehicle=DEFAULT_VEHICLE,scenario=DEFAULT_SCENARIO) {
 const v={...vehicle},s={...DEFAULT_SCENARIO,...scenario},errors=validateInputs(v,s);if(Object.keys(errors).length)throw Object.assign(new Error(Object.values(errors).join(' ')),{fields:errors});
 const p={U:Math.max(v.speedKmh/3.6,LIMITS.minimumSpeedMps),m:Math.max(LIMITS.minimumMassKg,Math.min(LIMITS.maximumMassKg,v.baseMassKg+v.payloadKg)),Iz:v.yawInertiaKgM2,a:v.cgToFrontM,b:v.cgToRearM,Cf:v.frontCorneringStiffnessNPerRad,Cr:v.rearCorneringStiffnessNPerRad,ratio:v.steeringRatio};
 const warnings=[];
 if(p.U!==v.speedKmh/3.6)warnings.push(`Speed protection active: ${v.speedKmh} km/h entered; calculation uses ${p.U} m/s (1.8 km/h).`);
 if(p.m!==v.baseMassKg+v.payloadKg)warnings.push(`Mass protection active: calculation uses ${p.m} kg.`);
 if(Math.abs(s.steeringAmplitudeDeg)>5)warnings.push('Large steering input exceeds the suggested small-angle study range; tyres remain linear without saturation.');
 // Deterministic fixed subdivisions keep the reference low-speed protection usable
 // when the selected output interval is too coarse for the lateral subsystem.
 const norm=Math.max((p.Cf+p.Cr)/(p.m*p.U)+Math.abs((-p.a*p.Cf+p.b*p.Cr)/(p.m*p.U*p.U)-1),Math.abs((-p.a*p.Cf+p.b*p.Cr)/p.Iz)+(p.a*p.a*p.Cf+p.b*p.b*p.Cr)/(p.Iz*p.U));
 const substeps=Math.max(1,Math.ceil(s.timeStepS*norm/1.5));
 if(!Number.isFinite(norm)||Math.ceil(s.durationS/s.timeStepS)*substeps>LIMITS.maximumIntegrationSteps)throw new Error('This parameter combination requires too much numerical work. Increase inertia/mass or speed, reduce stiffness or duration, and try again.');
 if(substeps>1)warnings.push(`RK4 uses ${substeps} fixed internal subdivisions per output interval for numerical stability; output interval remains ${s.timeStepS} s.`);
 let state=[0,0,0,0,0]; const samples=[sampleFromState(0,state,p,s)],count=Math.ceil(s.durationS/s.timeStepS);
 for(let i=0;i<count;i++) {
  const t=i*s.timeStepS,dt=Math.min(s.timeStepS,s.durationS-t);if(dt<=0)break;
  for(let j=0;j<substeps;j++)state=rk4(t+j*dt/substeps,state,dt/substeps,p,s);
  const row=sampleFromState(Math.min(s.durationS,(i+1)*s.timeStepS),state,p,s);
  if(Object.values(row).some(value=>!Number.isFinite(value)))throw new Error('Numerical calculation exceeded its finite range. Reduce the time step or review the vehicle parameters.');
  samples.push(row);
 }
 const final=samples.at(-1);
 if(Math.abs(final.sideslipDeg)>5||Math.abs(final.lateralAccelerationG)>.5)warnings.push('Response is outside the suggested gentle-handling range. This linear model does not calculate grip saturation.');
 return {moduleId:MODULE_ID,moduleVersion:MODULE_VERSION,parameters:v,scenario:s,outputVectorOrder:[...OUTPUT_VECTOR_ORDER],samples,final,platformVector:platformVector(final),warnings,effective:{speedMps:p.U,totalMassKg:p.m,wheelbaseM:p.a+p.b},solver:{method:'RK4',outputTimeStepS:s.timeStepS,internalSubsteps:substeps}};
}
export function resultCsv(result) {const keys=['timeS','roadWheelAngleDeg',...OUTPUT_VECTOR_ORDER];return [keys.join(','),...result.samples.map(row=>keys.map(key=>row[key]).join(','))].join('\r\n');}
export function sampleAtTime(result,timeS) {
 const rows=result.samples;let low=0,high=rows.length-1;
 while(low<high){const middle=Math.floor((low+high)/2);if(rows[middle].timeS<timeS)low=middle+1;else high=middle;}
 return low>0&&Math.abs(rows[low-1].timeS-timeS)<=Math.abs(rows[low].timeS-timeS)?rows[low-1]:rows[low];
}
