import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring, random,
} from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";

// ── "ARCHIVE" — a documentary-style format, 5th distinct visual language ─────
// The four existing formats are all "card" formats: a subject, a big number, a
// slam. Fine for a stat, useless for a STORY. This one is built for stories that
// span time — the whole edit is a move from past to present.
//
// Nothing here is reused from the other formats:
//   grade      sepia + heavy grain in act 1, bleeding into full colour by act 3
//   framing    letterbox bars that open, cinema aspect inside a 9:16 frame
//   type       typewriter reveal, monospace slate cards — no Impact slams
//   transport  a YEAR SCRUB that rolls 1966 -> 2024 as the timeline bar fills
//   texture    film scratches, dust, gate weave (tiny random frame offset)
//
// Story (verified 2026-08-10):
//   1966  Paco Gento wins his 6th European Cup — record set
//   58yr  nobody matches it
//   2024  Modric, Kroos, Carvajal and Nacho all reach 6 in the same season
//   Ronaldo, the competition's top scorer ever, is on 5
export const AR_FPS = 30;
const ACT1 = 150;
const ACT2 = 90;
const ACT3 = 170;
const ACT4 = 110;
const T = 14;
export const AR_TOTAL = ACT1 + ACT2 + ACT3 + ACT4 - 3 * T;   // 478f = 15.9s

const MONO = '"Courier New", ui-monospace, monospace';
const SERIF = '"Times New Roman", Georgia, serif';
const PAPER = "#e8dcc3";
const INK = "#12100c";

export type ArchiveProps = {
  yearFrom: string;
  yearTo: string;
  slate: string;
  act1Name: string;
  act1File: string;
  act1Line: string;
  act1Sub: string;
  gapLine: string;
  gapSub: string;
  act3Line: string;
  people: { name: string; file: string }[];
  bigNumber: string;
  bigLabel: string;
  footnote: string;
  bait: string;
  baitSub: string;
};

export const DEFAULT_ARCHIVE_PROPS: ArchiveProps = {
  yearFrom: "1966",
  yearTo: "2024",
  slate: "EUROPEAN CUP · ARCHIVE",
  act1Name: "PACO GENTO",
  act1File: "gento",
  act1Line: "WINS HIS 6th EUROPEAN CUP",
  act1Sub: "A RECORD IS SET",
  gapLine: "58 YEARS",
  gapSub: "NOBODY CAME CLOSE",
  act3Line: "FOUR MEN MATCHED IT",
  people: [
    { name: "MODRIC", file: "modric" },
    { name: "KROOS", file: "kroos" },
    { name: "CARVAJAL", file: "carvajal" },
    { name: "NACHO", file: "nacho" },
  ],
  bigNumber: "6",
  bigLabel: "MOST EVER WON BY A PLAYER",
  footnote: "RONALDO — THE COMPETITION'S TOP SCORER — HAS 5",
  bait: "WHO GETS 7 FIRST? 👇",
  baitSub: "NAME HIM 🏆",
};

// ── film texture ─────────────────────────────────────────────────────────────

// Gate weave: real projected film never sits perfectly still. A sub-pixel
// wobble on the whole frame is most of why footage "feels" like film.
const useWeave = (amt = 1) => {
  const frame = useCurrentFrame();
  return {
    x: (random(`wx${frame}`) - 0.5) * 2.4 * amt,
    y: (random(`wy${frame}`) - 0.5) * 2.4 * amt,
  };
};

const Scratches: React.FC<{ density?: number }> = ({ density = 1 }) => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay" }}>
      {new Array(Math.round(4 * density)).fill(0).map((_, i) => {
        if (random(`s${i}${seed}`) > 0.55) return null;
        const x = random(`sx${i}${seed}`) * 100;
        const h = 20 + random(`sh${i}${seed}`) * 70;
        const top = random(`st${i}${seed}`) * 60;
        return <div key={i} style={{
          position: "absolute", left: `${x}%`, top: `${top}%`, width: 2, height: `${h}%`,
          background: "#fff", opacity: 0.16,
        }} />;
      })}
      {new Array(Math.round(26 * density)).fill(0).map((_, i) => {
        const x = random(`dx${i}${seed}`) * 100;
        const y = random(`dy${i}${seed}`) * 100;
        const s = 2 + random(`ds${i}${seed}`) * 4;
        return <div key={`d${i}`} style={{
          position: "absolute", left: `${x}%`, top: `${y}%`, width: s, height: s,
          borderRadius: "50%", background: random(`dc${i}${seed}`) > 0.5 ? "#fff" : "#000",
          opacity: 0.22,
        }} />;
      })}
    </AbsoluteFill>
  );
};

