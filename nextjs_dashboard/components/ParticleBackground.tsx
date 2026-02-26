"use client";

import { useEffect, useState } from "react";

/**
 * Lightweight CSS-only particle background.
 * Replaces tsparticles to avoid heavy compilation on WSL2.
 * Auto-detects dark/light mode from document.documentElement.
 */
export function ParticleBackground() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const check = () => setIsDark(document.documentElement.classList.contains("dark"));
    check();
    const observer = new MutationObserver(check);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  const color = isDark ? "0, 217, 255" : "102, 126, 234";

  return (
    <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none" aria-hidden>
      {/* Floating particles via CSS */}
      {Array.from({ length: 20 }).map((_, i) => (
        <span
          key={i}
          className="particle-dot"
          style={{
            "--x": `${Math.random() * 100}%`,
            "--y": `${Math.random() * 100}%`,
            "--size": `${1.5 + Math.random() * 2.5}px`,
            "--duration": `${15 + Math.random() * 25}s`,
            "--delay": `${-Math.random() * 20}s`,
            "--opacity": `${0.1 + Math.random() * 0.2}`,
            "--color": color,
          } as React.CSSProperties}
        />
      ))}
      {/* Connection lines (subtle grid) */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.03]">
        <defs>
          <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse">
            <path d="M 80 0 L 0 0 0 80" fill="none" stroke={`rgb(${color})`} strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
    </div>
  );
}
