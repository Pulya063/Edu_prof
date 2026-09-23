"use client";

import Image from "next/image";
import type { CSSProperties } from "react";
import { useScaledFrame } from "./useScaledFrame";

const WIDTH = 920;

export default function MacbookDisplay() {
  const { frameRef, scale } = useScaledFrame<HTMLDivElement>(WIDTH);

  return (
    <div ref={frameRef} className="macbook-composite" style={{ "--macbook-canvas-scale": scale } as CSSProperties}>
      <Image className="macbook-composite-art" src="/fence-macbook-hero-transparent.png" alt="" width={1536} height={1024} priority sizes="(max-width: 900px) 93vw, 780px" />
    </div>
  );
}
