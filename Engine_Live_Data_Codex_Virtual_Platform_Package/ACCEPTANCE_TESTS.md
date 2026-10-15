# Acceptance Tests

These tests verify the virtual Engine Live-Data Demonstration section. The physical 1NZ stage is tested separately, has no electric water pump, and is not compared with the virtual stage. Keep the numerical cases below unchanged when adapting the tests to the existing platform's test runner. `CODEX_MASTER_PROMPT.md` governs the integration scope.

Use a numerical tolerance of approximately `1e-6` for pure calculations and a practical display tolerance of `±0.01` for rounded UI values.

## 1. Input capping

| Raw input | Accepted value |
|---|---:|
| Battery voltage = 16.0 V | 14.9 V |
| Battery voltage = 6.0 V | 8.0 V |
| TPS = 120% | 100% |
| MAP = 10 kPa | 20 kPa |
| O2 voltage = 1.2 V | 0.95 V |
| ECT1 voltage = 0.1 V | 0.2 V |
| Engine speed = -100 rpm | 0 rpm |

The UI must identify that a value was capped or show the accepted value clearly.

## 2. ECT conversion checkpoints

| Voltage | Expected temperature |
|---:|---:|
| 4.8 V | -20.00 °C |
| 4.3 V | 0.00 °C |
| 3.5 V | 25.00 °C |
| 2.5 V | 50.00 °C |
| 1.5 V | 75.00 °C |
| 1.0 V | 90.00 °C |
| 0.6 V | 105.00 °C |
| 0.3 V | 125.00 °C |
| 0.2 V | 135.00 °C |

## 3. Fuel system — stoichiometric switching point

Inputs:

```text
EngineSpeed = 800 rpm
MAP = 35 kPa
TPS = 2%
O2 voltage = 0.45 V
ECT1 temperature = 90 °C
Battery voltage = 13.8 V
InjectionEnable = 1
```

Expected:

```text
EngineLoad = 10.6058823529%
LambdaEstimate = 1.0000
ClosedLoopActive = 1
STFT = 0.00%
WarmupEnrichment = 0.00%
BatteryCompensation = 0.00 ms
BaseInjectorPW = 1.679 ms
InjectorPW = 1.679 ms
```

## 4. Fuel system — lean indication

Use the previous inputs but set O2 voltage to 0.10 V.

Expected:

```text
LambdaEstimate = 1.1225
STFT = +14.70%
InjectorPW = 1.925813 ms
```

The UI explanation should state that positive correction adds fuel.

## 5. Fuel system — rich indication

Use the same warm-idle inputs but set O2 voltage to 0.90 V.

Expected:

```text
LambdaEstimate = 0.8425
STFT = -18.90%
InjectorPW = 1.361669 ms
```

The UI explanation should state that negative correction removes fuel.

## 6. Closed-loop disabling

With InjectionEnable = 1 but either:

- ECT1 temperature below 70 °C, or
- engine speed below 600 rpm,

expected:

```text
ClosedLoopActive = 0
STFT = 0
```

## 7. Idle and ignition response

Inputs:

```text
EngineSpeed = 620 rpm
TPS = 2%
MAP = 45 kPa
ECT1 temperature = 90 °C
AccessoryLoad = 80%
EngineState = RUN (3)
IgnitionEnable = 1
```

Expected:

```text
TargetIdleRPM = 750 rpm
IdleActive = 1
RPMError = 130 rpm
IdleControlDuty = 52.80%
IgnitionTiming = 10.43° BTDC
```

## 8. Cooling — normal warm operation

Inputs:

```text
ECT1 voltage = 1.0 V
ECT2 voltage = 1.1 V
A/C request = 0
EngineState = RUN
Battery voltage = 13.8 V
Emergency stop = 0
```

Expected:

```text
ECT1Temp = 90.00 °C
ECT2Temp = 87.00 °C
SensorDifference = 3.00 °C
SensorDisagreement = 0
ControlTemperature = 90.00 °C
FanDuty = 28.5714286%
WaterPumpDuty = 70.00%
CoolingLoopActive = 1
```

