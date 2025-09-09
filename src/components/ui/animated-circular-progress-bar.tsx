import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { useState, useEffect } from "react";
import "./firework.css";

interface AnimatedCircularProgressBarProps {
  max?: number;
  min?: number;
  value: number;
  gaugePrimaryColor: string;
  gaugeSecondaryColor: string;
  className?: string;
}

export function AnimatedCircularProgressBar({
  max = 100,
  min = 0,
  value = 0,
  gaugePrimaryColor,
  gaugeSecondaryColor,
  className,
}: AnimatedCircularProgressBarProps) {
  const circumference = 2 * Math.PI * 45;
  const percentPx = circumference / 100;
  const currentPercent = Math.round(((value - min) / (max - min)) * 100);
  
  const [showGreenCircle, setShowGreenCircle] = useState(false);
  const [showFirework, setShowFirework] = useState(false);
  
  // Trigger animations when reaching 100%
  useEffect(() => {
    if (currentPercent === 100) {
      // Show green circle IMMEDIATELY - starts animating simultaneously with ring
      setShowGreenCircle(true);
      
      // Trigger firework earlier, during the animations
      const timer = setTimeout(() => {
        setShowFirework(true);
      }, 600); // Start firework at 60% of the main animations
      
      return () => {
        clearTimeout(timer);
      };
    } else {
      setShowGreenCircle(false);
      setShowFirework(false);
    }
  }, [currentPercent]);

  return (
    <div
      className={cn("relative size-40 text-2xl font-semibold", className)}
      style={
        {
          "--circle-size": "100px",
          "--circumference": circumference,
          "--percent-to-px": `${percentPx}px`,
          "--gap-percent": "5",
          "--offset-factor": "0",
          "--transition-length": "1s",
          "--transition-step": "200ms",
          "--delay": "0s",
          "--percent-to-deg": "3.6deg",
          transform: "translateZ(0)",
        } as React.CSSProperties
      }
    >
      <svg
        fill="none"
        className="size-full"
        strokeWidth="2"
        viewBox="0 0 100 100"
      >
        {currentPercent <= 90 && currentPercent >= 0 && (
          <circle
            cx="50"
            cy="50"
            r="45"
            strokeWidth="10"
            strokeDashoffset="0"
            strokeLinecap="round"
            strokeLinejoin="round"
            className=" opacity-100"
            style={
              {
                stroke: gaugeSecondaryColor,
                "--stroke-percent": 90 - currentPercent,
                "--offset-factor-secondary": "calc(1 - var(--offset-factor))",
                strokeDasharray:
                  "calc(var(--stroke-percent) * var(--percent-to-px)) var(--circumference)",
                transform:
                  "rotate(calc(1turn - 90deg - (var(--gap-percent) * var(--percent-to-deg) * var(--offset-factor-secondary)))) scaleY(-1)",
                transition: "all var(--transition-length) ease var(--delay)",
                transformOrigin:
                  "calc(var(--circle-size) / 2) calc(var(--circle-size) / 2)",
              } as React.CSSProperties
            }
          />
        )}
        <circle
          cx="50"
          cy="50"
          r="45"
          strokeWidth="10"
          strokeDashoffset="0"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="opacity-100"
          style={
            {
              stroke: currentPercent === 100 ? '#22c55e' : gaugePrimaryColor, // Green when 100%, otherwise use primary color
              "--stroke-percent": currentPercent,
              strokeDasharray:
                "calc(var(--stroke-percent) * var(--percent-to-px)) var(--circumference)",
              transition:
                "var(--transition-length) ease var(--delay),stroke var(--transition-length) ease var(--delay)",
              transitionProperty: "stroke-dasharray,transform",
              transform:
                "rotate(calc(-90deg + var(--gap-percent) * var(--offset-factor) * var(--percent-to-deg)))",
              transformOrigin:
                "calc(var(--circle-size) / 2) calc(var(--circle-size) / 2)",
            } as React.CSSProperties
          }
        />
      </svg>
      {/* Center completion indicator - animates in when 100% complete */}
      {showGreenCircle && (
        <div 
          className="absolute inset-0 m-auto rounded-full bg-green-500 flex items-center justify-center animate-in zoom-in duration-1000"
          style={{ width: '80%', height: '80%' }}>
          <Check className="w-1/2 h-1/2 text-white animate-in zoom-in duration-300 delay-700" strokeWidth={3} />
        </div>
      )}
      
      {/* Firework effect - five radial sticks (behind circle) */}
      {showFirework && (
        <div className="absolute inset-0 pointer-events-none -z-10">
          {Array.from({ length: 5 }).map((_, index) => {
            const angle = (index * 72) - 90; // Start from top, 72 degrees apart (360/5)
            return (
              <div
                key={index}
                className="absolute h-0.5 bg-green-400 rounded-full"
                style={{
                  left: '50%',
                  top: '50%',
                  transformOrigin: '0 50%',
                  transform: `rotate(${angle}deg) translateY(-50%) translateX(15px)`, // Closer to center
                  animation: `firework-${index} 0.45s ease-out forwards`,
                }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
