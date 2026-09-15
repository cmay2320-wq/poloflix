document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("playerRoot");
  const video = document.getElementById("videoEl");
  if (!root || !video) return;

  const videoUrl = root.dataset.videoUrl;
  const resumeAt = parseFloat(root.dataset.resume || "0");
  const mediaType = root.dataset.mediaType;
  const mediaId = parseInt(root.dataset.mediaId, 10);
  const nextUrl = root.dataset.nextUrl;

  if (!videoUrl) return; // "no video uploaded yet" state - nothing to wire up

  // ---------------------------------------------------------------
  // SOURCE SETUP - HLS.js for .m3u8, native <video> otherwise
  // ---------------------------------------------------------------
  let hls = null;
  if (videoUrl.endsWith(".m3u8") && window.Hls && Hls.isSupported()) {
    hls = new Hls();
    hls.loadSource(videoUrl);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      buildQualityMenuFromHls(hls.levels);
    });
    hls.on(Hls.Events.LEVEL_SWITCHED, (evt, data) => {
      highlightActiveQuality(data.level === -1 ? "Auto" : hls.levels[data.level].height + "p");
    });
  } else {
    video.src = videoUrl;
  }

  video.addEventListener("loadedmetadata", () => {
    if (resumeAt > 0 && resumeAt < video.duration - 5) {
      video.currentTime = resumeAt;
    }
    durTime.textContent = formatTime(video.duration);
  });

  // ---------------------------------------------------------------
  // PLAY / PAUSE
  // ---------------------------------------------------------------
  const playPauseBtn = document.getElementById("playPauseBtn");
  const playPauseBtnSmall = document.getElementById("playPauseBtnSmall");
  const playIcon = '<svg viewBox="0 0 24 24" width="34" height="34"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>';
  const pauseIcon = '<svg viewBox="0 0 24 24" width="34" height="34"><path fill="currentColor" d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>';
  const playIconSmall = '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>';
  const pauseIconSmall = '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>';

  function togglePlay() {
    if (video.paused) video.play();
    else video.pause();
  }
  playPauseBtn.addEventListener("click", togglePlay);
  playPauseBtnSmall.addEventListener("click", togglePlay);
  video.addEventListener("click", togglePlay);

  video.addEventListener("play", () => {
    root.classList.remove("is-paused");
    playPauseBtn.innerHTML = pauseIcon;
    playPauseBtnSmall.innerHTML = pauseIconSmall;
  });
  video.addEventListener("pause", () => {
    root.classList.add("is-paused");
    playPauseBtn.innerHTML = playIcon;
    playPauseBtnSmall.innerHTML = playIconSmall;
  });

  document.getElementById("skipBackBtn").addEventListener("click", () => (video.currentTime -= 10));
  document.getElementById("skipFwdBtn").addEventListener("click", () => (video.currentTime += 10));

  // ---------------------------------------------------------------
  // SEEK BAR + TIME DISPLAY
  // ---------------------------------------------------------------
  const seekBar = document.getElementById("seekBar");
  const curTime = document.getElementById("curTime");
  const durTime = document.getElementById("durTime");
  let seeking = false;

  video.addEventListener("timeupdate", () => {
    if (!video.duration || seeking) return;
    seekBar.value = (video.currentTime / video.duration) * 100;
    curTime.textContent = formatTime(video.currentTime);
  });
  seekBar.addEventListener("input", () => (seeking = true));
  seekBar.addEventListener("change", () => {
    if (video.duration) video.currentTime = (seekBar.value / 100) * video.duration;
    seeking = false;
  });

  function formatTime(sec) {
    if (!isFinite(sec)) return "0:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60)
      .toString()
      .padStart(2, "0");
    return `${m}:${s}`;
  }

  // ---------------------------------------------------------------
  // VOLUME
  // ---------------------------------------------------------------
  const volBar = document.getElementById("volBar");
  const volBtn = document.getElementById("volBtn");
  volBar.addEventListener("input", () => {
    video.volume = volBar.value;
    video.muted = video.volume === 0;
  });
  volBtn.addEventListener("click", () => {
    video.muted = !video.muted;
    volBar.value = video.muted ? 0 : video.volume;
  });

  // ---------------------------------------------------------------
  // FULLSCREEN
  // ---------------------------------------------------------------
  function toggleFullscreen() {
    if (!document.fullscreenElement) root.requestFullscreen?.();
    else document.exitFullscreen?.();
  }
  document.getElementById("fullscreenBtn").addEventListener("click", toggleFullscreen);
  document.getElementById("fullscreenBtnSmall").addEventListener("click", toggleFullscreen);

  // ---------------------------------------------------------------
  // QUALITY MENU
  // ---------------------------------------------------------------
  const qualityBtn = document.getElementById("qualityBtn");
  const qualityMenu = document.getElementById("qualityMenu");
  qualityBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    qualityMenu.classList.toggle("is-open");
  });
  document.addEventListener("click", () => qualityMenu.classList.remove("is-open"));

  qualityMenu.querySelectorAll(".quality-option").forEach((opt) => {
    opt.addEventListener("click", (e) => {
      e.stopPropagation();
      const label = opt.dataset.quality;
      if (hls) {
        if (label === "Auto") {
          hls.currentLevel = -1;
        } else {
          const target = hls.levels.findIndex((l) => `${l.height}p` === label);
          if (target !== -1) hls.currentLevel = target;
        }
      }
      highlightActiveQuality(label);
      qualityMenu.classList.remove("is-open");
    });
  });

  function highlightActiveQuality(label) {
    qualityMenu.querySelectorAll(".quality-option").forEach((opt) => {
      opt.classList.toggle("is-active", opt.dataset.quality === label);
    });
  }

  function buildQualityMenuFromHls(levels) {
    if (!levels || !levels.length) return;
    // Real renditions from the HLS manifest replace the static PLAN placeholders.
    const options = ["Auto", ...levels.map((l) => `${l.height}p`).reverse()];
    qualityMenu.innerHTML = options
      .map(
        (label, i) =>
          `<button class="quality-option ${i === 0 ? "is-active" : ""}" data-quality="${label}">${label}${i === 0 ? ' <svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z"/></svg>' : ""}</button>`
      )
      .join("");
    qualityMenu.querySelectorAll(".quality-option").forEach((opt) => {
      opt.addEventListener("click", (e) => {
        e.stopPropagation();
        const label = opt.dataset.quality;
        if (label === "Auto") hls.currentLevel = -1;
        else {
          const target = hls.levels.findIndex((l) => `${l.height}p` === label);
          if (target !== -1) hls.currentLevel = target;
        }
        highlightActiveQuality(label);
        qualityMenu.classList.remove("is-open");
      });
    });
  }

  // ---------------------------------------------------------------
  // SUBTITLES TOGGLE
  // ---------------------------------------------------------------
  document.getElementById("ccBtn").addEventListener("click", () => {
    const track = video.textTracks[0];
    if (!track) return;
    track.mode = track.mode === "showing" ? "hidden" : "showing";
  });

  // ---------------------------------------------------------------
  // KEYBOARD SHORTCUTS
  // ---------------------------------------------------------------
  document.addEventListener("keydown", (e) => {
    if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
    switch (e.code) {
      case "Space":
        e.preventDefault();
        togglePlay();
        break;
      case "ArrowLeft":
        video.currentTime -= 10;
        break;
      case "ArrowRight":
        video.currentTime += 10;
        break;
      case "KeyF":
        toggleFullscreen();
        break;
      case "KeyM":
        video.muted = !video.muted;
        break;
    }
  });

  // ---------------------------------------------------------------
  // AUTO-PLAY NEXT EPISODE + PROGRESS SAVING
  // ---------------------------------------------------------------
  function saveProgress() {
    if (!video.duration) return;
    fetch("/api/progress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        media_type: mediaType,
        media_id: mediaId,
        position: Math.floor(video.currentTime),
        duration: Math.floor(video.duration),
      }),
    }).catch(() => {});
  }

  setInterval(saveProgress, 10000);
  window.addEventListener("beforeunload", saveProgress);
  video.addEventListener("pause", saveProgress);

  video.addEventListener("ended", () => {
    saveProgress();
    if (nextUrl) window.location.href = nextUrl;
  });
});
