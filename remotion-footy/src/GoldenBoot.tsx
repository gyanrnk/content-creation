import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring,
} from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";

// ── WORLD CUP 2026 GOLDEN BOOT — fresh, verified (ESPN, Aug 2026) ─────────────
//   1. Kylian Mbappe  — 6 goals, 2 assists  (won Golden Boot on assists tiebreak)
//   2. Lionel Messi   — 6 goals
//   3. Erling Haaland — 5 goals
// Format modelled on UCLGoals (proven): intro -> countdown cards -> winner reveal.
export const GB_FPS = 30;
const INTRO = 46;
const SEG = 72;
const WIN = 190;
const T1 = 8, T2 = 12;
export const GB_TOTAL = INTRO + 2 * SEG + WIN - (2 * T1 + T2);

const FONT = '"Arial Black", Impact, sans-serif';

type P = { rank: number; name: string; goals: number; assists: number; country: string; accent: string; file: string };
const CONTENDERS: P[] = [
  { rank: 3, name: "HAALAND", goals: 5, assists: 0, country: "NORWAY", accent: "#7ab8ff", file: "haaland" },
  { rank: 2, name: "MESSI", goals: 6, assists: 0, country: "ARGENTINA", accent: "#6ec8ff", file: "messi" },
];
const WINNER: P = { rank: 1, name: "MBAPPE", goals: 6, assists: 2, country: "FRANCE", accent: "#ffcd42", file: "mbappe" };

const beatShake = (frame: number, amt = 6) => {
  const b = frame % 15;
  return Math.exp(-b * 0.55) * Math.sin(frame * 2.5) * amt;
};

