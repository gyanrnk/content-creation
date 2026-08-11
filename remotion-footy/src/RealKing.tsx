import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring,
} from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";

// ── "THE REAL KING 👑" — Ronaldo record-reveal ────────────────────────────────
// Concept lifted from StrixR7's biggest hits (Ronaldo's Difference 19M, The Real
// King 7.5M) but rebuilt as our footage-free REAL-STAT graphic (no copyright).
// Verified stats (ESPN/UEFA/Squawka, Jul 2026):
//   976 career goals (most ever) · 143 international (WR) · 140 UCL (record)
//   · 6 World Cups played (first man ever) · 5x Ballon d'Or.
export const RK_FPS = 30;
const INTRO = 44;
const SEG = 64;
const FIN = 152;
const T1 = 8, T2 = 12;
const GOLD = "#ffcd42";
export const RK_TOTAL = INTRO + 4 * SEG + FIN - (4 * T1 + T2);

const FONT = '"Arial Black", Impact, sans-serif';

type Stat = { big: number; head: string; sub: string };
const STATS: Stat[] = [
  { big: 976, head: "CAREER GOALS", sub: "MOST IN HISTORY 🐐" },
  { big: 143, head: "INTERNATIONAL GOALS", sub: "WORLD RECORD 🌍" },
  { big: 140, head: "CHAMPIONS LEAGUE GOALS", sub: "ALL-TIME RECORD 🏆" },
  { big: 6, head: "WORLD CUPS PLAYED", sub: "FIRST MAN EVER 🔥" },
];

const beatShake = (frame: number, amt = 6) => {
  const b = frame % 15;
  return Math.exp(-b * 0.55) * Math.sin(frame * 2.5) * amt;
};

