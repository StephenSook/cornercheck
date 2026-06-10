import React from "react";
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio, Video } from "@remotion/media";
import { BEATS, FPS, type Beat } from "./beats";

const BG = "#0b1220";
const TEXT = "#e6edf3";
const SUB = "#9fb3c8";
const GREEN = "#7ee2b8";

// Beat 1: animated title card from the committed PNG. Slow scale + fade,
// deterministic, text stays pixel-perfect (the reason this is not AI b-roll).
const TitleCard: React.FC = () => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 3 * FPS], [1.0, 1.05], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, 8, 3 * FPS - 8, 3 * FPS], [0, 1, 1, 0]);
  return (
    <AbsoluteFill style={{ backgroundColor: BG, opacity }}>
      <Img
        src={staticFile("title.png")}
        style={{ width: "100%", height: "100%", transform: `scale(${scale})` }}
      />
    </AbsoluteFill>
  );
};

// Beat 10 second half: end card with a gentle fade-in.
const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ backgroundColor: BG, opacity }}>
      <Img src={staticFile("end.png")} style={{ width: "100%", height: "100%" }} />
    </AbsoluteFill>
  );
};

// Placeholder shown until real footage lands in public/footage/.
const Placeholder: React.FC<{ beat: Beat }> = ({ beat }) => {
  const mm = Math.floor(beat.from / 60);
  const ss = String(Math.floor(beat.from % 60)).padStart(2, "0");
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        justifyContent: "center",
        alignItems: "center",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        color: TEXT,
        padding: 120,
      }}
    >
      <div style={{ color: GREEN, fontSize: 34, letterSpacing: "0.18em", fontWeight: 700 }}>
        {beat.mode.toUpperCase()} · {mm}:{ss}
      </div>
      <div style={{ fontSize: 64, fontWeight: 800, margin: "18px 0 30px" }}>
        {beat.title}
      </div>
      <div style={{ fontSize: 30, color: SUB, maxWidth: 1400, lineHeight: 1.5, textAlign: "center" }}>
        {beat.script || "(no voiceover on this beat)"}
      </div>
      <div style={{ marginTop: 40, fontSize: 26, color: SUB }}>
        drop footage at public/footage/{beat.id}.mp4 and set `footage` in beats.ts
      </div>
    </AbsoluteFill>
  );
};

// Assembly-reference caption (toggle off for the final render; final captions
// come from the VO transcription pass).
const GuideCaption: React.FC<{ beat: Beat }> = ({ beat }) => (
  <div
    style={{
      position: "absolute",
      bottom: 48,
      left: 0,
      right: 0,
      display: "flex",
      justifyContent: "center",
    }}
  >
    <div
      style={{
        background: "rgba(11,18,32,0.82)",
        color: TEXT,
        borderRadius: 14,
        padding: "14px 26px",
        fontSize: 26,
        maxWidth: 1500,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {beat.script}
    </div>
  </div>
);

export const Demo: React.FC<{ showGuide: boolean }> = ({ showGuide }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {BEATS.map((beat) => {
        const from = Math.round(beat.from * fps);
        const duration = Math.round((beat.to - beat.from) * fps);
        return (
          <Sequence key={beat.id} from={from} durationInFrames={duration} premountFor={fps}>
            {beat.id === "beat1" ? (
              <TitleCard />
            ) : beat.footage ? (
              <AbsoluteFill>
                {/* Screen clips carry stray mic audio; the camera bookends keep theirs. */}
                <Video
                  src={staticFile(`footage/${beat.footage}`)}
                  muted={beat.mode !== "camera"}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
                {beat.vo ? <Audio src={staticFile(`vo/${beat.vo}`)} /> : null}
                {showGuide && beat.script ? <GuideCaption beat={beat} /> : null}
              </AbsoluteFill>
            ) : (
              <Placeholder beat={beat} />
            )}
            {beat.id === "beat10" ? (
              <Sequence from={Math.round(5 * fps)} layout="none" premountFor={fps}>
                <EndCard />
              </Sequence>
            ) : null}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
