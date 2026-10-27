# Common vehicle reference for platform visualisations

The user-supplied **Common Baseline Values and Standard Format for All Platforms** establishes Genesis GV70 as the shared vehicle identity. Future vehicle visualisations should use its common proportions and identify deviations as model-specific. It does not supply a 3D mesh, exterior images, CAD, internal component layout, material details or a specific trim; these dimensions alone cannot establish exact manufacturer geometry or an accurate internal fuel system. Current illustrations remain labelled as generic until suitable references are available and verified.

A copy of the supplied source is retained at `docs/reference/vehicle-baseline.pdf` (SHA-256 `898642ee3ca7c12d00558ea62eca6b4d28231a7fe7556f5ad8d9162525c58fd1`).

The shared values are maintained in `apps/core/vehicle_baseline.py`: mass 2,000 kg (rounded project assumption); four wheels; 235/55R19 tyres; radius 0.371 m; wheelbase 2.875 m; front, rear and average track widths 1.649 m, 1.665 m and 1.657 m; assumed centre-of-gravity height 0.600 m; length 4.715 m, width 1.910 m and height 1.630 m. These are design references, not measurements of an individual vehicle.

The document calls for SI calculation units, consistent project-defined `System_Parameter` signal names, and common road-vehicle dynamics terminology referencing ISO 8855. A display speed in km/h may accompany calculation speed in m/s. Final drive, axle layout, gradient, friction, payload, drive cycle and topic-specific component sizes remain adjustable where relevant to the model. Do not assert that a signal is calculated or that an input is adjustable unless the module actually supports it.

## Current model deviations

- Wheel-Slip: documented module defaults are 1,500 kg and 0.31 m; both can be changed. Its current car is a generic side-view illustration.
- BrakeLab: documented default mass is 1,500 kg and fixed wheel-radius calibration is 0.31 m. Its current car is a generic energy-flow diagram.
- Fuel Delivery: the solver does not model vehicle mass, dimensions or GV70 component geometry; the 3D assembly is generic.
- 12 V Micro-Hybrid: the aggregate stop-start calculation does not use body or wheel geometry; the car is an illustrative sequence.

Do not silently alter these module-specific specifications or acceptance results. A deliberate baseline scenario or a change to model defaults requires reconciling the module source and updating verification and result documentation. Do not rename existing integration fields in a breaking change; map canonical signal names with documented units when an integration contract is implemented.
