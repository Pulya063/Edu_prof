import { useEffect, useRef, useState } from "react";

export function useScaledFrame<T extends HTMLElement>(designWidth: number) {
  const frameRef = useRef<T>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;

    const syncScale = () => setScale(frame.getBoundingClientRect().width / designWidth);
    syncScale();

    const observer = new ResizeObserver(syncScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [designWidth]);

  return { frameRef, scale };
}
