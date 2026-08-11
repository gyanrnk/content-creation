import React from "react";
import {
  AbsoluteFill, Img, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring, Sequence,
} from "remotion";

// ── "GUESS THE PLAYER" — clue stack, countdown, reveal ───────────────────────
// Rotation format #2. Chosen for comment-bait: viewers answer in the comments
// before the reveal, and the countdown holds them to the end (retention).
//
// No TransitionSeries here on purpose — the silhouette must stay locked in place
// the whole time. Cutting between cards would break the "same person" illusion
// that makes the guess work. Clues STACK rather than replace, so a viewer who
// lands late still has every clue on screen.
export const GP_FPS = 30;
const C_TITLE = 40;
const C_CLUE = 75;
const C_COUNT = 45;
const C_REVEAL = 150;
export const GP_TOTAL = C_TITLE + 3 * C_CLUE + C_COUNT + C_REVEAL;   // 460f = 15.3s
const REVEAL_AT = C_TITLE + 3 * C_CLUE + C_COUNT;

const FONT = '"Arial Black", Impact, sans-serif';
const GOLD = "#ffcd42";
const NEON = "#3ee6ff";

export type GuessProps = {
  category: string;
  clues: string[];
  answerFile: string;
  answerName: string;
  answerLine: string;
  bait: string;
  baitSub: string;
};

export const DEFAULT_GUESS_PROPS: GuessProps = {
  category: "GUESS THE PLAYER",
  clues: ["976 career goals", "140 Champions League goals", "5 Ballon d'Ors"],
  answerFile: "ronaldo",
  answerName: "RONALDO",
  answerLine: "THE KING 👑",
  bait: "GOT IT? 👇",
  baitSub: "COMMENT KARO 🔥",
};

