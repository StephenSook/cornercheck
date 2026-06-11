"""Original ambient bed for the CornerCheck demo (175s), composed in code.

License-clean by construction (no samples, no third-party audio). Design intent:
dark, clinical, melody-free so it can never fight the voiceover. Structure follows
the beat timeline: near-silent under the cold open, blooms at the title card and
at each beat boundary (the no-speech gaps), warms slightly under the close, and
resolves to silence before the end card finishes.

Run: python3 scripts/compose_bed.py  ->  public/vo/music-bed.wav
"""

import wave
from pathlib import Path

import numpy as np

SR = 48000
DUR = 175.0
t = np.arange(int(SR * DUR)) / SR

# Beat boundaries where a small swell breathes between VO lines.
BOUNDARIES = [22.0, 25.0, 48.0, 72.0, 90.0, 107.0, 125.0, 140.0, 153.0, 163.0]
END_BLOOM = 171.8

rng = np.random.default_rng(20260610)  # deterministic render


def lfo(freq: float, phase: float = 0.0) -> np.ndarray:
    return 0.5 * (1.0 + np.sin(2 * np.pi * freq * t + phase))


def tone(freq: float, detune_hz: float = 0.0) -> np.ndarray:
    return np.sin(2 * np.pi * (freq + detune_hz) * t)


def envelope() -> np.ndarray:
    """Global dynamics: fade-in, low under speech, swells in gaps, out by 174.5s."""
    env = np.full_like(t, 0.55)  # base bed level (ducking happens in the mix too)
    env *= np.clip(t / 2.5, 0, 1)  # fade in
    env *= np.clip((174.5 - t) / 2.5, 0, 1)  # fade out before the video ends
    # Swells: +45% for ~2.4s centered on each boundary, gaussian-shaped.
    for b in BOUNDARIES:
        env += 0.25 * np.exp(-((t - b) ** 2) / (2 * 1.0**2))
    env += 0.30 * np.exp(-((t - END_BLOOM) ** 2) / (2 * 1.2**2))
    # Title card (22-25) holds the bloom rather than dipping between two swells.
    env += 0.18 * ((t > 22.2) & (t < 24.8)).astype(float)
    return np.clip(env, 0, 1.1)


def compose() -> np.ndarray:
    d2, a2 = 73.416, 110.0  # D2 and its fifth
    d4, f4, a4 = 293.66, 349.23, 440.0  # D minor triad, the "air" layer

    sub = 0.50 * tone(d2) + 0.50 * tone(d2, 0.16)  # 0.16 Hz beating = slow shimmer
    fifth = (0.40 * tone(a2) + 0.12 * tone(a2 * 3)) * lfo(0.05, 1.3)
    air = (
        0.16 * tone(d4, 0.21) * lfo(0.031, 0.0)
        + 0.13 * tone(f4, -0.18) * lfo(0.043, 2.1)
        + 0.11 * tone(a4, 0.12) * lfo(0.037, 4.2)
    )
    # Filtered noise breath, only audible inside the swells.
    noise = rng.standard_normal(t.shape)
    kernel = np.ones(900) / 900.0  # crude lowpass via moving average
    breath = 0.10 * np.convolve(noise, kernel, mode="same")

    env = envelope()
    swell_only = np.clip(env - 0.55, 0, None) / 0.55  # breath rides the swells only
    mono = (0.42 * sub + 0.30 * fifth + air) * env + breath * swell_only * 0.5

    # Stereo width: right channel gets a 11ms delay on the air layer's share.
    delay = int(0.011 * SR)
    right = np.copy(mono)
    right[delay:] = 0.82 * mono[delay:] + 0.18 * mono[:-delay]
    stereo = np.stack([mono, right], axis=1)
    stereo /= np.max(np.abs(stereo)) * 1.25  # ~-2 dBFS headroom, mix gain set in Remotion
    return stereo


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "public" / "vo" / "music-bed.wav"
    data = (compose() * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"wrote {out} ({DUR}s)")


if __name__ == "__main__":
    main()
