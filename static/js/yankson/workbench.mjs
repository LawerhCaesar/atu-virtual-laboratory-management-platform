/* Move existing controls, preserving their listeners and unique identifiers. */
export function mountWorkbench() {
  const get = (selector) => document.querySelector(selector);
  const app = get("#yp-workbench");
  const bench = document.createElement("div");
  bench.id = "ys-workbench";
  const left = document.createElement("aside");
  left.id = "ys-inputs";
  left.setAttribute("aria-label", "Inputs and controls");
  const right = document.createElement("section");
  right.id = "ys-output-pane";
  right.setAttribute("aria-label", "Outputs and results");
  const heading = document.createElement("h2");
  heading.textContent = "Outputs and results";
  right.append(heading);
  app.before(bench);
  bench.append(left, right);
  const steps = document.createElement("p");
  steps.className = "ys-workflow";
  steps.textContent =
    "Check microphone → Test phrase only → Choose identity → Short contact and speak, or long contact → Observe → Save result";
  left.append(steps);
  function group(title, nodes) {
    const section = document.createElement("details");
    section.className = "ys-input-group";
    section.open = true;
    const label = document.createElement("summary");
    label.textContent = title;
    section.append(label);
    for (const node of nodes.filter(Boolean)) section.append(node);
    left.append(section);
    return section;
  }
  const clock = get("#ys-run").closest("section");
  clock.classList.add("ys-clock-controls");
  const master = get("#lab-master-reset");
  if (master) left.append(master.parentElement);
  const quick = document.createElement("div");
  quick.id = "ys-quick-controls";
  const buttons = document.createElement("div");
  buttons.className = "ys-quick-buttons";
  buttons.append(get("#ys-run"), get("#ys-stop"));
  quick.append(buttons, get("#ys-status"), get("#ys-time"));
  left.prepend(quick);
  left.append(clock);
  group("1 · Device and microphone setup", [
    get("#yp-check"),
    get("#yp-capabilities"),
    get("#ya-mic-start").parentElement,
  ]);
  const micDiagnostic = get("#ya-microphone");
  right.append(micDiagnostic);
  micDiagnostic.querySelector("details").open = true;
  group("2 · Identity and measured contact", [
    get(".ys-device-panel"),
    get("#yp-practice").closest("label"),
    get("#yp-hold").closest("section"),
  ]);
  group("3 · Personal voice command", [get("#yp-command").closest("section")]);
  group("4 · Simulated test events", [get("#ys-short").closest("section")]);
  group("5 · Components and connections", [get("#yp-circuit")]);
  const wiring = get(".yp-diagram-scroll");
  right.append(wiring, get("#yp-wiring-status"));
  group("6 · Electrical inputs", [
    get("#ya-electric-fields"),
    get("#ya-check").parentElement,
  ]);
  group("7 · Timing and CAN parameters", [
    get("#yp-parameters").closest("details"),
    get("#ys-faults"),
  ]);
  group("8 · Guided experiments", [get("#yp-experiments").closest("details")]);
  group("9 · Lecturer exercises", [
    get("#ya-exercise-title").closest("details"),
  ]);
  const exports = get("#ys-csv").parentElement;
  const exportPanel = document.createElement("section");
  exportPanel.className = "content-panel";
  exportPanel.append(exports);
  right.append(exportPanel);
  group("Output view and camera", [
    get("#ya-tab-engine").closest("nav"),
    get("#ya-camera-wide").parentElement,
  ]);
  const status = get(".yp-status-grid");
  status.append(get("#yp-reason"));
  const statusDetails = document.createElement("details");
  statusDetails.id = "ys-status-details";
  const statusLabel = document.createElement("summary");
  statusLabel.textContent = "Detailed readiness, contact and latest decision";
  statusDetails.append(statusLabel, status);
  const strip = document.createElement("div");
  strip.id = "ys-readiness-strip";
  strip.setAttribute("aria-label", "Current test status");
  right.prepend(strip, statusDetails);
  const latestSpeech = document.createElement("p");
  latestSpeech.id = "ys-latest-speech";
  latestSpeech.className = "small";
  right.insertBefore(latestSpeech, statusDetails);
  let statusOutputs = [];
  function statusStrip(row = window.YanksonLab.row) {
    const values = [
      ["Capture", get("#ya-mic-status").dataset.state || "NOT RUN"],
      ["Recognition", get("#yp-speech").dataset.state || "NOT RUN"],
      [
        "Identity",
        get("#yp-identity-source").textContent.replace("Identity: ", ""),
      ],
      [
        "Contact",
        get("#yp-contact-result").textContent.split(". Model")[0] ||
          "not measured",
      ],
      [
        "Permission",
        row[2]
          ? Math.max(
              0,
              window.YanksonLab.parameters[3] - (row[0] - row[24]),
            ).toFixed(1) + " s model"
          : "none",
      ],
      ["Starter request", row[3] ? "ON" : "OFF"],
      ["Run request", row[7] ? "ON" : "OFF"],
      ["CAN", row[5] ? "VALID" : "INVALID"],
      ["Engine", row[8].toFixed(0) + " RPM"],
    ];
    if (!statusOutputs.length) {
      strip.replaceChildren(
        ...values.map(([name]) => {
          const card = document.createElement("div");
          const label = document.createElement("strong");
          const text = document.createElement("span");
          label.textContent = name;
          statusOutputs.push(text);
          card.append(label, text);
          return card;
        }),
      );
    }
    values.forEach((entry, index) => {
      statusOutputs[index].textContent = entry[1];
    });
    const transcript = get("#yp-transcript").textContent;
    const diagnostic = get("#yp-diagnostic-count").textContent;
    latestSpeech.textContent = transcript
      ? transcript + " · " + diagnostic
      : diagnostic;
  }
  window.addEventListener("yankson:sample", (event) =>
    statusStrip(event.detail),
  );
  window.addEventListener("yankson:microphone", () => statusStrip());
  window.addEventListener("yankson:evidence", () => statusStrip());
  statusStrip();
  for (const selector of [
    "#yp-capabilities",
    "#ya-device-status",
    "#yp-contact-result",
    "#yp-progress",
    "#yp-speech",
    "#yp-transcript",
    "#yp-diagnostic-count",
    "#ys-contact",
    "#ys-auth",
    "#ys-reject",
  ]) {
    const result = get(selector);
    if (result) status.append(result);
  }
  right.insertBefore(get("#yp-reason"), statusDetails);
  right.insertBefore(get("#yp-phrase-check"), statusDetails);
  const guideDownload = get("#ya-learning a[download]");
  if (guideDownload) exportPanel.append(guideDownload);
  right.append(
    get("#ya-results"),
    get("#ys-supervisor"),
    get("#ys-chart").closest("section"),
    get("#ys-results"),
  );
  get("#ya-circuit-panel").prepend(wiring);
  get("#ya-signals-panel").prepend(micDiagnostic);
  right.insertBefore(get("#ya-results"), heading.nextSibling);
  for (const selector of ["#ya-mic-start", "#yp-test-phrase"]) {
    get(selector).addEventListener("click", () =>
      get("#ya-tab-signals").click(),
    );
  }
  app.hidden = true;
  app.setAttribute("aria-hidden", "true");

  const emptyDetails = get("#ys-supervisor").closest("details");
  if (emptyDetails && !emptyDetails.querySelector("input,button,section"))
    emptyDetails.remove();
  window.dispatchEvent(new Event("yankson:workbench-ready"));
}
