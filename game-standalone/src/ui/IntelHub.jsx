import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HelpCircle, ChevronDown, MessageSquare, Bell, Info } from 'lucide-react'
import { useOutbreakData } from '../mockData'

const IntelHub = ({ vibe }) => {
  const { news, loading } = useOutbreakData()
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rts-panel w-full h-[300px] flex flex-col overflow-hidden"
    >
      <div className="p-3 border-b border-white/5 bg-white/5 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-teal" />
          <h2 className="text-[10px] font-black uppercase tracking-tighter text-white">Signal Feed</h2>
        </div>
        <div className="flex gap-2">
           <span className="text-[8px] hud-label animate-pulse">RECEIVING...</span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-3 custom-scrollbar space-y-2 bg-black/20">
        {news.slice(0, 10).map((art, i) => (
          <div key={i} className="border-l-2 border-teal/30 pl-3 py-1 hover:bg-white/5 transition-colors cursor-pointer group">
            <div className="flex justify-between items-center mb-0.5">
              <span className="text-[7px] font-bold text-teal/60 uppercase tracking-widest">{art.source}</span>
              <span className="text-[7px] text-gray-600 font-mono">{art.date}</span>
            </div>
            <h3 className="text-[10px] font-bold text-white/80 group-hover:text-teal leading-tight">{art.title}</h3>
          </div>
        ))}
        {loading && <div className="p-4 text-center text-[8px] hud-label animate-pulse">Scanning frequencies...</div>}
      </div>

      <div className="p-2 border-t border-white/5 flex gap-2">
         <input 
            type="text" 
            placeholder="ENCRYPTED COMMAND..." 
            className="flex-1 bg-black/40 border border-white/10 px-3 py-1.5 text-[10px] font-mono focus:border-teal outline-none transition-all"
         />
         <button className="px-3 py-1.5 border border-teal/40 bg-teal/10 hover:bg-teal/20 transition-all text-[8px] font-black uppercase">Send</button>
      </div>
    </motion.div>
  )
}

export default IntelHub
