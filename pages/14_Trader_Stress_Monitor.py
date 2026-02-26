"""
Trader Stress Monitor — Real-time facial stress detection for trading sessions.

Uses MediaPipe FaceLandmarker + streamlit-webrtc to process webcam frames in the
browser without requiring a separate desktop window.

Stress score formula (from original app):
    score = 0.6*eyebrow_raise + 0.8*lip_tension + 0.4*head_nod
            + 0.2*symmetry + 0.3*(blink_rate/30)

Thresholds: Calm < 0.08 · Mild 0.08–0.15 · High > 0.25
"""

import os
import threading
import time
from collections import deque
from datetime import datetime

import av
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trader Stress Monitor",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "Real-Time-Stress-Detection-main",
        "Real-Time-Stress-Detection-main",
        "app",
        "face_landmarker.task",
    )
)

LIP_INDICES     = [61, 291]
EYEBROW_INDICES = [70, 300]
HEAD_INDICES    = [10, 152]
EYE_INDICES     = [159, 145, 386, 374]
KEY_DRAW_INDICES = [10, 152, 234, 454, 61, 291, 70, 300, 159, 145, 386, 374]

DEFAULT_THRESHOLDS = {"calm": 0.08, "mild": 0.15, "high": 0.25}

# ── Shared state ──────────────────────────────────────────────────────────────
class StressState:
    """Thread-safe container shared between WebRTC video thread and Streamlit thread."""

    def __init__(self):
        self.lock = threading.Lock()

        # Current reading
        self.score: float = 0.0
        self.level: str = "Calm"
        self.face_detected: bool = False
        self.metrics: dict = {
            "eyebrow_raise": 0.0,
            "lip_tension":   0.0,
            "head_nod":      0.0,
            "symmetry":      0.0,
            "blink_rate":    0.0,
        }

        # History — keep ~10 min at one sample per frame at ~10 fps storage
        self.history: deque = deque(maxlen=600)

        # Blink tracking (maintained by callback thread)
        self._blink_count: int  = 0
        self._frame_count: int  = 0
        self._prev_eye_state: int = 1
        self._blink_rate: float = 0.0

        # Session
        self.session_start: float = time.time()


def _get_state() -> StressState:
    if "stress_state" not in st.session_state:
        st.session_state.stress_state = StressState()
    return st.session_state.stress_state


# ── MediaPipe model (loaded once per process) ─────────────────────────────────
@st.cache_resource
def load_face_landmarker(model_path: str):
    """Load MediaPipe FaceLandmarker in IMAGE mode (synchronous, single-frame).
    Returns the landmarker object on success, or a string error message on failure.
    """
    try:
        import os
        os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions
        from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
            VisionTaskRunningMode,
        )

        opts = FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=model_path),
            running_mode=VisionTaskRunningMode.IMAGE,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1,
        )
        return FaceLandmarker.create_from_options(opts)
    except Exception as exc:  # ImportError, RuntimeError, numpy ABI mismatch, etc.
        return str(exc)


