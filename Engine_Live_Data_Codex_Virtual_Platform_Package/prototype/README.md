# Standalone Reference Prototype — Engine Demonstration Section

**REFERENCE ONLY: DO NOT BUILD A NEW PLATFORM.** This prototype illustrates the behaviour to implement as one Engine Live-Data Demonstration section inside the colleague's existing virtual automotive platform. The authoritative implementation instructions are in `../CODEX_MASTER_PROMPT.md`.

The prototype's original code, styling and “Engine Live-Data Virtual Laboratory” title are retained for reference. They do not require a new application, a copied platform shell, an iframe embedding or a redesign. Codex must first inspect and reuse the host repository's routing, components, styles and state conventions.

Open `index.html` in a modern browser. No installation, server or internet connection is required.

The prototype demonstrates:

- capped numeric inputs;
- ignition, fingerprint authorisation, A/C, start, stop and E-stop controls;
- the four required engine systems;
- exact reference calculations;
- the start/run state machine;
- live explanations;
- 60-second rolling history;
- CSV export.

The trend graph normalises each selected signal to its own configured range so signals with different units can be seen together. The actual numerical values remain visible in the cards and legend.

This prototype is a reference, not a requirement to replace the existing platform's framework or design system. Codex should integrate the same behaviour using the repository's existing components and chart library.

ECT1/ECT2, the duty-controlled fan and the electric-water-pump output shown here are virtual model elements. The separate physical 1NZ setup has no electric water pump. Virtual and physical stages are tested independently with no comparison.