const StadiumBg: React.FC<{ accent: string; ken?: number }> = ({ accent, ken = 0.06 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = 1.05 + interpolate(frame, [0, durationInFrames], [0, ken]);
  return (
    <AbsoluteFill style={{ backgroundColor: "#05060a", overflow: "hidden" }}>
      <Img src={staticFile("bg_stadium.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, filter: "blur(3px) brightness(0.5)" }} />
      <AbsoluteFill style={{ background: accent, mixBlendMode: "overlay", opacity: 0.35 }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 60% 55% at 50% 42%, ${accent}66 0%, transparent 60%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, transparent 45%, #05060aee 100%)" }} />
    </AbsoluteFill>
  );
};

const Cutout: React.FC<{ file: string; accent: string; delay?: number; grow?: number }> = ({ file, accent, delay = 0, grow = 0 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.7 } });
  const ty = interpolate(s, [0, 1], [340, 0]);
  const sc = interpolate(s, [0, 1], [0.92, 1]) + (grow ? interpolate(frame, [0, durationInFrames], [0, grow]) : 0);
  return (
    <div style={{ position: "absolute", bottom: 0, width: "100%", height: "72%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px) scale(${sc})`, transformOrigin: "bottom center" }}>
      <Img src={staticFile(`cut/${file}.png`)} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 45px ${accent}) drop-shadow(0 12px 20px #000a)` }} />
    </div>
  );
};

const Scrim = () => <AbsoluteFill style={{ background: "linear-gradient(to top, #05060a 4%, transparent 26%)" }} />;

// Golden-boot emoji badge that pops in on the beat.
const BootBadge: React.FC<{ delay: number; size?: number; top?: string }> = ({ delay, size = 150, top = "8%" }) => {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - delay, fps: GB_FPS, config: { damping: 9, mass: 0.5 } });
  return <div style={{ position: "absolute", top, width: "100%", textAlign: "center", fontSize: size, transform: `scale(${interpolate(s, [0, 1], [0, 1])})` }}>🥇</div>;
};

const StatLine: React.FC<{ goals: number; assists: number; accent: string; start?: number }> = ({ goals, assists, accent, start = 8 }) => {
  const frame = useCurrentFrame();
  const g = Math.round(interpolate(frame, [start, start + 26], [0, goals], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return (
    <div style={{ position: "absolute", top: "17%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900 }}>
      <div style={{ fontSize: 300, color: "#fff", lineHeight: 0.9, textShadow: `0 0 40px ${accent}, 0 0 90px ${accent}, 0 8px 24px #000`, letterSpacing: -6 }}>{g}</div>
      <div style={{ fontSize: 58, color: accent, letterSpacing: 8, marginTop: -8 }}>GOALS{assists ? `  •  ${assists} ASSISTS` : ""}</div>
    </div>
  );
};

const ContenderCard: React.FC<{ p: P }> = ({ p }) => {
  const frame = useCurrentFrame();
  const sh = beatShake(frame);
  const nameS = spring({ frame: frame - 6, fps: GB_FPS, config: { damping: 16 } });
  return (
    <AbsoluteFill>
      <StadiumBg accent={p.accent} />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, ${sh * 0.6}px)` }}>
        <StatLine goals={p.goals} assists={p.assists} accent={p.accent} />
        <Cutout file={p.file} accent={p.accent} />
        <Scrim />
        <div style={{ position: "absolute", top: 90, left: 60, width: 150, height: 150, borderRadius: 90, background: "#0a0c14ee", border: `7px solid ${p.accent}`, display: "flex", justifyContent: "center", alignItems: "center", fontFamily: FONT, fontWeight: 900, fontSize: 74, color: p.accent, boxShadow: `0 0 30px ${p.accent}88` }}>#{p.rank}</div>
        <div style={{ position: "absolute", bottom: 150, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 92, color: "#fff", opacity: interpolate(nameS, [0, 1], [0, 1]), transform: `translateY(${interpolate(nameS, [0, 1], [40, 0])}px)`, textShadow: "0 4px 20px #000, 0 0 30px #0008", letterSpacing: 2 }}>{p.name}</div>
        <div style={{ position: "absolute", bottom: 96, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 40, color: "#aeb4c4", letterSpacing: 6 }}>{p.country}</div>
        <div style={{ position: "absolute", bottom: 44, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 34, color: p.accent, letterSpacing: 5 }}>WORLD CUP 2026</div>
      </div>
    </AbsoluteFill>
  );
};

const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const s = spring({ frame, fps: GB_FPS, config: { damping: 14 } });
  return (
    <AbsoluteFill>
      <StadiumBg accent={WINNER.accent} ken={0.05} />
      <Cutout file="mbappe" accent={WINNER.accent} />
      <Scrim />
      <BootBadge delay={6} size={130} top="6%" />
      <div style={{ position: "absolute", top: "22%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 88, color: "#fff", transform: `scale(${interpolate(s, [0, 1], [0.7, 1])})`, opacity: s, textShadow: "0 6px 30px #000" }}>WORLD CUP 2026</div>
      <div style={{ position: "absolute", top: "31%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 128, color: WINNER.accent, opacity: s, textShadow: `0 0 50px ${WINNER.accent}` }}>GOLDEN BOOT</div>
      <div style={{ position: "absolute", top: "43%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 56, color: "#fff", opacity: interpolate(frame, [16, 28], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" }) }}>KAUN JEETA? 🔥</div>
    </AbsoluteFill>
  );
};

const Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const g = Math.round(interpolate(frame, [12, 50], [0, WINNER.goals], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const crownS = spring({ frame: frame - 8, fps: GB_FPS, config: { damping: 9, mass: 0.5 } });
  const kingOp = interpolate(frame, [82, 104], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sh = beatShake(frame, 4);
  return (
    <AbsoluteFill>
      <StadiumBg accent={WINNER.accent} ken={0.09} />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, 0)` }}>
        <div style={{ position: "absolute", top: "16%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 260, color: "#fff", textShadow: `0 0 50px ${WINNER.accent}, 0 0 110px ${WINNER.accent}` }}>{g}</div>
        <div style={{ position: "absolute", top: "42%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 52, color: WINNER.accent, letterSpacing: 6 }}>GOALS • 2 ASSISTS</div>
        <Cutout file="mbappe" accent={WINNER.accent} grow={0.1} />
        <Scrim />
        <div style={{ position: "absolute", top: "7%", width: "100%", textAlign: "center", fontSize: 150, transform: `scale(${interpolate(crownS, [0, 1], [0, 1])})` }}>👑</div>
        <div style={{ position: "absolute", top: "2%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 62, color: "#fff", textShadow: "0 4px 20px #000" }}>AUR WINNER HAI...</div>
        <div style={{ position: "absolute", bottom: 156, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 120, color: WINNER.accent, textShadow: `0 0 40px ${WINNER.accent}, 0 4px 20px #000` }}>MBAPPE</div>
        <div style={{ position: "absolute", bottom: 84, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 56, color: "#fff", opacity: kingOp, letterSpacing: 3 }}>🥇 GOLDEN BOOT WINNER</div>
      </div>
    </AbsoluteFill>
  );
};

export const GoldenBoot: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("beat.wav")} />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={INTRO}><Intro /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={slide({ direction: "from-right" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><ContenderCard p={CONTENDERS[0]} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={wipe({ direction: "from-bottom" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><ContenderCard p={CONTENDERS[1]} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={springTiming({ config: { damping: 200 }, durationInFrames: T2 })} presentation={fade()} />
        <TransitionSeries.Sequence durationInFrames={WIN}><Reveal /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