# ── Metric & score helpers ────────────────────────────────────────────────────
def _compute_metrics(landmarks, img_w: int, img_h: int, state: StressState):
    """Return (eyebrow_raise, lip_tension, head_nod, symmetry, blink_rate)."""
    # Eyebrow raise
    brow = np.array([landmarks[EYEBROW_INDICES[0]].x * img_w,
                     landmarks[EYEBROW_INDICES[0]].y * img_h])
    eye  = np.array([landmarks[EYE_INDICES[0]].x  * img_w,
                     landmarks[EYE_INDICES[0]].y  * img_h])
    eyebrow_raise = float(np.linalg.norm(brow - eye) / img_h)

    # Lip tension
    lip_l = np.array([landmarks[LIP_INDICES[0]].x * img_w,
                      landmarks[LIP_INDICES[0]].y * img_h])
    lip_r = np.array([landmarks[LIP_INDICES[1]].x * img_w,
                      landmarks[LIP_INDICES[1]].y * img_h])
    lip_tension = float(np.linalg.norm(lip_l - lip_r) / img_w)

    # Head nod
    chin     = np.array([landmarks[HEAD_INDICES[1]].x * img_w,
                         landmarks[HEAD_INDICES[1]].y * img_h])
    forehead = np.array([landmarks[HEAD_INDICES[0]].x * img_w,
                         landmarks[HEAD_INDICES[0]].y * img_h])
    head_nod = float(abs(chin[1] - forehead[1]) / img_h)

    # Symmetry
    symmetry = float(abs(landmarks[61].y - landmarks[291].y))

    # Blink (eye aspect ratio)
    left_ear  = abs(landmarks[EYE_INDICES[0]].y - landmarks[EYE_INDICES[1]].y)
    right_ear = abs(landmarks[EYE_INDICES[2]].y - landmarks[EYE_INDICES[3]].y)
    ear = (left_ear + right_ear) / 2.0
    eye_state = 1 if ear > 0.01 else 0

    if state._prev_eye_state == 1 and eye_state == 0:
        state._blink_count += 1
    state._prev_eye_state = eye_state
    state._frame_count   += 1

    if state._frame_count >= 30:
        state._blink_rate   = state._blink_count * 2.0  # extrapolate to per-min
        state._blink_count  = 0
        state._frame_count  = 0

    return eyebrow_raise, lip_tension, head_nod, symmetry, state._blink_rate


def _compute_score(metrics: tuple, thresholds: dict) -> float:
    eyebrow_raise, lip_tension, head_nod, symmetry, blink_rate = metrics
    score = (
        0.6 * eyebrow_raise
        + 0.8 * lip_tension
        + 0.4 * head_nod
        + 0.2 * symmetry
        + 0.3 * (blink_rate / 30.0)
    )
    return min(float(score), 1.0)


def _score_to_level(score: float, thresholds: dict) -> tuple:
    """Return (level_str, bgr_color_for_opencv)."""
    if score >= thresholds["high"]:
        return "High", (40, 40, 220)    # BGR red
    elif score >= thresholds["mild"]:
        return "Mild", (0, 180, 255)    # BGR amber
    else:
        return "Calm", (50, 200, 80)    # BGR green