const StadiumBg: React.FC<{ ken?: number }> = ({ ken = 0.06 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = 1.05 + interpolate(frame, [0, durationInFrames], [0, ken]);
  return (
    <AbsoluteFill style={{ backgroundColor: "#05060a", overflow: "hidden" }}>
      <Img src={staticFile("bg_stadium.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, filter: "blur(3px) brightness(0.5)" }} />
      <AbsoluteFill style={{ background: GOLD, mixBlendMode: "overlay", opacity: 0.35 }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 60% 55% at 50% 42%, ${GOLD}66 0%, transparent 60%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, transparent 45%, #05060aee 100%)" }} />
    </AbsoluteFill>
  );
};

const Cutout: React.FC<{ delay?: number; grow?: number }> = ({ delay = 0, grow = 0 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.7 } });
  const ty = interpolate(s, [0, 1], [340, 0]);
  const sc = interpolate(s, [0, 1], [0.92, 1]) + (grow ? interpolate(frame, [0, durationInFrames], [0, grow]) : 0);
  return (
    <div style={{ position: "absolute", bottom: 0, width: "100%", height: "72%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px) scale(${sc})`, transformOrigin: "bottom center" }}>
      <Img src={staticFile("cut/ronaldo.png")} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 45px ${GOLD}) drop-shadow(0 12px 20px #000a)` }} />
    </div>
  );
};

const Scrim = () => <AbsoluteFill style={{ background: "linear-gradient(to top, #05060a 4%, transparent 26%)" }} />;

const StatCard: React.FC<{ s: Stat; idx: number }> = ({ s, idx }) => {
  const frame = useCurrentFrame();
  const sh = beatShake(frame);
  const shown = Math.round(interpolate(frame, [6, 34], [0, s.big], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const pop = 1 + 0.06 * Math.exp(-((frame % 15) * 0.4));
  const headS = spring({ frame: frame - 2, fps: RK_FPS, config: { damping: 16 } });
  const subS = spring({ frame: frame - 30, fps: RK_FPS, config: { damping: 15 } });
  return (
    <AbsoluteFill>
      <StadiumBg />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, ${sh * 0.6}px)` }}>
        <div style={{ position: "absolute", top: "9%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 46, color: "#fff", letterSpacing: 5, opacity: headS, transform: `translateY(${interpolate(headS, [0, 1], [-24, 0])}px)`, textShadow: "0 3px 14px #000" }}>{s.head}</div>
        <div style={{ position: "absolute", top: "15%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 320, color: "#fff", transform: `scale(${pop})`, textShadow: `0 0 40px ${GOLD}, 0 0 90px ${GOLD}, 0 8px 24px #000`, letterSpacing: -6 }}>{shown}</div>
        <Cutout />
        <Scrim />
        <div style={{ position: "absolute", top: 84, left: 60, width: 150, height: 150, borderRadius: 90, background: "#0a0c14ee", border: `7px solid ${GOLD}`, display: "flex", justifyContent: "center", alignItems: "center", fontFamily: FONT, fontWeight: 900, fontSize: 66, color: GOLD, boxShadow: `0 0 30px ${GOLD}88` }}>{idx + 1}/4</div>
        <div style={{ position: "absolute", bottom: 156, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 66, color: GOLD, opacity: subS, transform: `translateY(${interpolate(subS, [0, 1], [30, 0])}px)`, textShadow: `0 0 26px ${GOLD}, 0 4px 16px #000` }}>{s.sub}</div>
        <div style={{ position: "absolute", bottom: 92, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 60, color: "#fff", textShadow: "0 4px 20px #000", letterSpacing: 2 }}>RONALDO</div>
        <div style={{ position: "absolute", bottom: 48, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 32, color: "#cdd3e0", letterSpacing: 6 }}>THE REAL KING 👑</div>
      </div>
    </AbsoluteFill>
  );
};

const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const s = spring({ frame, fps: RK_FPS, config: { damping: 14 } });
  const crownS = spring({ frame: frame - 4, fps: RK_FPS, config: { damping: 9, mass: 0.5 } });
  return (
    <AbsoluteFill>
      <StadiumBg ken={0.05} />
      <Cutout />
      <Scrim />
      <div style={{ position: "absolute", top: "6%", width: "100%", textAlign: "center", fontSize: 130, transform: `scale(${interpolate(crownS, [0, 1], [0, 1])})` }}>👑</div>
      <div style={{ position: "absolute", top: "24%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 92, color: "#fff", transform: `scale(${interpolate(s, [0, 1], [0.7, 1])})`, opacity: s, textShadow: "0 6px 30px #000" }}>CRISTIANO</div>
      <div style={{ position: "absolute", top: "34%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 128, color: GOLD, opacity: s, textShadow: `0 0 50px ${GOLD}` }}>RONALDO</div>
      <div style={{ position: "absolute", top: "47%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 54, color: "#fff", opacity: interpolate(frame, [16, 28], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" }) }}>4 NUMBERS = 💀</div>
    </AbsoluteFill>
  );
};

const Finale: React.FC = () => {
  const frame = useCurrentFrame();
  const crownS = spring({ frame: frame - 6, fps: RK_FPS, config: { damping: 8, mass: 0.5 } });
  const kingS = spring({ frame: frame - 16, fps: RK_FPS, config: { damping: 12 } });
  const ballonOp = interpolate(frame, [46, 64], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const baitOp = interpolate(frame, [84, 104], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const baitPulse = 1 + 0.05 * Math.sin(frame * 0.35);
  const sh = beatShake(frame, 4);
  return (
    <AbsoluteFill>
      <StadiumBg ken={0.1} />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, 0)` }}>
        <Cutout grow={0.1} />
        <Scrim />
        <div style={{ position: "absolute", top: "7%", width: "100%", textAlign: "center", fontSize: 180, transform: `scale(${interpolate(crownS, [0, 1], [0, 1])})` }}>👑</div>
        <div style={{ position: "absolute", top: "30%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 118, color: GOLD, opacity: kingS, transform: `scale(${interpolate(kingS, [0, 1], [0.6, 1])})`, textShadow: `0 0 46px ${GOLD}, 0 4px 20px #000`, lineHeight: 0.95 }}>THE REAL<br />KING</div>
        <div style={{ position: "absolute", top: "50%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 58, color: "#fff", opacity: ballonOp, textShadow: "0 4px 16px #000", letterSpacing: 2 }}>5× BALLON D'OR 🏆</div>
        <div style={{ position: "absolute", bottom: 96, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 68, color: "#fff", opacity: baitOp, transform: `scale(${baitPulse})`, textShadow: `0 0 30px ${GOLD}, 0 4px 18px #000` }}>GOAT? 👇</div>
        <div style={{ position: "absolute", bottom: 50, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 34, color: "#cdd3e0", opacity: baitOp, letterSpacing: 5 }}>COMMENT KARO</div>
      </div>
    </AbsoluteFill>
  );
};

export const RealKing: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("beat.wav")} />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={INTRO}><Intro /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={slide({ direction: "from-right" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><StatCard s={STATS[0]} idx={0} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={wipe({ direction: "from-left" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><StatCard s={STATS[1]} idx={1} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={slide({ direction: "from-right" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><StatCard s={STATS[2]} idx={2} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={wipe({ direction: "from-bottom" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><StatCard s={STATS[3]} idx={3} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={springTiming({ config: { damping: 200 }, durationInFrames: T2 })} presentation={fade()} />
        <TransitionSeries.Sequence durationInFrames={FIN}><Finale /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
