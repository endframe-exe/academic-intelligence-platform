import { useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import {
  BookOpen,
  CalendarClock,
  FileSpreadsheet,
  LayoutDashboard,
  LineChart,
  UserCircle,
} from "lucide-react";
import { cn, usePrefersReducedMotion } from "../../lib/utils";

const DOCK_ITEMS = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Academics", to: "/academics", icon: FileSpreadsheet },
  { label: "Predictions", to: "/predictions", icon: LineChart },
  { label: "Study Planner", to: "/study-planner", icon: CalendarClock },
  { label: "Syllabus Lab", to: "/syllabus-lab", icon: BookOpen },
  { label: "Profile", to: "/profile", icon: UserCircle },
];

function DockButton({
  item,
  active,
  mouseX,
  reducedMotion,
  onSelect,
}: {
  item: (typeof DOCK_ITEMS)[number];
  active: boolean;
  mouseX: ReturnType<typeof useMotionValue<number>>;
  reducedMotion: boolean;
  onSelect: () => void;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const [hovered, setHovered] = useState(false);

  const distance = useTransform(mouseX, (val) => {
    if (reducedMotion || val === Infinity || !ref.current) return 150;
    const rect = ref.current.getBoundingClientRect();
    return val - (rect.left + rect.width / 2);
  });

  const rawSize = useTransform(distance, [-110, 0, 110], [40, 52, 40]);
  const size = useSpring(rawSize, { stiffness: 260, damping: 24 });
  const Icon = item.icon;

  return (
    <div className="relative flex flex-col items-center">
      {hovered && (
        <span
          role="tooltip"
          className="pointer-events-none absolute -top-8 whitespace-nowrap border border-[var(--hairline)] bg-[#efe9dd] px-2 py-0.5 text-[10px] uppercase tracking-[0.1em] text-[#141c2b]"
        >
          {item.label}
        </span>
      )}
      <motion.button
        ref={ref}
        type="button"
        aria-label={item.label}
        aria-current={active ? "page" : undefined}
        style={reducedMotion ? { width: 42, height: 42 } : { width: size, height: size }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onFocus={() => setHovered(true)}
        onBlur={() => setHovered(false)}
        onClick={onSelect}
        className={cn(
          "relative flex items-center justify-center border border-[var(--hairline)] bg-[#efe9dd] text-[#141c2b] transition-colors cursor-pointer",
          active ? "border-[#2c4a8f] text-[#2c4a8f]" : "hover:border-[#141c2b]"
        )}
      >
        <Icon className="h-4 w-4" strokeWidth={1.75} />
        {active && (
          <span
            aria-hidden="true"
            className="absolute bottom-0 left-1 right-1 h-[1px] bg-[#2c4a8f]"
          />
        )}
      </motion.button>
    </div>
  );
}

export function MagnificationDock() {
  const location = useLocation();
  const navigate = useNavigate();
  const reducedMotion = usePrefersReducedMotion();
  const mouseX = useMotionValue<number>(Infinity);

  return (
    <>
      {/* Desktop dock */}
      <nav
        aria-label="Workspace quick navigation"
        onMouseMove={(e) => mouseX.set(e.clientX)}
        onMouseLeave={() => mouseX.set(Infinity)}
        className="fixed bottom-4 left-1/2 z-30 hidden -translate-x-1/2 items-end gap-2 border border-[var(--hairline)] bg-[#e5ded0]/95 px-3 py-2 backdrop-blur-sm md:flex"
      >
        {DOCK_ITEMS.map((item) => (
          <DockButton
            key={item.to}
            item={item}
            active={location.pathname.startsWith(item.to)}
            mouseX={mouseX}
            reducedMotion={reducedMotion}
            onSelect={() => navigate(item.to)}
          />
        ))}
      </nav>

      {/* Mobile accessible bottom bar */}
      <nav
        aria-label="Workspace mobile navigation"
        className="fixed bottom-0 left-0 right-0 z-30 flex items-center justify-around border-t border-[var(--hairline)] bg-[#e5ded0] py-2 md:hidden"
      >
        {DOCK_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = location.pathname.startsWith(item.to);
          return (
            <button
              key={item.to}
              type="button"
              aria-label={item.label}
              aria-current={active ? "page" : undefined}
              onClick={() => navigate(item.to)}
              className={cn(
                "flex flex-col items-center gap-0.5 px-2 py-1 text-[9px] uppercase tracking-[0.06em]",
                active ? "text-[#2c4a8f] font-bold" : "text-[#4a5364]"
              )}
            >
              <Icon className="h-4 w-4" strokeWidth={1.75} />
              <span>{item.label.split(" ")[0]}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
}
