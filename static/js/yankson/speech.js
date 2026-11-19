/* Recognition lifecycle only. Engine authorization remains in practical.js. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.YanksonSpeech = api;
})(typeof globalThis === "undefined" ? this : globalThis, function () {
  const normalize = (value) =>
    value
      .normalize("NFKC")
      .toLocaleLowerCase("en")
      .replace(/[\p{P}\p{S}]/gu, " ")
      .replace(/\s+/g, " ")
      .trim();

  function create({
    recognitionFactory,
    status,
    event,
    result,
    beforeStart = () => {},
    startupMs = 8000,
    sessionMs = 20000,
    timers = globalThis,
    now = () => performance.now(),
  }) {
    let active = null;
    let sequence = 0;

    function report(request, code, detail = {}) {
      event({
        requestId: request.id,
        mode: request.mode,
        runId: request.context.runId,
        targetPhrase: request.phrase,
        language: request.context.language || "en-US",
        permissionAtRequest: request.context.permissionAtRequest ?? null,
        identity: request.context.identity || "unknown",
        requestToEventMs: now() - request.requestedAt,
        timingMeaning: "Time from service request; acoustic onset not measured",
        code,
        errorCode: request.errorCode || null,
        monotonicMs: now(),
        ...detail,
      });
    }
    function finish(request, code, message, abort = false) {
      if (active !== request) return;
      active = null;
      timers.clearTimeout(request.startupTimer);
      timers.clearTimeout(request.endTimer);
      report(request, code, { message });
      status(code, message, false);
      if (abort) {
        try {
          request.recognition.abort();
        } catch {}
      }
    }
    function cancel(reason = "Cancelled by user.") {
      if (active) finish(active, "CANCELLED", reason, true);
    }
    function start(mode, phrase, context = {}) {
      if (active) return false;
      beforeStart();
      const request = {
        id: ++sequence,
        requestedAt: now(),
        mode,
        phrase,
        context,
        started: false,
        consumed: false,
      };
      try {
        request.recognition = recognitionFactory();
        if (!request.recognition)
          throw new Error("Speech recognition unavailable in this browser.");
        active = request;
        status(
          "REQUESTING",
          "Requesting recognition. Check the browser microphone prompt.",
          true,
        );
        report(request, "REQUESTING");
        const recognition = request.recognition;
        recognition.lang = context.language || "en-US";
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.onstart = () => {
          if (active !== request) return;
          request.started = true;
          timers.clearTimeout(request.startupTimer);
          report(request, "start");
          status("LISTENING", "Listening… say “" + phrase + "”.", true);
        };
        for (const name of [
          "audiostart",
          "soundstart",
          "speechstart",
          "speechend",
          "soundend",
          "audioend",
        ]) {
          recognition["on" + name] = () => {
            if (active === request) report(request, name);
          };
        }
        recognition.onresult = (response) => {
          if (active !== request || request.consumed) return;
          const final = Array.from(response.results).find(
            (item) => item.isFinal,
          );
          if (!final) return;
          request.consumed = true;
          const transcript = final[0].transcript;
          const detail = {
            phrase: transcript,
            normalized: normalize(transcript),
            matched: normalize(transcript) === normalize(phrase),
            requestId: request.id,
            mode,
            context,
            receivedMonotonicMs: now(),
          };
          report(request, "result", detail);
          finish(
            request,
            "RESULT",
            (detail.matched ? "MATCH" : "NO MATCH") +
              " — recognized “" +
              transcript +
              "”.",
            true,
          );
          result(detail);
        };
        recognition.onnomatch = () =>
          finish(request, "NO_MATCH", "No matching speech was returned.", true);
        recognition.onerror = (error) => {
          request.errorCode = error.error;
          const explanations = {
            "not-allowed": "Microphone permission denied.",
            "audio-capture": "No usable microphone. Check the selected input.",
            "no-speech": "No speech detected.",
            network: "Speech service network failure.",
            aborted: "Listening cancelled.",
            "service-not-allowed": "Speech service unavailable.",
          };
          finish(
            request,
            "ERROR",
            (explanations[error.error] || "Recognition service error.") +
              " [" +
              error.error +
              "]",
            true,
          );
        };
        recognition.onend = () => {
          report(request, "end");
          if (active === request)
            finish(
              request,
              "NO_RESULT",
              "Recognition ended without a final transcript.",
            );
        };
        request.startupTimer = timers.setTimeout(
          () =>
            finish(
              request,
              "STARTUP_TIMEOUT",
              "Recognition has not started. The permission prompt may still be unanswered, or the service may be unavailable. Cancelled safely. Retry after checking both.",
              true,
            ),
          startupMs,
        );
        request.endTimer = timers.setTimeout(
          () =>
            finish(
              request,
              "SESSION_TIMEOUT",
              "Recognition timed out without a final result.",
              true,
            ),
          sessionMs,
        );
        status(
          "STARTING SERVICE",
          "Starting recognition service. Listening begins only after its start event.",
          true,
        );
        recognition.start();
        return true;
      } catch (error) {
        if (active === request)
          finish(
            request,
            "ERROR",
            "Could not start recognition: " + error.message,
            true,
          );
        else status("UNSUPPORTED", error.message, false);
        return false;
      }
    }
    return {
      start,
      cancel,
      get active() {
        return active;
      },
    };
  }
  return { normalize, create };
});
