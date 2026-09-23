const form = document.getElementById("brief-form");
const generateBtn = document.getElementById("generate");
const emptyEl = document.getElementById("empty");
const resultEl = document.getElementById("result");
const modeBadge = document.getElementById("mode-badge");

function gradeColor(grade) {
  return (
    {
      A: "var(--good)",
      B: "var(--good)",
      C: "var(--warn)",
      D: "var(--warn)",
      F: "var(--bad)",
    }[grade] || "var(--muted)"
  );
}

async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.mode === "live") {
      modeBadge.textContent = "LIVE xAI";
      modeBadge.className = "badge badge-live";
    } else {
      modeBadge.textContent = "OFFLINE MODE";
      modeBadge.className = "badge badge-muted";
    }
  } catch {
    modeBadge.textContent = "OFFLINE MODE";
    modeBadge.className = "badge badge-muted";
  }
}

function render(result) {
  emptyEl.classList.add("hidden");
  resultEl.classList.remove("hidden");

  const { script, score, audioUrl, audio } = result;

  const ring = document.getElementById("score-ring");
  ring.style.setProperty("--val", score.overall);
  document.getElementById("score-value").textContent = score.overall;

  const gradeBadge = document.getElementById("grade-badge");
  gradeBadge.textContent = `Grade ${score.grade}`;
  gradeBadge.style.color = gradeColor(score.grade);
  gradeBadge.style.borderColor = gradeColor(score.grade);

  document.getElementById("episode-title").textContent = script.title;
  document.getElementById("episode-sub").textContent =
    `${script.wordCount} words · ~${script.estimatedSeconds}s · ${script.source} (${script.model})`;

  const notes = document.getElementById("score-notes");
  notes.innerHTML = "";
  score.notes.forEach((n) => {
    const li = document.createElement("li");
    li.textContent = n;
    notes.appendChild(li);
  });

  const metrics = document.getElementById("metrics");
  metrics.innerHTML = "";
  score.metrics.forEach((m) => {
    const el = document.createElement("div");
    el.className = "metric";
    el.innerHTML = `
      <span class="label">${m.label}</span>
      <span class="track"><span class="fill" style="width:${m.score}%"></span></span>
      <span class="val">${m.score}</span>
      <span class="detail">${m.detail}</span>`;
    metrics.appendChild(el);
  });

  const retention = document.getElementById("retention");
  retention.innerHTML = "";
  score.retentionCurve.forEach((r) => {
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${Math.round(r * 100)}%`;
    bar.title = `${Math.round(r * 100)}% retained`;
    retention.appendChild(bar);
  });

  const player = document.getElementById("player");
  player.src = audioUrl;
  document.getElementById("audio-meta").textContent =
    `${audio.format.toUpperCase()} · ${audio.durationSeconds}s · ${Math.round(
      audio.bytes / 1024,
    )} KB · voice=${audio.voice} · source=${audio.source}`;

  const scriptEl = document.getElementById("script");
  scriptEl.innerHTML = "";
  script.segments.forEach((seg) => {
    const el = document.createElement("div");
    el.className = "seg";
    el.innerHTML = `<span class="tag ${seg.role}">${seg.role}</span><div>${seg.text}</div>`;
    scriptEl.appendChild(el);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  generateBtn.disabled = true;
  generateBtn.textContent = "Generating…";
  try {
    const payload = {
      product: document.getElementById("product").value,
      audience: document.getElementById("audience").value,
      keyPoints: document
        .getElementById("points")
        .value.split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
      tone: document.getElementById("tone").value,
      targetSeconds: Number(document.getElementById("seconds").value) || 60,
    };
    const res = await fetch("/api/episode", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.json()).error || "Request failed");
    render(await res.json());
  } catch (err) {
    alert(`Failed to generate episode: ${err.message}`);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Generate episode";
  }
});

loadHealth();
