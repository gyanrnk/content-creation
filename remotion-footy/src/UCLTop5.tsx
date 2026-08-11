import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring, random,
} from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";

// ── UCL Top-5 goalscorers, REAL all-time numbers ──────────────────────
export const U5_FPS = 30;
const INTRO = 48;
const SEG = 56;
const WIN = 176;
const T1 = 9, T2 = 12;
export const U5_TOTAL = INTRO + 4 * SEG + WIN - (4 * T1 + T2);

const FONT = '"Arial Black", Impact, sans-serif';

type P = { rank: number; name: string; num: number; accent: string; file: string; tag: string };
const PLAYERS: P[] = [
  { rank: 5, name: "RAÚL",        num: 71,  accent: "#d8dde6", file: "raul",        tag: "⚽" },
  { rank: 4, name: "BENZEMA",     num: 90,  accent: "#7ab8ff", file: "benzema",     tag: "⚽" },
  { rank: 3, name: "LEWANDOWSKI", num: 105, accent: "#ff8c50", file: "lewandowski", tag: "🔥" },
  { rank: 2, name: "MESSI",       num: 129, accent: "#6ec8ff", file: "messi",       tag: "🐐" },
];
const CR7: P = { rank: 1, name: "RONALDO", num: 140, accent: "#ffcd42", file: "ronaldo", tag: "👑" };

// ── IMPACT ENGINE: one-shot hits on entry (no constant jitter) ──
const shakeBurst = (f: number, amt = 15) =>
  f < 0 ? 0 : Math.exp(-f * 0.26) * Math.sin(f * 1.7) * amt;
const punch = (f: number, amt = 0.08) =>
  f < 0 ? 0 : Math.exp(-f * 0.22) * Math.cos(f * 0.7) * amt;

// ── ANIMATED BACKGROUND LAYERS ──────────────────────────────────
// Floating dust — deterministic per-index (random() is seeded/stable in Remotion)
const Dust: React.FC<{ n?: number }> = ({ n = 26 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {Array.from({ length: n }).map((_, i) => {
        const bx = random(`x${i}`) * 100;
        const by = random(`y${i}`) * 100;
        const sz = 2 + random(`s${i}`) * 5;
        const sp = 0.15 + random(`v${i}`) * 0.5;
        const y = (by - frame * sp * 0.06 + 100) % 100;
        const x = bx + Math.sin(frame * 0.02 + i) * 2.2;
        const op = 0.12 + 0.22 * (0.5 + 0.5 * Math.sin(frame * 0.05 + i));
        return (
          <div key={i} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: sz, height: sz, borderRadius: "50%", background: "radial-gradient(circle,#fff,transparent 70%)", opacity: op, filter: "blur(0.5px)" }} />
        );
      })}
    </AbsoluteFill>
  );
};

// Slow rotating light beams
const LightBeams: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const rot = frame * 0.15;
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", opacity: 0.28, pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: "50%", top: "38%", width: 1600, height: 1600, transform: `translate(-50%,-50%) rotate(${rot}deg)`, background: `conic-gradient(from 0deg, transparent 0deg, ${accent}55 8deg, transparent 16deg, transparent 90deg, ${accent}44 98deg, transparent 106deg, transparent 200deg, ${accent}33 208deg, transparent 216deg)` }} />
    </AbsoluteFill>
  );
};

// Drifting lens flare
const LensFlare: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const x = 50 + Math.sin(frame * 0.018) * 30;
  const y = 30 + Math.cos(frame * 0.013) * 10;
  return <AbsoluteFill style={{ background: `radial-gradient(circle 140px at ${x}% ${y}%, ${accent}55, transparent 70%)`, mixBlendMode: "screen", pointerEvents: "none" }} />;
};