const Vignette = () => (
  <AbsoluteFill style={{ background: "radial-gradient(ellipse 78% 70% at 50% 46%, transparent 40%, #000 100%)", pointerEvents: "none" }} />
);

// Cinema bars inside the vertical frame — they open at the top of the film.
const Letterbox: React.FC<{ open: number }> = ({ open }) => {
  const h = interpolate(open, [0, 1], [26, 13]);
  return (
    <>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: `${h}%`, background: "#000", zIndex: 40 }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: `${h}%`, background: "#000", zIndex: 40 }} />
    </>
  );
};

const Slate: React.FC<{ text: string }> = ({ text }) => (
  <div style={{
    position: "absolute", top: "15.5%", width: "100%", textAlign: "center",
    fontFamily: MONO, fontSize: 24, letterSpacing: 7, color: "#b9ac90", zIndex: 45,
  }}>{text}</div>
);

// Typewriter — characters land one at a time with a blinking caret.
const Typer: React.FC<{ text: string; start: number; cps?: number; style?: React.CSSProperties }> =
  ({ text, start, cps = 26, style }) => {
    const frame = useCurrentFrame();
    const n = Math.max(0, Math.floor(((frame - start) / AR_FPS) * cps));
    const shown = text.slice(0, n);
    const done = n >= text.length;
    const caret = Math.floor(frame / 8) % 2 === 0;
    if (frame < start) return null;
    return (
      <div style={style}>
        {shown}{!done || caret ? <span style={{ opacity: 0.75 }}>▌</span> : null}
      </div>
    );
  };

// ── acts ─────────────────────────────────────────────────────────────────────

const Act1: React.FC<{ p: ArchiveProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const w = useWeave(1.4);
  const open = spring({ frame: frame - 4, fps, config: { damping: 22, mass: 1.2 } });
  const rise = spring({ frame: frame - 10, fps, config: { damping: 26, mass: 1.8, stiffness: 52 } });
  const ty = interpolate(rise, [0, 1], [90, 0]);
  const yearS = spring({ frame, fps, config: { damping: 12, mass: 0.7 } });
  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${w.x}px, ${w.y}px)` }}>
        <div style={{ position: "absolute", bottom: "13%", width: "100%", height: "52%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px)`, opacity: rise }}>
          <Img src={staticFile(`cut/${p.act1File}.png`)} style={{
            height: "100%", maxWidth: "82%", objectFit: "contain",
            filter: "sepia(0.85) contrast(1.15) brightness(0.95) drop-shadow(0 14px 26px #000)",
          }} />
        </div>
        <AbsoluteFill style={{ background: `linear-gradient(to top, ${INK} 14%, transparent 42%)` }} />
        {/* The typed block sits over the subject's chest, so it needs its own
            plate — without this the sepia photo eats the copy entirely. */}
        <AbsoluteFill style={{ background: `linear-gradient(to bottom, ${INK} 14%, ${INK}f2 34%, ${INK}d9 50%, transparent 62%)` }} />

        <div style={{
          position: "absolute", top: "20%", width: "100%", textAlign: "center",
          fontFamily: SERIF, fontWeight: 700, fontSize: 210, color: PAPER,
          transform: `scale(${interpolate(yearS, [0, 1], [1.35, 1])})`,
          opacity: yearS, letterSpacing: 6,
        }}>{p.yearFrom}</div>

        <Typer text={p.act1Name} start={26} cps={20} style={{
          position: "absolute", top: "38%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontWeight: 700, fontSize: 52, color: PAPER, letterSpacing: 3,
        }} />
        <Typer text={p.act1Line} start={54} cps={30} style={{
          position: "absolute", top: "44%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontSize: 32, color: "#c7b998", letterSpacing: 2,
        }} />
        <Typer text={p.act1Sub} start={92} cps={22} style={{
          position: "absolute", top: "50%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontWeight: 700, fontSize: 36, color: "#e2b45a", letterSpacing: 5,
        }} />
      </div>
      <Scratches density={1.5} />
      <Vignette />
      <Slate text={p.slate} />
      <Letterbox open={open} />
    </AbsoluteFill>
  );
};

