"use client";

import dynamic from "next/dynamic";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useRef } from "react";

const Tilt = dynamic(() => import("react-parallax-tilt"), { ssr: false });

interface StatsCardsProps {
  pending: number;
  inProgress: number;
  approved: number;
}

function AnimatedNumber({ value }: { value: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const motionValue = useMotionValue(0);
  const rounded = useTransform(motionValue, (v) => Math.round(v));

  useEffect(() => {
    const controls = animate(motionValue, value, {
      duration: 0.8,
      ease: [0.25, 0.1, 0.25, 1],
    });
    return controls.stop;
  }, [value, motionValue]);

  useEffect(() => {
    const unsubscribe = rounded.on("change", (v) => {
      if (ref.current) ref.current.textContent = String(v);
    });
    return unsubscribe;
  }, [rounded]);

  return <span ref={ref}>{value}</span>;
}

export function StatsCards({ pending, inProgress, approved }: StatsCardsProps) {
  const stats = [
    {
      label: "Pending Approval",
      value: pending,
      icon: "⏳",
      gradient: "from-amber-400 to-orange-500",
      glowColor: "rgba(245, 158, 11, 0.15)",
      iconBg: "bg-gradient-to-br from-amber-400/20 to-orange-500/20",
    },
    {
      label: "In Progress",
      value: inProgress,
      icon: "⚙️",
      gradient: "from-cyan-400 to-blue-500",
      glowColor: "rgba(0, 217, 255, 0.15)",
      iconBg: "bg-gradient-to-br from-cyan-400/20 to-blue-500/20",
    },
    {
      label: "Approved Today",
      value: approved,
      icon: "✅",
      gradient: "from-emerald-400 to-green-500",
      glowColor: "rgba(16, 185, 129, 0.15)",
      iconBg: "bg-gradient-to-br from-emerald-400/20 to-green-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {stats.map((stat, index) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: index * 0.1,
            type: "spring",
            stiffness: 100,
            damping: 15,
          }}
        >
          <Tilt
            tiltMaxAngleX={8}
            tiltMaxAngleY={8}
            glareEnable={true}
            glareMaxOpacity={0.08}
            glareColor="#ffffff"
            glarePosition="all"
            perspective={800}
            transitionSpeed={400}
            scale={1.02}
          >
            <div
              className="glass-card rounded-2xl p-6 relative overflow-hidden"
              style={{ boxShadow: `0 8px 32px ${stat.glowColor}` }}
            >
              {/* Gradient accent line */}
              <div
                className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${stat.gradient}`}
              />

              <div className="flex items-center justify-between relative z-10">
                <div>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {stat.label}
                  </p>
                  <p
                    className={`text-4xl font-bold mt-3 bg-gradient-to-r ${stat.gradient} bg-clip-text text-transparent`}
                  >
                    <AnimatedNumber value={stat.value} />
                  </p>
                </div>
                <div
                  className={`text-4xl p-3 rounded-xl ${stat.iconBg} backdrop-blur-sm`}
                >
                  {stat.icon}
                </div>
              </div>
            </div>
          </Tilt>
        </motion.div>
      ))}
    </div>
  );
}
