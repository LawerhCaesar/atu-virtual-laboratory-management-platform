// Local capture diagnostic. Audio samples remain in memory for the visible analyser.
export function mountMicrophone(host) {
  host.innerHTML = `<details open><summary>Check your actual microphone · waveform and sample bytes</summary>
    <p>Test capture before requesting engine permission. Watch the waveform while speaking, then stop. Recognition is checked separately.</p>
    <div class="ys-buttons"><button id="ya-mic-start" class="btn btn-outline-primary">Test microphone</button><button id="ya-mic-stop" class="btn btn-outline-secondary">Stop microphone test</button></div>
    <p id="ya-mic-status" role="status">Microphone test is off.</p>
    <canvas id="ya-mic-wave" width="700" height="100" role="img" aria-label="Live local microphone waveform"></canvas>
    <pre id="ya-mic-bytes">No samples. Diagnostic bytes are not saved or exported.</pre></details>`;
  const get = (id) => document.getElementById(id);
  let stream = null;
  let context = null;
  let frame = 0;
  let generation = 0;
  let guidanceTimer = 0;
  const events = [];

  function state(code, message) {
    get("ya-mic-status").dataset.state = code;
    get("ya-mic-status").textContent = message;
    events.push({
      code,
      message,
      monotonicMs: performance.now(),
      runId: window.YanksonLab.runId,
    });
    window.dispatchEvent(
      new CustomEvent("yankson:microphone", { detail: events.at(-1) }),
    );
  }
  function stop(message = "Microphone test stopped.", code = "STOPPED") {
    generation++;
    clearTimeout(guidanceTimer);
    cancelAnimationFrame(frame);
    stream?.getTracks().forEach((track) => track.stop());
    stream = null;
    const previousContext = context;
    context = null;
    previousContext?.close().catch(() => {});
    get("ya-mic-start").disabled = false;
    get("ya-mic-bytes").textContent = "No retained audio samples.";
    state(code, message);
  }
  get("ya-mic-stop").onclick = () => stop();
  get("ya-mic-start").onclick = async () => {
    stop();
    const epoch = generation;
    get("ya-mic-start").disabled = true;
    state(
      "REQUESTING",
      "Requesting microphone access. Choose Allow in the browser prompt, or Cancel this test.",
    );
    guidanceTimer = setTimeout(() => {
      if (epoch === generation && !stream)
        state(
          "WAITING_FOR_PERMISSION",
          "Still waiting for microphone access. An unanswered prompt is not a denial. Check the address-bar microphone icon, or cancel and retry.",
        );
    }, 5000);
    try {
      if (!isSecureContext || !navigator.mediaDevices?.getUserMedia)
        throw new Error(
          "Microphone capture requires HTTPS or localhost and a supported browser.",
        );
      const acquired = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });
      if (epoch !== generation) {
        acquired.getTracks().forEach((track) => track.stop());
        return;
      }
      clearTimeout(guidanceTimer);
      stream = acquired;
      const localContext = new (
        window.AudioContext || window.webkitAudioContext
      )();
      context = localContext;
      await localContext.resume();
      if (epoch !== generation) {
        acquired.getTracks().forEach((track) => track.stop());
        await localContext.close().catch(() => {});
        return;
      }
      for (const track of stream.getTracks())
        track.addEventListener("ended", () => {
          if (epoch === generation)
            stop(
              "The microphone track ended. Check the device and retry.",
              "TRACK_ENDED",
            );
        });
      const analyser = context.createAnalyser();
      analyser.fftSize = 256;
      context.createMediaStreamSource(stream).connect(analyser);
      const data = new Uint8Array(256);
      const paint = get("ya-mic-wave").getContext("2d");
      state("CAPTURING", "Capture active. Speak to check the local waveform.");
      let last = 0;
      function tick(time) {
        if (epoch !== generation || !stream) return;
        if (time - last >= 80) {
          last = time;
          analyser.getByteTimeDomainData(data);
          let squared = 0;
          paint.clearRect(0, 0, 700, 100);
          paint.strokeStyle = "#73e3cb";
          paint.lineWidth = 2;
          paint.beginPath();
          data.forEach((value, index) => {
            const x = (index * 700) / 255;
            const y = (value * 100) / 255;
            if (index) paint.lineTo(x, y);
            else paint.moveTo(x, y);
            squared += ((value - 128) / 128) ** 2;
          });
          paint.stroke();
          const rms = Math.sqrt(squared / data.length);
          get("ya-mic-status").textContent =
            `Live microphone · level ${Math.round(rms * 100)}% RMS of full scale · ${context.sampleRate} samples/s. ${rms < 0.003 ? "Very quiet. Check the selected input." : "Signal detected. Test phrase recognition separately."}`;
          get("ya-mic-bytes").textContent =
            "Latest 16 analyser bytes (128 is approximately silence)\n" +
            Array.from(data.slice(0, 16), (value) =>
              value.toString(2).padStart(8, "0"),
            ).join(" ");
        }
        frame = requestAnimationFrame(tick);
      }
      frame = requestAnimationFrame(tick);
    } catch (error) {
      if (epoch !== generation) return;
      const messages = {
        NotAllowedError:
          "Microphone permission denied. Check browser site settings.",
        NotFoundError: "No audio input was found.",
        NotReadableError: "Microphone is busy or unreadable.",
        AbortError: "Audio capture was interrupted.",
        SecurityError: "Browser security settings prevent capture.",
      };
      stop(
        (messages[error.name] || error.message) + " [" + error.name + "]",
        "ERROR",
      );
    }
  };
  for (const name of [
    "pagehide",
    "yankson:stop",
    "yankson:recognition-request",
  ])
    window.addEventListener(name, () => stop());
  window.addEventListener("yankson:reset", () => {
    stop();
    events.length = 0;
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop("Page hidden. Capture stopped.");
  });
  window.YanksonMicrophone = {
    stop,
    trace: () => events.slice(),
    get capturing() {
      return !!stream;
    },
  };
}
