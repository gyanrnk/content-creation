import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring,
} from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";

export const UCL_FPS = 30;
const INTRO = 42;
const SEG = 54;
const WIN = 168;
const T1 = 8, T2 = 12;
export const UCL_TOTAL = INTRO + 4 * SEG + WIN - (4 * T1 + T2);

const FONT = '"Arial Black", Impact, sans-serif';

type P = { rank: number; name: string; num: number; accent: string; file: string };
const PLAYERS: P[] = [
  { rank: 5, name: "RAUL", num: 71, accent: "#d8dde6", file: "raul" },
  { rank: 4, name: "BENZEMA", num: 90, accent: "#7ab8ff", file: "benzema" },
  { rank: 3, name: "LEWANDOWSKI", num: 105, accent: "#ff8c50", file: "lewandowski" },
  { rank: 2, name: "MESSI", num: 129, accent: "#6ec8ff", file: "messi" },
];
const CR7: P = { rank: 1, name: "RONALDO", num: 141, accent: "#ffcd42", file: "ronaldo" };

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

const BigNumber: React.FC<{ num: number; accent: string; start?: number; dur?: number }> = ({ num, accent, start = 5, dur = 34 }) => {
  const frame = useCurrentFrame();
  const shown = Math.round(interpolate(frame, [start, start + dur], [0, num], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const pop = 1 + 0.06 * Math.exp(-((frame % 15) * 0.4));
  return (
    <div style={{ position: "absolute", top: "20%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 320, color: "#fff", transform: `scale(${pop})`, textShadow: `0 0 40px ${accent}, 0 0 90px ${accent}, 0 8px 24px #000`, letterSpacing: -6 }}>{shown}</div>
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

const PlayerCard: React.FC<{ p: P }> = ({ p }) => {
  const frame = useCurrentFrame();
  const sh = beatShake(frame);
  const nameS = spring({ frame: frame - 6, fps: UCL_FPS, config: { damping: 16 } });
  return (
    <AbsoluteFill>
      <StadiumBg accent={p.accent} />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, ${sh * 0.6}px)` }}>
        <BigNumber num={p.num} accent={p.accent} />
        <Cutout file={p.file} accent={p.accent} />
        <Scrim />
        <div style={{ position: "absolute", top: 90, left: 60, width: 150, height: 150, borderRadius: 90, background: "#0a0c14ee", border: `7px solid ${p.accent}`, display: "flex", justifyContent: "center", alignItems: "center", fontFamily: FONT, fontWeight: 900, fontSize: 74, color: p.accent, boxShadow: `0 0 30px ${p.accent}88` }}>#{p.rank}</div>
        <div style={{ position: "absolute", bottom: 130, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 92, color: "#fff", opacity: interpolate(nameS, [0, 1], [0, 1]), transform: `translateY(${interpolate(nameS, [0, 1], [40, 0])}px)`, textShadow: "0 4px 20px #000, 0 0 30px #0008", letterSpacing: 2 }}>{p.name}</div>
        <div style={{ position: "absolute", bottom: 80, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 40, color: "#aeb4c4", letterSpacing: 6 }}>UCL GOALS</div>
      </div>
    </AbsoluteFill>
  );
};

const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const s = spring({ frame, fps: UCL_FPS, config: { damping: 14 } });
  return (
    <AbsoluteFill>
      <StadiumBg accent={CR7.accent} ken={0.05} />
      <Cutout file="ronaldo" accent={CR7.accent} />
      <Scrim />
      <div style={{ position: "absolute", top: "23%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 96, color: "#fff", transform: `scale(${interpolate(s, [0, 1], [0.7, 1])})`, opacity: s, textShadow: "0 6px 30px #000" }}>MOST</div>
      <div style={{ position: "absolute", top: "33%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 132, color: CR7.accent, opacity: s, textShadow: `0 0 50px ${CR7.accent}` }}>UCL GOALS</div>
      <div style={{ position: "absolute", top: "45%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 60, color: "#fff", opacity: interpolate(frame, [14, 26], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" }) }}>TOP 5 🌟</div>
    </AbsoluteFill>
  );
};

const Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const shown = Math.round(interpolate(frame, [12, 60], [0, CR7.num], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const crownS = spring({ frame: frame - 8, fps: UCL_FPS, config: { damping: 9, mass: 0.5 } });
  const kingOp = interpolate(frame, [80, 100], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sh = beatShake(frame, 4);
  return (
    <AbsoluteFill>
      <StadiumBg accent={CR7.accent} ken={0.09} />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, 0)` }}>
        <div style={{ position: "absolute", top: "18%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 300, color: "#fff", textShadow: `0 0 50px ${CR7.accent}, 0 0 110px ${CR7.accent}` }}>{shown}</div>
        <Cutout file="ronaldo" accent={CR7.accent} grow={0.1} />
        <Scrim />
        <div style={{ position: "absolute", top: "8%", width: "100%", textAlign: "center", fontSize: 150, transform: `scale(${interpolate(crownS, [0, 1], [0, 1])})` }}>👑</div>
        <div style={{ position: "absolute", top: "3%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 64, color: "#fff", textShadow: "0 4px 20px #000" }}>AND #1 IS...</div>
        <div style={{ position: "absolute", bottom: 150, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 118, color: CR7.accent, textShadow: `0 0 40px ${CR7.accent}, 0 4px 20px #000` }}>RONALDO</div>
        <div style={{ position: "absolute", bottom: 80, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 60, color: "#fff", opacity: kingOp, letterSpacing: 3 }}>THE UCL KING</div>
      </div>
    </AbsoluteFill>
  );
};

export const UCLGoals: React.FC = () => {
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
