import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring,
} from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";

// ── "WHAT IF" — imaginary transfer, real stats ───────────────────────────────
// Rotation format #3. This was the channel's best SUBSCRIBER converter
// (7.4 subs per 1000 views vs 0.5 for the pure-views winner), so it earns a slot.
//
// HONESTY GUARD: every card carries a permanent "IMAGINARY TRANSFER" strip and
// the intro says it outright. The stats attached to each player are real; only
// the move is hypothetical. Without that label this format reads as fake
// transfer news, which is both dishonest and a misinformation risk.
export const WI_FPS = 30;
const INTRO = 54;
const CARD = 126;
const FIN = 120;
const T1 = 12, T2 = 10;
export const wiTotal = (n: number) => INTRO + n * CARD + FIN - (n * T1 + T2);
export const WI_TOTAL = wiTotal(3);

const FONT = '"Arial Black", Impact, sans-serif';
const GOLD = "#ffcd42";
const NEON = "#3ee6ff";

export type Swap = {
  player: string;       // cutout slug
  name: string;
  from: string;
  to: string;
  toColor: string;
  stat: string;         // real, verified line
};

export type WhatIfProps = {
  title: string;
  subtitle: string;
  swaps: Swap[];
  footer: string;
  finaleLine: string;
  bait: string;
  baitSub: string;
};

export const DEFAULT_WHATIF_PROPS: WhatIfProps = {
  title: "WHAT IF?",
  subtitle: "Imaginary moves. Real numbers. 👀",
  swaps: [
    { player: "haaland", name: "HAALAND", from: "MAN CITY", to: "REAL MADRID", toColor: "#e8e8ec", stat: "354 career goals" },
    { player: "mbappe", name: "MBAPPE", from: "REAL MADRID", to: "LIVERPOOL", toColor: "#e2453b", stat: "60 Champions League goals" },
    { player: "lewandowski", name: "LEWANDOWSKI", from: "BARCELONA", to: "BAYERN", toColor: "#e2453b", stat: "105 Champions League goals" },
  ],
  footer: "IMAGINARY TRANSFER · REAL STATS",
  finaleLine: "WHICH ONE BREAKS THE LEAGUE?",
  bait: "PICK ONE 👇",
  baitSub: "COMMENT KARO 🔥",
};

