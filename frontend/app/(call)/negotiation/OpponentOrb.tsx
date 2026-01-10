"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";

type OpponentOrbProps = {
  isThinking: boolean;
  spinTrigger: number;
  statusLabel: string;
  audioLevel: number;
};

type Particle = {
  id: number;
  size: number;
  x: number;
  y: number;
  dx: number;
  dy: number;
  f1: number;
  f2: number;
  p1: number;
};

export function OpponentOrb({
  isThinking,
  spinTrigger,
  statusLabel,
  audioLevel,
}: OpponentOrbProps) {
  const [motionPhase, setMotionPhase] = useState(0);
  const motionRafRef = useRef<number | null>(null);
  const lastMotionTimeRef = useRef<number | null>(null);
  const audioTargetRef = useRef(audioLevel);
  const audioSmoothRef = useRef(audioLevel);

  useEffect(() => {
    audioTargetRef.current = audioLevel;
  }, [audioLevel]);

  const seededRandom = (seed: number) => {
    let t = seed;
    return () => {
      t += 0x6d2b79f5;
      let m = Math.imul(t ^ (t >>> 15), 1 | t);
      m ^= m + Math.imul(m ^ (m >>> 7), 61 | m);
      return ((m ^ (m >>> 14)) >>> 0) / 4294967296;
    };
  };

  const particles = useMemo<Particle[]>(
    () =>
      Array.from({ length: 48 }).map((_, index) => {
        const rng = seededRandom(index + 1);
        const angle = rng() * Math.PI * 2;
        const radius = Math.sqrt(rng()) * 32;
        return {
          id: index,
          size: 3 + (index % 3) * 2,
          x: Math.cos(angle) * radius,
          y: Math.sin(angle) * radius,
          dx: rng() * 2 - 1,
          dy: rng() * 2 - 1,
          f1: 0.6 + rng() * 0.9,
          f2: 0.7 + rng() * 1.1,
          p1: rng() * Math.PI * 2,
        };
      }),
    []
  );

  useEffect(() => {
    const tick = (time: number) => {
      if (lastMotionTimeRef.current === null) {
        lastMotionTimeRef.current = time;
      }
      const delta = time - (lastMotionTimeRef.current ?? time);
      lastMotionTimeRef.current = time;
      const baseSpeed = 0.001;
      const smooth = audioSmoothRef.current + (audioTargetRef.current - audioSmoothRef.current) * 0.08;
      audioSmoothRef.current = smooth;
      const audioBoost = smooth * 0.002;
      const step = delta * (baseSpeed + audioBoost);
      setMotionPhase((prev) => prev + step);
      motionRafRef.current = requestAnimationFrame(tick);
    };

    motionRafRef.current = requestAnimationFrame(tick);

    return () => {
      if (motionRafRef.current) {
        cancelAnimationFrame(motionRafRef.current);
      }
      lastMotionTimeRef.current = null;
    };
  }, []);

  return (
    <div className="absolute left-8 top-24 flex flex-col items-start gap-3">
      <div className="relative h-28 w-28 overflow-hidden rounded-full bg-black/90">
        <div
          className="absolute inset-0 rounded-full bg-olive-20 blur-2xl"
          style={{ transform: `scale(${0.75 + audioLevel * 0.5})` }}
        />
        {isThinking ? (
          <motion.div
            key={spinTrigger}
            className="absolute inset-2 rounded-full border border-olive-soft-40"
            animate={{ opacity: [0.2, 0.6, 0.2] }}
            transition={{ duration: 1.1, ease: "easeInOut", repeat: 2 }}
          />
        ) : null}
        <div className="absolute inset-0">
          {particles.map((particle) => {
            const activeLevel = audioSmoothRef.current;
            const phase = motionPhase + particle.p1 * 0.4;
            const speedBoost = 1 + activeLevel * 1.8;
            const flowX = Math.cos(phase * particle.f1) * 2.2 * speedBoost;
            const flowY = Math.sin(phase * particle.f2) * 2.2 * speedBoost;
            const swirlX =
              Math.sin(phase + particle.p1) * particle.dx * 1.8 * speedBoost;
            const swirlY =
              Math.cos(phase + particle.p1) * particle.dy * 1.8 * speedBoost;
            const expansion = 0.7 + activeLevel * 0.55;
            const sizeBoost = 1 + activeLevel * 0.9;
            const x = (particle.x + flowX + swirlX * 0.45) * expansion;
            const y = (particle.y + flowY + swirlY * 0.45) * expansion;
            const opacity = 0.4 + activeLevel * 0.6;
            return (
              <div
                key={particle.id}
                className="absolute left-1/2 top-1/2 rounded-full bg-olive-soft"
                style={{
                  width: particle.size * sizeBoost,
                  height: particle.size * sizeBoost,
                  transform: `translate(-50%, -50%) translate(${x}px, ${y}px)`,
                  opacity,
                }}
              />
            );
          })}
        </div>
      </div>
      <div className="rounded-full border border-white/20 bg-black/40 px-4 py-2 text-xs font-semibold text-white backdrop-blur">
        Opponent status: {statusLabel}
      </div>
    </div>
  );
}
