export function mountEvidenceControls() {
  const left = document.querySelector("#ys-inputs");
  const right = document.querySelector("#ys-output-pane");
  const controls = document.createElement("details");
  controls.className = "ys-input-group";
  controls.open = false;
  controls.innerHTML = `<summary>Experiment record and replay</summary>
    <p>Record every attempt, including failures. Human-source selections are operator attestations requiring review against the event log.</p>
    <label>Test ID and experiment question<input id="ye-question" class="form-control" maxlength="240"></label>
    <label>Baseline and one controlled change<textarea id="ye-change" class="form-control" maxlength="1500"></textarea></label>
    <label>Input source<select id="ye-source" class="form-select"><option>simulated test input</option><option>mocked browser callback</option><option>operator-attested human speech</option><option>operator-attested device verification</option></select></label>
    <label>Conditions, distance, noise and active identity<textarea id="ye-conditions" class="form-control" maxlength="1500"></textarea></label>
    <label>Expected result and pass criterion<textarea id="ye-expected" class="form-control" maxlength="1500"></textarea></label>
    <label>Observed result and explanation<textarea id="ye-observed" class="form-control" maxlength="1500"></textarea></label>
    <label>Trial result<select id="ye-result" class="form-select"><option>NOT RUN</option><option>PASS</option><option>FAIL</option><option>BLOCKED</option></select></label>
    <button id="ye-record" class="btn btn-outline-primary">Record this trial</button>
    <p id="ye-record-status" role="status"></p>
    <label>Evidence reference filename and description<input id="ye-reference" class="form-control" maxlength="500"></label>
    <button id="ye-attach" class="btn btn-outline-secondary">Attach reference to this run</button>
    <label>Validate an exported run<input id="ye-replay-file" type="file" accept="application/json,.json" class="form-control"></label>
    <p id="ye-replay-status" role="status">Replay validation uses saved deterministic input rows. It does not repeat spoken audio.</p>
    <label>Recorded animation speed<select id="ye-replay-speed" class="form-select"><option value=".25">0.25× slow motion</option><option value="1" selected>1×</option><option value="2">2×</option></select></label>
    <button id="ye-play" class="btn btn-outline-primary">Replay recorded animation</button>
    <button id="ye-pause" class="btn btn-outline-secondary">Pause recorded animation</button>
    <p id="ye-play-status" role="status">Replay is separate from the live calculation clock.</p>`;
  (document.getElementById("ys-input-advanced") || left).append(controls);
  const output = document.createElement("section");
  output.className = "content-panel";
  output.innerHTML =
    '<h2>Recorded trials and study evidence</h2><p id="ye-run-id"></p><p>Thesis results remain based on the recorded “Hey Start” demonstration. Stand images illustrate a future hardware concept; they are not evidence of physical construction.</p><div class="table-responsive" tabindex="0" role="region" aria-label="Selected-run trial records"><table class="table"><caption>Selected-run trials</caption><thead><tr><th>Test</th><th>Source</th><th>Expected</th><th>Observed</th><th>Status</th></tr></thead><tbody id="ye-trials"></tbody></table></div>';
  (document.getElementById("ys-output-advanced") || right).append(output);
  const get = (id) => document.getElementById(id);
  const evidence = window.YanksonEvidence;
  function render() {
    get("ye-run-id").textContent = "Run " + evidence.runId;
    get("ye-trials").replaceChildren(
      ...evidence.snapshot().trials.map((trial) => {
        const row = document.createElement("tr");
        for (const value of [
          trial.testId,
          trial.inputSource,
          trial.expected,
          trial.observed,
          trial.status,
        ]) {
          const cell = document.createElement("td");
          cell.textContent = value;
          row.append(cell);
        }
        return row;
      }),
    );
  }
  get("ye-record").onclick = () => {
    if (
      !get("ye-question").value.trim() ||
      !get("ye-expected").value.trim() ||
      !get("ye-observed").value.trim()
    ) {
      get("ye-record-status").textContent =
        "Provide a test question, expected criterion and observed result.";
      return;
    }
    evidence.trial({
      testId: get("ye-question").value.trim(),
      inputSource: get("ye-source").value,
      change: get("ye-change").value,
      conditions: get("ye-conditions").value,
      expected: get("ye-expected").value,
      observed: get("ye-observed").value,
      status: get("ye-result").value,
      activePhrase: document.getElementById("yp-command").value,
      identity: document.getElementById("yp-identity-source").textContent,
      configuration: window.YanksonCircuit.snapshot(),
    });
    get("ye-record-status").textContent =
      "Trial recorded in selected-run evidence. Export run JSON to save it.";
    render();
  };
  get("ye-attach").onclick = () => {
    if (!get("ye-reference").value.trim()) return;
    evidence.reference({ description: get("ye-reference").value.trim() });
    get("ye-record-status").textContent =
      "Reference attached. Independent verification remains a separate result.";
  };
  get("ye-replay-file").onchange = async (event) => {
    try {
      const file = event.target.files[0];
      if (!file || file.size > 30000000)
        throw Error("Select a run JSON file under 30 MB.");
      const data = JSON.parse(await file.text());
      const model = window.YanksonEngine;
      model.validateParameters(data.parameters);
      if (
        JSON.stringify(data.columns) !== JSON.stringify(model.columns) ||
        !Array.isArray(data.inputs) ||
        !data.inputs.length ||
        data.inputs.length > 30001 ||
        data.rows?.length !== data.inputs.length
      )
        throw Error("Incomplete input/output contract.");
      const engine = model.createEngine(data.parameters);
      let maximumError = 0;
      data.inputs.forEach((input, index) => {
        const expected = data.rows[index];
        if (
          !Array.isArray(input) ||
          input.length !== 19 ||
          !input.every(Number.isFinite) ||
          !Array.isArray(expected) ||
          expected.length !== 28 ||
          !expected.every(Number.isFinite)
        )
          throw Error("Invalid numeric sample.");
        if (Math.abs(input[0] - engine.time) > 1e-9)
          throw Error("Input times are not a complete fixed-step timeline.");
        engine.step(input.slice(1)).forEach((value, column) => {
          maximumError = Math.max(
            maximumError,
            Math.abs(value - expected[column]),
          );
        });
      });
      const passed = maximumError <= 1e-9;
      get("ye-replay-status").textContent =
        (passed ? "PASS" : "FAIL") +
        " · " +
        data.rows.length +
        " deterministic rows · maximum absolute error " +
        maximumError +
        " · tolerance 1e-9.";
      evidence.add("replay-validation", {
        status: passed ? "PASS" : "FAIL",
        rows: data.rows.length,
        maximumError,
        file: file.name,
        source: "saved effective inputs",
      });
    } catch (error) {
      get("ye-replay-status").textContent = "Replay rejected: " + error.message;
    }
  };
  let frame = 0;
  let cursor = 0;
  let last = 0;
  let replay = null;
  function stop() {
    cancelAnimationFrame(frame);
    last = 0;
  }
  get("ye-play").onclick = () => {
    stop();
    window.YanksonLab.pause();
    replay = window.YanksonLab.snapshot().rows;
    cursor = 0;
    if (!replay.length) return;
    function tick(now) {
      if (last)
        cursor += ((now - last) / 1000) * Number(get("ye-replay-speed").value);
      last = now;
      const sample =
        replay[Math.min(replay.length - 1, Math.floor(cursor / 0.01))];
      window.YanksonTeaching.replay(sample);
      get("ye-play-status").textContent =
        "Recorded model time " +
        sample[0].toFixed(2) +
        " s · replay " +
        Number(get("ye-replay-speed").value) +
        "× · live calculation paused.";
      if (cursor <= replay.at(-1)[0]) frame = requestAnimationFrame(tick);
    }
    frame = requestAnimationFrame(tick);
  };
  get("ye-pause").onclick = stop;
  for (const event of ["pagehide", "yankson:reset", "yankson:stop"])
    window.addEventListener(event, stop);
  window.addEventListener("yankson:run-start", render);
  render();
}
