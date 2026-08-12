import React from "react";
import {
  AbsoluteFill, OffthreadVideo, Audio, staticFile, useCurrentFrame,
  useVideoConfig, interpolate, spring, Sequence,
} from "remotion";

// ── "THE DROP" — Below The Blue's first short ────────────────────────────────
// Hybrid: Veo generates the water (three clips stitched by stitch_drop.py into
// drop_base.mp4), Remotion lays the data on top. Veo cannot hold a legible
// number on screen; Remotion cannot invent an ocean. Each does its half.
//
// The whole video is one descent, so the depth counter is the through-line —
// it is driven off the marker table below, which guarantees the number on
// screen reads EXACTLY the marker value at the moment that marker appears.
// (Driving it off a separate easing curve drifts and shows 1,004 m next to a
// "1,000 m" card.)
//
// Verified 2026-08-11:
//   40 m     recreational scuba limit (PADI)
//   200 m    photic zone ends
//   332 m    deepest scuba dive, Ahmed Gabr 2014 (Guinness) — 332.35 m
//   1,000 m  midnight zone begins
//   2,250 m  deepest confirmed sperm whale dive
//   3,800 m  Titanic wreck
//   8,849 m  Everest, 8,848.86 m (China/Nepal 2020)
//   10,935 m Challenger Deep (2020 survey, +/- 6 m)
//   gap      2,086 m
export const DR_FPS = 30;
export const DR_TOTAL = 498;          // 16.6s — matches drop_base.mp4

const MONO = '"Courier New", ui-monospace, monospace';
const SANS = '"Arial Black", Impact, sans-serif';
const ICE = "#8fe9ff";

type Marker = { at: number; depth: number; label: string; big?: boolean };

const MARKERS: Marker[] = [
  { at: 1.6, depth: 40, label: "Scuba divers stop here" },
  { at: 3.2, depth: 200, label: "Sunlight ends" },
  { at: 4.8, depth: 332, label: "Deepest human dive. Ever." },
  { at: 6.4, depth: 1000, label: "THE MIDNIGHT ZONE", big: true },
  { at: 8.0, depth: 2250, label: "A sperm whale turns back" },
  { at: 9.6, depth: 3800, label: "The Titanic sits here" },
  { at: 11.2, depth: 8849, label: "Mount Everest would be HERE", big: true },
  { at: 13.0, depth: 10935, label: "CHALLENGER DEEP", big: true },
];

const HOLD = 13.0;                    // counter yahin ruk jaata he
const fmt = (n: number) => Math.round(n).toLocaleString("en-US");

/** Marker table se hi depth nikaalo — number aur card kabhi alag nahi honge. */
const depthAt = (t: number) => {
  if (t <= 0) return 0;
  if (t >= HOLD) return 10935;
  const pts = [{ at: 0, depth: 0 }, ...MARKERS];
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1];
    if (t >= a.at && t <= b.at) {
      const k = (t - a.at) / (b.at - a.at);
      return a.depth + (b.depth - a.depth) * k;
    }
  }
  return 10935;
};

const Grain: React.FC = () => (
  <AbsoluteFill style={{ background: "radial-gradient(ellipse 80% 70% at 50% 45%, transparent 45%, #00060caa 100%)", pointerEvents: "none" }} />
);

const Counter: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / DR_FPS;
  const d = depthAt(t);
  const landed = t >= HOLD;
  // har marker pe halka sa punch
  const near = MARKERS.reduce((acc, m) => Math.min(acc, Math.abs(t - m.at)), 9);
  const pop = 1 + (near < 0.4 ? 0.07 * (1 - near / 0.4) : 0);
  return (
    <div style={{ position: "absolute", top: "7%", width: "100%", textAlign: "center" }}>
      <div style={{
        fontFamily: MONO, fontWeight: 700, fontSize: landed ? 128 : 116,
        color: landed ? "#fff" : ICE, transform: `scale(${pop})`,
        textShadow: `0 0 34px ${ICE}, 0 0 90px ${ICE}66, 0 4px 22px #000`,
        letterSpacing: -2,
      }}>{fmt(d)}<span style={{ fontSize: 52, marginLeft: 8 }}>m</span></div>
      <div style={{ fontFamily: MONO, fontSize: 22, color: "#9fb6c4", letterSpacing: 9, marginTop: 2 }}>
        {landed ? "THE BOTTOM" : "DEPTH"}
      </div>
    </div>
  );
};

