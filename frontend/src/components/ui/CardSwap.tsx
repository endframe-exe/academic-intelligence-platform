import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";
import { usePrefersReducedMotion } from "../../lib/utils";

export interface EditorialCardItem {
  code: string;
  category: string;
  title: string;
  summary: string;
  metricsLabel: string;
  route: string;
}

export function CardSwap({
  cards,
  onSelectCard,
}: {
  cards: EditorialCardItem[];
  onSelectCard?: (card: EditorialCardItem) => void;
}) {
  const reducedMotion = usePrefersReducedMotion();
  const [activeIndex, setActiveIndex] = useState(0);
  const [paused, setPaused] = useState(reducedMotion);
  const frontCardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reducedMotion) {
      setPaused(true);
    }
  }, [reducedMotion]);

  useEffect(() => {
    if (reducedMotion || paused || cards.length <= 1) return;
    const timer = window.setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % cards.length);
    }, 5200);
    return () => window.clearInterval(timer);
  }, [reducedMotion, paused, cards.length]);

  useEffect(() => {
    if (reducedMotion || !frontCardRef.current) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        frontCardRef.current,
        { y: 10, opacity: 0.72 },
        { y: 0, opacity: 1, duration: 0.35, ease: "power2.out", clearProps: "transform,opacity" }
      );
    }, frontCardRef);
    return () => ctx.revert();
  }, [activeIndex, reducedMotion]);

  const current = cards[activeIndex];
  const prev = () => setActiveIndex((i) => (i - 1 + cards.length) % cards.length);
  const next = () => setActiveIndex((i) => (i + 1) % cards.length);

  // Ordered layers from back to front for desktop perspective stack
  const orderedIndices = cards.map((_, offset) => (activeIndex + offset) % cards.length);

  return (
    <div
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => {
        if (!reducedMotion) setPaused(false);
      }}
      onFocus={() => setPaused(true)}
      onBlur={() => {
        if (!reducedMotion) setPaused(false);
      }}
      className="rounded-none border border-[var(--hairline)] bg-[#efe9dd] p-5 sm:p-6"
    >
      <div className="mb-4 flex items-center justify-between border-b border-[var(--hairline)] pb-3">
        <span className="text-[11px] uppercase tracking-[0.14em] text-[#767e8c]">
          Sheet {activeIndex + 1} of {cards.length} — {current.code}
        </span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label="Previous module"
            onClick={prev}
            className="rounded-none border border-[var(--hairline)] p-1.5 text-[#141c2b] hover:border-[#2c4a8f] hover:text-[#2c4a8f] cursor-pointer"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            aria-label={paused ? "Resume module rotation" : "Pause module rotation"}
            onClick={() => setPaused((p) => !p)}
            className="rounded-none border border-[var(--hairline)] p-1.5 text-[#141c2b] hover:border-[#2c4a8f] hover:text-[#2c4a8f] cursor-pointer"
          >
            {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
          </button>
          <button
            type="button"
            aria-label="Next module"
            onClick={next}
            className="rounded-none border border-[var(--hairline)] p-1.5 text-[#141c2b] hover:border-[#2c4a8f] hover:text-[#2c4a8f] cursor-pointer"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Layered square-cornered paper stack */}
      <div className="relative hidden min-h-[260px] sm:block">
        {orderedIndices
          .slice(1)
          .reverse()
          .map((cardIdx, reverseStep) => {
            const depth = orderedIndices.length - 1 - reverseStep;
            const card = cards[cardIdx];
            return (
              <div
                key={card.code}
                aria-hidden="true"
                className="pointer-events-none absolute inset-x-0 top-0 rounded-none border border-[var(--hairline)] bg-[#e5ded0] p-5"
                style={{
                  transform: `translate(${depth * 6}px, ${depth * 6}px)`,
                  opacity: Math.max(0.45, 1 - depth * 0.2),
                  height: "232px",
                }}
              >
                <span className="text-[10px] uppercase tracking-[0.12em] text-[#767e8c]">
                  {card.code}
                </span>
              </div>
            );
          })}

        <div
          ref={frontCardRef}
          className="relative z-10 min-h-[232px] rounded-none border border-[#141c2b]/40 bg-[#efe9dd] p-5 flex flex-col justify-between"
        >
          <div>
            <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
              {current.category}
            </p>
            <h3 className="mt-2 font-editorial text-2xl font-medium text-[#141c2b]">
              {current.title}
            </h3>
            <p className="mt-3 text-xs leading-6 text-[#4a5364]">{current.summary}</p>
          </div>
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--hairline)] pt-3">
            <span className="text-[11px] text-[#767e8c]">{current.metricsLabel}</span>
            {onSelectCard && (
              <button
                type="button"
                onClick={() => onSelectCard(current)}
                className="text-[11px] uppercase tracking-[0.12em] text-[#2c4a8f] underline underline-offset-4 hover:text-[#141c2b] cursor-pointer"
              >
                Open Module →
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Narrow-screen static accessible card */}
      <div className="rounded-none border border-[var(--hairline)] bg-[#e5ded0] p-4 sm:hidden">
        <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
          {current.category}
        </p>
        <h3 className="mt-2 font-editorial text-xl font-medium text-[#141c2b]">
          {current.title}
        </h3>
        <p className="mt-2 text-xs leading-6 text-[#4a5364]">{current.summary}</p>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-[var(--hairline)] pt-3">
          <span className="text-[11px] text-[#767e8c]">{current.metricsLabel}</span>
          {onSelectCard && (
            <button
              type="button"
              onClick={() => onSelectCard(current)}
              className="text-[11px] uppercase tracking-[0.12em] text-[#2c4a8f] underline underline-offset-4"
            >
              Open →
            </button>
          )}
        </div>
      </div>

      {/* 1px hairline indicator rules */}
      <div className="mt-6 flex gap-2">
        {cards.map((card, idx) => (
          <button
            key={card.code}
            type="button"
            aria-label={`View ${card.title}`}
            aria-current={idx === activeIndex ? "true" : undefined}
            onClick={() => setActiveIndex(idx)}
            className="py-2 flex-1 cursor-pointer"
          >
            <span
              className={`block h-[1px] w-full transition-colors ${
                idx === activeIndex ? "bg-[#2c4a8f]" : "bg-[var(--hairline)]"
              }`}
            />
          </button>
        ))}
      </div>
    </div>
  );
}