// The transport shot: years roll and a bar fills. This is the "time passing"
// beat that a card format simply cannot do.
const Act2: React.FC<{ p: ArchiveProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const w = useWeave(1.1);
  const from = parseInt(p.yearFrom, 10), to = parseInt(p.yearTo, 10);
  const t = interpolate(frame, [8, 62], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const year = Math.round(from + (to - from) * t);
  const blur = interpolate(t, [0, 0.5, 1], [0, 5, 0]);
  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${w.x}px, ${w.y}px)` }}>
        <div style={{
          position: "absolute", top: "31%", width: "100%", textAlign: "center",
          fontFamily: SERIF, fontWeight: 700, fontSize: 230, color: PAPER,
          filter: `blur(${blur}px)`, letterSpacing: 4,
        }}>{year}</div>

        {/* timeline */}
        <div style={{ position: "absolute", top: "52%", left: "12%", width: "76%", height: 4, background: "#3a352a" }}>
          <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${t * 100}%`, background: "#e2b45a", boxShadow: "0 0 18px #e2b45a" }} />
          <div style={{ position: "absolute", left: `${t * 100}%`, top: -7, width: 3, height: 18, background: PAPER }} />
        </div>

        <div style={{
          position: "absolute", top: "58%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontWeight: 700, fontSize: 74, color: "#e2b45a",
          opacity: interpolate(frame, [58, 74], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          letterSpacing: 4,
        }}>{p.gapLine}</div>
        <Typer text={p.gapSub} start={72} cps={26} style={{
          position: "absolute", top: "67%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontSize: 34, color: "#c7b998", letterSpacing: 3,
        }} />
      </div>
      <Scratches density={1.2} />
      <Vignette />
      <Slate text={p.slate} />
      <Letterbox open={1} />
    </AbsoluteFill>
  );
};