## 9. Cooling — high demand with A/C

Inputs:

```text
ECT1 voltage = 0.55 V
ECT2 voltage = 0.62 V
A/C request = 1
EngineState = RUN
Battery voltage = 13.8 V
Emergency stop = 0
```

Expected approximately:

```text
ECT1Temp = 108.3333 °C
ECT2Temp = 104.25 °C
SensorDisagreement = 0
FanDuty = 100%
WaterPumpDuty = 97.50%
```

## 10. Cooling — ECT disagreement fail-safe

Inputs:

```text
ECT1 voltage = 1.0 V
ECT2 voltage = 2.0 V
EngineState = RUN
Battery voltage = 13.8 V
Emergency stop = 0
```

Expected:

```text
ECT1Temp = 90.0 °C
ECT2Temp = 62.5 °C
SensorDifference = 27.5 °C
SensorDisagreement = 1
FanDuty = 100%
WaterPumpDuty = 100%
```

## 11. Start permission blocked by low battery

Inputs:

```text
IgnitionSwitch = 1
StartAuthorisation = 1
StartRequest = 1
EmergencyStop = 0
BatteryVoltage = 9.0 V
```

Expected state remains OFF because safe start requires at least 9.5 V.

## 12. Normal start sequence

Initial state OFF. Use:

```text
IgnitionSwitch = 1
StartAuthorisation = 1
StartRequest pulse = 1
EmergencyStop = 0
BatteryVoltage = 13.8 V
EngineSpeed = 800 rpm
```

Expected sequence:

1. OFF changes to PRIME.
2. PRIME keeps `FuelPumpState = 1` for 2.0 s.
3. State changes to CRANK and `StarterState = 1`.
4. Because RPM is at least 500, state changes to RUN on the next calculation step.
5. In RUN: fuel pump, injection and ignition are enabled; starter is off.

## 13. Crank timeout

Hold EngineSpeed below 500 rpm throughout CRANK. After 5.0 seconds in CRANK, state must change to SHUTDOWN, then return to OFF after 0.5 seconds.

## 14. Emergency stop

From RUN, activate EmergencyStop.

Expected:

- start/run state changes to SHUTDOWN;
- fuel pump, starter, injection and ignition outputs become 0;
- cooling emergency branch sets fan and virtual pump duty to 0;
- emergency stop remains latched in the UI until reset.

## 15. UI and integration checks

- Students cannot edit any calculated value or output.
- Run advances state time and graphs.
- Pause preserves state and history.
- Reset returns state to OFF and clears history.
- CSV export contains canonical signal names.
- No page compares virtual results with physical results.
- Water-pump output is labelled as virtual.
- The educational disclaimer is visible.

## 16. Existing-platform integration acceptance

- Repository inspection identifies the host framework, routing, components, styles, state conventions and test commands before implementation.
- Engine Live-Data Demonstration appears as one section in the existing platform's navigation; the four models are internal views of that section.
- The implementation uses the host's existing shell, routing, components, style conventions, state patterns and chart library where available.
- No replacement platform, new standalone application/project/deployment or redesign of unrelated areas has been introduced.
- Existing navigation and unrelated sections continue to work; navigating away from the engine section cleans up its timers and subscriptions.
- All original input caps, units, equations, dependencies, state codes, transitions, branch priorities, outputs, presets and expected numerical results are preserved.
- The cooling view identifies virtual ECT1/ECT2, a duty-controlled fan and a virtual electric water pump. It explicitly states that the physical 1NZ setup has no electric water pump.
- Virtual and physical test evidence remain independent, with no comparison page, combined comparison dataset or agreement/error calculation between stages.
- The applicable host lint, type-check, test and build commands pass. Report any unavailable or blocked check honestly.

These are checks for the colleague's eventual integrated implementation. Passing the packaged reference tests alone does not establish that platform integration is complete.
