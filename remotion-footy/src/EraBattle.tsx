import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring,
} from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";

// ── "GOLDEN ERA vs NEW ERA" — the mountain the new generation has to climb ────
// Format lifted from our own best performer (New Era vs Golden Era, 1830 views /
// 71.9% retention) but rebuilt on the Remotion engine: no Veo clips, no footage,
// renders in minutes. Sub-converting shape (WHAT IF / VS battle) + real stats.
//
// THREE DATA RULES BAKED IN (from channel analytics, Aug 2026):
//   1. <20s hard cap  — 33s video collapsed to 36% retention
//   2. loop ending    — finale fades back to the intro's opening frame, so a
//                       replay is seamless (our 139.9% retention video proved it)
//   3. on-screen bait — the question lives IN the video, not just description
//
// Verified numbers (Aug 7, 2026):
//   Career goals  Ronaldo 976 (multiple trackers) vs Haaland 354 (FootyStats;
//                 sources vary 354-358, all agree "350+")
//   UCL goals     Ronaldo 140 vs Mbappe 60 in 89 games (ESPN, 6th all-time)
//   Ballon d'Ors  Messi 8 (2009-12, 2015, 2019, 2021, 2023) vs Haaland 0
//                 (2026 award not presented until 26 Oct 2026, so 8 still stands)
export const EB_FPS = 30;
// PACING (v2): slides were snapping past before the eye could land on a number.
// Segments longer, transitions ~2x slower, and the two sides now arrive STAGGERED
// (gold first, neon after) so each half gets its own beat instead of both at once.
const INTRO = 60;      // 2.0s — time to actually read the title
const SEG = 132;       // 4.4s per duel (was 3.7s)
const FIN = 126;
const T1 = 14, T2 = 10;   // T1 was 8 (0.27s) — far too quick to register

// Duration is a function of duel count so one composition serves every pack.
// 3 duels = 530f = 17.7s. The generator refuses to emit packs over the 20s cap.
export const ebTotal = (n: number) => INTRO + n * SEG + FIN - (n * T1 + T2);
export const EB_TOTAL = ebTotal(3);

const FONT = '"Arial Black", Impact, sans-serif';
const GOLD = "#ffcd42";
const NEON = "#3ee6ff";

export type Duel = {
  head: string;
  oldFile: string; oldName: string; oldVal: number;
  newFile: string; newName: string; newVal: number;
};

// Everything the render needs comes in as props, so make_packs.py can drive this
// composition with --props and never touch the .tsx again.
export type EraProps = {
  titleTop: string;
  titleBottom: string;
  subtitle: string;
  duels: Duel[];
  footer: string;
  score: string;
  finaleLine: string;
  finaleNames: string;
  finaleFaces: string[];   // 1 = centred single, 2 = split pair
  bait: string;
  baitSub: string;
};

export const DEFAULT_ERA_PROPS: EraProps = {
  titleTop: "GOLDEN ERA",
  titleBottom: "NEW ERA",
  subtitle: "3 records. No mercy. 👀",
  duels: [
    { head: "CAREER GOALS", oldFile: "ronaldo", oldName: "RONALDO", oldVal: 976, newFile: "haaland", newName: "HAALAND", newVal: 354 },
    { head: "CHAMPIONS LEAGUE GOALS", oldFile: "ronaldo", oldName: "RONALDO", oldVal: 140, newFile: "mbappe", newName: "MBAPPE", newVal: 60 },
    // Strictly 1-v-1. An earlier cut showed "13" (Messi 8 + CR7 5) next to Messi's
    // face alone — on screen the big number reads as HIS total, which would have
    // been flat wrong. Never pair an aggregate with a single portrait.
    { head: "BALLON D'ORS", oldFile: "messi", oldName: "MESSI", oldVal: 8, newFile: "haaland", newName: "HAALAND", newVal: 0 },
  ],
  footer: "GOLDEN ERA vs NEW ERA",
  score: "3 - 0",
  finaleLine: "GOLDEN ERA STILL ON TOP",
  finaleNames: "RONALDO + MESSI",
  finaleFaces: ["ronaldo", "messi"],
  bait: "CAN THEY CATCH UP? 👇",
  baitSub: "DROP A NAME 🔥",
};