const StadiumBg: React.FC<{ tint: string }> = ({ tint }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = 1.05 + interpolate(frame, [0, durationInFrames], [0, 0.07]);
  return (
    <AbsoluteFill style={{ backgroundColor: "#05060a", overflow: "hidden" }}>
      <Img src={staticFile("bg_stadium.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, filter: "blur(3px) brightness(0.45)" }} />
      <AbsoluteFill style={{ background: tint, mixBlendMode: "overlay", opacity: 0.24 }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 62% 55% at 50% 46%, ${tint}44 0%, transparent 62%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, transparent 44%, #05060aee 100%)" }} />
    </AbsoluteFill>
  );
};

const Scrim = () => <AbsoluteFill style={{ background: "linear-gradient(to top, #05060a 6%, transparent 30%)" }} />;

// The label strip that keeps this format honest. Present on every single card.
const HonestyStrip: React.FC<{ text: string }> = ({ text }) => (
  <div style={{
    position: "absolute", bottom: 26, width: "100%", textAlign: "center",
    fontFamily: FONT, fontSize: 24, color: "#aeb6c6", letterSpacing: 5,
  }}>{text}</div>
);

const SwapCard: React.FC<{ s: Swap; idx: number; total: number; footer: string }> =
  ({ s, idx, total, footer }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const rise = spring({ frame, fps, config: { damping: 24, mass: 1.6, stiffness: 55 } });
    const ty = interpolate(rise, [0, 1], [320, 0]);
    // Arrow + destination land after the player is settled, so the eye reads
    // player -> then the move, not both at once.
    const arrow = spring({ frame: frame - 34, fps, config: { damping: 16, mass: 1.0 } });
    const toS = spring({ frame: frame - 52, fps, config: { damping: 12, mass: 0.8 } });
    const statOp = interpolate(frame, [74, 92], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const fit = (t: string, base: number, max: number) => (t.length > max ? Math.floor(base * max / t.length) : base);
    return (
      <AbsoluteFill>
        <StadiumBg tint={s.toColor} />
        <div style={{ position: "absolute", bottom: 0, width: "100%", height: "60%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px)` }}>
          <Img src={staticFile(`cut/${s.player}.png`)} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 46px ${s.toColor}) drop-shadow(0 12px 20px #000a)` }} />
        </div>
        <Scrim />
        <AbsoluteFill style={{ background: "linear-gradient(to bottom, #05060af2 0%, #05060ad9 34%, #05060a70 48%, transparent 60%)" }} />

        <div style={{ position: "absolute", top: 74, left: 52, fontFamily: FONT, fontWeight: 900, fontSize: 40, color: GOLD, opacity: 0.85 }}>{idx + 1}/{total}</div>

        <div style={{ position: "absolute", top: "6%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: fit(s.name, 86, 11), color: "#fff", textShadow: "0 4px 20px #000" }}>{s.name}</div>
        <div style={{ position: "absolute", top: "15%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 36, color: "#9aa2b4", letterSpacing: 4 }}>{s.from}</div>
        <div style={{ position: "absolute", top: "20.5%", width: "100%", textAlign: "center", fontSize: 62, opacity: arrow, transform: `translateY(${interpolate(arrow, [0, 1], [-26, 0])}px)` }}>⬇️</div>
        <div style={{
          position: "absolute", top: "28%", width: "100%", textAlign: "center",
          fontFamily: FONT, fontWeight: 900, fontSize: fit(s.to, 76, 12), color: s.toColor,
          opacity: toS, transform: `scale(${interpolate(toS, [0, 1], [0.6, 1])})`,
          textShadow: `0 0 44px ${s.toColor}, 0 4px 18px #000`,
        }}>{s.to}</div>

        <div style={{ position: "absolute", top: "37%", width: "100%", textAlign: "center", opacity: statOp }}>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 42, color: "#05060a", background: GOLD, padding: "8px 26px", borderRadius: 40, boxShadow: `0 0 30px ${GOLD}` }}>{s.stat}</span>
        </div>

        <HonestyStrip text={footer} />
      </AbsoluteFill>
    );
  };

const Intro: React.FC<{ p: WhatIfProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 20, mass: 1.3, stiffness: 62 } });
  const sub = interpolate(frame, [22, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <StadiumBg tint={NEON} />
      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "56%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${interpolate(s, [0, 1], [300, 0])}px)` }}>
        <Img src={staticFile(`cut/${p.swaps[0].player}.png`)} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 46px ${NEON}) drop-shadow(0 12px 20px #000a)` }} />
      </div>
      <Scrim />
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, #05060af5 0%, #05060ad9 32%, transparent 52%)" }} />
      <div style={{ position: "absolute", top: "9%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 150, color: GOLD, opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.6, 1])})`, textShadow: `0 0 56px ${GOLD}` }}>{p.title}</div>
      <div style={{ position: "absolute", top: "24%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 44, color: "#fff", opacity: sub, textShadow: "0 4px 18px #000" }}>{p.subtitle}</div>
    </AbsoluteFill>
  );
};

const Finale: React.FC<{ p: WhatIfProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 14 } });
  const baitOp = interpolate(frame, [46, 64], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pulse = 1 + 0.05 * Math.sin(frame * 0.35);
  const loopOut = interpolate(frame, [FIN - 16, FIN - 2], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <StadiumBg tint={GOLD} />
      <div style={{ opacity: loopOut }}>
        <AbsoluteFill style={{ display: "flex", flexDirection: "row", alignItems: "flex-end", justifyContent: "center" }}>
          {p.swaps.slice(0, 3).map((sw, i) => (
            <div key={i} style={{
              width: "33%", height: `${44 + 4 * (i === 1 ? 1 : 0)}%`, display: "flex",
              alignItems: "flex-end", justifyContent: "center",
              transform: `translateY(${interpolate(spring({ frame: frame - i * 7, fps, config: { damping: 20, mass: 1.3 } }), [0, 1], [300, 0])}px)`,
            }}>
              <Img src={staticFile(`cut/${sw.player}.png`)} style={{ height: "100%", objectFit: "contain", filter: `drop-shadow(0 0 30px ${GOLD}) drop-shadow(0 10px 18px #000a)` }} />
            </div>
          ))}
        </AbsoluteFill>
        <Scrim />
        <AbsoluteFill style={{ background: "linear-gradient(to bottom, #05060af2 0%, #05060ad9 30%, transparent 50%)" }} />
        <div style={{ position: "absolute", top: "8%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 52, color: "#fff", opacity: s, letterSpacing: 2, textShadow: "0 3px 18px #000" }}>{p.finaleLine}</div>
        <div style={{ position: "absolute", bottom: 106, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 66, color: GOLD, opacity: baitOp, transform: `scale(${pulse})`, textShadow: `0 0 30px ${GOLD}, 0 4px 18px #000` }}>{p.bait}</div>
        <div style={{ position: "absolute", bottom: 56, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 30, color: "#cdd3e0", opacity: baitOp, letterSpacing: 5 }}>{p.baitSub}</div>
      </div>
    </AbsoluteFill>
  );
};

export const WhatIf: React.FC<Partial<WhatIfProps>> = (given) => {
  const p: WhatIfProps = { ...DEFAULT_WHATIF_PROPS, ...given };
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("beat.wav")} />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={INTRO}><Intro p={p} /></TransitionSeries.Sequence>
        {p.swaps.map((s, i) => (
          <React.Fragment key={i}>
            <TransitionSeries.Transition
              timing={linearTiming({ durationInFrames: T1 })}
              presentation={slide({ direction: i % 2 ? "from-left" : "from-right" })}
            />
            <TransitionSeries.Sequence durationInFrames={CARD}>
              <SwapCard s={s} idx={i} total={p.swaps.length} footer={p.footer} />
            </TransitionSeries.Sequence>
          </React.Fragment>
        ))}
        <TransitionSeries.Transition timing={springTiming({ config: { damping: 200 }, durationInFrames: T2 })} presentation={fade()} />
        <TransitionSeries.Sequence durationInFrames={FIN}><Finale p={p} /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
