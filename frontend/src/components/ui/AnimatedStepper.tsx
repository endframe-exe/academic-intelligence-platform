import React, { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn, usePrefersReducedMotion } from "../../lib/utils";

export interface StepDefinition {
  id: string;
  title: string;
  subtitle?: string;
  validate?: () => string | null;
  content: React.ReactNode;
}

export function AnimatedStepper({
  steps,
  completeLabel = "Complete",
  onComplete,
  submitting = false,
}: {
  steps: StepDefinition[];
  completeLabel?: string;
  onComplete: () => void | Promise<void>;
  submitting?: boolean;
}) {
  const [current, setCurrent] = useState(0);
  const [direction, setDirection] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const reducedMotion = usePrefersReducedMotion();

  const step = steps[current];
  const progressPct = ((current + 1) / steps.length) * 100;

  const goNext = async () => {
    if (step.validate) {
      const msg = step.validate();
      if (msg) {
        setError(msg);
        return;
      }
    }
    setError(null);
    if (current === steps.length - 1) {
      await onComplete();
    } else {
      setDirection(1);
      setCurrent((c) => c + 1);
    }
  };

  const goBack = () => {
    setError(null);
    setDirection(-1);
    setCurrent((c) => Math.max(0, c - 1));
  };

  const jumpTo = (idx: number) => {
    if (idx <= current) {
      setError(null);
      setDirection(idx < current ? -1 : 1);
      setCurrent(idx);
    }
  };

  return (
    <div className="border border-[var(--hairline)] bg-[#efe9dd] p-5 sm:p-8">
      {/* Step indicators */}
      <div className="mb-4 flex flex-wrap gap-2">
        {steps.map((s, idx) => {
          const isCurrent = idx === current;
          const isCompleted = idx < current;
          return (
            <button
              key={s.id}
              type="button"
              aria-current={isCurrent ? "step" : undefined}
              disabled={idx > current}
              onClick={() => jumpTo(idx)}
              className={cn(
                "flex items-center gap-2 border px-3 py-1.5 text-[11px] uppercase tracking-[0.1em] transition-colors",
                isCurrent
                  ? "border-[#2c4a8f] text-[#2c4a8f] font-bold"
                  : isCompleted
                    ? "border-[#141c2b] text-[#141c2b] cursor-pointer"
                    : "border-[var(--hairline)] text-[#767e8c] opacity-60 cursor-not-allowed"
              )}
            >
              <span>0{idx + 1}</span>
              <span className="hidden sm:inline">{s.title}</span>
            </button>
          );
        })}
      </div>

      {/* Hairline 1px progress rule */}
      <div className="mb-6 h-[1px] w-full bg-[var(--hairline)]" aria-hidden="true">
        <div
          className="h-full bg-[#2c4a8f] transition-all duration-300"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      <div aria-live="polite" className="mb-4">
        <h2 className="font-editorial text-2xl font-medium text-[#141c2b]">
          {step.title}
        </h2>
        {step.subtitle && (
          <p className="mt-1 text-xs leading-6 text-[#4a5364]">{step.subtitle}</p>
        )}
      </div>

      {/* Step content */}
      <div className="relative overflow-hidden">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={step.id}
            initial={reducedMotion ? false : { opacity: 0, x: direction * 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={reducedMotion ? undefined : { opacity: 0, x: direction * -16 }}
            transition={{ duration: reducedMotion ? 0 : 0.2 }}
          >
            {step.content}
          </motion.div>
        </AnimatePresence>
      </div>

      {error && (
        <p role="alert" className="mt-4 border-l-2 border-[#141c2b] bg-[#e5ded0] px-3 py-2 text-xs text-[#141c2b]">
          {error}
        </p>
      )}

      <div className="mt-8 flex items-center justify-between border-t border-[var(--hairline)] pt-5">
        <button
          type="button"
          onClick={goBack}
          disabled={current === 0 || submitting}
          className="editorial-btn"
        >
          Back
        </button>
        <span className="text-[11px] uppercase tracking-[0.1em] text-[#767e8c]">
          Step {current + 1} / {steps.length}
        </span>
        <button
          type="button"
          onClick={() => void goNext()}
          disabled={submitting}
          className="editorial-btn editorial-btn-primary"
        >
          {submitting
            ? "Saving..."
            : current === steps.length - 1
              ? completeLabel
              : "Continue"}
        </button>
      </div>
    </div>
  );
}
