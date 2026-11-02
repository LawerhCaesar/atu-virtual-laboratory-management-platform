// A presentation adapter only. Never changes the solver or invents hydraulic outputs.
export const MODES={0:'No active intervention',1:'ABS APPLY',2:'ABS HOLD',3:'ABS RELEASE','-1':'TCS RESTORE','-2':'TCS HOLD','-3':'TCS REDUCE'};
export function visualState(result,index){
 const row=result.samples[index],feedback=result.samples[Math.max(0,index-1)],c=result.config;
 const sampleTime=feedback.timeS,brake=sampleTime<c.brakeStepTimeS?c.brakeBefore:c.brakeAfter;
 let throttle=sampleTime<c.throttleStepTimeS?c.throttleBefore:c.throttleAfter;if(brake>.01)throttle=0;
 const mode=row.controllerMode;
 return {row,feedback,roadMu:c.roadMu,vehicleMassKg:c.vehicleMassKg,mode,modeLabel:MODES[mode],wheelAngleRad:row.wheelAngleRad,brakeFraction:c.maxBrakeTorqueNm?row.brakeTorqueNm/c.maxBrakeTorqueNm:0,driveFraction:c.maxDriveTorqueNm?row.driveTorqueNm/c.maxDriveTorqueNm:0,requestedBrakeNm:brake*c.maxBrakeTorqueNm,requestedDriveNm:throttle*c.maxDriveTorqueNm,pumpIllustration:mode===3,hydraulicCue:mode===1?'Build brake torque':mode===2?'Hold brake torque':mode===3?'Release brake torque':row.brakeTorqueNm>0?'Direct brake request':'No brake demand',driveCue:mode===-3?'Reduce drive torque':mode===-2?'Hold drive torque':mode===-1?'Restore drive torque':'Direct drive request',contactCue:row.brakeSlip>.2?'Braking slip above release threshold':row.driveSlip>.18?'Drive slip above reduction threshold':'Below upper intervention thresholds',sensorOmegaRadS:feedback.wheelPeripheralSpeedKph/3.6/c.wheelRadiusM,feedbackTimeS:feedback.timeS,outputTimeS:row.timeS};
}
