/** Educational operating-point allocation from Codex_BrakeLab_Prompt.md.
 * No DOM, framework, hardware, time integration or network dependency.
 * @typedef {{brakeDemand:number, vehicleMassKg:number, vehicleSpeedKph:number,
 * batterySocPct:number, batteryTempC:number, batteryVoltageV:number,
 * chargeCurrentLimitA:number, chargePowerLimitKw:number, motorRegenTorqueLimitNm:number,
 * motorRegenPowerLimitKw:number, regenEnabled:boolean|number}} BrakeAllocationInputs
 * @typedef {{maxServiceDecelMps2:number,wheelRadiusM:number,gearRatio:number,
 * drivetrainEfficiency:number,regenEfficiency:number,speedCutoffMps:number,
 * fullRegenSpeedMps:number,socDeratePct:number,socStopPct:number,coldCutoffC:number,
 * coldFullC:number,hotFullC:number,hotCutoffC:number,minimumSpeedMps:number,forceEpsilonN:number}} BrakeAllocationCalibration
 * @typedef {'NO_BRAKING'|'REGEN_DISABLED'|'LOW_SPEED'|'DRIVER_DEMAND'|'MOTOR_TORQUE'|'MOTOR_POWER'|'BATTERY_SOC'|'BATTERY_TEMPERATURE'|'BATTERY_CURRENT'|'BATTERY_POWER'|'BATTERY_ACCEPTANCE'} ActiveLimitCode
 * @typedef {{requestedDecelerationMps2:number,requestedForceN:number,requestedWheelTorqueNm:number,
 * vehicleSpeedMps:number,wheelSpeedRpm:number,motorSpeedRpm:number,speedFactor:number,
 * socFactor:number,temperatureFactor:number,currentDerivedChargePowerKw:number,baseChargePowerKw:number,
 * allowedBatteryPowerKw:number,torqueForceLimitN:number,powerForceLimitN:number,batteryForceLimitN:number,
 * regenerativeForceN:number,frictionForceN:number,regenerativeWheelTorqueNm:number,frictionWheelTorqueNm:number,
 * mechanicalRegenPowerKw:number,batteryChargePowerKw:number,regenerativeCurrentA:number,
 * regenerativePercent:number,frictionPercent:number,forceBalanceResidualN:number,activeLimitCode:ActiveLimitCode,
 * activeLimitLabel:string,warnings:string[],visual:{stopTimeEstimateS:number,stopDistanceEstimateM:number,
 * animationDurationS:number,regenIntensity01:number,frictionHeatIntensity01:number,batteryChargeIntensity01:number}} BrakeAllocationResult
 */
export const MODULE_ID = "brakelab";
export const MODULE_VERSION = "1.0.0";
export const DEFAULT_BRAKE_CALIBRATION = Object.freeze({maxServiceDecelMps2:3.5,
  wheelRadiusM:.31, gearRatio:9, drivetrainEfficiency:.92, regenEfficiency:.88,
  speedCutoffMps:2, fullRegenSpeedMps:5, socDeratePct:80, socStopPct:95,
  coldCutoffC:-5, coldFullC:15, hotFullC:40, hotCutoffC:55, minimumSpeedMps:.1, forceEpsilonN:1});
