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
        followUpReportedEvidence: {
          source: "Yankson_Codex_Follow_Up_With_Test_Results.txt",
          classification: "Owner-supplied summaries; underlying Windows trace and screenshot archive not inspected in this local review. Separate from current-run trials.",
          november21: {
            date: "2026-11-21", identity: "practice identity (simulated)", contact: "mouse press; no physical fingerprint reader tested",
            microphone: "Owner confirmed waveform moved with voice; capture only, not recognition accuracy",
            shortAuthorizationModelTimes: [1.44, 6.55, 8.28],
            shortMeasuredSeconds: [1.4279, 0.2122, 0.2000],
            directStart: {measuredContactSeconds: 1.7782, modelContactSeconds: 1.61, crankingModelTime: 12.08, runningModelTime: 13.77, crankIntervalSeconds: 1.69, finalRPMApproximate: 750, starter: "OFF", runSupply: "ON", can: "VALID"},
            voiceRetest: "NOT COMPLETED: source none, recognitionEvidence empty, voice_accepted zero across 16347 rows; NOT RUN recognition. Listen after direct start had no permission. Not proof of recognizer failure.",
            blockedListenModelTimes: [17.62, 21.28, 26.59],
            originalRunId: "28c052cf-4a54-4c90-9a8b-7dd9784e496a",
            reportedRawSha256: "8e35b2b21837ca93c0b6814e7ba47e92b036754136e8dab331a86c705485023b"
          },
          november20: "Reset record isolation reported successful; stale visible contact value required correction. Start Engine phrase-only diagnostic matched without crank; complete personalized spoken start not completed.",
          november17: {
            measuredContactSeconds: 1.0367, modelContactSeconds: 1.04, authorizationModelTime: 1.06,
            phrase: "Hey Start", transcript: "hey start", match: true, voiceAcceptedModelTime: 10.34,
            crankingModelTime: 10.34, runningModelTime: 12.03, crankIntervalSeconds: 1.69,
            rows: 11669, columns: 28,
            historicalMetadataDiscrepancy: "The original export reportedly says human recognition trials were not performed, conflicting with its recognized phrase, accepted event and contemporaneous observation. Preserve that original; this note explains the discrepancy without rewriting it."
          }
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
          status: "OUTSIDE VIRTUAL STUDY SCOPE",
          reason:
            "This study is virtual-only. Stand images are future concepts, not physical construction evidence. This describes new exports; original historical exports are preserved unchanged.",
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
