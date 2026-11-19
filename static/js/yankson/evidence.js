/* Selected-run provenance. No raw audio or credential material is collected. */
(() => {
  let runId = crypto.randomUUID();
  let started = performance.now();
  let createdAt = new Date().toISOString();
  let records = [];
  let trials = [];
  let references = [];
  let resetReason = "Initial load";
  let initialConfiguration = null;
  const engineSha256 =
    "7e34037a0d2c797f9594d8a9cca8dcb43ca1e8f60336bac74da27dfdb1360279";
  function add(type, detail = {}) {
    const entry = {
      runId,
      sequence: records.length + 1,
      type,
      utc: new Date().toISOString(),
      monotonicElapsedMs: performance.now() - started,
      modelTime: window.YanksonLab?.time ?? 0,
      ...detail,
    };
    records.push(entry);
    window.dispatchEvent(
      new CustomEvent("yankson:evidence", { detail: entry }),
    );
    return entry;
  }
  function begin(reason) {
    runId = crypto.randomUUID();
    started = performance.now();
    createdAt = new Date().toISOString();
    records = [];
    trials = [];
    references = [];
    resetReason = reason;
    initialConfiguration =
      window.YanksonCircuit?.snapshot().configuration ?? null;
    add("run-start", { reason, configuration: initialConfiguration });
  }
  window.YanksonEvidence = {
    begin,
    add,
    get runId() {
      return runId;
    },
    setInitialConfiguration(value) {
      if (!initialConfiguration) initialConfiguration = value;
    },
    trial(value) {
      const trial = {
        ...value,
        runId,
        timestamp: new Date().toISOString(),
        evidenceSequences: records
          .filter((r) =>
            ["speech", "microphone", "command-decision"].includes(r.type),
          )
          .map((r) => r.sequence),
      };
      trials.push(trial);
      return trial;
    },
    reference(value) {
      references.push({
        ...value,
        status:
          "operator-supplied reference; not independently verified by this page",
      });
    },
    snapshot() {
      return {
        schema: "atu.yankson.evidence.v1",
        runId,
        createdAt,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        deployment: JSON.parse(document.getElementById("platform-deployment")?.textContent || "null"),
        build: window.YanksonBuild || { scope: "Build identity unavailable" },
        generation: window.YanksonLab?.generation ?? null,
        historicalReportedTrials: {
          source: "Yankson_Codex_Retest_Corrections_17_Nov_2026.md",
          date: "2026-11-17",
          classification:
            "External retest report; original trial JSON not supplied with this brief",
          defaultPhrase: {
            phrase: "Hey Start",
            transcript: "hey start",
            identity: "practice identity (simulated)",
            outcome:
              "reported successful human start; starter OFF, run supply ON",
            crankModelTime: 10.34,
            runningModelTime: 12.03,
          },
          customPhrase: {
            phrase: "Yankson Start",
            finalResults: 7,
            matches: 0,
            outcome: "reported mismatches; no crank; not population accuracy",
          },
          association:
            "Historical external evidence, never attributed to the active run",
        },
        engineSha256,
        resetReason,
        environment: {
          browser: navigator.userAgent,
          secureContext: isSecureContext,
          microphoneApi: !!navigator.mediaDevices?.getUserMedia,
          recognitionApi: !!(
            window.SpeechRecognition || window.webkitSpeechRecognition
          ),
          platformAuthenticatorApi: !!window.PublicKeyCredential,
        },
        initialConfiguration,
        records: records.slice(),
        trials: trials.slice(),
        references: references.slice(),
        physicalObjective: {
          status: "NOT ACHIEVED",
          reason:
            "Time constraints prevented any construction attempt within the project period.",
        },
        humanVoiceEvidence: {
          attestedTrials: trials.filter(
            (t) => t.inputSource === "operator-attested human speech",
          ).length,
          classification:
            "Operator attestations and browser events require review together. Automated callbacks do not establish human recognition accuracy.",
        },
      };
    },
  };
  for (const type of ["input", "change"])
    document.addEventListener(type, (event) => {
      if (!event.target.closest("#ys-workbench,#yp-workbench,#ys-faults"))
        return;
      if (!event.target.id) return;
      add("control-change", {
        control: event.target.id,
        value:
          event.target.type === "checkbox"
            ? event.target.checked
            : event.target.value,
      });
    });
})();