# ── Video frame callback factory ──────────────────────────────────────────────
def make_video_callback(shared: StressState, landmarker, thresholds: dict):
    """Return a closure that processes each webcam frame."""

    def callback(frame: av.VideoFrame) -> av.VideoFrame:
        try:
            from mediapipe.tasks.python.vision.core.image import Image as MPImage, ImageFormat
        except Exception:
            img = frame.to_ndarray(format="bgr24")
            cv2.putText(img, "mediapipe unavailable", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        img = frame.to_ndarray(format="bgr24")
        h, w = img.shape[:2]

        if landmarker is None:
            cv2.putText(img, "Model not loaded — check logs", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        # Run face detection
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_img = MPImage(image_format=ImageFormat.SRGB, data=rgb)
        try:
            result = landmarker.detect(mp_img)
        except Exception:
            result = None

        if result and result.face_landmarks:
            lms = result.face_landmarks[0]

            # ── Metrics ──────────────────────────────────────────────────────
            with shared.lock:
                metrics = _compute_metrics(lms, w, h, shared)
            score = _compute_score(metrics, thresholds)
            level, bgr = _score_to_level(score, thresholds)

            # ── Overlay: key landmarks ────────────────────────────────────────
            for idx in KEY_DRAW_INDICES:
                lm = lms[idx]
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(img, (cx, cy), 4, (0, 255, 255), -1)

            # ── Overlay: stress border ────────────────────────────────────────
            if level == "High":
                cv2.rectangle(img, (0, 0), (w - 1, h - 1), bgr, 8)

            # ── Overlay: score badge ──────────────────────────────────────────
            cv2.rectangle(img, (8, 8), (260, 56), (0, 0, 0), -1)
            cv2.putText(
                img, f"Stress: {level}   score={score:.3f}",
                (14, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, bgr, 2,
            )

            # ── Elapsed timer (top right) ─────────────────────────────────────
            elapsed = int(time.time() - shared.session_start)
            timer   = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
            cv2.rectangle(img, (w - 95, 8), (w - 8, 52), (0, 0, 0), -1)
            cv2.putText(img, timer, (w - 88, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # ── Write shared state ────────────────────────────────────────────
            with shared.lock:
                shared.score        = score
                shared.level        = level
                shared.face_detected = True
                shared.metrics = {
                    "eyebrow_raise": metrics[0],
                    "lip_tension":   metrics[1],
                    "head_nod":      metrics[2],
                    "symmetry":      metrics[3],
                    "blink_rate":    metrics[4],
                }
                shared.history.append({
                    "time":  datetime.now(),
                    "score": score,
                    "level": level,
                })
        else:
            # No face
            cv2.putText(img, "No face detected", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (120, 120, 255), 2)
            with shared.lock:
                shared.face_detected = False

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    return callback


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.title("Trader Stress Monitor")
    st.caption(
        "Real-time facial stress detection powered by "
        "**MediaPipe FaceLandmarker** + **WebRTC**"
    )

    # ── Model availability check ──────────────────────────────────────────────
    if not os.path.exists(MODEL_PATH):
        st.error(
            f"**face_landmarker.task** not found.\n\n"
            f"Expected path: `{MODEL_PATH}`\n\n"
            "Download it from the [MediaPipe GitHub releases]"
            "(https://storage.googleapis.com/mediapipe-models/face_landmarker/"
            "face_landmarker/float16/latest/face_landmarker.task)."
        )
        return

    landmarker = load_face_landmarker(MODEL_PATH)
    if isinstance(landmarker, str):
        # String means an error message was returned
        st.error(
            "**MediaPipe failed to initialise.** The most common cause is a "
            "NumPy version conflict (mediapipe requires NumPy < 2.0).\n\n"
            f"Run in a terminal:\n```\npip install \"numpy<2\"\n```\n\n"
            f"**Details:** `{landmarker[:300]}`"
        )
        st.info(
            "In the meantime you can still use all other pages of the app. "
            "After the fix, restart Streamlit."
        )
        return
    if landmarker is None:
        st.error("MediaPipe FaceLandmarker failed to initialise. Check the logs.")
        return

    # ── Shared state ──────────────────────────────────────────────────────────
    shared = _get_state()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Thresholds")
        thresholds = {
            "calm": st.slider("Calm  ↔ Mild  (score)", 0.02, 0.20,
                              DEFAULT_THRESHOLDS["calm"], 0.01, key="thr_calm"),
            "mild": st.slider("Mild  ↔ High  (score)", 0.05, 0.40,
                              DEFAULT_THRESHOLDS["mild"], 0.01, key="thr_mild"),
            "high": st.slider("High  threshold (score)", 0.10, 0.60,
                              DEFAULT_THRESHOLDS["high"], 0.01, key="thr_high"),
        }

        st.divider()
        st.header("Session Notes")
        note_text = st.text_area("Current conditions / notes:", height=80, key="note_text")
        if st.button(" Save Note", use_container_width=True):
            if "session_notes" not in st.session_state:
                st.session_state.session_notes = []
            st.session_state.session_notes.append(
                {"time": datetime.now().strftime("%H:%M:%S"), "note": note_text}
            )
            st.success("Saved!")

        if st.session_state.get("session_notes"):
            st.divider()
            for n in reversed(st.session_state.session_notes[-5:]):
                st.markdown(f"**{n['time']}** — {n['note']}")

        st.divider()
        if st.button(" Clear Session History", use_container_width=True):
            with shared.lock:
                shared.history.clear()
                shared.session_start = time.time()
            st.rerun()

        st.divider()
        st.markdown("### ℹ How it works")
        st.markdown(
            "| Indicator | Weight |\n"
            "|---|---|\n"
            "| Eyebrow Raise | 0.6 |\n"
            "| Lip Tension | 0.8 |\n"
            "| Head Nod | 0.4 |\n"
            "| Facial Symmetry | 0.2 |\n"
            "| Blink Rate | 0.3 |\n"
        )

    # ── Main content ──────────────────────────────────────────────────────────
    col_video, col_metrics = st.columns([3, 2], gap="medium")

    with col_video:
        st.subheader("Live Feed")
        st.caption(
            "Click **START** → allow camera access → stress overlay appears on the feed."
        )

        rtc_config = RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )
        callback = make_video_callback(shared, landmarker, thresholds)

        ctx = webrtc_streamer(
            key="trader-stress-monitor",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=rtc_config,
            video_frame_callback=callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    # ── Metrics panel ─────────────────────────────────────────────────────────
    with col_metrics:
        st.subheader("Live Metrics")

        score_ph   = st.empty()
        alert_ph   = st.empty()
        st.divider()
        metric_ph  = st.empty()
        st.divider()
        st.caption("**Raw values** — updated every ~1 second")
        table_ph   = st.empty()

    # ── History & statistics ──────────────────────────────────────────────────
    st.divider()
    hist_header = st.empty()
    chart_ph    = st.empty()
    stats_ph    = st.empty()

    # ── Export ────────────────────────────────────────────────────────────────
    export_ph = st.empty()

    # ── Running / idle state ──────────────────────────────────────────────────
    running = ctx and ctx.state.playing

    if running:
        # Auto-refresh every 800 ms while stream is active
        st_autorefresh(interval=800, key="stress_autorefresh")

        with shared.lock:
            score        = shared.score
            level        = shared.level
            face_ok      = shared.face_detected
            metrics_snap = dict(shared.metrics)
            history_snap = list(shared.history)

        # ── Score badge ───────────────────────────────────────────────────────
        level_palette = {"Calm": "#2e7d32", "Mild": "#f57c00", "High": "#c62828"}
        badge_color   = level_palette.get(level, "#555")

        if face_ok:
            score_ph.markdown(
                f"<div style='text-align:center; padding:12px; border-radius:10px;"
                f" background:{badge_color}; color:white;'>"
                f"<span style='font-size:2.2rem; font-weight:800;'>{level.upper()}</span>"
                f"<br><span style='font-size:1.3rem;'>score = {score:.4f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            if level == "High":
                alert_ph.error(" **HIGH STRESS** — Consider closing positions or taking a break.")
            elif level == "Mild":
                alert_ph.warning(" **Mild stress** — Stay disciplined; avoid impulsive trades.")
            else:
                alert_ph.success(" **Calm** — You're in the zone.")
        else:
            score_ph.info(" No face detected — centre yourself in the camera view.")
            alert_ph.empty()

        # ── Metric progress bars ──────────────────────────────────────────────
        bar_defs = [
            ("Eyebrow Raise", "eyebrow_raise", 0.20),
            ("Lip Tension",   "lip_tension",   1.00),
            ("Head Nod",      "head_nod",       0.50),
            ("Symmetry",      "symmetry",       0.20),
            ("Blink Rate/min","blink_rate",     30.0),
        ]
        with metric_ph.container():
            for label, key, max_val in bar_defs:
                val = metrics_snap.get(key, 0.0)
                pct = min(val / max_val, 1.0)
                color = "#c62828" if pct > 0.7 else "#f57c00" if pct > 0.4 else "#2e7d32"
                st.markdown(
                    f"<div style='margin-bottom:6px;'>"
                    f"<span style='font-size:0.85rem; font-weight:600;'>{label}</span>"
                    f"<span style='float:right; font-size:0.85rem;'>{val:.4f}</span>"
                    f"</div>"
                    f"<div style='background:#e0e0e0; border-radius:6px; height:12px;'>"
                    f"  <div style='background:{color}; width:{int(pct*100)}%; "
                    f"  height:12px; border-radius:6px;'></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # ── Raw table ─────────────────────────────────────────────────────────
        if face_ok:
            df_vals = pd.DataFrame(
                [{"Metric": k.replace("_", " ").title(), "Value": round(v, 5)}
                 for k, v in metrics_snap.items()]
            ).set_index("Metric")
            table_ph.dataframe(df_vals, use_container_width=True)

        # ── History chart ─────────────────────────────────────────────────────
        if len(history_snap) > 5:
            hist_header.subheader(" Stress History (Session)")
            df_hist = pd.DataFrame(history_snap)
            df_hist["time"] = pd.to_datetime(df_hist["time"])
            df_hist = df_hist.set_index("time")[["score"]]
            chart_ph.line_chart(df_hist, use_container_width=True, height=220)

            # Stats
            n_total = len(history_snap)
            pct = {lvl: sum(1 for h in history_snap if h["level"] == lvl) / n_total * 100
                   for lvl in ("Calm", "Mild", "High")}
            avg_score = sum(h["score"] for h in history_snap) / n_total
            elapsed_s = int(time.time() - shared.session_start)

            c1, c2, c3, c4, c5 = stats_ph.columns(5)
            c1.metric("Session",    f"{elapsed_s//60:02d}:{elapsed_s%60:02d}")
            c2.metric("Avg Score",  f"{avg_score:.3f}")
            c3.metric("% Calm",     f"{pct['Calm']:.0f}%")
            c4.metric("% Mild",     f"{pct['Mild']:.0f}%")
            c5.metric("% High",     f"{pct['High']:.0f}%")

            # Export button
            df_export = pd.DataFrame(history_snap)
            csv = df_export.to_csv(index=False).encode("utf-8")
            export_ph.download_button(
                "⬇ Export Session CSV", csv,
                f"stress_session_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv", use_container_width=False,
            )
    else:
        # ── Idle state — show instructions ────────────────────────────────────
        score_ph.empty()
        alert_ph.empty()
        metric_ph.empty()
        table_ph.empty()

        st.info(
            "▶  Click the **START** button in the video panel above and allow "
            "camera access. The stress overlay will appear on the live feed and "
            "the metrics panel will update in real time."
        )

        with st.expander(" Methodology & Scoring", expanded=True):
            st.markdown(
                """
### Stress Score Formula

$$
\\text{score} = 0.6 \\cdot \\text{eyebrow\\_raise}
              + 0.8 \\cdot \\text{lip\\_tension}
              + 0.4 \\cdot \\text{head\\_nod}
              + 0.2 \\cdot \\text{symmetry}
              + 0.3 \\cdot \\frac{\\text{blink\\_rate}}{30}
$$

| Indicator | Landmarks | Weight | Interpretation |
|---|---|---|---|
| **Eyebrow Raise** | 70, 300 vs 159 | 0.6 | Surprise / anxiety |
| **Lip Tension** | 61 → 291 width | 0.8 | Jaw / mouth clenching |
| **Head Nod** | 10 ↕ 152 | 0.4 | Chin-to-forehead distance changes |
| **Facial Symmetry** | 61 vs 291 y-diff | 0.2 | Asymmetric tension |
| **Blink Rate** | EAR threshold | 0.3 | Cognitive load indicator |

### Thresholds
| Level | Score Range | Action |
|---|---|---|
|  **Calm** | < 0.08 | Continue trading normally |
|  **Mild** | 0.08 – 0.25 | Increase caution; review position sizes |
|  **High** | > 0.25 | Consider stepping away; avoid new positions |

> *Scores are normalised 0–1. Adjust thresholds in the sidebar to match your baseline.*
"""
            )


main()
