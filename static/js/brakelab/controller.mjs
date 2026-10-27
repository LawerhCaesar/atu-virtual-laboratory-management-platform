import {DEFAULT_BRAKE_INPUTS, DEFAULT_BRAKE_CALIBRATION, MODULE_ID, MODULE_VERSION, calculateBrakeAllocation, clamp} from "./model.mjs";

/** Screen playback only. Operating-point results are never integrated or overwritten. */
export function playbackFrame(result, elapsedS, calibration=DEFAULT_BRAKE_CALIBRATION) {
  const duration=result.visual.animationDurationS;
  const progress=duration>0 ? clamp(elapsedS/duration,0,1) : 0;
  const physicalTimeS=progress*result.visual.stopTimeEstimateS;
  const speedMps=result.vehicleSpeedMps*(1-progress);
  const distanceM=result.visual.stopDistanceEstimateM*(progress*(2-progress));
  const available=clamp((speedMps-calibration.speedCutoffMps)/(calibration.fullRegenSpeedMps-calibration.speedCutoffMps),0,1);
  const fade=result.speedFactor>0 ? clamp(available/result.speedFactor,0,1) : 0;
  return {progress,physicalTimeS,speedKph:speedMps*3.6,distanceM,
    wheelAngleDeg:(distanceM%(2*Math.PI*calibration.wheelRadiusM/.08))/(2*Math.PI*calibration.wheelRadiusM/.08)*360,
    regenIntensity:result.visual.regenIntensity01*fade,
    chargeIntensity:result.visual.regenIntensity01*result.visual.batteryChargeIntensity01*fade,
    frictionIntensity:speedMps>0 ? result.visual.frictionHeatIntensity01 : 0};
}

export class BrakeSimulation {
  constructor() { this.reset(); }
  reset() { this.calculate(DEFAULT_BRAKE_INPUTS); }
  calculate(inputs) {
    const result=calculateBrakeAllocation(inputs);
    this.inputs={...inputs}; this.result=result; this.error=null;
    this.elapsedS=0; this.running=false; this.hasRun=false; this.mode="Preview";
  }
  fail(error) { this.error=error.message; this.running=false; this.mode="Calculation error"; }
  run(inputs, motion=true) {
    this.calculate(inputs); this.hasRun=true;
    this.running=motion && this.result.visual.animationDurationS>0;
    this.mode=this.running ? "Playing" : !motion ? "Static result · motion off" : this.result.vehicleSpeedMps===0 ? "Stationary" : "No braking · no stopping estimate";
  }
  pause() { if (this.running) { this.running=false; this.mode="Paused"; } }
  resume() { if (!this.error && this.hasRun && this.elapsedS<this.result.visual.animationDurationS) { this.running=true; this.mode="Playing"; } }
  tick(dt) {
    if (!this.running) return;
    if (!Number.isFinite(dt) || dt<0) throw new Error("Playback time step must be finite and non-negative.");
    this.elapsedS=Math.min(this.result.visual.animationDurationS,this.elapsedS+dt);
    if (this.elapsedS>=this.result.visual.animationDurationS) { this.running=false; this.mode="Illustration complete"; }
  }
  frame() { return playbackFrame(this.result,this.elapsedS); }
  payload() {
    if (this.error) throw new Error(`Cannot export last-valid results: ${this.error}`);
    return {moduleId:MODULE_ID,moduleVersion:MODULE_VERSION,sourceBasis:"Programmer guide and supplied prompt; no SLX or MATLAB runtime verification",
      inputs:{...this.inputs},calibration:{...DEFAULT_BRAKE_CALIBRATION},
      result:{...this.result,warnings:[...this.result.warnings],visual:{...this.result.visual}},
      status:{valid:true,forceBalanceValid:Math.abs(this.result.forceBalanceResidualN)<.001},
      playback:{illustrative:true,elapsedS:this.elapsedS,mode:this.mode}};
  }
}