// Subtle film grain (turbulence), slowly drifting so it reads as moving
const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const tx = Math.sin(frame * 0.4) * 6;
  const ty = Math.cos(frame * 0.37) * 6;
  return (
    <AbsoluteFill style={{ opacity: 0.06, mixBlendMode: "overlay", pointerEvents: "none", transform: `translate(${tx}px,${ty}px)` }}>
      <svg width="110%" height="110%">
        <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" /></filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};

const StadiumBg: React.FC<{ accent: string; ken?: number; push?: number }> = ({ accent, ken = 0.06, push = 0 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = 1.06 + interpolate(frame, [0, durationInFrames], [0, ken]) + push;
  const drift = Math.sin(frame * 0.02) * 8;
  return (
    <AbsoluteFill style={{ backgroundColor: "#05060a", overflow: "hidden" }}>
      <Img src={staticFile("bg_stadium.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale}) translateX(${drift}px)`, filter: "blur(3px) brightness(0.5)" }} />
      <AbsoluteFill style={{ background: accent, mixBlendMode: "overlay", opacity: 0.35 }} />
      <LightBeams accent={accent} />
      <Dust />
      <LensFlare accent={accent} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 60% 55% at 50% 42%, ${accent}66 0%, transparent 60%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, transparent 45%, #05060aee 100%)" }} />
    </AbsoluteFill>
  );
};

// white "hit" flash on entry
const Flash: React.FC<{ at?: number; peak?: number }> = ({ at = 0, peak = 0.42 }) => {
  const f = useCurrentFrame();
  const op = interpolate(f - at, [0, 7], [peak, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ background: "#fff", opacity: op, mixBlendMode: "screen", pointerEvents: "none" }} />;
};

// Reusable moving light-sweep highlight, clipped to its box
const Sweep: React.FC<{ start: number; dur?: number; angle?: number }> = ({ start, dur = 22, angle = 105 }) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [start, start + dur], [-140, 140], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ overflow: "hidden", pointerEvents: "none" }}>
      <div style={{ position: "absolute", inset: 0, transform: `translateX(${p}%)`, background: `linear-gradient(${angle}deg, transparent 42%, rgba(255,255,255,0.35) 50%, transparent 58%)` }} />
    </AbsoluteFill>
  );
};

// Metallic shine text — gradient sweeps across the glyphs
const ShineText: React.FC<{ children: React.ReactNode; accent: string; size: number; weight?: number }> = ({ children, accent, size, weight = 900 }) => {
  const f = useCurrentFrame();
  const pos = interpolate(f % 60, [0, 60], [0, 200]);
  return (
    <span style={{ fontFamily: FONT, fontWeight: weight, fontSize: size, letterSpacing: 2, backgroundImage: `linear-gradient(100deg, #fff 20%, ${accent} 45%, #fff 55%, #cfd6e6 80%)`, backgroundSize: "200% 100%", backgroundPosition: `${pos}% 0`, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent", filter: `drop-shadow(0 4px 18px #000) drop-shadow(0 0 22px ${accent}88)` }}>{children}</span>
  );
};

// living player cutout: entry spring + slow zoom + glow pulse + punch + light sweep
const Cutout: React.FC<{ file: string; accent: string; punchAmt?: number; grow?: number; sweepAt?: number }> = ({ file, accent, punchAmt = 0.09, grow = 0.06, sweepAt = 18 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 15, mass: 0.7 } });
  const ty = interpolate(s, [0, 1], [340, 0]);
  const zoom = interpolate(frame, [0, durationInFrames], [0, grow]);
  const sc = interpolate(s, [0, 1], [0.92, 1]) + punch(frame, punchAmt) + zoom;
  const drift = Math.sin(frame * 0.03) * 6; // subtle left-right parallax
  const glow = 40 + 18 * (0.5 + 0.5 * Math.sin(frame * 0.12)); // glow pulse
  return (
    <div style={{ position: "absolute", bottom: 0, width: "100%", height: "72%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translate(${drift}px,${ty}px) scale(${sc})`, transformOrigin: "bottom center" }}>
      <div style={{ position: "relative", height: "100%" }}>
        <Img src={staticFile(`cut/${file}.png`)} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 ${glow}px ${accent}) drop-shadow(0 12px 20px #000a)` }} />
        {/* light sweep across the player */}
        <div style={{ position: "absolute", inset: 0, WebkitMaskImage: `url(${staticFile(`cut/${file}.png`)})`, WebkitMaskSize: "contain", WebkitMaskRepeat: "no-repeat", WebkitMaskPosition: "center", maskImage: `url(${staticFile(`cut/${file}.png`)})`, maskSize: "contain", maskRepeat: "no-repeat", maskPosition: "center" }}>
          <Sweep start={sweepAt} dur={20} />
        </div>
      </div>
    </div>
  );
};

const Scrim = () => <AbsoluteFill style={{ background: "linear-gradient(to top, #05060a 4%, transparent 26%)" }} />;

// emoji that SLAMS in (spring overshoot)
const Slam: React.FC<{ children: React.ReactNode; delay?: number; top: string; size: number; rot?: number }> = ({ children, delay = 0, top, size, rot = 0 }) => {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - delay, fps: U5_FPS, config: { damping: 8, mass: 0.5 } });
  return (
    <div style={{ position: "absolute", top, width: "100%", textAlign: "center", fontSize: size, transform: `scale(${interpolate(s, [0, 1], [0, 1])}) rotate(${interpolate(s, [0, 1], [rot, 0])}deg)` }}>{children}</div>
  );
};

