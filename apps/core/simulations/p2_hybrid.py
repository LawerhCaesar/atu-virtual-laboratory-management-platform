"""Deterministic P2 propulsion model: supplied Lawrence Equations 5.1–5.20.

No framework dependencies. Forward rectangular integration uses each interval's
left state for SOC, energy and squared metrics. Discontinuous protection therefore
has at most one output-step latency; exports disclose the method and step.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math


@dataclass(frozen=True)
class Parameters:
    low_torque_threshold_nm: float = 80
    high_torque_threshold_nm: float = 200
    low_torque_motor_share: float = 1
    blended_motor_share: float = .5
    engine_max_torque_nm: float = 142
    motor_max_torque_nm: float = 165
    motor_peak_power_w: float = 35000
    soc_protection_threshold: float = .30
    gear_ratio: float = 1
    final_drive_ratio: float = 3.94
    driveline_efficiency: float = .90
    motor_efficiency: float = .92
    inverter_efficiency: float = .95
    auxiliary_load_w: float = 500
    battery_open_circuit_voltage_v: float = 350
    battery_internal_resistance_ohm: float = .045
    battery_nominal_energy_wh: float = 12000
    omega_epsilon_rad_s: float = .001
    numerical_epsilon: float = 1e-6


# Metadata drives the UI and server validation; limits are numerical work/domain
# protections, not OEM operating envelopes. Thresholds are cross-validated below.
PARAMETER_RULES = [
 ('low_torque_threshold_nm','Low torque threshold','Nm',0,400,1),
 ('high_torque_threshold_nm','High torque threshold','Nm',0,400,1),
 ('low_torque_motor_share','Low torque motor share','fraction',0,1,.01),
 ('blended_motor_share','Blended motor share','fraction',0,1,.01),
 ('engine_max_torque_nm','Engine maximum torque','Nm',0,2000,1),
 ('motor_max_torque_nm','Motor maximum torque','Nm',0,2000,1),
 ('motor_peak_power_w','Motor peak power','W',0,500000,100),
 ('soc_protection_threshold','SOC protection threshold','fraction',0,1,.01),
 ('gear_ratio','Gear ratio','ratio',.01,20,.01),
 ('final_drive_ratio','Final drive ratio','ratio',.01,20,.01),
 ('driveline_efficiency','Driveline efficiency','fraction',.01,1,.01),
 ('motor_efficiency','Motor efficiency','fraction',.01,1,.01),
 ('inverter_efficiency','Inverter efficiency','fraction',.01,1,.01),
 ('auxiliary_load_w','Auxiliary electrical load','W',0,100000,10),
 ('battery_open_circuit_voltage_v','Battery open circuit voltage','V',1,2000,1),
 ('battery_internal_resistance_ohm','Battery internal resistance','ohm',.000001,10,.001),
 ('battery_nominal_energy_wh','Battery nominal energy','Wh',.01,1000000,100),
 ('omega_epsilon_rad_s','Angular speed epsilon','rad/s',.000001,1,.001),
 ('numerical_epsilon','Numerical denominator epsilon','ratio',1e-12,.001,1e-6),
]
INPUT_RULES = [
 ('requested_torque_nm','Requested torque','Nm',0,400,1,140),
 ('motor_speed_rpm','Motor speed','rpm',0,20000,50,2500),
 ('initial_soc','Initial SOC','fraction',0,1,.01,.70),
 ('duration_s','Simulation duration','s',.01,600,.1,30),
 ('time_step_s','Integration time step','s',.001,.1,.001,.01),
]
FUEL_RULES = [
 ('fuel_capacity_litres','Fuel tank capacity','L',.01,10000,1,55),
 ('initial_fuel_litres','Fuel currently in tank','L',0,10000,.1,20),
 ('fuel_density_kg_per_l','Fuel density','kg/L',.1,2,.01,.74),
 ('fuel_lhv_mj_per_kg','Fuel lower heating value','MJ/kg',1,100,.1,43),
 ('assumed_engine_efficiency','Assumed engine efficiency','fraction',.01,1,.01,.30),
 ('fuel_price_per_l','Fuel price per litre','currency/L',0,100000,1,0),
]

def fuel_settings(request):
    enabled=request.get('fuel_estimate_enabled',False)
    source=request.get('fuel_assumptions',{})
    if type(enabled) is not bool or not isinstance(source,dict):
        raise ValidationError({'fuel_assumptions':'Use a boolean estimate switch and an object of fuel assumptions.'})
    errors={k:'Unknown fuel assumption.' for k in source if k not in {r[0] for r in FUEL_RULES}}
    values={}
    for k,label,unit,lo,hi,_,default in FUEL_RULES:
        v=source.get(k,default)
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not lo<=v<=hi or not math.isfinite(v):errors[k]=f'{label}: use {lo}–{hi} {unit}.'
        else:values[k]=float(v)
    if not errors and values['initial_fuel_litres']>values['fuel_capacity_litres']:errors['initial_fuel_litres']='Fuel currently in tank must not exceed tank capacity.'
    if errors:raise ValidationError(errors)
    return enabled,values

SIGNALS = [
 ('time_s','Time','s'),('requested_torque_nm','Requested torque','Nm'),
 ('engine_torque_nm','Engine torque','Nm'),('motor_torque_nm','Motor torque','Nm'),
 ('motor_share_fraction','Motor share command','fraction'),('clutch_state','Clutch state','code'),
 ('torque_regime_code','Torque regime','code'),('requested_wheel_torque_nm','Requested wheel torque','Nm'),
 ('actual_wheel_torque_nm','Actual wheel torque','Nm'),('wheel_torque_error_nm','Wheel torque error','Nm'),
 ('motor_speed_rad_s','Motor angular speed','rad/s'),('motor_mechanical_power_w','Motor mechanical power','W'),
 ('battery_terminal_power_w','Battery terminal power','W'),('battery_current_a','Battery current','A'),
 ('battery_terminal_voltage_v','Battery terminal voltage','V'),('battery_internal_loss_power_w','Internal loss power','W'),
 ('soc_percent','Battery SOC','%'),('delta_soc_percent','Delta SOC','percentage points'),
 ('battery_energy_used_wh','Battery energy used','Wh'),('battery_loss_energy_wh','Battery loss energy','Wh'),
 ('battery_efficiency_percent','Battery energy efficiency','%'),('battery_current_rms_a','RMS battery current','A'),
 ('torque_rmse_nm','Torque RMSE','Nm'),
]
SCOPE_GROUPS = [
 {'name':'Torque Split','panels':[['requested_torque_nm','engine_torque_nm','motor_torque_nm']]},
 {'name':'Mode and State','panels':[['motor_share_fraction'],['clutch_state'],['torque_regime_code'],['soc_percent']]},
 {'name':'Wheel Torque Tracking','panels':[['requested_wheel_torque_nm','actual_wheel_torque_nm','wheel_torque_error_nm']]},
 {'name':'Motor and Power','panels':[['motor_torque_nm'],['motor_speed_rad_s'],['motor_mechanical_power_w','battery_terminal_power_w']]},
 {'name':'Battery Electrical','panels':[['battery_terminal_power_w'],['battery_current_a'],['battery_terminal_voltage_v'],['battery_internal_loss_power_w']]},
 {'name':'Battery Energy and SOC','panels':[['soc_percent'],['delta_soc_percent'],['battery_energy_used_wh','battery_loss_energy_wh'],['battery_efficiency_percent'],['battery_current_rms_a']]},
 {'name':'Torque Error Metrics','panels':[['wheel_torque_error_nm','torque_rmse_nm']]},
]
COMPATIBILITY = list(zip(
 ['T_req_Nm','T_engine_Nm','T_motor_Nm','T_wheel_requested_Nm','T_wheel_actual_Nm','SOC_percent','Battery_current_A','Battery_energy_Wh','Battery_loss_energy_Wh','Battery_efficiency_percent','Torque_RMSE_Nm','Torque_regime_code'],
 ['requested_torque_nm','engine_torque_nm','motor_torque_nm','requested_wheel_torque_nm','actual_wheel_torque_nm','soc_percent','battery_current_a','battery_energy_used_wh','battery_loss_energy_wh','battery_efficiency_percent','torque_rmse_nm','torque_regime_code']))
LIMITATIONS = [
 'P2 constant requested torque and constant motor speed; propulsion discharge only.',
 'Written-equation reference verification. Source SLX, model-data guide and thesis were not supplied; no independent Simulink or vehicle validation.',
 'No regeneration, fuel maps, engine starts, drive cycles, vehicle speed/distance, thermal dynamics or battery ageing.',
 'Model constants are independent of the common Genesis GV70 visual reference; they are not GV70 powertrain calibration.',
 'Forward interval integration with SOC clamped to [0,1]. Protection switches on the next recorded state. Compare smaller time steps near SOC events.',
 'Protected discriminants can yield mathematically defined but physically infeasible battery states. Warnings remain part of every export.',
 'Auxiliary load remains at SOC zero under the supplied equations; depletion is flagged, not a physical battery cutoff.',
]
EQUATIONS = [
 ('5.1','Motor share = low share below low threshold, blended share otherwise; regime 1/2/3 at the two thresholds.'),
 ('5.2–5.3','ω = rpm·2π/60; Tm,lim = min(Tm,max, Ppeak/(ω+εω)); Tm = clamp(αTreq,0,Tm,lim), or zero below SOC threshold.'),
 ('5.4–5.7','Te = clamp(Treq−Tm,0,Te,max); clutch open only in low regime with acceptable SOC. Tw,req=Treq·ig·ifd·ηd; Tw,act=(uc·Te+Tm)·ig·ifd·ηd; error=Tw,req−Tw,act.'),
 ('5.8–5.12','Pm=Tm·ω; Pb=Pm/(ηm·ηinv)+Paux; D=Voc²−4RPb; Dp=clamp(D,1e−9,1e12); I=(Voc−√Dp)/(2R); Vt=Voc−IR.'),
 ('5.13–5.15','Qn=(Enom/Voc)·3600; dSOC/dt=−I/Qn; Ploss=I²R.'),
 ('5.16–5.20','Eb=∫Pb dt/3600; Eloss=∫Ploss dt/3600; ηb=100Eb/(Eb+Eloss+ε); Irms=√(∫I²dt/max(t,ε)); RMSE=√(∫error²dt/max(t,ε)).'),
]


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('; '.join(errors.values()))


def model_info():
    defaults = asdict(Parameters())
    return {
        'model_id':'p2-full-parallel-torque-intensity','model_version':'1.1.0',
        'formula_version':'simulink-parity-5.1-to-5.20',
        'inputs':[dict(key=k,label=l,unit=u,min=a,max=b,step=s,default=d) for k,l,u,a,b,s,d in INPUT_RULES],
        'parameters':[dict(key=k,label=l,unit=u,min=a,max=b,step=s,default=defaults[k]) for k,l,u,a,b,s in PARAMETER_RULES],
        'fuel_inputs':[dict(key=k,label=l,unit=u,min=a,max=b,step=s,default=d) for k,l,u,a,b,s,d in FUEL_RULES],
        'signals':[dict(key=k,label=l,unit=u) for k,l,u in SIGNALS],
        'scope_groups':SCOPE_GROUPS,'compatibility_order':COMPATIBILITY,
        'limitations':LIMITATIONS,'equations':EQUATIONS,'max_samples':60001,
    }


def validate_inputs(request):
    if not isinstance(request, dict):
        raise ValidationError({'request':'Expected a JSON object.'})
    allowed = {r[0] for r in INPUT_RULES} | {'parameter_overrides','case_name','fuel_assumptions','fuel_estimate_enabled'}
    errors = {k:'Unknown input.' for k in request if k not in allowed}
    overrides = request.get('parameter_overrides', {})
    if not isinstance(overrides, dict):
        raise ValidationError({'parameter_overrides':'Expected an object of approved parameters.'})
    defaults = asdict(Parameters())
    errors.update({k:'Unknown parameter.' for k in overrides if k not in defaults})
    values = {}
    for key,label,unit,minimum,maximum,_,default in INPUT_RULES + [(*r,defaults[r[0]]) for r in PARAMETER_RULES]:
        source = request if key in allowed else overrides
        value = source.get(key, default)
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not minimum <= value <= maximum or not math.isfinite(value):
            errors[key] = f'{label} must be a finite number from {minimum:g} to {maximum:g} {unit}.'
        else:
            values[key] = float(value)
    name = request.get('case_name','Custom case')
    if not isinstance(name,str) or not 1 <= len(name.strip()) <= 80:
        errors['case_name']='Case name must contain 1–80 characters.'
    if errors:
        raise ValidationError(errors)
    if values['high_torque_threshold_nm'] <= values['low_torque_threshold_nm']:
        errors['high_torque_threshold_nm']='High threshold must exceed low threshold.'
    if math.ceil(values['duration_s']/values['time_step_s'])+1 > 60001:
        errors['time_step_s']='Use at most 60,001 samples per run; increase the time step or reduce duration.'
    if errors:
        raise ValidationError(errors)
    fuel_settings(request)
    inputs = {r[0]:values[r[0]] for r in INPUT_RULES}
    return inputs, Parameters(**{k:values[k] for k in defaults}), name.strip()


def classify_regime(torque, p):
    # Eq. 5.1. Research classification; not a diagnostic trouble code.
    if torque < p.low_torque_threshold_nm:
        return 1, p.low_torque_motor_share
    return (2 if torque < p.high_torque_threshold_nm else 3), p.blended_motor_share


def calculate_state(inputs, p, soc):
    torque, rpm = inputs['requested_torque_nm'], inputs['motor_speed_rpm']
    regime, share = classify_regime(torque,p)
    omega = rpm*2*math.pi/60  # Eq. 5.8
    limit = min(p.motor_max_torque_nm,p.motor_peak_power_w/(omega+p.omega_epsilon_rad_s))  # 5.2
    protected = soc < p.soc_protection_threshold
    motor = 0 if protected else min(share*torque,limit)  # 5.3
    engine = min(max(torque-motor,0),p.engine_max_torque_nm)  # 5.4
    clutch = int(protected or torque >= p.low_torque_threshold_nm)
    ratio = p.gear_ratio*p.final_drive_ratio*p.driveline_efficiency
    requested, actual = torque*ratio,(clutch*engine+motor)*ratio  # 5.5–5.7
    mechanical = motor*omega  # 5.9
    power = mechanical/(p.motor_efficiency*p.inverter_efficiency)+p.auxiliary_load_w  # 5.10
    discriminant = p.battery_open_circuit_voltage_v**2-4*p.battery_internal_resistance_ohm*power
    dp = max(1e-9,min(discriminant,1e12))
    current = (p.battery_open_circuit_voltage_v-math.sqrt(dp))/(2*p.battery_internal_resistance_ohm)  # 5.11
    voltage = p.battery_open_circuit_voltage_v-current*p.battery_internal_resistance_ohm  # 5.12
    loss = current**2*p.battery_internal_resistance_ohm  # 5.15
    limits = []
    if protected: limits.append('SOC protection: motor traction disabled; engine clutch closed.')
    if share*torque > limit: limits.append('Motor torque/power limit active.')
    if torque-motor > p.engine_max_torque_nm: limits.append('Engine torque saturation active.')
    if abs(requested-actual)>1e-8: limits.append('Requested wheel torque is not fully delivered.')
    if discriminant != dp: limits.append('Battery discriminant protected: electrical demand is infeasible under the unprotected battery equation.')
    if soc <= 0: limits.append('SOC depleted: auxiliary demand remains in the supplied model; not a physical cutoff.')
    return {
        'requested_torque_nm':torque,'engine_torque_nm':engine,'motor_torque_nm':motor,
        'motor_share_fraction':share,'clutch_state':clutch,'torque_regime_code':regime,
        'requested_wheel_torque_nm':requested,'actual_wheel_torque_nm':actual,'wheel_torque_error_nm':requested-actual,
        'motor_speed_rad_s':omega,'motor_mechanical_power_w':mechanical,'battery_terminal_power_w':power,
        'battery_current_a':current,'battery_terminal_voltage_v':voltage,'battery_internal_loss_power_w':loss,
        'soc_percent':soc*100,'delta_soc_percent':(inputs['initial_soc']-soc)*100,
    }, limits


def simulate(request):
    inputs,p,name = validate_inputs(request)
    fuel_enabled,fuel=fuel_settings(request)
    identity = json.dumps({'inputs':inputs,'parameters':asdict(p),'fuel_estimate_enabled':fuel_enabled,'fuel_assumptions':fuel,'version':'1.1.0'},sort_keys=True,separators=(',',':'))
    run_id = hashlib.sha256(identity.encode()).hexdigest()[:16]
    duration,step = inputs['duration_s'],inputs['time_step_s']
    count = math.ceil(duration/step)
    soc=inputs['initial_soc']; eb=el=i2=e2=0.0
    capacity=(p.battery_nominal_energy_wh/p.battery_open_circuit_voltage_v)*3600  # 5.14
    rows=[]; seen=set(); fuel_rows=[]; fuel_used=0.0
    for n in range(count+1):
        time = min(n*step,duration)
        row,limits=calculate_state(inputs,p,soc)
        seen.update(limits)
        row.update(time_s=time,battery_energy_used_wh=eb,battery_loss_energy_wh=el,
                   battery_efficiency_percent=100*eb/(eb+el+p.numerical_epsilon),
                   battery_current_rms_a=math.sqrt(i2/max(time,p.numerical_epsilon)),
                   torque_rmse_nm=math.sqrt(e2/max(time,p.numerical_epsilon)))  # 5.16–5.20
        if not all(math.isfinite(v) for v in row.values()):
            raise ValidationError({'calculation':'Non-finite calculation; choose less extreme parameters.'})
        rows.append(row)
        shaft_kw=row['engine_torque_nm']*row['clutch_state']*row['motor_speed_rad_s']/1000
        flow_gps=shaft_kw/fuel['assumed_engine_efficiency']/fuel['fuel_lhv_mj_per_kg'] if fuel_enabled else None
        used_litres=fuel_used/(1000*fuel['fuel_density_kg_per_l']) if fuel_enabled else None
        fuel_rows.append({'time_s':time,'engine_shaft_power_kw':shaft_kw,'estimated_fuel_flow_gps':flow_gps,'estimated_fuel_used_litres':used_litres,
                          'estimated_fuel_remaining_litres':max(0,fuel['initial_fuel_litres']-used_litres) if fuel_enabled else None,
                          'fuel_budget_deficit_litres':max(0,used_litres-fuel['initial_fuel_litres']) if fuel_enabled else None,
                          'estimated_fuel_cost':used_litres*fuel['fuel_price_per_l'] if fuel_enabled else None})
        if n == count: break
        dt=min(step,duration-time)
        if fuel_enabled:fuel_used+=flow_gps*dt
        soc=max(0,min(1,soc-row['battery_current_a']/capacity*dt))  # 5.13
        eb+=row['battery_terminal_power_w']*dt/3600
        el+=row['battery_internal_loss_power_w']*dt/3600
        i2+=row['battery_current_a']**2*dt
        e2+=row['wheel_torque_error_nm']**2*dt
    warnings = sorted(seen)
    if fuel_enabled:warnings.append('Fuel use is a separate constant-efficiency estimate; no idle fuel, engine map or empty-tank shutdown is modeled.')
    if fuel_enabled and fuel_rows[-1]['fuel_budget_deficit_litres']>1e-9:warnings.append('Estimated fuel consumption exceeds the fuel loaded. The original torque/battery model continues; no fuel cutoff is imposed.')
    if not 500 <= inputs['motor_speed_rpm'] <= 6000: warnings.append('Motor speed is outside the recommended 500–6,000 rpm research range.')
    if not .3 <= inputs['initial_soc'] <= .8: warnings.append('Initial SOC is outside the recommended 0.30–0.80 research range.')
    return {
        'metadata':{'model_id':'p2-full-parallel-torque-intensity','model_version':'1.1.0',
                    'formula_version':'simulink-parity-5.1-to-5.20','run_id':run_id,'case_name':name,
                    'integration':'Forward interval integration; final partial interval included',
                    'verification':'Supplied written equations and reference cases; source SLX unavailable'},
        'inputs':inputs,'parameters':asdict(p),'summary':rows[-1],
        'fuel_inventory':{'enabled':fuel_enabled,'assumptions':fuel,'method':'Optional constant engine efficiency, connected engine torque × imposed shaft speed; forward interval integration. No idle, map, startup or fuel cutoff.','summary':fuel_rows[-1],'time_series':fuel_rows},
        'active_limits':sorted(seen),'warnings':warnings,'assumptions':LIMITATIONS,
        'time_series':rows,'scope_groups':SCOPE_GROUPS,
    }


def compare(request):
    if not isinstance(request,dict) or set(request)-{'cases'} or not isinstance(request.get('cases'),list) or not 2 <= len(request['cases']) <= 4:
        raise ValidationError({'cases':'Supply two to four named cases.'})
    validated=[validate_inputs(case) for case in request['cases']]
    if len({v[2] for v in validated}) != len(validated):
        raise ValidationError({'cases':'Use distinct case names.'})
    if sum(math.ceil(v[0]['duration_s']/v[0]['time_step_s'])+1 for v in validated)>120004:
        raise ValidationError({'cases':'Comparison exceeds 120,004 samples; increase the time step or reduce duration.'})
    results=[simulate(case) for case in request['cases']]
    return {'cases':results,'summary_rows':[{'case_name':r['metadata']['case_name'],**r['summary']} for r in results],
            'interpretation':'Compare the same duration, rpm, SOC and calibration to isolate torque demand. Trends describe this P2 model only; they do not establish physical optimality.'}
