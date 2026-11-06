(() => {
  const $ = (id) => document.getElementById(id);
  const input = $("imageInput"), zone = $("dropzone"), form = $("uploadForm");
  const selected = $("selectedFile"), fileName = $("fileName"), clear = $("clearFile");
  const button = $("analyzeButton"), buttonText = $("buttonText");
  const title = $("dropTitle"), subtitle = $("dropSubtitle"), visual = $("uploadVisual");
  const intro = $("cinematicIntro"), transition = $("scanTransition");
  const themeToggle = $("themeToggle"), themeIcon = $("themeIcon"), themeLabel = $("themeLabel");
  const skipBtn = $("skipIntroBtn"), replayBtn = $("replayIntroBtn");
  const cardWrapper = $("nexaCardWrapper");
  const initialVisual = visual ? visual.innerHTML : "";
  const allowed = ["image/jpeg", "image/png", "image/webp"];
  let stageTimers = [];
  let introTimers = [];
  let introActive = false;

  const year = $("year");
  if (year) year.textContent = new Date().getFullYear();

  // Theme selection is remembered locally in this browser.
  const savedTheme = (() => { try { return localStorage.getItem("nexavision-theme"); } catch (_) { return null; } })();
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    const isLight = theme === "light";
    if (themeIcon) themeIcon.textContent = isLight ? "☾" : "☼";
    if (themeLabel) themeLabel.textContent = isLight ? "Dark mode" : "Light mode";
    if (themeToggle) themeToggle.setAttribute("aria-label", isLight ? "Switch to dark theme" : "Switch to light theme");
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = isLight ? "#f4f7fc" : "#080d1b";
  }
  applyTheme(savedTheme === "light" ? "light" : "dark");
  themeToggle?.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    applyTheme(next);
    try { localStorage.setItem("nexavision-theme", next); } catch (_) {}
  });

  // =========================================================================
  // 3D CARD INTRO CONTROLLER: POP UP -> 3D ROTATE -> POP DOWN -> WEBSITE OPEN
  // =========================================================================
  function clearIntroTimers() {
    introTimers.forEach((id) => clearTimeout(id));
    introTimers = [];
  }

  function finishIntro() {
    if (!intro || !introActive) return;
    introActive = false;
    clearIntroTimers();

    // 1. Trigger the smooth fade-out and lift of the intro backdrop
    intro.classList.add("is-fading-out");
    document.body.classList.add("intro-finished");

    // 2. Remember that intro has played for this browser session
    try {
      sessionStorage.setItem("nexavision_intro_played", "true");
    } catch (_) {}

    // 3. Clean up the intro container so it doesn't intercept pointer events
    window.setTimeout(() => {
      intro.classList.add("is-gone");
      intro.classList.remove("is-fading-out");
      if (cardWrapper) cardWrapper.classList.remove("is-animating");
    }, 700);
  }

  function playCinematicIntro() {
    if (!intro) return;
    clearIntroTimers();
    introActive = true;

    // Reset visibility states
    intro.classList.remove("is-gone", "is-fading-out");
    intro.setAttribute("aria-hidden", "false");
    document.body.classList.remove("intro-finished");

    // Restart hardware-accelerated 3D card animation
    if (cardWrapper) {
      cardWrapper.classList.remove("is-animating");
      void cardWrapper.offsetWidth; // force DOM reflow to re-trigger keyframe
      cardWrapper.classList.add("is-animating");
    }

    // Sequence timing: Card pops up, rotates 360°, and pops down (~2.85s)
    // As it pops down, smoothly transition into the open website.
    introTimers.push(window.setTimeout(() => {
      if (!introActive) return;
      finishIntro();
    }, 2850));
  }

  // Quick Controls: Skip button & Escape key
  skipBtn?.addEventListener("click", finishIntro);
  replayBtn?.addEventListener("click", () => {
    try { sessionStorage.removeItem("nexavision_intro_played"); } catch (_) {}
    playCinematicIntro();
  });
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && introActive) {
      finishIntro();
    }
  });

  // Session & Result Check:
  // Plays once per browser session.
  // If user just uploaded an image (POST result), immediately show results.
  const hasResult = document.body.dataset.hasResult === "true";
  const introAlreadyPlayed = (() => {
    try { return sessionStorage.getItem("nexavision_intro_played") === "true"; }
    catch (_) { return false; }
  })();
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (intro && !hasResult && !introAlreadyPlayed && !prefersReduced) {
    playCinematicIntro();
  } else if (intro) {
    intro.classList.add("is-gone");
    document.body.classList.add("intro-finished");
  }

  if (!input || !zone) return;

  function setFile(file) {
    if (!file) return;
    if (!allowed.includes(file.type)) {
      alert("Please select a JPG, PNG, or WEBP image.");
      input.value = "";
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("Please choose an image smaller than 10 MB.");
      input.value = "";
      return;
    }
    if (fileName) fileName.textContent = file.name;
    if (selected) selected.hidden = false;
    if (title) title.textContent = "Image locked in";
    if (subtitle) subtitle.textContent = "Ready for a cinematic scan";
    if (visual) visual.innerHTML = '<div class="upload-ring"><svg viewBox="0 0 48 48" aria-hidden="true"><path d="m10 25 9 9 19-21" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>';
    zone.classList.add("file-loaded");

    const scanPreview = $("scanPreview"), scanShell = $("scanImageShell");
    if (scanPreview && scanShell) {
      const reader = new FileReader();
      reader.onload = () => {
        scanPreview.src = reader.result;
        scanShell.classList.add("has-image");
      };
      reader.readAsDataURL(file);
    }
  }

  input.addEventListener("change", () => setFile(input.files[0]));
  ["dragenter", "dragover"].forEach(type => zone.addEventListener(type, event => {
    event.preventDefault();
    zone.classList.add("dragging");
  }));
  ["dragleave", "drop"].forEach(type => zone.addEventListener(type, event => {
    event.preventDefault();
    zone.classList.remove("dragging");
  }));
  zone.addEventListener("drop", event => {
    const file = event.dataTransfer.files[0];
    if (!file) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    setFile(file);
  });

  clear?.addEventListener("click", () => {
    input.value = "";
    if (selected) selected.hidden = true;
    if (title) title.textContent = "Drop any image here";
    if (subtitle) subtitle.textContent = "or click to browse files";
    if (visual) visual.innerHTML = initialVisual;
    zone.classList.remove("file-loaded");
    const scanPreview = $("scanPreview"), scanShell = $("scanImageShell");
    if (scanPreview) scanPreview.removeAttribute("src");
    if (scanShell) scanShell.classList.remove("has-image");
  });

  // =========================================================================
  // CINEMATIC SCAN SEQUENCE (TIMED TO EXACTLY 5 SECONDS)
  // =========================================================================
  function clearScanTimers() {
    stageTimers.forEach(id => clearTimeout(id));
    stageTimers = [];
  }

  function startCinematicScan() {
    if (!transition) return;
    clearScanTimers();

    const titleNode = $("transitionTitle"), subtitleNode = $("transitionSubtitle");
    const counter = $("scanCounter"), frame = $("scanFrame"), engine = $("scanEngine");
    const progressLabel = $("scanProgressLabel"), percent = $("scanPercent"), bar = $("scanProgressBar");
    const logs = Array.from(document.querySelectorAll("#scanLog span"));

    // 4 Distinct Forensic Stages Paced Exactly Across 5 Seconds (1250ms each)
    const stages = [
      { t: "INITIALIZING VISION ENGINE", s: "Acquiring image frame and normalizing resolution...", p: 25, c: "SCAN 01 / 04", f: "FRAME ACQUIRED", e: "BOOTING", l: "INITIALIZING" },
      { t: "MAPPING PIXEL STRUCTURE", s: "Scanning color channels, high-frequency edges & gradients...", p: 52, c: "SCAN 02 / 04", f: "PIXELS MAPPED", e: "FEATURE EXTRACTION", l: "PIXEL MAPPING" },
      { t: "ANALYZING VISUAL SIGNALS", s: "Examining multi-scale artificial diffusion signatures...", p: 78, c: "SCAN 03 / 04", f: "SIGNALS SCANNED", e: "INFERENCE RUNNING", l: "SIGNAL ANALYSIS" },
      { t: "GENERATING ANALYSIS REPORT", s: "Verifying device provenance and assembling forensic metrics...", p: 96, c: "SCAN 04 / 04", f: "FRAME PROCESSED", e: "BUILDING REPORT", l: "REPORT ASSEMBLY" }
    ];

    transition.classList.add("is-active");
    transition.setAttribute("aria-hidden", "false");
    document.body.classList.add("is-scanning");

    stages.forEach((stage, index) => {
      stageTimers.push(window.setTimeout(() => {
        if (titleNode) titleNode.textContent = stage.t;
        if (subtitleNode) subtitleNode.textContent = stage.s;
        if (counter) counter.textContent = stage.c;
        if (frame) frame.textContent = stage.f;
        if (engine) engine.textContent = stage.e;
        if (progressLabel) progressLabel.textContent = stage.l;
        if (percent) percent.textContent = String(stage.p).padStart(2, "0") + "%";
        if (bar) bar.style.width = stage.p + "%";
        logs.forEach((log, i) => log.classList.toggle("done", i <= index));
      }, index * 1250));
    });

    // Final 100% tick at 4.75s
    stageTimers.push(window.setTimeout(() => {
      if (progressLabel) progressLabel.textContent = "COMPLETE";
      if (percent) percent.textContent = "100%";
      if (bar) bar.style.width = "100%";
    }, 4750));
  }

  function dismissCinematicScan() {
    clearScanTimers();
    if (!transition) return;
    transition.classList.remove("is-active");
    transition.setAttribute("aria-hidden", "true");
    document.body.classList.remove("is-scanning");
  }

  function renderAnalysisReport(result, imageUrl) {
    const card = $("resultCard");
    const body = $("resultCardBody");
    const statusText = $("modelStatusText");

    if (card) card.classList.add("has-output");
    if (statusText) statusText.textContent = "Analysis complete";

    if (body && result && imageUrl) {
      const isAI = result.ai_probability >= 50;
      const labelClass = isAI ? "result-ai" : "result-real";
      const forensicTagHtml = result.forensic_note ? `
        <div class="result-forensic-tag" style="margin: 10px 0 0; padding: 6px 10px; border-radius: 6px; background: rgba(117, 229, 239, 0.08); border: 1px solid rgba(117, 229, 239, 0.22); color: var(--cyan); font-size: 10px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">
          <span>◈</span><span>${result.forensic_note}</span>
        </div>` : "";

      body.innerHTML = `
        <div class="result-content">
          <div class="result-image-wrap">
            <img src="${imageUrl}" alt="Uploaded image preview">
            <span class="image-scan-line"></span>
            <span class="image-tag">ANALYZED IMAGE</span>
          </div>
          <div class="result-summary">
            <span class="mini-label">ESTIMATED CLASSIFICATION</span>
            <h3 class="${labelClass}">${result.label}</h3>
            <div class="probability-row">
              <span>AI-generation score</span>
              <strong>${result.ai_probability}%</strong>
            </div>
            <div class="meter"><span style="width: ${result.ai_probability}%"></span></div>
            <div class="probability-row confidence">
              <span>Model confidence estimate</span>
              <strong>${result.confidence}%</strong>
            </div>
            ${forensicTagHtml}
            <p class="disclaimer">This is a model estimate, not proof. Lighting, compression, editing, and unfamiliar image types can affect results.</p>
          </div>
        </div>
      `;

      // Smooth scroll to results
      const analyzerSection = $("analyzer") || card;
      analyzerSection?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  // Exact 5-Second Processing Form Handler
  form?.addEventListener("submit", async event => {
    event.preventDefault();
    if (!input.files.length) {
      alert("Please choose an image first.");
      return;
    }

    if (button) button.disabled = true;
    if (buttonText) buttonText.textContent = "Analyzing image…";

    const scanStartTime = Date.now();
    startCinematicScan();

    const formData = new FormData(form);
    let apiData = null;
    let apiFailed = false;

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });
      apiData = await response.json();
      if (!response.ok || !apiData.success) {
        apiFailed = true;
      }
    } catch (_) {
      apiFailed = true;
    }

    // Ensure the user experiences the full 5-second cinematic analysis sequence
    const elapsed = Date.now() - scanStartTime;
    const remainingDelay = Math.max(0, 5000 - elapsed);

    window.setTimeout(() => {
      dismissCinematicScan();
      if (!apiFailed && apiData && apiData.success) {
        renderAnalysisReport(apiData.result, apiData.image_url);
      } else {
        // Fallback to traditional full POST submit
        HTMLFormElement.prototype.submit.call(form);
      }
      if (button) button.disabled = false;
      if (buttonText) buttonText.textContent = "Analyze image";
    }, remainingDelay);
  });
})();