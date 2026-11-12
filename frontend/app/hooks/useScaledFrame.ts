import { useEffect, useRef, useState } from "react";

export function useScaledFrame<T extends HTMLElement>(designWidth: number) {
  const frameRef = useRef<T>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;

    let raf: number;
    let currentScale = 1;
    const syncScale = () => {
      if (raf) cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const newScale = frame.getBoundingClientRect().width / designWidth;
        if (Math.abs(newScale - currentScale) > 0.001) {
          currentScale = newScale;
          setScale(newScale);
        }
      });
    };
    syncScale();

    const observer = new ResizeObserver(syncScale);
    observer.observe(frame);
    return () => {
      observer.disconnect();
      if (raf) cancelAnimationFrame(raf);
    };
  }, [designWidth]);

  return { frameRef, scale };
}
