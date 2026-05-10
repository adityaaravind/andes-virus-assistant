import React from 'react'
import { motion } from 'framer-motion'
import { ShieldAlert, Terminal, Cpu } from 'lucide-react'
import { useOutbreakData } from '../mockData'
import JiggleMeter3D from '../components/JiggleMeter3D'

const MainHub = () => {
  const { stats, loading } = useOutbreakData()
  const summary = stats?.summary || { confirmed_cases: 0, deaths: 0, nationalities: 0, ship_status: "Syncing..." }

  // Derive simple scores for the meters
  const riskScore = Math.min(100, (summary.confirmed_cases * 15) + (summary.nationalities * 5));

  return (
    <div className="absolute top-6 left-6 z-20 flex flex-col gap-4 w-[400px]">
      {/* ── MISSION COMMAND HEADER ── */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="rts-panel p-6 w-full"
      >
        <div className="flex items-center gap-3 mb-4">
           <div className="p-1.5 border border-teal/30 bg-teal/5">
              <Terminal className="w-4 h-4 text-teal" />
           </div>
           <div>
              <span className="hud-label">Op Intelligence</span>
              <p className="text-[8px] text-gray-500 font-mono animate-pulse">UPLINK: STABLE // AES-256</p>
           </div>
        </div>
        <h1 className="text-5xl font-black mb-2 tracking-tighter leading-none text-white">
          ANDES<br/>OS
        </h1>
        
        <div className="mt-6 flex flex-col gap-4">
           <div className="flex justify-between items-end border-b border-white/5 pb-2">
              <span className="hud-label">Bio-Threat</span>
              <span className="hud-value">{riskScore}%</span>
           </div>
           <div className="flex justify-between items-end border-b border-white/5 pb-2">
              <span className="hud-label">Fatality Variance</span>
              <span className="hud-value text-red-alert">{summary.deaths * 20}%</span>
           </div>
        </div>
      </motion.div>

      {/* ── TACTICAL DATA GRID ── */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
        className="rts-panel p-4 grid grid-cols-2 gap-4"
      >
        {[
          { label: "Cases", value: summary.confirmed_cases, color: "text-teal" },
          { label: "Deaths", value: summary.deaths, color: "text-red-alert" },
          { label: "Nations", value: summary.nationalities, color: "text-amber" },
          { label: "Status", value: summary.ship_status, color: "text-white", small: true }
        ].map((stat, i) => (
          <div key={i} className="flex flex-col border-l border-white/10 pl-3 py-1">
            <p className="hud-label mb-1">{stat.label}</p>
            <h2 className={`${stat.small ? 'text-[10px]' : 'text-2xl'} font-black ${stat.color} tracking-tighter`}>{stat.value}</h2>
          </div>
        ))}
      </motion.div>

      {/* QUICK ACTION */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
        className="rts-panel p-4 flex items-center gap-4"
      >
        <div className="w-10 h-10 border border-teal/20 flex items-center justify-center bg-teal/5">
           <ShieldAlert className="w-5 h-5 text-teal" />
        </div>
        <button className="flex-1 py-2 border border-teal/40 bg-teal/10 hover:bg-teal/20 transition-all text-[10px] font-bold uppercase tracking-widest">
          Initiate Triage
        </button>
      </motion.div>
    </div>
  )
}

export default MainHub