export const FIELDS = [
  ["brakeDemand","Brake demand","ratio",.4,0,1,.05,"Driver and vehicle","Fraction of the 3.5 m/s² maximum service deceleration. The calculation normalises demand to 0–1 and warns about raw out-of-range entries."],
  ["vehicleMassKg","Vehicle mass","kg",1500,800,3500,50,"Driver and vehicle","Mass multiplies requested deceleration to produce the required braking force. It must be positive."],
  ["vehicleSpeedKph","Vehicle speed","km/h",60,0,160,1,"Driver and vehicle","Sets wheel/motor speed, low-speed fade and power-derived force limits. Negative entries are calculated as zero with a warning."],
  ["batterySocPct","Battery SOC","%",50,0,100,1,"Battery","State of charge is an independent input, not an evolving state. Acceptance derates above 80% and reaches zero at 95%."],
  ["batteryTempC","Battery temperature","°C",25,-15,65,1,"Battery","Full acceptance is 15–40 °C. It falls to zero at −5 °C and 55 °C. This model does not simulate battery heating."],
  ["batteryVoltageV","Battery voltage","V",350,200,800,10,"Battery","Converts the charging-current limit into power and calculated battery power into current. It must be positive."],
  ["chargeCurrentLimitA","Charge-current limit","A",120,20,400,10,"Battery","Maximum battery charging current; voltage × current gives the competing charging-power limit. Zero prevents recovery."],
  ["chargePowerLimitKw","Charge-power limit","kW",45,5,200,5,"Battery","Direct charging-power ceiling before SOC and temperature derating. The smaller of this and voltage × current controls base acceptance."],
  ["motorRegenTorqueLimitNm","Motor regenerative-torque limit","N·m",180,20,500,10,"Motor and regenerative system","Motor torque is multiplied by gear ratio, drivetrain efficiency and low-speed factor, then divided by wheel radius to obtain a force limit."],
  ["motorRegenPowerLimitKw","Motor regenerative-power limit","kW",50,5,250,5,"Motor and regenerative system","Motor power is converted to a regenerative-force limit using speed. Friction braking supplies any remaining requested force."],
  ["regenEnabled","Regeneration Enabled","",true,0,1,1,"Motor and regenerative system","Off sends all requested braking force to friction. The reusable function also accepts a finite numeric enable factor, clamped to 0–1, as in the reference."],
].map(([key,label,unit,value,min,max,step,group,purpose])=>({key,label,unit,value,min,max,step,group,purpose}));
export const DEFAULT_BRAKE_INPUTS = Object.freeze(Object.fromEntries(FIELDS.map(f=>[f.key,f.value])));
// Display metadata only; all values are calculated by the pure function below.
export const OUTPUTS = [
  ["requestedDecelerationMps2","Requested deceleration","m/s²",2],
  ["requestedForceN","Requested force","N",1], ["requestedWheelTorqueNm","Requested wheel torque","N·m",1],
  ["vehicleSpeedMps","Operating-point speed","m/s",2], ["wheelSpeedRpm","Wheel speed","rpm",1], ["motorSpeedRpm","Motor speed","rpm",1],
  ["speedFactor","Speed factor","ratio",3], ["socFactor","SOC factor","ratio",3], ["temperatureFactor","Temperature factor","ratio",3],
  ["currentDerivedChargePowerKw","Current-derived charge power","kW",2], ["baseChargePowerKw","Base charge power","kW",2],
  ["allowedBatteryPowerKw","Allowed battery power","kW",2], ["torqueForceLimitN","Torque force limit","N",1],
  ["powerForceLimitN","Power force limit","N",1], ["batteryForceLimitN","Battery force limit","N",1],
  ["regenerativeForceN","Regenerative force","N",1], ["frictionForceN","Friction force","N",1],
  ["regenerativeWheelTorqueNm","Regenerative wheel torque","N·m",1], ["frictionWheelTorqueNm","Friction wheel torque","N·m",1],
  ["mechanicalRegenPowerKw","Mechanical regenerative power","kW",2], ["batteryChargePowerKw","Battery charging power","kW",2],
  ["regenerativeCurrentA","Regenerative current","A",2], ["regenerativePercent","Regenerative share","%",1],
  ["frictionPercent","Friction share","%",1], ["forceBalanceResidualN","Force-balance residual","N",6],
];
export const clamp = (x,a,b)=>Math.min(b,Math.max(a,x));

export function validateInputs(inputs) {
  const errors = {}, warnings = [];
  for (const f of FIELDS) {
    const value=inputs[f.key];
    if (f.key === "regenEnabled") {
      if (typeof value !== "boolean" && !Number.isFinite(value)) errors[f.key]="Use a boolean or finite numeric enable factor.";
      else if (typeof value === "number" && (value<0 || value>1)) warnings.push("Regeneration enable is normalised to 0–1 for calculation.");
    } else if (!Number.isFinite(value)) errors[f.key]="Enter a finite number.";
    else if (value<f.min || value>f.max) warnings.push(`${f.label} is outside the suggested educational range ${f.min}–${f.max} ${f.unit}.`);
  }
  for (const key of ["vehicleMassKg","batteryVoltageV"]) if (inputs[key]<=0) errors[key]="Must be greater than zero.";
  for (const key of ["chargeCurrentLimitA","chargePowerLimitKw","motorRegenTorqueLimitNm","motorRegenPowerLimitKw"])
    if (inputs[key]<0) errors[key]="Must not be negative; zero is allowed.";
  return {valid:!Object.keys(errors).length,errors,warnings};
}