/** Left-edge scale — kitna neeche aa chuke he, ek nazar me. */
const Scale: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / DR_FPS;
  const p = Math.min(1, depthAt(t) / 10935);
  return (
    <div style={{ position: "absolute", left: 34, top: "26%", width: 3, height: "46%", background: "#ffffff1f" }}>
      <div style={{ position: "absolute", top: 0, width: "100%", height: `${p * 100}%`, background: ICE, boxShadow: `0 0 14px ${ICE}` }} />
      <div style={{ position: "absolute", top: `${p * 100}%`, left: -5, width: 13, height: 2, background: "#fff" }} />
    </div>
  );
};

// NOTE: har Card <Sequence> ke andar hona chahiye. Bina uske useCurrentFrame()
// global frame deta he — spring kab ka settle, aur fade-out opacity 0 kar deta
// he, to card render hote hue bhi INVISIBLE rehta he. Pehle build me yahi hua tha.
const Card: React.FC<{ m: Marker }> = ({ m }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 20, mass: 1.1, stiffness: 70 } });
  const dx = interpolate(s, [0, 1], [340, 0]);
  const out = interpolate(frame, [36, 46], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: "44%", width: "100%", opacity: Math.min(s, out), transform: `translateX(${dx}px)` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "0 46px" }}>
        <div style={{ height: 2, flex: 1, background: ICE, opacity: 0.7 }} />
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 40, color: ICE, textShadow: "0 2px 14px #000" }}>{fmt(m.depth)} m</div>
        <div style={{ height: 2, flex: 1, background: ICE, opacity: 0.7 }} />
      </div>
      <div style={{
        marginTop: 10, textAlign: "center", padding: "0 44px",
        fontFamily: SANS, fontWeight: 900,
        fontSize: m.big ? 58 : 42, color: "#fff",
        textShadow: `0 0 26px ${ICE}88, 0 3px 18px #000, 0 3px 18px #000`,
      }}>{m.label}</div>
    </div>
  );
};

export const Drop: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / DR_FPS;

  const hookOp = interpolate(t, [0.15, 0.5, 1.5, 1.9], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const payoffS = spring({ frame: frame - 14.2 * DR_FPS, fps, config: { damping: 16, mass: 1.0 } });
  const baitOp = interpolate(t, [15.2, 15.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pulse = 1 + 0.045 * Math.sin(frame * 0.32);

  const CARD_FRAMES = Math.round(1.55 * DR_FPS);

  return (
    <AbsoluteFill style={{ backgroundColor: "#00060c" }}>
      <OffthreadVideo src={staticFile("drop_base.mp4")} muted />
      <Audio src={staticFile("score_drop.wav")} />
      <Grain />

      {/* top scrim — counter ko bright surface pe bhi padha jaana chahiye */}
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, #00060ce6 0%, #00060c99 18%, transparent 34%)" }} />

      <Counter />
      <Scale />

      {hookOp > 0.01 && (
        <div style={{
          position: "absolute", top: "31%", width: "100%", textAlign: "center",
          fontFamily: SANS, fontWeight: 900, fontSize: 62, color: "#fff",
          opacity: hookOp, padding: "0 40px", textShadow: "0 3px 20px #000",
        }}>HOW DEEP DOES IT<br />ACTUALLY GO?</div>
      )}

      {MARKERS.map((m) => (
        <Sequence
          key={m.depth}
          from={Math.round(m.at * DR_FPS)}
          durationInFrames={CARD_FRAMES}
          layout="none"
        >
          <Card m={m} />
        </Sequence>
      ))}

      {t >= 14.2 && (
        <div style={{
          position: "absolute", top: "40%", width: "100%", textAlign: "center",
          padding: "0 44px", opacity: payoffS,
          transform: `scale(${interpolate(payoffS, [0, 1], [0.82, 1])})`,
        }}>
          <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 50, color: "#fff", textShadow: `0 0 26px ${ICE}88, 0 3px 18px #000` }}>
            Everest's peak would still be
          </div>
          <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 86, color: ICE, marginTop: 8, textShadow: `0 0 34px ${ICE}, 0 3px 18px #000` }}>
            2,086 m
          </div>
          <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 46, color: "#fff", textShadow: "0 3px 18px #000" }}>
            underwater.
          </div>
        </div>
      )}

      <div style={{
        position: "absolute", bottom: 108, width: "100%", textAlign: "center",
        fontFamily: SANS, fontWeight: 900, fontSize: 56, color: "#fff",
        opacity: baitOp, transform: `scale(${pulse})`,
        textShadow: `0 0 28px ${ICE}, 0 3px 18px #000`,
      }}>WOULD YOU GO DOWN? 👇</div>
      <div style={{
        position: "absolute", bottom: 62, width: "100%", textAlign: "center",
        fontFamily: MONO, fontSize: 26, color: "#9fb6c4", opacity: baitOp, letterSpacing: 6,
      }}>BELOW THE BLUE</div>
    </AbsoluteFill>
  );
};
