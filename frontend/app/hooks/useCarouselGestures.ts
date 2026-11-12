import { useEffect, useRef } from "react";

const SWIPE_DISTANCE = 40;
const WHEEL_DISTANCE = 40;
const GESTURE_IDLE_MS = 140;

/**
 * Horizontal swipes for a set of cards, on a phone and on a trackpad.
 *
 * While the cards overflow, the browser scrolls them natively and this hook stays out of the way.
 * Otherwise one swipe moves one step: trackpad inertia keeps sending wheel events, so the lock holds
 * until they stop. The wheel listener is non-passive (React's onWheel is passive and cannot prevent
 * the browser's back-swipe navigation).
 */
export function useCarouselGestures<T extends HTMLElement>(move: (direction: number) => void, scrollerSelector?: string) {
  const ref = useRef<T>(null);
  const moveRef = useRef(move);
  moveRef.current = move;

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const scroller = () => (scrollerSelector ? node.matches(scrollerSelector) ? node : node.querySelector<HTMLElement>(scrollerSelector) : null);
    const overflowing = () => {
      const element = scroller();
      if (!element || element.scrollWidth <= element.clientWidth + 1) return false;
      // Content can stick out of a box that does not scroll; only a real scroller handles the swipe natively.
      return ["auto", "scroll"].includes(getComputedStyle(element).overflowX);
    };
    const syncTouchAction = () => { node.style.touchAction = overflowing() ? "pan-x pan-y" : "pan-y"; };

    let total = 0;
    let locked = false;
    let idle = 0;
    const onWheel = (event: WheelEvent) => {
      const unit = event.deltaMode === 1 ? 16 : 1;
      const dx = event.deltaX * unit;
      if (dx === 0 || Math.abs(dx) <= Math.abs(event.deltaY * unit) || overflowing()) return;
      event.preventDefault();
      window.clearTimeout(idle);
      idle = window.setTimeout(() => { total = 0; locked = false; }, GESTURE_IDLE_MS);
      if (locked) return;
      total += dx;
      if (Math.abs(total) >= WHEEL_DISTANCE) {
        moveRef.current(total > 0 ? 1 : -1);
        locked = true;
        total = 0;
      }
    };

    let start: { x: number; y: number } | null = null;
    const onPointerDown = (event: PointerEvent) => {
      start = event.pointerType === "mouse" ? null : { x: event.clientX, y: event.clientY };
    };
    const onPointerUp = (event: PointerEvent) => {
      if (!start) return;
      const dx = event.clientX - start.x;
      const dy = event.clientY - start.y;
      start = null;
      if (overflowing() || Math.abs(dx) < SWIPE_DISTANCE || Math.abs(dx) < Math.abs(dy) * 1.4) return;
      moveRef.current(dx > 0 ? -1 : 1);
    };
    const onPointerCancel = () => { start = null; };

    syncTouchAction();
    const resize = new ResizeObserver(syncTouchAction);
    resize.observe(node);
    node.addEventListener("wheel", onWheel, { passive: false });
    node.addEventListener("pointerdown", onPointerDown);
    node.addEventListener("pointerup", onPointerUp);
    node.addEventListener("pointercancel", onPointerCancel);
    return () => {
      window.clearTimeout(idle);
      resize.disconnect();
      node.removeEventListener("wheel", onWheel);
      node.removeEventListener("pointerdown", onPointerDown);
      node.removeEventListener("pointerup", onPointerUp);
      node.removeEventListener("pointercancel", onPointerCancel);
    };
  }, [scrollerSelector]);

  return ref;
}