function validateCalibration(c) {
  for (const key of Object.keys(DEFAULT_BRAKE_CALIBRATION)) if (!Number.isFinite(c[key])) throw new Error(`${key} must be finite.`);
  for (const key of ["maxServiceDecelMps2","wheelRadiusM","gearRatio","minimumSpeedMps","forceEpsilonN"])
    if (c[key]<=0) throw new Error(`${key} must be positive.`);
  for (const key of ["drivetrainEfficiency","regenEfficiency"]) if (c[key]<=0 || c[key]>1) throw new Error(`${key} must be in (0,1].`);
  if (c.speedCutoffMps<0 || c.fullRegenSpeedMps<=c.speedCutoffMps) throw new Error("Speed thresholds must be ordered: 0 ≤ cut-off < full regeneration.");
  if (c.socDeratePct<0 || c.socStopPct>100 || c.socStopPct<=c.socDeratePct) throw new Error("SOC thresholds must be ordered within 0–100%.");
  if (!(c.coldCutoffC<c.coldFullC && c.coldFullC<=c.hotFullC && c.hotFullC<c.hotCutoffC)) throw new Error("Cold/hot temperature thresholds must be ordered.");
}

/** @param {BrakeAllocationInputs} rawInputs
 * @param {BrakeAllocationCalibration} calibration
 * @returns {BrakeAllocationResult} */
