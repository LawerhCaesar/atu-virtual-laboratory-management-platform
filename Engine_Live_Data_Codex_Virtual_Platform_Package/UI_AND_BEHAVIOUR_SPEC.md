# Engine Live-Data Demonstration — UI and Behaviour Specification

## Integration boundary

Implement this UI as **one section inside the colleague's already-existing virtual automotive platform**. `CODEX_MASTER_PROMPT.md` is authoritative. Inspect and reuse the host repository's routing, shell, components, styles and state conventions before coding. Do not build a new platform, introduce a separate application, or redesign unrelated areas. The layout below describes only the content area of this engine section; adapt it to the host's established patterns.

The four model views belong within this section. ECT1/ECT2, the duty-controlled fan and the electric water pump are virtual model elements. The separate physical 1NZ setup has **no electric water pump**. The virtual and physical stages are tested independently, with no comparison, shared comparison dataset or agreement metric.

## 1. Section identity

**Page title:** Engine Live-Data Demonstration  
**Research context:** Virtual Modelling and Physical Demonstration of Engine Live-Data Relationships for Virtual-Platform Integration

The section should immediately explain that the student controls virtual inputs while the ECU-calculation layer produces calculated values and commanded outputs.

## 2. Recommended desktop layout

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Engine Live-Data Demonstration                                            │
│ Purpose + disclaimer            [Run] [Pause] [Reset] [Export CSV]       │
│ Simulation time: 00:00.00       Current state: OFF                        │
├──────────────────────┬─────────────────────────────────────────────────────┤
│ STUDENT INPUTS       │ OVERVIEW / SYSTEM TABS                             │
│                      │                                                     │
│ Power & engine       │ [Overview] [Fuel] [Idle] [Cooling] [Start/Run]     │
│ Battery              │                                                     │
│ RPM                  │ Dependency flow                                     │
│ TPS                  │ Inputs → ECU calculation → Outputs                  │
│ MAP                  │                                                     │
│ Accessory load       │ Live cards: measured / calculated / commanded       │
│                      │                                                     │
│ Fuel feedback        │ Status lamps and engine-state stepper               │
│ O2 voltage           │                                                     │
│                      │ Trend graph                                          │
│ Cooling sensors      │                                                     │
│ ECT1 voltage         │ Plain-language explanation                          │
│ ECT2 voltage         │                                                     │
│                      │                                                     │
│ Operating controls   │                                                     │
│ Ignition             │                                                     │
│ Fingerprint auth     │                                                     │
│ A/C request          │                                                     │
│ Start / Stop / E-stop│                                                     │
│                      │                                                     │
│ Presets              │                                                     │
└──────────────────────┴─────────────────────────────────────────────────────┘
```

On smaller screens, place the input panel above the system view or make it a drawer.

## 3. Header requirements

The header should include:

- page title;
- one-sentence overview;
- educational disclaimer;
- Run, Pause and Reset controls;
- simulation time;
- current engine state;
- CSV export control.

The educational disclaimer must remain visible or easily accessible:

> Simplified educational model; not Toyota 1NZ, OEM or production ECU calibration data. Do not use it for road-vehicle or safety-critical control.

## 4. Input panel

### 4.1 Numeric controls

Each numeric input should contain:

- plain-language label;
- unit;
- range slider;
- number field;
- visible minimum and maximum;
- accepted/capped value if the user enters an out-of-range number;
- short tooltip explaining where the signal is used.

### 4.2 Binary controls

Use switches for:

- ignition switch;
- fingerprint authorised;
- A/C request.

Use momentary buttons for:

- voice/manual start request;
- normal stop request.

Use a latching emergency-stop control that remains active until reset.

### 4.3 Presets

Provide:

- Warm idle;
- Lean oxygen response;
- High cooling demand;
- Idle load disturbance;
- ECT sensor disagreement.

A preset changes sensor and operating inputs only. It must not force the engine state or bypass the start logic.

## 5. Overview tab

The overview should show the four systems as linked cards:

1. Fuel and injection
2. Idle and ignition
3. Cooling
4. Start and run

Each card should contain:

- the main dependency flow;
- two or three important current values;
- active/inactive status;
- a control that opens the detailed tab.

Also display the data categories:

- **Measured/status input**
- **ECU-calculated value**
- **Commanded output**
- **Operating status**

## 6. Fuel and injection tab

### Dependency flow

```text
Oxygen-sensor voltage
→ Lambda estimate
→ STFT / equivalent closed-loop correction
→ Injector pulse width
```

### Required values

Measured inputs:

- O2 sensor voltage
- Engine speed
- MAP
- TPS
- ECT1 temperature
- Battery voltage

Calculated values:

- Engine load
- Lambda estimate
- STFT/equivalent closed-loop correction
- Warm-up enrichment
- Battery compensation
- Base injector pulse width

Commanded output:

- Final injector pulse width

Statuses:

- Injection enabled
- Closed loop active

### Plain-language explanation

Generate a live sentence such as:

> O2 voltage is below the switching region, so the simplified model estimates a lean condition. Positive fuel correction increases injector pulse width.

## 7. Idle and ignition tab

### Dependency flow

```text
ECT1 temperature + actual RPM + accessory load
→ Target idle RPM + RPM error
→ Idle-control duty + ignition timing
```

### Required values

Measured inputs:

- Actual RPM
- TPS
- MAP
- ECT1 temperature
- Accessory load

Calculated values:

- Target idle RPM
- RPM error

Commanded outputs:

- Idle-control duty
- Ignition timing

Status:

- Idle active

### Plain-language explanation

Example:

> Actual RPM is below the coolant-dependent target. The model increases idle-control duty to reduce the error.

## 8. Cooling tab

### Dependency flow

```text
ECT1 voltage + ECT2 voltage
→ ECT1 temperature + ECT2 temperature
→ Sensor difference + control temperature
→ Fan duty + virtual electric-water-pump duty
```

### Required values

Measured inputs:

- ECT1 voltage
- ECT2 voltage
- A/C request
- Battery voltage

Calculated values:

- ECT1 temperature
- ECT2 temperature
- Sensor difference
- Control temperature

Commanded outputs:

- PWM fan duty
- Virtual electric-water-pump duty

Statuses:

- Sensor disagreement
- Cooling loop active

### Fail-safe display

When ECT difference exceeds 15 °C, clearly display:

> ECT sensor disagreement detected. The virtual fail-safe commands 100% fan and pump duty.

The interface must identify ECT1 and ECT2 as virtual sensor inputs and label the water pump as **virtual**. Include a clear note that the separate physical 1NZ setup has no electric water pump and that the stages are tested independently with no comparison.

## 9. Start and run tab

### State display

Show this stepper:

```text
OFF → PRIME → CRANK → RUN → SHUTDOWN
```

Display:

- current state;
- elapsed time in state;
- reason a start is blocked, where applicable;
- prime timer;
- crank timeout.

### Inputs

- Ignition switch
- Fingerprint authorised
- Voice/manual start request
- Stop request
- Emergency stop
- Battery voltage
- Engine speed

### Outputs/statuses

- Start permitted
- Fuel-pump state
- Starter state
- Injection enable
- Ignition enable

Use clear status lamps or badges.

## 10. Graph behaviour

Keep at least 60 seconds of rolling history.

Recommended graph groups:

- Fuel: O2 voltage, lambda, STFT and injector PW
- Idle: actual RPM, target RPM, idle duty and ignition timing
- Cooling: ECT1, ECT2, fan duty and pump duty
- Start/run: state code, fuel-pump, starter, injection enable and ignition enable

Use the platform's existing chart library. Graphs should include:

- signal name;
- unit;
- legend;
- readable time axis;
- tooltip or cursor value where supported.

## 11. Simulation controls

### Run

Starts or resumes the 0.05-second fixed-step model.

### Pause

Stops virtual time while preserving inputs, engine state and history.

### Reset

Returns the engine state to OFF, clears elapsed state time and history, and returns operating controls to their safe defaults. Numeric sensor defaults may be restored or retained according to the platform's existing reset convention, but document the behaviour.

### Emergency stop

Immediately moves the start/run state logic towards SHUTDOWN and forces the cooling emergency branch. It remains latched until reset.

## 12. Export format

CSV should contain one row per recorded time point and at least:

- simulation time;
- accepted/capped input values;
- engine state and elapsed state time;
- all fuel calculations;
- all idle/ignition calculations;
- all cooling calculations;
- all commanded outputs;
- all binary statuses.

Use canonical signal names in the header so exported data can be read consistently.

## 13. Accessibility and teaching quality

- Do not communicate status by colour alone.
- Provide visible text labels for ON/OFF and ACTIVE/INACTIVE.
- Support keyboard operation for switches and buttons.
- Use sensible number formatting; retain enough precision to show relationships.
- Explain abbreviations such as ECT, MAP, TPS, STFT and PWM.
- Do not allow a student to edit ECU-calculated values directly.
