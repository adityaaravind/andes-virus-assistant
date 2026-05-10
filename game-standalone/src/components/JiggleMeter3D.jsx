import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const JiggleMeter3D = ({ value, label, color, max = 100, unit = "%" }) => {
  const [jitter, setJitter] = useState({ x: 0, y: 0, r: 0 });

  // Simulate "alive" organic vibration
  useEffect(() => {
    const interval = setInterval(() => {
      setJitter({
        x: (Math.random() - 0.5) * 1.5,
        y: (Math.random() - 0.5) * 1.5,
        r: (Math.random() - 0.5) * 2
      });
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const rotation = (value / max) * 180 - 90; // -90 to 90 degrees

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div 
        className="relative w-48 h-48 rounded-full border-4 border-white/5 flex items-center justify-center shadow-[0_0_50px_-12px_rgba(0,0,0,0.5)]"
        style={{ 
          perspective: '1000px', 
          transformStyle: 'preserve-3d',
          transform: 'rotateX(25deg) rotateY(-10deg)',
          background: `radial-gradient(circle at center, ${color}11 0%, transparent 70%)`
        }}
      >
        {/* Outer Glowing Ring */}
        <div 
          className="absolute inset-[-10px] rounded-full border-2 opacity-20 blur-[4px]"
          style={{ borderColor: color }}
        />

        {/* Dial Ticks */}
        <div className="absolute inset-2 rounded-full border border-white/10" />
        
        {/* Progress Arc */}
        <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full -rotate-90">
          <circle 
            cx="50" cy="50" r="45" 
            fill="none" 
            stroke={color} 
            strokeWidth="4" 
            strokeDasharray={`${(value/max)*283} 283`}
            className="transition-all duration-1000 ease-out"
            style={{ filter: `drop-shadow(0 0 8px ${color})` }}
          />
        </svg>

        {/* THE LIVING NEEDLE */}
        <div 
          className="absolute top-1/2 left-1/2 w-1 h-20 origin-bottom rounded-full"
          style={{ 
            backgroundColor: color,
            boxShadow: `0 0 15px ${color}`,
            transform: `translate(-50%, -100%) rotate(${rotation + jitter.r}deg) translate(${jitter.x}px, ${jitter.y}px)`,
            transition: 'transform 0.1s linear'
          }}
        >
           <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full" style={{ backgroundColor: color, boxShadow: `0 0 10px ${color}` }} />
        </div>

        {/* Center Readout */}
        <div className="z-10 text-center transform translate-z-20">
          <h2 className="text-4xl font-black text-white leading-none" style={{ textShadow: `0 0 15px ${color}` }}>
            {value}<span className="text-sm opacity-50">{unit}</span>
          </h2>
          <p className="text-[8px] font-mono text-gray-400 tracking-[0.2em] uppercase mt-1">{label}</p>
        </div>
      </div>
    </div>
  );
};

export default JiggleMeter3D;