export function calculateBrakeAllocation(rawInputs, calibration=DEFAULT_BRAKE_CALIBRATION) {
  const validation=validateInputs(rawInputs);
  if (!validation.valid) throw new Error(Object.entries(validation.errors).map(([k,v])=>`${k}: ${v}`).join(" "));
  validateCalibration(calibration);
  const i=rawInputs, c=calibration, warnings=[...validation.warnings];
  const brakeDemand=clamp(i.brakeDemand,0,1), vehicleSpeedKph=Math.max(0,i.vehicleSpeedKph), batterySocPct=clamp(i.batterySocPct,0,100);
  const enableFactor=typeof i.regenEnabled === "boolean" ? Number(i.regenEnabled) : clamp(i.regenEnabled,0,1);
  if (brakeDemand!==i.brakeDemand) warnings.push(`Calculation uses brake demand ${brakeDemand}; the raw entry is retained.`);
  if (vehicleSpeedKph!==i.vehicleSpeedKph) warnings.push("Calculation uses zero speed; the raw negative entry is retained.");
  if (batterySocPct!==i.batterySocPct) warnings.push(`Calculation uses SOC ${batterySocPct}%; the raw entry is retained.`);
  const vehicleSpeedMps=vehicleSpeedKph/3.6, safeSpeedMps=Math.max(vehicleSpeedMps,c.minimumSpeedMps);
  const requestedDecelerationMps2=brakeDemand*c.maxServiceDecelMps2;
  const requestedForceN=i.vehicleMassKg*requestedDecelerationMps2;
  const requestedWheelTorqueNm=requestedForceN*c.wheelRadiusM;
  const wheelAngularSpeedRadS=vehicleSpeedMps/c.wheelRadiusM;
  const wheelSpeedRpm=wheelAngularSpeedRadS*60/(2*Math.PI);
  const motorSpeedRpm=wheelAngularSpeedRadS*c.gearRatio*60/(2*Math.PI);
  const speedFactor=clamp((vehicleSpeedMps-c.speedCutoffMps)/(c.fullRegenSpeedMps-c.speedCutoffMps),0,1);
  const torqueForceLimitN=speedFactor*i.motorRegenTorqueLimitNm*c.gearRatio*c.drivetrainEfficiency/c.wheelRadiusM;
  const powerForceLimitN=speedFactor*i.motorRegenPowerLimitKw*1000/safeSpeedMps;
  const socFactor=clamp((c.socStopPct-batterySocPct)/(c.socStopPct-c.socDeratePct),0,1);
  const coldFactor=clamp((i.batteryTempC-c.coldCutoffC)/(c.coldFullC-c.coldCutoffC),0,1);
  const hotFactor=clamp((c.hotCutoffC-i.batteryTempC)/(c.hotCutoffC-c.hotFullC),0,1);
  const temperatureFactor=Math.min(coldFactor,hotFactor);
  const currentDerivedChargePowerKw=i.batteryVoltageV*i.chargeCurrentLimitA/1000;
  const baseChargePowerKw=Math.min(i.chargePowerLimitKw,currentDerivedChargePowerKw);
  const allowedBatteryPowerKw=baseChargePowerKw*socFactor*temperatureFactor;
  const batteryForceLimitN=allowedBatteryPowerKw*1000/(c.regenEfficiency*safeSpeedMps);
  const regenerativeForceN=enableFactor*Math.max(0,Math.min(requestedForceN,torqueForceLimitN,powerForceLimitN,batteryForceLimitN));
  const frictionForceN=Math.max(0,requestedForceN-regenerativeForceN);
  const regenerativeWheelTorqueNm=regenerativeForceN*c.wheelRadiusM, frictionWheelTorqueNm=frictionForceN*c.wheelRadiusM;
  const mechanicalRegenPowerKw=regenerativeForceN*vehicleSpeedMps/1000;
  const batteryChargePowerKw=Math.min(mechanicalRegenPowerKw*c.regenEfficiency,allowedBatteryPowerKw);
  const regenerativeCurrentA=batteryChargePowerKw*1000/i.batteryVoltageV;
  const safeRequestedForceN=Math.max(requestedForceN,c.forceEpsilonN);
  const regenerativePercent=100*regenerativeForceN/safeRequestedForceN, frictionPercent=100*frictionForceN/safeRequestedForceN;
  const forceBalanceResidualN=requestedForceN-regenerativeForceN-frictionForceN;
  let activeLimitCode="DRIVER_DEMAND", activeLimitLabel="Driver braking demand";
  const tolerance=1e-7;
  if (requestedForceN<=c.forceEpsilonN) { activeLimitCode="NO_BRAKING"; activeLimitLabel="No braking requested"; }
  else if (enableFactor<=tolerance) { activeLimitCode="REGEN_DISABLED"; activeLimitLabel="Regenerative braking disabled"; }
  else if (speedFactor<=tolerance) { activeLimitCode="LOW_SPEED"; activeLimitLabel="Low-speed regenerative cut-off"; }
  else if (socFactor<=tolerance) { activeLimitCode="BATTERY_SOC"; activeLimitLabel="Battery state-of-charge limit"; }
  else if (temperatureFactor<=tolerance) { activeLimitCode="BATTERY_TEMPERATURE"; activeLimitLabel="Battery temperature limit"; }
  else {
    // Stable ordering deliberately preserves the reference's tie-breaking priority.
    const candidates=[["DRIVER_DEMAND",requestedForceN],["MOTOR_TORQUE",torqueForceLimitN],["MOTOR_POWER",powerForceLimitN],["BATTERY_ACCEPTANCE",batteryForceLimitN]];
    candidates.sort((a,b)=>a[1]-b[1]); activeLimitCode=candidates[0][0];
    if (activeLimitCode==="MOTOR_TORQUE") activeLimitLabel="Motor regenerative-torque limit";
    else if (activeLimitCode==="MOTOR_POWER") activeLimitLabel="Motor regenerative-power limit";
    else if (activeLimitCode==="BATTERY_ACCEPTANCE") {
      if (socFactor<1-tolerance && socFactor<=temperatureFactor+tolerance) { activeLimitCode="BATTERY_SOC"; activeLimitLabel="Battery state-of-charge limit"; }
      else if (temperatureFactor<1-tolerance) { activeLimitCode="BATTERY_TEMPERATURE"; activeLimitLabel="Battery temperature limit"; }
      else if (currentDerivedChargePowerKw<=i.chargePowerLimitKw+tolerance) { activeLimitCode="BATTERY_CURRENT"; activeLimitLabel="Battery charging-current limit"; }
      else { activeLimitCode="BATTERY_POWER"; activeLimitLabel="Battery charging-power limit"; }
    }
  }
  const stopTimeEstimateS=requestedDecelerationMps2>0 ? vehicleSpeedMps/requestedDecelerationMps2 : 0;
  const stopDistanceEstimateM=requestedDecelerationMps2>0 ? vehicleSpeedMps**2/(2*requestedDecelerationMps2) : 0;
  const animationDurationS=stopTimeEstimateS>0 ? clamp(stopTimeEstimateS,1,8) : 0;
  const result={requestedDecelerationMps2,requestedForceN,requestedWheelTorqueNm,vehicleSpeedMps,wheelSpeedRpm,motorSpeedRpm,
    speedFactor,socFactor,temperatureFactor,currentDerivedChargePowerKw,baseChargePowerKw,allowedBatteryPowerKw,
    torqueForceLimitN,powerForceLimitN,batteryForceLimitN,regenerativeForceN,frictionForceN,regenerativeWheelTorqueNm,
    frictionWheelTorqueNm,mechanicalRegenPowerKw,batteryChargePowerKw,regenerativeCurrentA,regenerativePercent,frictionPercent,
    forceBalanceResidualN,activeLimitCode,activeLimitLabel,warnings,
    visual:{stopTimeEstimateS,stopDistanceEstimateM,animationDurationS,regenIntensity01:clamp(regenerativePercent/100,0,1),
      frictionHeatIntensity01:clamp(frictionPercent/100,0,1),batteryChargeIntensity01:baseChargePowerKw>0 ? clamp(batteryChargePowerKw/baseChargePowerKw,0,1) : 0}};
  if (![...OUTPUTS.map(([key])=>result[key]),...Object.values(result.visual)].every(Number.isFinite))
    throw new Error("Inputs produce non-finite results. Choose a numerically safe classroom-range scenario.");
  return result;
}