const beatShake = (frame: number, amt = 6) => {
  const b = frame % 15;
  return Math.exp(-b * 0.55) * Math.sin(frame * 2.5) * amt;
};

const StadiumBg: React.FC<{ ken?: number; tint?: string }> = ({ ken = 0.06, tint = GOLD }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = 1.05 + interpolate(frame, [0, durationInFrames], [0, ken]);
  return (
    <AbsoluteFill style={{ backgroundColor: "#05060a", overflow: "hidden" }}>
      <Img src={staticFile("bg_stadium.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, filter: "blur(3px) brightness(0.5)" }} />
      <AbsoluteFill style={{ background: tint, mixBlendMode: "overlay", opacity: 0.26 }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 60% 55% at 50% 42%, ${tint}4d 0%, transparent 60%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, transparent 45%, #05060aee 100%)" }} />
    </AbsoluteFill>
  );
};

// Split the backdrop down the middle: warm gold left (old), cold neon right (new).
const EraSplit: React.FC = () => (
  <AbsoluteFill>
    <div style={{ position: "absolute", left: 0, top: 0, width: "50%", height: "100%", background: `linear-gradient(to right, ${GOLD}26, transparent)` }} />
    <div style={{ position: "absolute", right: 0, top: 0, width: "50%", height: "100%", background: `linear-gradient(to left, ${NEON}26, transparent)` }} />
    <div style={{ position: "absolute", left: "50%", top: 0, width: 3, height: "100%", background: "linear-gradient(to bottom, transparent, #ffffff55, transparent)" }} />
  </AbsoluteFill>
);

const Scrim = () => <AbsoluteFill style={{ background: "linear-gradient(to top, #05060a 6%, transparent 30%)" }} />;

const Half: React.FC<{ file: string; side: "L" | "R"; accent: string; dim?: boolean; delay?: number; h?: string }> =
  ({ file, side, accent, dim = false, delay = 0, h = "74%" }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    // Heavy + well damped = a long, smooth glide in (~1.5s) instead of a snap.
    const s = spring({ frame: frame - delay, fps, config: { damping: 26, mass: 1.9, stiffness: 52 } });
    const dx = interpolate(s, [0, 1], [side === "L" ? -300 : 300, 0]);
    return (
      <div style={{ position: "absolute", bottom: 0, [side === "L" ? "left" : "right"]: 0, width: "54%", height: h, display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateX(${dx}px)` }}>
        <Img src={staticFile(`cut/${file}.png`)} style={{ height: "100%", objectFit: "contain", filter: dim ? `grayscale(0.5) brightness(0.75) drop-shadow(0 10px 18px #000a)` : `drop-shadow(0 0 45px ${accent}) drop-shadow(0 12px 20px #000a)` }} />
      </div>
    );
  };

const DuelCard: React.FC<{ d: Duel; idx: number; total: number; footer: string }> = ({ d, idx, total, footer }) => {
  const frame = useCurrentFrame();
  const sh = beatShake(frame);
  // Staggered count-ups: gold side ticks up first and finishes before the neon
  // side starts moving, so the viewer reads one number at a time.
  const oldShown = Math.round(interpolate(frame, [16, 66], [0, d.oldVal], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const newShown = Math.round(interpolate(frame, [40, 90], [0, d.newVal], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const pop = 1 + 0.05 * Math.exp(-((frame % 15) * 0.4));
  const gapS = spring({ frame: frame - 98, fps: EB_FPS, config: { damping: 12, mass: 0.9 } });
  const gap = d.oldVal - d.newVal;
  return (
    <AbsoluteFill>
      <StadiumBg />
      <EraSplit />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, ${sh * 0.5}px)` }}>
        <div style={{ position: "absolute", top: "5.5%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 46, color: "#fff", letterSpacing: 3, textShadow: "0 3px 14px #000" }}>{d.head}</div>
        <div style={{ position: "absolute", top: 86, left: 54, fontFamily: FONT, fontWeight: 900, fontSize: 42, color: GOLD, opacity: 0.85 }}>{idx + 1}/{total}</div>

        <Half file={d.oldFile} side="L" accent={GOLD} delay={2} />
        <Half file={d.newFile} side="R" accent={NEON} dim delay={26} />
        <Scrim />

        <div style={{ position: "absolute", top: "14%", left: 0, width: "50%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 172, color: "#fff", transform: `scale(${pop})`, textShadow: `0 0 34px ${GOLD}, 0 0 80px ${GOLD}, 0 6px 20px #000` }}>{oldShown}</div>
        <div style={{ position: "absolute", top: "14%", right: 0, width: "50%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 172, color: "#e6e9f0", textShadow: `0 0 26px ${NEON}, 0 6px 20px #000` }}>{newShown}</div>

        <div style={{ position: "absolute", top: "26%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 62, color: "#fff", textShadow: "0 0 20px #000, 0 4px 14px #000" }}>VS</div>

        <div style={{ position: "absolute", top: "34%", width: "100%", textAlign: "center", transform: `scale(${interpolate(gapS, [0, 1], [0, 1])})` }}>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 70, color: "#05060a", background: GOLD, padding: "8px 30px", borderRadius: 50, boxShadow: `0 0 34px ${GOLD}` }}>+{gap} 👑</span>
        </div>

        <div style={{ position: "absolute", bottom: 76, left: 0, width: "50%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 46, color: GOLD, textShadow: `0 0 22px ${GOLD}, 0 4px 14px #000` }}>{d.oldName}</div>
        <div style={{ position: "absolute", bottom: 76, right: 0, width: "50%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 46, color: NEON, textShadow: "0 4px 14px #000" }}>{d.newName}</div>
        <div style={{ position: "absolute", bottom: 32, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 28, color: "#cdd3e0", letterSpacing: 6 }}>{footer}</div>
      </div>
    </AbsoluteFill>
  );
};

const Intro: React.FC<{ p: EraProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const s = spring({ frame, fps: EB_FPS, config: { damping: 22, mass: 1.4, stiffness: 60 } });
  const sub = interpolate(frame, [28, 46], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });
  // Intro faces = the two headliners of duel 1, so the title always matches the art.
  const d0 = p.duels[0];
  // Long era names ("CHAMPIONS LEAGUE") would overflow 1080px at 104px, so shrink to fit.
  const fit = (s: string) => (s.length > 11 ? Math.floor(104 * 11 / s.length) : 104);
  return (
    <AbsoluteFill>
      <StadiumBg ken={0.05} />
      <EraSplit />
      {/* Cutouts sit lower + shorter here so the title stack never lands on a face. */}
      <Half file={d0.oldFile} side="L" accent={GOLD} delay={0} h="60%" />
      <Half file={d0.newFile} side="R" accent={NEON} delay={16} h="60%" />
      <Scrim />
      {/* Top scrim: guarantees contrast for the title no matter what the cutouts do. */}
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, #05060af2 0%, #05060ad9 30%, #05060a80 44%, transparent 56%)" }} />
      <div style={{ position: "absolute", top: "7%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: fit(p.titleTop), color: GOLD, transform: `scale(${interpolate(s, [0, 1], [0.7, 1])})`, opacity: s, textShadow: `0 0 50px ${GOLD}` }}>{p.titleTop}</div>
      <div style={{ position: "absolute", top: "16.5%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 72, color: "#fff", opacity: s, textShadow: "0 6px 30px #000" }}>vs</div>
      <div style={{ position: "absolute", top: "23.5%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: fit(p.titleBottom), color: NEON, opacity: s, textShadow: `0 0 50px ${NEON}` }}>{p.titleBottom}</div>
      <div style={{ position: "absolute", top: "34%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 48, color: "#fff", opacity: sub, textShadow: "0 4px 18px #000" }}>{p.subtitle}</div>
    </AbsoluteFill>
  );
};

// Both Golden Era faces rise together. Ronaldo won duels 1-2 and Messi won duel 3,
// so a finale showing Ronaldo alone would credit him with a win that was Messi's.
// side "C" = one winner took every duel, so a single centred cutout. Rendering the
// same face twice (as an earlier build did) read as two different players.
const RiseCut: React.FC<{ file: string; side: "L" | "R" | "C"; delay?: number }> = ({ file, side, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 24, mass: 1.6, stiffness: 55 } });
  const ty = interpolate(s, [0, 1], [360, 0]);
  const box: React.CSSProperties = side === "C"
    ? { left: 0, width: "100%", height: "68%" }
    : { [side === "L" ? "left" : "right"]: "-4%", width: "58%", height: "64%" };
  return (
    <div style={{ position: "absolute", bottom: 0, ...box, display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px)` }}>
      <Img src={staticFile(`cut/${file}.png`)} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 46px ${GOLD}) drop-shadow(0 12px 20px #000a)` }} />
    </div>
  );
};

// Finale doubles as the LOOP JOINT: the last ~16 frames drain everything back to
// the bare stadium plate, which is exactly what Intro frame 0 looks like (its
// spring is still at 0, so cutouts are off-screen and the title is invisible).
// Replay therefore cuts back with no visible seam.
const Finale: React.FC<{ p: EraProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const crownS = spring({ frame: frame - 6, fps: EB_FPS, config: { damping: 8, mass: 0.5 } });
  const scoreS = spring({ frame: frame - 18, fps: EB_FPS, config: { damping: 12 } });
  const baitOp = interpolate(frame, [52, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const baitPulse = 1 + 0.05 * Math.sin(frame * 0.35);
  const sh = beatShake(frame, 4);
  const loopOut = interpolate(frame, [FIN - 16, FIN - 2], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <StadiumBg ken={0.1} />
      <EraSplit />
      <div style={{ opacity: loopOut }}>
        {p.finaleFaces.length >= 2 ? (
          <>
            <RiseCut file={p.finaleFaces[0]} side="L" delay={0} />
            <RiseCut file={p.finaleFaces[1]} side="R" delay={10} />
          </>
        ) : (
          <RiseCut file={p.finaleFaces[0]} side="C" delay={0} />
        )}
        <Scrim />
        {/* Same trick as the intro: guarantee the copy reads over any cutout. */}
        <AbsoluteFill style={{ background: "linear-gradient(to bottom, #05060af2 0%, #05060ad9 32%, #05060a80 46%, transparent 58%)" }} />
        <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translate(${sh}px, 0)` }}>
          <div style={{ position: "absolute", top: "2.5%", width: "100%", textAlign: "center", fontSize: 140, transform: `scale(${interpolate(crownS, [0, 1], [0, 1])})` }}>👑</div>
          <div style={{ position: "absolute", top: "17%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 116, color: GOLD, opacity: scoreS, transform: `scale(${interpolate(scoreS, [0, 1], [0.6, 1])})`, textShadow: `0 0 46px ${GOLD}, 0 4px 20px #000` }}>{p.score}</div>
          <div style={{ position: "absolute", top: "29%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 38, color: "#fff", opacity: scoreS, letterSpacing: 4, textShadow: "0 3px 16px #000, 0 0 30px #000" }}>{p.finaleLine}</div>
          <div style={{ position: "absolute", top: "35.5%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 44, color: GOLD, opacity: scoreS, textShadow: "0 3px 14px #000" }}>{p.finaleNames}</div>
          <div style={{ position: "absolute", bottom: 104, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 62, color: "#fff", opacity: baitOp, transform: `scale(${baitPulse})`, textShadow: `0 0 30px ${NEON}, 0 4px 18px #000` }}>{p.bait}</div>
          <div style={{ position: "absolute", bottom: 54, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 32, color: "#cdd3e0", opacity: baitOp, letterSpacing: 5 }}>{p.baitSub}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Transitions rotate so consecutive cards never wipe the same way.
const PRESENTS = [
  slide({ direction: "from-right" }),
  wipe({ direction: "from-left" }),
  wipe({ direction: "from-bottom" }),
  slide({ direction: "from-left" }),
];

export const EraBattle: React.FC<Partial<EraProps>> = (given) => {
  const p: EraProps = { ...DEFAULT_ERA_PROPS, ...given };
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("beat.wav")} />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={INTRO}><Intro p={p} /></TransitionSeries.Sequence>
        {p.duels.map((d, i) => (
          <React.Fragment key={i}>
            <TransitionSeries.Transition
              timing={linearTiming({ durationInFrames: T1 })}
              presentation={PRESENTS[i % PRESENTS.length]}
            />
            <TransitionSeries.Sequence durationInFrames={SEG}>
              <DuelCard d={d} idx={i} total={p.duels.length} footer={p.footer} />
            </TransitionSeries.Sequence>
          </React.Fragment>
        ))}
        <TransitionSeries.Transition timing={springTiming({ config: { damping: 200 }, durationInFrames: T2 })} presentation={fade()} />
        <TransitionSeries.Sequence durationInFrames={FIN}><Finale p={p} /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
