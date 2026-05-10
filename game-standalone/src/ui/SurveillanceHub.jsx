import React from 'react'
import { motion } from 'framer-motion'
import { Globe as GlobeIcon, Newspaper, ExternalLink, Ship } from 'lucide-react'
import { useOutbreakData } from '../mockData'
import GlobalSurveillanceGlobe from '../components/GlobalSurveillanceGlobe'

const SurveillanceHub = () => {
  const { stats, loading } = useOutbreakData()

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rts-panel h-full w-full flex flex-col overflow-hidden"
    >
      <div className="p-3 border-b border-white/5 bg-white/5 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <GlobeIcon className="w-4 h-4 text-teal" />
          <h2 className="text-[10px] font-black uppercase tracking-tighter text-white">Surveillance</h2>
        </div>
        <span className="text-[8px] font-mono text-red-alert font-bold bg-red-500/10 px-1.5 py-0.5 border border-red-500/20">HOTZONE</span>
      </div>
      <div className="flex-1 relative bg-black/40 flex items-center justify-center overflow-hidden">
         {/* REAL-TIME 3D GLOBE */}
         <div className="w-full h-full scale-[1.5]">
            <GlobalSurveillanceGlobe 
                locations={stats?.locations} 
                route={stats?.vessel_route} 
            />
         </div>
         
         <div className="absolute bottom-3 left-3 p-2 bg-black/60 border border-white/10 pointer-events-none">
            <div className="flex items-center gap-2 mb-1">
               <Ship className="w-3 h-3 text-amber" />
               <span className="text-[8px] hud-label">MV Hondius</span>
            </div>
            <p className="text-[9px] font-mono text-white/60">14.93 N | 23.51 W</p>
         </div>
      </div>
    </motion.div>
  )
}

export default SurveillanceHub