const StadiumBg: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = 1.05 + interpolate(frame, [0, durationInFrames], [0, 0.08]);
  return (
    <AbsoluteFill style={{ backgroundColor: "#05060a", overflow: "hidden" }}>
      <Img src={staticFile("bg_stadium.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, filter: "blur(4px) brightness(0.42)" }} />
      <AbsoluteFill style={{ background: accent, mixBlendMode: "overlay", opacity: 0.22 }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, transparent 40%, #05060af2 100%)" }} />
    </AbsoluteFill>
  );
};

// Silhouette until REVEAL_AT, then colour + focus snap back in ~12 frames.
const Mystery: React.FC<{ file: string }> = ({ file }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rise = spring({ frame, fps, config: { damping: 24, mass: 1.5, stiffness: 55 } });
  const ty = interpolate(rise, [0, 1], [280, 0]);
  const r = interpolate(frame, [REVEAL_AT, REVEAL_AT + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dark = 1 - r;
  const blur = interpolate(r, [0, 1], [16, 0]);
  const pop = 1 + 0.06 * Math.exp(-Math.max(0, frame - REVEAL_AT) * 0.25);
  return (
    <div style={{ position: "absolute", bottom: 0, width: "100%", height: "62%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `translateY(${ty}px) scale(${pop})` }}>
      <Img
        src={staticFile(`cut/${file}.png`)}
        style={{
          height: "100%", objectFit: "contain",
          filter: `brightness(${1 - dark}) contrast(${1 + dark}) blur(${blur}px) `
            + `drop-shadow(0 0 ${30 + 30 * r}px ${r > 0.5 ? GOLD : NEON}) drop-shadow(0 12px 20px #000a)`,
        }}
      />
    </div>
  );
};

const ClueRow: React.FC<{ text: string; index: number }> = ({ text, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 18, mass: 1.1, stiffness: 70 } });
  const dx = interpolate(s, [0, 1], [-420, 0]);
  return (
    <div style={{
      position: "absolute", top: `${20 + index * 9.5}%`, left: 0, width: "100%",
      display: "flex", justifyContent: "center", transform: `translateX(${dx}px)`, opacity: s,
    }}>
      <span style={{
        fontFamily: FONT, fontWeight: 900, fontSize: 44, color: "#05060a",
        background: index === 2 ? GOLD : "#e9edf5", padding: "12px 26px", borderRadius: 14,
        boxShadow: "0 8px 24px #000a", maxWidth: 960, textAlign: "center",
      }}>{text}</span>
    </div>
  );
};

const Countdown: React.FC = () => {
  const frame = useCurrentFrame();
  const n = 3 - Math.floor(frame / 15);
  if (n < 1) return null;
  const inTick = frame % 15;
  const scale = interpolate(inTick, [0, 5, 15], [1.7, 1, 0.95]);
  const op = interpolate(inTick, [0, 4, 14], [0, 1, 0.7]);
  return (
    <div style={{
      position: "absolute", top: "48%", width: "100%", textAlign: "center",
      fontFamily: FONT, fontWeight: 900, fontSize: 210, color: "#fff",
      transform: `scale(${scale})`, opacity: op,
      textShadow: `0 0 50px ${NEON}, 0 0 110px ${NEON}, 0 6px 24px #000`,
    }}>{n}</div>
  );
};

const Reveal: React.FC<{ name: string; line: string; bait: string; baitSub: string }> =
  ({ name, line, bait, baitSub }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const s = spring({ frame, fps, config: { damping: 9, mass: 0.6 } });
    const baitOp = interpolate(frame, [55, 75], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const pulse = 1 + 0.05 * Math.sin(frame * 0.35);
    const flash = interpolate(frame, [0, 6, 16], [0.85, 0.25, 0], { extrapolateRight: "clamp" });
    const fit = name.length > 10 ? Math.floor(120 * 10 / name.length) : 120;
    return (
      <AbsoluteFill>
        <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
        <div style={{
          position: "absolute", top: "8%", width: "100%", textAlign: "center",
          fontFamily: FONT, fontWeight: 900, fontSize: fit, color: GOLD,
          transform: `scale(${interpolate(s, [0, 1], [0.5, 1])}) rotate(${interpolate(s, [0, 1], [-6, 0])}deg)`,
          textShadow: `0 0 50px ${GOLD}, 0 6px 24px #000`,
        }}>{name}</div>
        <div style={{ position: "absolute", top: "19%", width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 40, color: "#fff", opacity: s, letterSpacing: 5, textShadow: "0 3px 16px #000" }}>{line}</div>
        <div style={{ position: "absolute", bottom: 104, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 64, color: "#fff", opacity: baitOp, transform: `scale(${pulse})`, textShadow: `0 0 30px ${NEON}, 0 4px 18px #000` }}>{bait}</div>
        <div style={{ position: "absolute", bottom: 54, width: "100%", textAlign: "center", fontFamily: FONT, fontSize: 32, color: "#cdd3e0", opacity: baitOp, letterSpacing: 5 }}>{baitSub}</div>
      </AbsoluteFill>
    );
  };

export const GuessPlayer: React.FC<Partial<GuessProps>> = (given) => {
  const p: GuessProps = { ...DEFAULT_GUESS_PROPS, ...given };
  const frame = useCurrentFrame();
  const revealed = frame >= REVEAL_AT;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("beat.wav")} />
      <StadiumBg accent={revealed ? GOLD : NEON} />
      <Mystery file={p.answerFile} />
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, #05060af2 0%, #05060ac9 34%, transparent 52%)" }} />

      {!revealed && (
        <div style={{ position: "absolute", top: "7%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 68, color: NEON, textShadow: `0 0 40px ${NEON}, 0 4px 18px #000` }}>
          {p.category}
        </div>
      )}

      {p.clues.slice(0, 3).map((c, i) => (
        <Sequence key={i} from={C_TITLE + i * C_CLUE} durationInFrames={REVEAL_AT - (C_TITLE + i * C_CLUE)} layout="none">
          <ClueRow text={c} index={i} />
        </Sequence>
      ))}

      <Sequence from={C_TITLE + 3 * C_CLUE} durationInFrames={C_COUNT} layout="none">
        <Countdown />
      </Sequence>

      <Sequence from={REVEAL_AT} durationInFrames={C_REVEAL} layout="none">
        <Reveal name={p.answerName} line={p.answerLine} bait={p.bait} baitSub={p.baitSub} />
      </Sequence>
    </AbsoluteFill>
  );
};
