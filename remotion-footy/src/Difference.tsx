import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring,
} from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";

// ── "RONALDO'S DIFFERENCE" — Ronaldo vs Messi record gap ──────────────────────
// Concept lifted from StrixR7's biggest hit (Ronaldo's Difference, 19M) but
// rebuilt as our footage-free REAL-STAT comparison (no copyright). CR7-positive:
// records where Ronaldo leads, honest selection, real numbers only.
// Verified (ESPN/UEFA, Jul 2026):
//   Career goals   976 vs 919  (+57)
//   Int'l goals    143 vs 125  (+18)
//   UCL goals      140 vs 129  (+11)
export const DF_FPS = 30;
const INTRO = 44;
const SEG = 70;
const FIN = 150;
const T1 = 8, T2 = 12;
const GOLD = "#ffcd42";
const GREY = "#9aa2b4";
export const DF_TOTAL = INTRO + 3 * SEG + FIN - (3 * T1 + T2);

const FONT = '"Arial Black", Impact, sans-serif';

type Duel = { head: string; r: number; m: number };
const DUELS: Duel[] = [
  { head: "CAREER GOALS", r: 976, m: 919 },
  { head: "INTERNATIONAL GOALS", r: 143, m: 125 },
  { head: "CHAMPIONS LEAGUE GOALS", r: 140, m: 129 },
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
      <AbsoluteFill style={{ background: GOLD, mixBlendMode: "overlay", opacity: 0.28 }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 60% 55% at 50% 42%, ${GOLD}55 0%, transparent 60%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, transparent 45%, #05060aee 100%)" }} />
    </AbsoluteFill>
  );
};

const Scrim = () => <AbsoluteFill style={{ background: "linear-gradient(to top, #05060a 6%, transparent 30%)" }} />;

