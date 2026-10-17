const panel = document.querySelector(".welcome-learning");
if (panel) {
  const byId = id => document.getElementById(id);
  const recent = [panel.dataset.factId];
  let timer, paused = false, busy = false, stopped = false;
  const next = byId("learning-next"), pause = byId("learning-pause");
  next.hidden = false; pause.hidden = false;
  function schedule() {
    clearTimeout(timer);
    if (!paused && !document.hidden && !stopped) timer = setTimeout(refresh, 60000);
  }
  function sourceUrl(value, hosts) {
    const url = new URL(value);
    if (url.protocol !== "https:" || !hosts.includes(url.hostname) || url.username || url.password) throw new Error("Invalid source");
    return url.href;
  }
  async function refresh(manual = false) {
    if (busy || stopped) return;
    clearTimeout(timer); busy = true; next.disabled = true;
    const abort = new AbortController(), timeout = setTimeout(() => abort.abort(), 5000);
    try {
      const url = new URL(panel.dataset.factUrl, location.origin);
      recent.forEach(id => url.searchParams.append("exclude", id));
      const response = await fetch(url, {signal: abort.signal, cache: "no-store", credentials: "omit", headers: {Accept: "application/json"}});
      if (!response.ok) throw new Error("Facts unavailable");
      const fact = await response.json();
      if (stopped || (paused && !manual)) return;
      if (!fact || typeof fact.id !== "string" || typeof fact.title !== "string" || typeof fact.text !== "string" || typeof fact.source_name !== "string") throw new Error("Invalid fact");
      const source = sourceUrl(fact.source_url, ["en.wikipedia.org", "afdc.energy.gov"]);
      const license = fact.license_url ? sourceUrl(fact.license_url, ["creativecommons.org"]) : "";
      if (fact.id === recent.at(-1)) throw new Error("Repeated current fact");
      byId("learning-topic").textContent = fact.title;
      byId("learning-text").textContent = fact.text;
      byId("learning-source").href = source;
      byId("learning-source").textContent = `Read more · ${fact.source_name}`;
      byId("learning-credit").textContent = fact.credit;
      byId("learning-license").hidden = !license;
      if (license) byId("learning-license").href = license;
      byId("learning-note").textContent = `${fact.mode === "online" ? "Random online learning" : "Source-checked backup"} · ${paused ? "Rotation paused." : "Changes every 60 seconds."} Facts may repeat over time.`;
      recent.push(fact.id); if (recent.length > 10) recent.shift();
      if (manual) byId("learning-announcement").textContent = `New fact: ${fact.title}`;
    } catch {
      if (!stopped) byId("learning-note").textContent = `Unable to refresh. Keeping this sourced fact. ${paused ? "Rotation paused." : "Retrying in 60 seconds."}`;
      if (manual && !stopped) byId("learning-announcement").textContent = "Unable to refresh. The previous sourced fact is still displayed.";
    } finally {
      clearTimeout(timeout); busy = false; next.disabled = false; schedule();
    }
  }
  next.addEventListener("click", () => refresh(true));
  pause.addEventListener("click", () => {
    paused = !paused; pause.setAttribute("aria-pressed", String(paused));
    pause.textContent = paused ? "Resume rotation" : "Pause rotation";
    byId("learning-note").textContent = paused ? "Rotation paused. You can still request another fact." : "Random automotive learning · Changes every 60 seconds. Facts may repeat over time.";
    schedule();
  });
  document.addEventListener("visibilitychange", schedule);
  window.addEventListener("pagehide", () => { stopped = true; clearTimeout(timer); });
  window.addEventListener("pageshow", event => { if (event.persisted) { stopped = false; schedule(); } });
  refresh();
}
