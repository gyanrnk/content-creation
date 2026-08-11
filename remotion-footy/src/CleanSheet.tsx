import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring, random,
} from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";

// ── "CLEAN SHEET KINGS" — a deliberately DIFFERENT-looking format ────────────
// Every existing format (EraBattle / GuessPlayer / WhatIf) shares one visual
// language: gold + neon on a blurred stadium plate. Uploading a fourth in that
// same skin would read as more of the same however fresh the data is.
//
// So this one changes the language on purpose:
//   palette   ice blue + white on near-black (no gold anywhere)
//   backdrop  a drawn GOAL NET in perspective, not a photo
//   motion    shockwave rings + chromatic split on impact (new)
//   data viz  a growing BAR per keeper — no other format uses bars
//   structure rank countdown 3 -> 1, giant ghost numeral behind the subject
//
// Topic picked because the channel had ZERO goalkeeper videos in 102 uploads,
// and the numbers clash-checked clean against every past description.
//
// Verified 2026-08-10 — UCL all-time clean sheets:
//   Neuer 62 (record) · Casillas 57 · Buffon 52
//   (van der Sar 50 and Cech 47 exist but no usable free portrait for #4, so
//    this is presented strictly as a TOP 3 — never skip a rank silently.)
export const CS_FPS = 30;
const INTRO = 50;
const CARD = 110;
const FIN = 120;
const T1 = 12, T2 = 10;
export const csTotal = (n: number) => INTRO + n * CARD + FIN - (n * T1 + T2);
export const CS_TOTAL = csTotal(3);

const FONT = '"Arial Black", Impact, sans-serif';
const ICE = "#6fe3ff";
const DEEP = "#04070f";

export type Keeper = {
  rank: number;
  name: string;
  file: string;
  value: number;
  club: string;
};

export type CleanSheetProps = {
  kicker: string;
  title: string;
  subtitle: string;
  unit: string;
  keepers: Keeper[];
  max: number;
  finaleLine: string;
  bait: string;
  baitSub: string;
  footer: string;
};

export const DEFAULT_CS_PROPS: CleanSheetProps = {
  kicker: "CHAMPIONS LEAGUE",
  title: "CLEAN SHEET KINGS",
  subtitle: "The wall nobody could break 🧤",
  unit: "CLEAN SHEETS",
  keepers: [
    { rank: 3, name: "BUFFON", file: "buffon", value: 52, club: "JUVENTUS · PARMA · PSG" },
    { rank: 2, name: "CASILLAS", file: "casillas", value: 57, club: "REAL MADRID · PORTO" },
    { rank: 1, name: "NEUER", file: "neuer", value: 62, club: "BAYERN · SCHALKE" },
  ],
  max: 62,
  finaleLine: "62 — THE UCL RECORD",
  bait: "WILL IT EVER FALL? 👇",
  baitSub: "NAME A KEEPER 🧤",
  footer: "UCL ALL-TIME CLEAN SHEETS",
};

// ── effects ──────────────────────────────────────────────────────────────────

// Drawn goal net in perspective. No photo — keeps this format visually apart
// from every other one, which all sit on the same blurred stadium still.
const NetBg: React.FC<{ drift?: number }> = ({ drift = 1 }) => {
  const frame = useCurrentFrame();
  const shift = (frame * 0.35 * drift) % 46;
  const net = `repeating-linear-gradient(90deg, ${ICE}22 0 2px, transparent 2px 46px),
               repeating-linear-gradient(0deg,  ${ICE}1c 0 2px, transparent 2px 46px)`;
  return (
    <AbsoluteFill style={{ backgroundColor: DEEP, overflow: "hidden" }}>
      <div style={{
        position: "absolute", left: "-30%", top: "-20%", width: "160%", height: "150%",
        backgroundImage: net, backgroundPosition: `${shift}px ${shift * 0.6}px`,
        transform: "perspective(900px) rotateX(52deg) scale(1.25)",
        transformOrigin: "50% 30%",
      }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 50% at 50% 34%, ${ICE}26 0%, transparent 62%)` }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 95% 95% at 50% 45%, transparent 38%, ${DEEP} 100%)` }} />
    </AbsoluteFill>
  );
};