// Rank badge = SVG ring that DRAWS + spins + pops (mini-event)
const RankRing: React.FC<{ rank: number; accent: string }> = ({ rank, accent }) => {
  const frame = useCurrentFrame();
  const R = 66, C = 2 * Math.PI * R;
  const draw = spring({ frame, fps: U5_FPS, config: { damping: 14 } });
  const off = C * (1 - draw);
  const pop = interpolate(spring({ frame: frame - 2, fps: U5_FPS, config: { damping: 9, mass: 0.5 } }), [0, 1], [0.2, 1]);
  const spin = interpolate(frame, [0, 30], [-90, 0], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 78, left: 54, width: 170, height: 170, transform: `scale(${pop})` }}>
      <svg width="170" height="170" style={{ position: "absolute", transform: `rotate(${spin}deg)` }}>
        <circle cx="85" cy="85" r={R} fill="#0a0c14ee" />
        <circle cx="85" cy="85" r={R} fill="none" stroke={accent} strokeWidth="8" strokeLinecap="round" strokeDasharray={C} strokeDashoffset={off} transform="rotate(-90 85 85)" style={{ filter: `drop-shadow(0 0 12px ${accent})` }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "flex", justifyContent: "center", alignItems: "center", fontFamily: FONT, fontWeight: 900, fontSize: 76, color: accent }}>#{rank}</div>
    </div>
  );
};

// Big count-up number with metallic shine + glow explosion on lock.
// Sits in the CLEAR top band (above the player's head) and renders ON TOP.
const BigNumber: React.FC<{ num: number; accent: string; top?: number; fs?: number; label?: boolean }> = ({ num, accent, top = 64, fs = 212, label = true }) => {
  const frame = useCurrentFrame();
  const shown = Math.round(interpolate(frame, [6, 40], [0, num], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const lock = 1 + punch(frame - 40, 0.12);
  const boom = interpolate(frame, [40, 52], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * Math.exp(-(frame - 40) * 0.12);
  return (
    <div style={{ position: "absolute", top, width: "100%", textAlign: "center", transform: `scale(${lock})` }}>
      <div style={{ position: "absolute", inset: 0, display: "flex", justifyContent: "center", alignItems: "flex-start", pointerEvents: "none" }}>
        <div style={{ width: 340, height: 340, marginTop: -40, borderRadius: "50%", background: `radial-gradient(circle, ${accent}, transparent 65%)`, opacity: Math.max(0, boom) * 0.7, filter: "blur(8px)" }} />
      </div>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: fs, color: "#fff", textShadow: `0 0 40px ${accent}, 0 0 90px ${accent}, 0 8px 24px #000`, letterSpacing: -4, lineHeight: 1 }}>{shown}</div>
      {label && <div style={{ fontFamily: FONT, fontSize: 34, color: "#c8ccd8", letterSpacing: 6, marginTop: 2, textShadow: "0 2px 10px #000" }}>UCL GOALS</div>}
    </div>
  );
};

const PlayerCard: React.FC<{ p: P }> = ({ p }) => {
  const frame = useCurrentFrame();
  const sh = shakeBurst(frame);
  const nameS = spring({ frame: frame - 8, fps: U5_FPS, config: { damping: 16 } });
  return (
    <AbsoluteFill>
      <StadiumBg accent={p.accent} />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, ${sh * 0.5}px)` }}>
        <Cutout file={p.file} accent={p.accent} />
        <Scrim />
        <RankRing rank={p.rank} accent={p.accent} />
        {/* number on TOP of the player so it can never be hidden */}
        <BigNumber num={p.num} accent={p.accent} />
        {/* tag emoji in top-right corner (clear of the number) */}
        <div style={{ position: "absolute", top: 108, right: 66, fontSize: 96, transform: `scale(${interpolate(spring({ frame: frame - 42, fps: U5_FPS, config: { damping: 8, mass: 0.5 } }), [0, 1], [0, 1])}) rotate(${interpolate(spring({ frame: frame - 42, fps: U5_FPS, config: { damping: 8, mass: 0.5 } }), [0, 1], [-22, 0])}deg)`, filter: "drop-shadow(0 4px 10px #000a)" }}>{p.tag}</div>
        {/* name slides up with metallic shine */}
        <div style={{ position: "absolute", bottom: 120, width: "100%", textAlign: "center", opacity: interpolate(nameS, [0, 1], [0, 1]), transform: `translateY(${interpolate(nameS, [0, 1], [46, 0])}px)` }}>
          <ShineText accent={p.accent} size={94}>{p.name}</ShineText>
        </div>
      </div>
      <Grain />
      <Flash />
    </AbsoluteFill>
  );
};

// ── PUNCHY 1-SECOND HOOK ──────────────────────────────────────
const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - 2, fps: U5_FPS, config: { damping: 12 } });
  const sh = shakeBurst(frame, 20);
  // gold particle burst from center
  const burst = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });
  const flick = frame < 10 ? (frame % 3 === 0 ? 0.5 : 0) : 0; // stadium light flicker
  return (
    <AbsoluteFill>
      <StadiumBg accent={CR7.accent} ken={0.05} push={interpolate(frame, [0, INTRO], [0.05, 0])} />
      <AbsoluteFill style={{ background: "#fff", opacity: flick, mixBlendMode: "screen" }} />
      {/* particle burst */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        {Array.from({ length: 30 }).map((_, i) => {
          const ang = (i / 30) * Math.PI * 2;
          const dist = burst * (300 + random(`d${i}`) * 260);
          const op = 1 - burst;
          return <div key={i} style={{ position: "absolute", left: "50%", top: "40%", width: 8, height: 8, borderRadius: "50%", background: CR7.accent, transform: `translate(${Math.cos(ang) * dist}px, ${Math.sin(ang) * dist}px)`, opacity: op, filter: "blur(1px)", boxShadow: `0 0 10px ${CR7.accent}` }} />;
        })}
      </AbsoluteFill>
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px,0)` }}>
        <div style={{ position: "absolute", top: "26%", width: "100%", textAlign: "center", transform: `scale(${interpolate(s, [0, 1], [0.55, 1])})`, opacity: s }}>
          <ShineText accent={CR7.accent} size={104}>TOP 5</ShineText>
        </div>
        <div style={{ position: "absolute", top: "38%", width: "100%", textAlign: "center", opacity: s }}>
          <ShineText accent={CR7.accent} size={132}>UCL GOALS</ShineText>
        </div>
        <Slam delay={14} top="52%" size={66}><span style={{ fontFamily: FONT, fontWeight: 900, color: "#fff", textShadow: `0 0 24px ${CR7.accent}` }}>#1 WILL SHOCK YOU 🤯</span></Slam>
      </div>
      <Grain />
      <Flash peak={0.85} />
    </AbsoluteFill>
  );
};

const Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const shown = Math.round(interpolate(frame, [12, 58], [0, CR7.num], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const kingOp = interpolate(frame, [86, 104], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sh = shakeBurst(frame, 6) + shakeBurst(frame - 58, 12);
  const lock = 1 + punch(frame - 58, 0.13);
  const boom = interpolate(frame, [58, 74], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * Math.exp(-(frame - 58) * 0.1);
  return (
    <AbsoluteFill>
      <StadiumBg accent={CR7.accent} ken={0.1} />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, 0)` }}>
        <Cutout file="ronaldo" accent={CR7.accent} grow={0.12} sweepAt={30} />
        <Scrim />
        <div style={{ position: "absolute", top: 24, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 60, color: "#fff", textShadow: "0 4px 20px #000" }}>AND #1 IS...</div>
        <Slam delay={8} top="5%" size={118}>👑</Slam>
        {/* number in the clear top band, ON TOP of Ronaldo */}
        <div style={{ position: "absolute", top: 236, width: "100%", textAlign: "center", transform: `scale(${lock})` }}>
          <div style={{ position: "absolute", inset: 0, display: "flex", justifyContent: "center", alignItems: "flex-start", pointerEvents: "none" }}>
            <div style={{ width: 400, height: 400, marginTop: -60, borderRadius: "50%", background: `radial-gradient(circle, ${CR7.accent}, transparent 65%)`, opacity: Math.max(0, boom) * 0.8, filter: "blur(10px)" }} />
          </div>
          <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 210, color: "#fff", textShadow: `0 0 50px ${CR7.accent}, 0 0 110px ${CR7.accent}`, lineHeight: 1 }}>{shown}</div>
          <div style={{ fontFamily: FONT, fontSize: 34, color: "#e8ddb0", letterSpacing: 6, marginTop: 2, textShadow: "0 2px 10px #000" }}>UCL GOALS</div>
        </div>
        <div style={{ position: "absolute", bottom: 150, width: "100%", textAlign: "center" }}>
          <ShineText accent={CR7.accent} size={118}>RONALDO</ShineText>
        </div>
        <div style={{ position: "absolute", bottom: 84, width: "100%", textAlign: "center", opacity: kingOp }}>
          <Slam delay={86} top="0%" size={58}><span style={{ fontFamily: FONT, fontWeight: 900, color: "#fff", letterSpacing: 3 }}>NOBODY CLOSE 💀</span></Slam>
        </div>
      </div>
      <Grain />
      <Flash />
    </AbsoluteFill>
  );
};

export const UCLTop5: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("beat.wav")} />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={INTRO}><Intro /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={slide({ direction: "from-right" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><PlayerCard p={PLAYERS[0]} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={wipe({ direction: "from-left" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><PlayerCard p={PLAYERS[1]} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={slide({ direction: "from-right" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><PlayerCard p={PLAYERS[2]} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={wipe({ direction: "from-bottom" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><PlayerCard p={PLAYERS[3]} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={springTiming({ config: { damping: 200 }, durationInFrames: T2 })} presentation={fade()} />
        <TransitionSeries.Sequence durationInFrames={WIN}><Reveal /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
