// Presentation only. These generic dimensions/timing are NOT a Toyota 1NZ model.
export const GEOMETRY = Object.freeze({ crankRadius: 0.36, rodLength: 1.25 });
export const FIRING_ORDER = Object.freeze([1, 3, 4, 2]);
export const wrap = (angle, period = 720) => ((angle % period) + period) % period;
export function valveLift(cycle, start) {
  const phase = wrap(cycle) - start;
  return phase > 0 && phase < 180 ? Math.sin(phase * Math.PI / 180) ** 2 : 0;
}

export function pistonPosition(degrees, r = GEOMETRY.crankRadius, l = GEOMETRY.rodLength) {
  if (!(r > 0 && l > r)) throw new RangeError("Rod length must exceed crank radius");
  const a = degrees * Math.PI / 180;
  return r * Math.cos(a) + Math.sqrt(l * l - r * r * Math.sin(a) ** 2);
}

export function cylinderPose(cylinder, angle, outputs = {}) {
  const offset = FIRING_ORDER.indexOf(cylinder) * 180;
  if (offset < 0) throw new RangeError("Unknown cylinder");
  // Zero is firing TDC: power, exhaust, intake, compression (idealised timing).
  const cycle = wrap(angle - offset);
  const stroke = ["Power", "Exhaust", "Intake", "Compression"][Math.floor(cycle / 180)];
  const radians = cycle * Math.PI / 180;
  return {
    cycle, stroke, piston: pistonPosition(cycle),
    pinY: GEOMETRY.crankRadius * Math.cos(radians),
    pinZ: GEOMETRY.crankRadius * Math.sin(radians),
    intake: cycle >= 360 && cycle < 540,
    exhaust: cycle >= 180 && cycle < 360,
    intakeLift: valveLift(cycle, 360), exhaustLift: valveLift(cycle, 180),
    // Command timing mapped onto the assumed firing order; not measured sparks.
    spark: Boolean(outputs.IgnitionEnable && wrap(cycle + (outputs.IgnitionTiming || 0)) < 10),
  };
}

export class CutawayClock {
  constructor() { this.angle = 0; this.fanAngle = 0; this.pumpAngle = 0; this.scale = 0.02; }
  advance(result, seconds) {
    const o = result.outputs;
    if (result.inputs.EmergencyStop) return;
    // Qualitative command animation: 600 rpm at 100% BEFORE playback scaling.
    // This is an arbitrary teaching cadence, never a predicted actuator speed.
    const dt = Math.max(0, seconds) * this.scale;
    this.fanAngle += (Number(o.FanDuty) || 0) / 100 * 3600 * dt;
    this.pumpAngle += (Number(o.WaterPumpDuty) || 0) / 100 * 3600 * dt;
    if (![2, 3].includes(o.EngineState)) return;
    // Called ONLY for completed, fixed simulation steps. No independent physics.
    this.angle += result.inputs.EngineSpeed * 6 * Math.max(0, seconds) * this.scale;
  }
  reset() { this.angle = 0; this.fanAngle = 0; this.pumpAngle = 0; }
}
