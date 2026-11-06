// Written master specification, v1.0.0. Source SLX unavailable for independent parity.
export const FIELDS = [
  ['stopDurationS','Stop duration','s',10,1,120], ['numberOfStops','Number of stops','count',3,0,20],
  ['initialSocPct','Initial battery SOC','%',80,40,100], ['accessoryLoadW','Accessory load','W',400,0,1200],
  ['minimumStopTimeS','Minimum stop time','s',5,1,30], ['movingFuelG','Moving fuel','g',100,1,1000],
  ['idleFuelRateGps','Idle fuel rate','g/s',.18,.10,.40], ['restartFuelPerStartG','Restart fuel','g/start',.20,.05,.60],
  ['batteryNominalVoltageV','Battery nominal voltage','V',12,12,12], ['batteryCapacityAh','Battery capacity','Ah',70,45,100],
  ['batteryInternalResistanceOhm','Battery internal resistance','Ω',.012,.005,.030], ['crankingCurrentA','Cranking current','A',250,150,500],
  ['minimumCrankVoltageV','Minimum crank voltage','V',9.5,9,10.5], ['minimumSocPct','Minimum SOC','%',60,50,75],
  ['maximumAccessoryLoadW','Maximum accessory load','W',800,400,1500], ['startEnergyJPerRestart','Start energy','J/restart',3000,1500,8000],
  ['batteryEfficiency','Battery efficiency','ratio',.90,.80,.98], ['alternatorEfficiency','Alternator efficiency','ratio',.65,.50,.75],
  ['engineEfficiency','Engine efficiency','ratio',.25,.20,.35], ['fuelLhvJPerKg','Fuel lower heating value','J/kg',43000000,42000000,44000000],
  ['fuelCapacityL','Fuel tank capacity','L',55,1,150], ['initialFuelL','Fuel currently in tank','L',20,0,150],
  ['fuelDensityKgPerL','Fuel density','kg/L',.74,.6,.9], ['fuelPricePerL','Fuel price per litre','currency/L',0,0,100],
];
export const FUEL_KEYS=['fuelCapacityL','initialFuelL','fuelDensityKgPerL','fuelPricePerL'];
export const DEFAULTS = Object.fromEntries(FIELDS.map(([key,,,value])=>[key,value]));
export function calculateMicroHybridStopStart(i) {
  const warnings=[];
  for (const [key,label,unit,,min,max] of FIELDS) {
    const v=i[key]; if (!Number.isFinite(v)) throw new Error(`${label} must be a finite number.`);
    if (v<0 && ['stopDurationS','numberOfStops','accessoryLoadW','minimumStopTimeS','movingFuelG','idleFuelRateGps','restartFuelPerStartG','maximumAccessoryLoadW','startEnergyJPerRestart'].includes(key)) throw new Error(`${label} cannot be negative.`);
    if (v<min || v>max) warnings.push(`${label}: ${v} ${unit} is outside the suggested ${min}–${max} range.`);
  }
  if(i.fuelCapacityL<=0||i.initialFuelL<0||i.initialFuelL>i.fuelCapacityL||i.fuelDensityKgPerL<=0||i.fuelDensityKgPerL>2||i.fuelPricePerL<0)throw new Error('Fuel: use a positive capacity, loaded litres between zero and capacity, density above zero and no greater than 2 kg/L, and a nonnegative price.');
  if(i.batteryNominalVoltageV!==12)warnings.push('This is the 12 V source model. A custom nominal voltage changes energy-to-SOC conversion, but the fixed 12 V crank-voltage curve is unchanged. This does not validate a 48 V system.');
  if (!Number.isSafeInteger(i.numberOfStops)) throw new Error('Number of stops must be a non-negative integer.');
  for (const key of ['batteryNominalVoltageV','batteryCapacityAh','fuelLhvJPerKg']) if (i[key]<=0) throw new Error('Battery voltage, capacity and fuel heating value must be greater than zero.');
  for (const key of ['batteryEfficiency','alternatorEfficiency','engineEfficiency']) if (i[key]<=0 || i[key]>1) throw new Error('Efficiencies must be greater than zero and at most one.');
  const denominator=i.batteryEfficiency*i.alternatorEfficiency*i.engineEfficiency*i.fuelLhvJPerKg;
  if (!Number.isFinite(denominator) || denominator<=0) throw new Error('Efficiency calculation is outside the numerical range.');
  const fuelEquivalentG=e=>1000*e/denominator;
  const predictedCrankVoltageV=11.8+.012*i.initialSocPct-i.crankingCurrentA*i.batteryInternalResistanceOhm;
  const accessoryFuelEquivalentRateGps=fuelEquivalentG(i.accessoryLoadW);
  const startEnergyFuelEquivalentPerRestartG=fuelEquivalentG(i.startEnergyJPerRestart);
  const netFuelSavingRateGps=i.idleFuelRateGps-accessoryFuelEquivalentRateGps;
  const breakEvenFeasible=netFuelSavingRateGps>0;
  const breakEvenStopTimeS=breakEvenFeasible?(i.restartFuelPerStartG+startEnergyFuelEquivalentPerRestartG)/netFuelSavingRateGps:null;
  const failedConditions=[];
  if(i.accessoryLoadW>i.maximumAccessoryLoadW) failedConditions.push('Accessory load exceeds the permitted engine-off limit.');
  if(i.stopDurationS<i.minimumStopTimeS) failedConditions.push('Stop duration is below the selected minimum stop time.');
  if(!breakEvenFeasible) failedConditions.push('Accessory energy creates no finite fuel break-even point.');
  else if(i.stopDurationS<breakEvenStopTimeS) failedConditions.push('Stop duration is below the calculated break-even time.');
  if(i.initialSocPct<i.minimumSocPct) failedConditions.push('Battery SOC is below the minimum stop-start threshold.');
  if(predictedCrankVoltageV<i.minimumCrankVoltageV) failedConditions.push('Predicted crank voltage is below the restart threshold.');
  const inhibitCode=i.accessoryLoadW>i.maximumAccessoryLoadW?7:(i.stopDurationS<i.minimumStopTimeS || !breakEvenFeasible || i.stopDurationS<breakEvenStopTimeS)?4:i.initialSocPct<i.minimumSocPct?5:predictedCrankVoltageV<i.minimumCrankVoltageV?6:0;
  const inhibitMessage={0:'Stop permitted.',4:'Automatic stop inhibited: stop is too short or below fuel break-even.',5:'Automatic stop inhibited: battery SOC is too low.',6:'Automatic stop inhibited: predicted crank voltage is too low.',7:'Automatic stop inhibited: accessory load is too high.'}[inhibitCode];
  const stopPermission=inhibitCode===0, acceptedStopCount=stopPermission?i.numberOfStops:0, rejectedStopCount=stopPermission?0:i.numberOfStops;
  const totalEngineOffTimeS=i.stopDurationS*acceptedStopCount, restartCount=acceptedStopCount;
  const accessoryEnergyJ=i.accessoryLoadW*totalEngineOffTimeS, startEnergyTotalJ=i.startEnergyJPerRestart*restartCount, totalElectricalEnergyJ=accessoryEnergyJ+startEnergyTotalJ;
  const accessoryEnergyWh=accessoryEnergyJ/3600, socDropPct=100*totalElectricalEnergyJ/(i.batteryNominalVoltageV*i.batteryCapacityAh*3600);
  const finalBatterySocPct=Math.min(100,Math.max(0,i.initialSocPct-socDropPct));
  const engineOffTerminalVoltageV=11.8+.012*finalBatterySocPct-(stopPermission?i.accessoryLoadW/i.batteryNominalVoltageV:0)*i.batteryInternalResistanceOhm;
  const conventionalIdleFuelG=i.idleFuelRateGps*i.stopDurationS*i.numberOfStops, conventionalFuelG=i.movingFuelG+conventionalIdleFuelG;
  const microHybridIdleFuelG=stopPermission?0:conventionalIdleFuelG, restartFuelPenaltyG=i.restartFuelPerStartG*restartCount, rechargeFuelPenaltyG=fuelEquivalentG(totalElectricalEnergyJ);
  const microHybridFuelG=i.movingFuelG+microHybridIdleFuelG+restartFuelPenaltyG+rechargeFuelPenaltyG;
  const idleFuelAvoidedG=conventionalIdleFuelG-microHybridIdleFuelG, fuelSavedG=conventionalFuelG-microHybridFuelG, fuelReductionPct=conventionalFuelG>0?100*fuelSavedG/conventionalFuelG:0;
  const result={modelVersion:'1.1.0',stopPermission,stopPermissionFlag:Number(stopPermission),inhibitCode,inhibitMessage,failedConditions,warnings,breakEvenFeasible,breakEvenStopTimeS,totalEngineOffTimeS,acceptedStopCount,rejectedStopCount,restartCount,predictedCrankVoltageV,engineOffTerminalVoltageV,finalBatterySocPct,socDropPct,conventionalIdleFuelG,microHybridIdleFuelG,idleFuelAvoidedG,conventionalFuelG,microHybridFuelG,restartFuelPenaltyG,rechargeFuelPenaltyG,fuelSavedG,fuelReductionPct,accessoryEnergyJ,accessoryEnergyWh,startEnergyTotalJ,totalElectricalEnergyJ,accessoryFuelEquivalentRateGps,startEnergyFuelEquivalentPerRestartG,netFuelSavingRateGps};
  const litres=g=>g/(1000*i.fuelDensityKgPerL);result.fuelInventory={capacityL:i.fuelCapacityL,initialFuelL:i.initialFuelL,densityKgPerL:i.fuelDensityKgPerL,conventionalUsedL:litres(conventionalFuelG),microHybridUsedL:litres(microHybridFuelG),savedL:litres(fuelSavedG),projectedRemainingL:Math.max(0,i.initialFuelL-litres(microHybridFuelG)),budgetDeficitL:Math.max(0,litres(microHybridFuelG)-i.initialFuelL),projectedLevelPct:100*Math.max(0,i.initialFuelL-litres(microHybridFuelG))/i.fuelCapacityL,conventionalCost:litres(conventionalFuelG)*i.fuelPricePerL,microHybridCost:litres(microHybridFuelG)*i.fuelPricePerL,costSaved:litres(fuelSavedG)*i.fuelPricePerL,method:'Whole-scenario fuel-mass accounting converted using the stated density. No empty-tank shutdown or time-resolved fuel-level sensor is modeled.'};if(Object.values(result.fuelInventory).some(v=>typeof v==='number'&&!Number.isFinite(v)))throw new Error('Fuel accounting is outside the numerical range.');if(result.fuelInventory.budgetDeficitL>0)warnings.push('Projected scenario fuel use exceeds the fuel loaded. Results are accounting estimates; no fuel cutoff is imposed.');
  if(Object.values(result).some(v=>typeof v==='number'&&!Number.isFinite(v))) throw new Error('Calculation is outside the numerical range.');
  return result;
}
