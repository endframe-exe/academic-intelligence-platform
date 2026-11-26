import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import gsap from "gsap";
import { Menu, X } from "lucide-react";
import { cn, usePrefersReducedMotion } from "../../lib/utils";
import { useAuth } from "../../context/AuthContext";

interface NavItem {
  label: string;
  to: string;
}

export function PillNav() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const reducedMotion = usePrefersReducedMotion();
  const navRef = useRef<HTMLElement>(null);
  const logoMarkRef = useRef<HTMLSpanElement>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const items = useMemo<NavItem[]>(() => {
    if (user) {
      return [
        { label: "Dashboard", to: "/dashboard" },
        { label: "Academics", to: "/academics" },
        { label: "Predictions", to: "/predictions" },
        { label: "Syllabus Lab", to: "/syllabus-lab" },
        { label: "Classroom Challenge", to: "/classroom-challenge" },
      ];
    }
    return [
      { label: "Overview", to: "/" },
      { label: "Classroom Challenge", to: "/classroom-challenge" },
      { label: "Sign In", to: "/login" },
    ];
  }, [user]);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (reducedMotion || !navRef.current) return;
    const ctx = gsap.context(() => {
      gsap.from(".editorial-nav-item", {
        y: -8,
        opacity: 0,
        duration: 0.4,
        stagger: 0.04,
        ease: "power2.out",
        clearProps: "transform,opacity",
      });
    }, navRef);
    return () => ctx.revert();
  }, [reducedMotion, items]);

  const handleLogoHover = () => {
    if (reducedMotion || !logoMarkRef.current) return;
    gsap.fromTo(
      logoMarkRef.current,
      { rotate: 0 },
      { rotate: 180, duration: 0.35, ease: "power2.out" }
    );
  };

  return (
    <header
      ref={navRef}
      className="fixed top-0 left-0 right-0 z-40 h-[58px] rounded-none border-b border-[var(--hairline)] bg-[#efe9dd]/92 backdrop-blur-sm"
    >
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link
          to={user ? "/dashboard" : "/"}
          onMouseEnter={handleLogoHover}
          className="flex items-center gap-2 text-[#141c2b] no-underline"
        >
          <span
            ref={logoMarkRef}
            aria-hidden="true"
            className="inline-flex h-5 w-5 rounded-none items-center justify-center border border-[#141c2b] text-[10px] font-bold"
          >
            S
          </span>
          <span className="font-editorial text-xl font-medium tracking-[-0.02em]">
            Scholia<span className="text-[#2c4a8f]">.</span>
          </span>
        </Link>

        <nav aria-label="Primary navigation" className="hidden items-center gap-6 md:flex">
          {items.map((item) => {
            const active =
              item.to === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "editorial-nav-item relative py-1 text-[11px] uppercase tracking-[0.12em] transition-colors",
                  active
                    ? "text-[#2c4a8f] font-bold"
                    : "text-[#4a5364] hover:text-[#2c4a8f]"
                )}
              >
                {item.label}
                {active && (
                  <span
                    aria-hidden="true"
                    className="absolute bottom-0 left-0 right-0 h-[1px] bg-[#2c4a8f]"
                  />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {user ? (
            <>
              <Link
                to="/profile"
                className="text-[11px] uppercase tracking-[0.1em] text-[#4a5364] hover:text-[#2c4a8f]"
              >
                {user.name.split(" ")[0]}
              </Link>
              <button
                type="button"
                onClick={logout}
                className="editorial-btn rounded-none py-1.5 px-3 text-[11px]"
              >
                Sign Out
              </button>
            </>
          ) : (
            <Link
              to="/register"
              className="editorial-btn editorial-btn-primary rounded-none py-1.5 px-4 text-[11px]"
            >
              Start Workspace
            </Link>
          )}
        </div>

        <button
          type="button"
          aria-expanded={mobileOpen}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          onClick={() => setMobileOpen((prev) => !prev)}
          className="inline-flex h-9 w-9 rounded-none items-center justify-center border border-[var(--hairline)] text-[#141c2b] md:hidden"
        >
          {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      {mobileOpen && (
        <nav
          aria-label="Mobile navigation"
          className="rounded-none border-b border-[var(--hairline)] bg-[#efe9dd] px-4 py-3 md:hidden"
        >
          <ul className="flex flex-col divide-y divide-[var(--hairline)]">
            {items.map((item) => {
              const active =
                item.to === "/"
                  ? location.pathname === "/"
                  : location.pathname.startsWith(item.to);
              return (
                <li key={item.to}>
                  <Link
                    to={item.to}
                    aria-current={active ? "page" : undefined}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      "block py-3 text-xs uppercase tracking-[0.12em]",
                      active ? "text-[#2c4a8f] font-bold" : "text-[#141c2b]"
                    )}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
            <li className="pt-3">
              {user ? (
                <div className="flex items-center justify-between">
                  <Link
                    to="/profile"
                    onClick={() => setMobileOpen(false)}
                    className="text-xs uppercase tracking-[0.1em] text-[#4a5364]"
                  >
                    Profile
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      logout();
                      setMobileOpen(false);
                    }}
                    className="editorial-btn rounded-none py-1.5 px-3"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <Link
                  to="/register"
                  onClick={() => setMobileOpen(false)}
                  className="editorial-btn editorial-btn-primary rounded-none block text-center"
                >
                  Start Workspace
                </Link>
              )}
            </li>
          </ul>
        </nav>
      )}
    </header>
  );
}
