import React from "react";
import {
  AbsoluteFill, Img, Audio, Sequence, staticFile,
  useCurrentFrame, useVideoConfig, interpolate, spring,
} from "remotion";

export const LD_FPS = 30;

type Mode = "gold" | "bright" | "dark" | "desat" | "reveal";
type Beat = {
  vo: number; dur: number; img: string; mode: Mode;
  zoom: "in" | "out"; shake?: boolean; sub: string; big?: string; flash?: boolean; cta?: boolean;
};

const BEATS: Beat[] = [
  { vo: 0, dur: 97, img: "portrait", mode: "gold", zoom: "in", sub: "For over 20 years, he ruled the game." },
  { vo: 1, dur: 194, img: "proud", mode: "bright", zoom: "in", sub: "5 Ballon d'Ors. 900+ goals. Records that may never fall." },
  { vo: 2, dur: 170, img: "portrait", mode: "dark", zoom: "in", shake: true, sub: "In 2026, at 41, he walked out for one last World Cup." },
  { vo: 3, dur: 179, img: "face", mode: "desat", zoom: "in", sub: "Portugal fell to Spain. Ronaldo left the pitch... in tears." },
  { vo: 4, dur: 91, img: "face", mode: "dark", zoom: "in", sub: "Yet even in defeat..." },
  { vo: 5, dur: 125, img: "passion", mode: "reveal", zoom: "in", sub: "He made history.", big: "6 WORLD CUPS", flash: true },
  { vo: 6, dur: 118, img: "portrait", mode: "gold", zoom: "out", sub: "A warrior. A legend. The end of an era." },
  { vo: 7, dur: 150, img: "passion", mode: "gold", zoom: "out", sub: "Thank you, Cristiano. GOAT or not?  👇", cta: true },
];

const STARTS: number[] = [];
BEATS.reduce((acc, b, i) => { STARTS[i] = acc; return acc + b.dur; }, 0);
export const LD_TOTAL = BEATS.reduce((a, b) => a + b.dur, 0);

const FONT = '"Arial Black", Impact, sans-serif';
const acc = (m: Mode) => (m === "dark" || m === "desat" ? "#46618f" : "#ffcd42");
const filterOf = (m: Mode) => {
  switch (m) {
    case "gold": return "brightness(0.98) contrast(1.06) saturate(1.25)";
    case "bright": return "brightness(1.06) contrast(1.05) saturate(1.1)";
    case "dark": return "brightness(0.5) contrast(1.18) saturate(0.9)";
    case "desat": return "grayscale(0.85) brightness(0.5) contrast(1.15)";
    case "reveal": return "brightness(1.08) contrast(1.1) saturate(1.3)";
  }
};

const Bg: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame(); const { durationInFrames } = useVideoConfig();
  const scale = 1.08 + (frame / durationInFrames) * 0.08;
  return (
    <AbsoluteFill style={{ backgroundColor: "#04050a" }}>
      <Img src={staticFile("bg_stadium.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, filter: "blur(6px) brightness(0.22)" }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 65% 60% at 50% 44%, ${accent}55, transparent 62%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 38%, #04050aee 100%)" }} />
    </AbsoluteFill>
  );
};

const Scene: React.FC<{ beat: Beat }> = ({ beat }) => {
  const frame = useCurrentFrame();
  const accent = acc(beat.mode);
  const fadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [beat.dur - 10, beat.dur], [1, 0], { extrapolateLeft: "clamp" });
  const op = Math.min(fadeIn, fadeOut);
  const z = beat.zoom === "in"
    ? interpolate(frame, [0, beat.dur], [1.0, 1.14])
    : interpolate(frame, [0, beat.dur], [1.14, 1.0]);
  const sh = beat.shake ? Math.sin(frame * 1.6) * interpolate(frame, [0, beat.dur], [5, 1]) : 0;
  const flash = beat.flash ? interpolate(frame, [0, 12], [1, 0], { extrapolateRight: "clamp" }) : 0;
  const bigS = beat.big ? spring({ frame: frame - 6, fps: LD_FPS, config: { damping: 10, mass: 0.5 } }) : 0;
  const subOp = interpolate(frame, [8, 18], [0, 1], { extrapolateRight: "clamp" });
  const ctaPulse = beat.cta ? 1 + 0.05 * Math.sin(frame * 0.35) : 1;

  return (
    <AbsoluteFill style={{ opacity: op }}>
      <Bg accent={accent} />
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: `translateX(${sh}px)` }}>
        {/* glow behind */}
        <AbsoluteFill style={{ background: `radial-gradient(ellipse 45% 45% at 50% 52%, ${accent}66, transparent 55%)` }} />
        {/* player cut-out */}
        <div style={{ position: "absolute", bottom: 0, width: "100%", height: "78%", display: "flex", justifyContent: "center", alignItems: "flex-end", transform: `scale(${z})`, transformOrigin: "bottom center" }}>
          <Img src={staticFile(`cr7/${beat.img}.png`)} style={{ height: "100%", objectFit: "contain", filter: `${filterOf(beat.mode)} drop-shadow(0 0 40px ${accent}aa)` }} />
        </div>
        <AbsoluteFill style={{ background: "linear-gradient(to top, #04050a 6%, transparent 30%)" }} />
        {/* big word */}
        {beat.big && (
          <div style={{ position: "absolute", top: "16%", width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 130, color: "#fff", transform: `scale(${interpolate(bigS, [0, 1], [0.4, 1])})`, textShadow: `0 0 45px ${accent}, 0 0 100px ${accent}` }}>{beat.big}</div>
        )}
        {beat.big && (
          <div style={{ position: "absolute", top: "9%", width: "100%", textAlign: "center", fontSize: 120, transform: `scale(${interpolate(bigS, [0, 1], [0, 1])})` }}>🏆</div>
        )}
        {/* subtitle */}
        <div style={{ position: "absolute", bottom: 90, width: "84%", left: "8%", textAlign: "center", opacity: subOp, transform: `scale(${ctaPulse})` }}>
          <span style={{ fontFamily: '"Segoe UI", Arial, sans-serif', fontWeight: 800, fontSize: beat.cta ? 52 : 46, color: beat.cta ? "#ffcd42" : "#fff", textShadow: "0 3px 14px #000, 0 0 20px #000c", lineHeight: 1.25 }}>{beat.sub}</span>
        </div>
      </div>
      {/* gold flash on reveal */}
      {beat.flash && <AbsoluteFill style={{ backgroundColor: "#fff", opacity: flash * 0.85 }} />}
    </AbsoluteFill>
  );
};

export const LastDance: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("cr7/music.wav")} />
      {BEATS.map((b, i) => (
        <Sequence key={i} from={STARTS[i]} durationInFrames={b.dur}>
          <Scene beat={b} />
        </Sequence>
      ))}
      {BEATS.map((b, i) => (
        <Sequence key={`a${i}`} from={STARTS[i] + 5} durationInFrames={b.dur}>
          <Audio src={staticFile(`cr7/vo/v${b.vo}.mp3`)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