// Expanding rings — the "save impact". Fires at `at`, three staggered rings.
const Shockwave: React.FC<{ at: number; color?: string }> = ({ at, color = ICE }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {[0, 7, 14].map((d, i) => {
        const t = frame - at - d;
        if (t < 0 || t > 40) return null;
        const s = interpolate(t, [0, 40], [0.15, 2.3]);
        const o = interpolate(t, [0, 10, 40], [0, 0.5, 0]);
        return (
          <div key={i} style={{
            position: "absolute", left: "50%", top: "38%", width: 620, height: 620,
            marginLeft: -310, marginTop: -310, borderRadius: "50%",
            border: `${6 - i}px solid ${color}`, opacity: o,
            transform: `scale(${s})`,
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

// RGB split on impact — decays over ~14 frames. Used only on the #1 reveal.
const ChromaSplit: React.FC<{ at: number; children: React.ReactNode }> = ({ at, children }) => {
  const frame = useCurrentFrame();
  const t = Math.max(0, frame - at);
  const amt = t < 16 ? interpolate(t, [0, 16], [16, 0]) : 0;
  if (amt < 0.4) return <>{children}</>;
  return (
    <>
      <div style={{ position: "absolute", inset: 0, transform: `translateX(${-amt}px)`, filter: "url(#none)", opacity: 0.55, mixBlendMode: "screen" }}>
        <div style={{ position: "absolute", inset: 0, filter: "sepia(1) hue-rotate(-50deg) saturate(6)" }}>{children}</div>
      </div>
      <div style={{ position: "absolute", inset: 0, transform: `translateX(${amt}px)`, opacity: 0.55, mixBlendMode: "screen" }}>
        <div style={{ position: "absolute", inset: 0, filter: "sepia(1) hue-rotate(150deg) saturate(6)" }}>{children}</div>
      </div>
      <div style={{ position: "absolute", inset: 0 }}>{children}</div>
    </>
  );
};

// The bar — this format's signature. Grows to value/max.
const Bar: React.FC<{ value: number; max: number; delay: number; top: string }> =
  ({ value, max, delay, top }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const s = spring({ frame: frame - delay, fps, config: { damping: 22, mass: 1.3, stiffness: 60 } });
    const w = interpolate(s, [0, 1], [0, (value / max) * 78]);
    return (
      <div style={{ position: "absolute", top, left: "11%", width: "78%", height: 18 }}>
        <div style={{ position: "absolute", inset: 0, background: "#ffffff14", borderRadius: 10 }} />
        <div style={{
          position: "absolute", left: 0, top: 0, height: "100%", width: `${(w / 78) * 100}%`,
          background: `linear-gradient(90deg, ${ICE}, #ffffff)`, borderRadius: 10,
          boxShadow: `0 0 26px ${ICE}, 0 0 60px ${ICE}88`,
        }} />
      </div>
    );
  };

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: 0.05 }}>
      {new Array(40).fill(0).map((_, i) => {
        const x = random(`x${i}${Math.floor(frame / 3)}`) * 100;
        const y = random(`y${i}${Math.floor(frame / 3)}`) * 100;
        return <div key={i} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: 3, height: 3, background: "#fff" }} />;
      })}
    </AbsoluteFill>
  );
};

// ── scenes ───────────────────────────────────────────────────────────────────

const KeeperCard: React.FC<{ k: Keeper; p: CleanSheetProps }> = ({ k, p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const isTop = k.rank === 1;
  const rise = spring({ frame, fps, config: { damping: 25, mass: 1.7, stiffness: 55 } });
  const ty = interpolate(rise, [0, 1], [300, 0]);
  const shown = Math.round(interpolate(frame, [18, 70], [0, k.value], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const numS = spring({ frame: frame - 14, fps, config: { damping: 13, mass: 0.8 } });

  const body = (
    <AbsoluteFill>
      <NetBg drift={isTop ? 2 : 1} />
      {/* giant ghost rank numeral behind everything */}
      <div style={{
        position: "absolute", top: "16%", width: "100%", textAlign: "center",
        fontFamily: FONT, fontWeight: 900, fontSize: 640, lineHeight: 1,
        color: "#ffffff", opacity: 0.05,
      }}>{k.rank}</div>

      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "58%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px)` }}>
        <Img src={staticFile(`cut/${k.file}.png`)} style={{
          height: "100%", objectFit: "contain",
          filter: `drop-shadow(0 0 46px ${ICE}) drop-shadow(0 14px 22px #000c) ${isTop ? "" : "saturate(0.85)"}`,
        }} />
      </div>
      <AbsoluteFill style={{ background: `linear-gradient(to top, ${DEEP} 5%, transparent 30%)` }} />
      <AbsoluteFill style={{ background: `linear-gradient(to bottom, ${DEEP}f5 0%, ${DEEP}d0 32%, transparent 52%)` }} />

      <Shockwave at={14} color={ICE} />

      <div style={{ position: "absolute", top: 62, left: 54, fontFamily: FONT, fontWeight: 900, fontSize: 40, color: ICE, letterSpacing: 3 }}>#{k.rank}</div>
      <div style={{ position: "absolute", top: 66, right: 54, fontFamily: FONT, fontSize: 26, color: "#8fa0b8", letterSpacing: 4 }}>{p.kicker}</div>

      <div style={{
        position: "absolute", top: "12%", width: "100%", textAlign: "center",
        fontFamily: FONT, fontWeight: 900, fontSize: 190, color: "#fff",
        transform: `scale(${interpolate(numS, [0, 1], [0.55, 1])})`,
        textShadow: `0 0 40px ${ICE}, 0 0 110px ${ICE}77, 0 6px 22px #000`,
      }}>{shown}</div>
      <div style={{ position: "absolute", top: "26.5%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 30, color: ICE, letterSpacing: 8 }}>{p.unit}</div>

      <Bar value={k.value} max={p.max} delay={22} top="32%" />

      <div style={{ position: "absolute", bottom: 92, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: k.name.length > 9 ? 62 : 78, color: "#fff", textShadow: `0 0 28px ${ICE}, 0 4px 16px #000` }}>{k.name}</div>
      <div style={{ position: "absolute", bottom: 58, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 24, color: "#8fa0b8", letterSpacing: 3 }}>{k.club}</div>
      <div style={{ position: "absolute", bottom: 24, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 20, color: "#5d6b80", letterSpacing: 5 }}>{p.footer}</div>
      <Grain />
    </AbsoluteFill>
  );

  return isTop ? <ChromaSplit at={12}>{body}</ChromaSplit> : body;
};

const Intro: React.FC<{ p: CleanSheetProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 20, mass: 1.3, stiffness: 62 } });
  const sub = interpolate(frame, [20, 38], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <NetBg drift={1.6} />
      <Shockwave at={4} />
      <div style={{ position: "absolute", top: "22%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 30, color: ICE, letterSpacing: 10, opacity: s }}>{p.kicker}</div>
      <div style={{
        position: "absolute", top: "29%", width: "100%", textAlign: "center",
        fontFamily: FONT, fontWeight: 900, fontSize: 108, lineHeight: 0.95, color: "#fff",
        opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.62, 1])})`,
        textShadow: `0 0 56px ${ICE}, 0 6px 26px #000`,
      }}>{p.title}</div>
      <div style={{ position: "absolute", top: "48%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 42, color: ICE, opacity: sub }}>{p.subtitle}</div>
      <Grain />
    </AbsoluteFill>
  );
};

const Finale: React.FC<{ p: CleanSheetProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const top = p.keepers[p.keepers.length - 1];
  const s = spring({ frame, fps, config: { damping: 24, mass: 1.5, stiffness: 55 } });
  const ty = interpolate(s, [0, 1], [320, 0]);
  const baitOp = interpolate(frame, [46, 64], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pulse = 1 + 0.05 * Math.sin(frame * 0.35);
  const loopOut = interpolate(frame, [FIN - 16, FIN - 2], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <NetBg drift={2.4} />
      <div style={{ opacity: loopOut }}>
        <Shockwave at={6} />
        <div style={{ position: "absolute", bottom: 0, width: "100%", height: "62%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px)` }}>
          <Img src={staticFile(`cut/${top.file}.png`)} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 54px ${ICE}) drop-shadow(0 14px 22px #000c)` }} />
        </div>
        <AbsoluteFill style={{ background: `linear-gradient(to top, ${DEEP} 5%, transparent 32%)` }} />
        <AbsoluteFill style={{ background: `linear-gradient(to bottom, ${DEEP}f7 0%, ${DEEP}d6 30%, transparent 50%)` }} />
        <div style={{ position: "absolute", top: "5%", width: "100%", textAlign: "center", fontSize: 120 }}>🧤</div>
        <div style={{ position: "absolute", top: "20%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 72, color: "#fff", opacity: s, textShadow: `0 0 44px ${ICE}, 0 4px 20px #000` }}>{p.finaleLine}</div>
        <div style={{ position: "absolute", bottom: 104, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 62, color: ICE, opacity: baitOp, transform: `scale(${pulse})`, textShadow: `0 0 30px ${ICE}, 0 4px 18px #000` }}>{p.bait}</div>
        <div style={{ position: "absolute", bottom: 56, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 30, color: "#8fa0b8", opacity: baitOp, letterSpacing: 5 }}>{p.baitSub}</div>
        <Grain />
      </div>
    </AbsoluteFill>
  );
};

export const CleanSheet: React.FC<Partial<CleanSheetProps>> = (given) => {
  const p: CleanSheetProps = { ...DEFAULT_CS_PROPS, ...given };
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("beat.wav")} />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={INTRO}><Intro p={p} /></TransitionSeries.Sequence>
        {p.keepers.map((k, i) => (
          <React.Fragment key={i}>
            <TransitionSeries.Transition
              timing={linearTiming({ durationInFrames: T1 })}
              presentation={slide({ direction: "from-bottom" })}
            />
            <TransitionSeries.Sequence durationInFrames={CARD}>
              <KeeperCard k={k} p={p} />
            </TransitionSeries.Sequence>
          </React.Fragment>
        ))}
        <TransitionSeries.Transition timing={springTiming({ config: { damping: 200 }, durationInFrames: T2 })} presentation={fade()} />
        <TransitionSeries.Sequence durationInFrames={FIN}><Finale p={p} /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