// One player's half of the split screen.
const Half: React.FC<{ file: string; side: "L" | "R"; accent: string; dim?: boolean; delay?: number }> =
  ({ file, side, accent, dim = false, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.7 } });
  const dx = interpolate(s, [0, 1], [side === "L" ? -260 : 260, 0]);
  return (
    <div style={{ position: "absolute", bottom: 0, [side === "L" ? "left" : "right"]: 0, width: "54%", height: "74%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateX(${dx}px)` }}>
      <Img src={staticFile(`cut/${file}.png`)} style={{ height: "100%", objectFit: "contain", filter: dim ? `grayscale(0.55) brightness(0.72) drop-shadow(0 10px 18px #000a)` : `drop-shadow(0 0 45px ${accent}) drop-shadow(0 12px 20px #000a)` }} />
    </div>
  );
};

const DuelCard: React.FC<{ d: Duel; idx: number }> = ({ d, idx }) => {
  const frame = useCurrentFrame();
  const sh = beatShake(frame);
  const rShown = Math.round(interpolate(frame, [8, 38], [0, d.r], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const mShown = Math.round(interpolate(frame, [8, 38], [0, d.m], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const pop = 1 + 0.05 * Math.exp(-((frame % 15) * 0.4));
  const gapS = spring({ frame: frame - 42, fps: DF_FPS, config: { damping: 10, mass: 0.6 } });
  const gap = d.r - d.m;
  return (
    <AbsoluteFill>
      <StadiumBg />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, ${sh * 0.5}px)` }}>
        {/* header */}
        <div style={{ position: "absolute", top: "6.5%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 50, color: "#fff", letterSpacing: 4, textShadow: "0 3px 14px #000" }}>{d.head}</div>
        <div style={{ position: "absolute", top: 92, left: 54, fontFamily: FONT, fontWeight: 900, fontSize: 44, color: GOLD, opacity: 0.85 }}>{idx + 1}/3</div>
        {/* cutouts */}
        <Half file="ronaldo" side="L" accent={GOLD} delay={2} />
        <Half file="messi" side="R" accent={GREY} dim delay={6} />
        <Scrim />
        {/* numbers */}
        <div style={{ position: "absolute", top: "15%", left: 0, width: "50%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 176, color: "#fff", transform: `scale(${pop})`, textShadow: `0 0 34px ${GOLD}, 0 0 80px ${GOLD}, 0 6px 20px #000` }}>{rShown}</div>
        <div style={{ position: "absolute", top: "15%", right: 0, width: "50%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 176, color: "#e6e9f0", textShadow: "0 6px 20px #000" }}>{mShown}</div>
        {/* VS pill */}
        <div style={{ position: "absolute", top: "27%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 66, color: "#fff", textShadow: "0 0 20px #000, 0 4px 14px #000" }}>VS</div>
        {/* gap badge */}
        <div style={{ position: "absolute", top: "35%", width: "100%", textAlign: "center", transform: `scale(${interpolate(gapS, [0, 1], [0, 1])})` }}>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 74, color: "#05060a", background: GOLD, padding: "8px 30px", borderRadius: 50, boxShadow: `0 0 34px ${GOLD}` }}>+{gap} 🐐</span>
        </div>
        {/* name labels */}
        <div style={{ position: "absolute", bottom: 78, left: 0, width: "50%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 58, color: GOLD, textShadow: `0 0 22px ${GOLD}, 0 4px 14px #000` }}>RONALDO</div>
        <div style={{ position: "absolute", bottom: 78, right: 0, width: "50%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 58, color: GREY, textShadow: "0 4px 14px #000" }}>MESSI</div>
        <div style={{ position: "absolute", bottom: 34, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 30, color: "#cdd3e0", letterSpacing: 6 }}>THE DIFFERENCE 🐐</div>
      </div>
    </AbsoluteFill>
  );
};

const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const s = spring({ frame, fps: DF_FPS, config: { damping: 14 } });
  return (
    <AbsoluteFill>
      <StadiumBg ken={0.05} />
      <Half file="ronaldo" side="L" accent={GOLD} delay={0} />
      <Half file="messi" side="R" accent={GREY} dim delay={4} />
      <Scrim />
      <div style={{ position: "absolute", top: "20%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 96, color: "#fff", transform: `scale(${interpolate(s, [0, 1], [0.7, 1])})`, opacity: s, textShadow: "0 6px 30px #000" }}>RONALDO'S</div>
      <div style={{ position: "absolute", top: "30%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 132, color: GOLD, opacity: s, textShadow: `0 0 50px ${GOLD}` }}>DIFFERENCE</div>
      <div style={{ position: "absolute", top: "43%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 56, color: "#fff", opacity: interpolate(frame, [16, 28], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" }) }}>vs MESSI 👀</div>
    </AbsoluteFill>
  );
};

const Finale: React.FC = () => {
  const frame = useCurrentFrame();
  const crownS = spring({ frame: frame - 6, fps: DF_FPS, config: { damping: 8, mass: 0.5 } });
  const scoreS = spring({ frame: frame - 18, fps: DF_FPS, config: { damping: 12 } });
  const baitOp = interpolate(frame, [80, 100], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const baitPulse = 1 + 0.05 * Math.sin(frame * 0.35);
  const sh = beatShake(frame, 4);
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 15, mass: 0.7 } });
  const ty = interpolate(s, [0, 1], [340, 0]);
  return (
    <AbsoluteFill>
      <StadiumBg ken={0.1} />
      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "72%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px)` }}>
        <Img src={staticFile("cut/ronaldo.png")} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 50px ${GOLD}) drop-shadow(0 12px 20px #000a)` }} />
      </div>
      <Scrim />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, 0)` }}>
        <div style={{ position: "absolute", top: "6%", width: "100%", textAlign: "center", fontSize: 176, transform: `scale(${interpolate(crownS, [0, 1], [0, 1])})` }}>👑</div>
        <div style={{ position: "absolute", top: "28%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 120, color: GOLD, opacity: scoreS, transform: `scale(${interpolate(scoreS, [0, 1], [0.6, 1])})`, textShadow: `0 0 46px ${GOLD}, 0 4px 20px #000` }}>3 - 0</div>
        <div style={{ position: "absolute", top: "42%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 40, color: "#cdd3e0", opacity: scoreS, letterSpacing: 4 }}>RECORDS SHOWN 🐐</div>
        <div style={{ position: "absolute", bottom: 98, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 72, color: "#fff", opacity: baitOp, transform: `scale(${baitPulse})`, textShadow: `0 0 30px ${GOLD}, 0 4px 18px #000` }}>GOAT? 👇</div>
        <div style={{ position: "absolute", bottom: 50, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 34, color: "#cdd3e0", opacity: baitOp, letterSpacing: 5 }}>COMMENT KARO 🔥</div>
      </div>
    </AbsoluteFill>
  );
};

export const Difference: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("beat.wav")} />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={INTRO}><Intro /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={slide({ direction: "from-right" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><DuelCard d={DUELS[0]} idx={0} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={wipe({ direction: "from-left" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><DuelCard d={DUELS[1]} idx={1} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T1 })} presentation={wipe({ direction: "from-bottom" })} />
        <TransitionSeries.Sequence durationInFrames={SEG}><DuelCard d={DUELS[2]} idx={2} /></TransitionSeries.Sequence>
        <TransitionSeries.Transition timing={springTiming({ config: { damping: 200 }, durationInFrames: T2 })} presentation={fade()} />
        <TransitionSeries.Sequence durationInFrames={FIN}><Finale /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
