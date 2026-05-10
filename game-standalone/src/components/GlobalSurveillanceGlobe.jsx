import React from 'react';

const GlobalSurveillanceGlobe = ({ locations, route }) => {
  return (
    <div className="w-full h-full flex items-center justify-center relative">
       <div className="w-80 h-80 rounded-full border-2 border-teal/20 shadow-[0_0_100px_rgba(0,180,216,0.2)] animate-pulse relative">
          <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_center,_rgba(0,180,216,0.1)_0%,_transparent_70%)]" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-teal font-black text-xs tracking-widest text-center">
            RE-SYNCING<br/>ORBITAL ARRAY
          </div>
       </div>
       <div className="absolute top-4 right-4 text-[10px] tech-label bg-black/40 p-2 border border-white/5 rounded">
        GL-Surveillance: STANDBY
      </div>
    </div>
  );
};

export default GlobalSurveillanceGlobe;