// Colour returns here — the grade itself carries "past -> present".
const Act3: React.FC<{ p: ArchiveProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const w = useWeave(0.6);
  const colour = interpolate(frame, [0, 46], [1, 0], { extrapolateRight: "clamp" });
  const yearS = spring({ frame, fps, config: { damping: 12, mass: 0.7 } });
  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0c12" }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${w.x}px, ${w.y}px)`, filter: `sepia(${colour}) contrast(${1 + colour * 0.15})` }}>
        {/* Full-width columns with maxWidth on the image itself. Without the
            maxWidth the portraits keep their natural aspect and spill sideways
            into each other — four overlapping heads instead of a line-up. */}
        <div style={{ position: "absolute", bottom: "20%", width: "100%", height: "44%", display: "flex", justifyContent: "center", alignItems: "flex-end" }}>
          {p.people.map((pl, i) => {
            const s = spring({ frame: frame - 22 - i * 9, fps, config: { damping: 24, mass: 1.4, stiffness: 58 } });
            return (
              <div key={i} style={{
                width: `${100 / p.people.length}%`, height: "100%", display: "flex",
                alignItems: "flex-end", justifyContent: "center", overflow: "hidden",
                transform: `translateY(${interpolate(s, [0, 1], [230, 0])}px)`, opacity: s,
              }}>
                <Img src={staticFile(`cut/${pl.file}.png`)} style={{
                  height: "100%", maxWidth: "94%", objectFit: "contain",
                  filter: "drop-shadow(0 0 22px #e2b45a55) drop-shadow(0 10px 18px #000c)",
                }} />
              </div>
            );
          })}
        </div>
        <AbsoluteFill style={{ background: "linear-gradient(to top, #0a0c12 12%, transparent 40%)" }} />
        <AbsoluteFill style={{ background: "linear-gradient(to bottom, #0a0c12f2 12%, transparent 38%)" }} />

        <div style={{
          position: "absolute", top: "19%", width: "100%", textAlign: "center",
          fontFamily: SERIF, fontWeight: 700, fontSize: 190, color: PAPER,
          transform: `scale(${interpolate(yearS, [0, 1], [1.3, 1])})`, opacity: yearS, letterSpacing: 6,
        }}>{p.yearTo}</div>
        <Typer text={p.act3Line} start={30} cps={26} style={{
          position: "absolute", top: "35%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontWeight: 700, fontSize: 46, color: "#e2b45a", letterSpacing: 3,
        }} />

        {/* 15.5% keeps the name row clear of the 13% letterbox bar — at 8.5%
            it rendered underneath the black band and never showed. */}
        <div style={{ position: "absolute", bottom: "15.5%", width: "100%", display: "flex", justifyContent: "center" }}>
          {p.people.map((pl, i) => (
            <div key={i} style={{
              width: `${100 / p.people.length}%`, textAlign: "center", fontFamily: MONO,
              fontWeight: 700, fontSize: 23, color: PAPER, letterSpacing: 0,
              opacity: interpolate(frame, [40 + i * 9, 56 + i * 9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
            }}>{pl.name}</div>
          ))}
        </div>
      </div>
      <Scratches density={0.5} />
      <Vignette />
      <Slate text={p.slate} />
      <Letterbox open={1} />
    </AbsoluteFill>
  );
};

const Act4: React.FC<{ p: ArchiveProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const w = useWeave(0.5);
  const s = spring({ frame: frame - 4, fps, config: { damping: 11, mass: 0.8 } });
  const baitOp = interpolate(frame, [50, 68], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pulse = 1 + 0.045 * Math.sin(frame * 0.34);
  // Loop joint: drain to the same near-black slate that Act 1 opens on.
  const loopOut = interpolate(frame, [ACT4 - 18, ACT4 - 2], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      <div style={{ position: "absolute", inset: 0, opacity: loopOut, transform: `translate(${w.x}px, ${w.y}px)` }}>
        <div style={{
          position: "absolute", top: "20%", width: "100%", textAlign: "center",
          fontFamily: SERIF, fontWeight: 700, fontSize: 400, lineHeight: 1, color: "#e2b45a",
          transform: `scale(${interpolate(s, [0, 1], [0.5, 1])})`, opacity: s,
          textShadow: "0 0 70px #e2b45a55",
        }}>{p.bigNumber}</div>
        <Typer text={p.bigLabel} start={30} cps={30} style={{
          position: "absolute", top: "50%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontWeight: 700, fontSize: 36, color: PAPER, letterSpacing: 4,
        }} />
        <Typer text={p.footnote} start={58} cps={44} style={{
          position: "absolute", top: "57%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontSize: 24, color: "#9c917a", letterSpacing: 2,
        }} />
        <div style={{
          position: "absolute", bottom: "17%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontWeight: 700, fontSize: 52, color: PAPER,
          opacity: baitOp, transform: `scale(${pulse})`,
        }}>{p.bait}</div>
        <div style={{
          position: "absolute", bottom: "13%", width: "100%", textAlign: "center",
          fontFamily: MONO, fontSize: 26, color: "#9c917a", opacity: baitOp, letterSpacing: 5,
        }}>{p.baitSub}</div>
      </div>
      <Scratches density={0.8} />
      <Vignette />
      <Letterbox open={1} />
    </AbsoluteFill>
  );
};

export const Archive: React.FC<Partial<ArchiveProps>> = (given) => {
  const p: ArchiveProps = { ...DEFAULT_ARCHIVE_PROPS, ...given };
  const dis = () => (
    <TransitionSeries.Transition timing={linearTiming({ durationInFrames: T })} presentation={fade()} />
  );
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Purpose-written score (make_score.py) — synthesized from scratch, so
          there is nothing to claim and nothing to attribute. The generic
          beat.wav fought this format's pacing; this one follows the four acts. */}
      <Audio src={staticFile("score_archive.wav")} />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={ACT1}><Act1 p={p} /></TransitionSeries.Sequence>
        {dis()}
        <TransitionSeries.Sequence durationInFrames={ACT2}><Act2 p={p} /></TransitionSeries.Sequence>
        {dis()}
        <TransitionSeries.Sequence durationInFrames={ACT3}><Act3 p={p} /></TransitionSeries.Sequence>
        {dis()}
        <TransitionSeries.Sequence durationInFrames={ACT4}><Act4 p={p} /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
