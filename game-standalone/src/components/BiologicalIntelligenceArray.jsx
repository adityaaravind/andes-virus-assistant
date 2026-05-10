import React, { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Html, ContactShadows } from '@react-three/drei';
import * as THREE from 'three';
import { Cpu, Heart, Activity } from 'lucide-react';
import { motion } from 'framer-motion';

const SymptomMarker = ({ position, label, detail, active }) => {
  return (
    <group position={position}>
      <mesh>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial 
          color={active ? "#ff007f" : "#00b4d8"} 
          emissive={active ? "#ff007f" : "#00b4d8"}
          emissiveIntensity={active ? 4 : 0.5}
        />
      </mesh>
      {active && (
        <Html distanceFactor={6}>
          <div className="bg-black/90 backdrop-blur-2xl border-l-4 border-neon-pink p-4 min-w-[200px] shadow-2xl">
             <p className="text-[10px] tech-label text-neon-pink mb-1">Biological Engagement</p>
             <h4 className="text-sm font-black text-white uppercase tracking-tighter mb-2">{label}</h4>
             <p className="text-[10px] text-gray-400 leading-relaxed font-mono">{detail}</p>
          </div>
        </Html>
      )}
    </group>
  );
};

const BiologicalModel = ({ activeCase }) => {
  const groupRef = useRef();
  
  useFrame((state) => {
    if (groupRef.current) {
       groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.2;
    }
  });

  const getSymptoms = (caseId) => {
    const base = [
      { pos: [0, 1.3, 0], label: "High Fever", detail: "Temperature > 39.5°C reported within 24h of prodrome.", active: true },
    ];
    if (caseId === 2 || caseId === 3) {
      base.push({ pos: [0, 0.4, 0.2], label: "Pulmonary Edema", detail: "Severe fluid accumulation in lung tissue. Critical failure point.", active: true });
    }
    base.push({ pos: [0.3, 0, 0.1], label: "Myalgia", detail: "Acute muscle pain in lower extremities and lumbar region.", active: true });
    return base;
  };

  return (
    <group ref={groupRef}>
      <mesh position={[0, 0, 0]}>
        <capsuleGeometry args={[0.35, 2.2, 8, 32]} />
        <meshStandardMaterial 
          color="#00b4d8" 
          wireframe 
          transparent 
          opacity={0.15} 
          metalness={1}
        />
      </mesh>
      <mesh position={[0, 0, 0]}>
        <cylinderGeometry args={[0.02, 0.02, 2, 8]} />
        <meshStandardMaterial color="#00b4d8" emissive="#00b4d8" emissiveIntensity={2} />
      </mesh>
      {getSymptoms(activeCase).map((s, i) => (
        <SymptomMarker key={i} {...s} />
      ))}
      <ContactShadows position={[0, -1.2, 0]} opacity={0.4} scale={5} blur={2.5} far={2} color="#00b4d8" />
    </group>
  );
};

const BiologicalIntelligenceArray = () => {
  const [selectedCase, setSelectedCase] = useState(1);
  const cases = [
    { id: 1, label: "CASE_001", status: "DECEASED", date: "APR 11" },
    { id: 2, label: "CASE_002", status: "DECEASED", date: "APR 26" },
    { id: 3, label: "CASE_003", status: "STABLE", date: "MAY 02" },
  ];

  return (
    <section className="min-h-screen w-full flex flex-col items-center justify-center p-6 gap-12 pt-32">
      <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-3 gap-12">
        <div className="flex flex-col gap-4">
           <div className="mb-8">
              <span className="tech-label">Diagnostic Interface</span>
              <h2 className="text-4xl font-black glow-text-teal uppercase leading-none mt-2">Case Files</h2>
           </div>
           {cases.map((c) => (
             <button 
               key={c.id}
               onClick={() => setSelectedCase(c.id)}
               className={`p-6 border-l-4 transition-all text-left ${selectedCase === c.id ? 'bg-teal/10 border-teal shadow-[0_0_30px_rgba(0,180,216,0.1)]' : 'bg-white/5 border-white/10 opacity-40 hover:opacity-100'}`}
             >
                <div className="flex justify-between items-center mb-2">
                   <span className="text-[10px] font-black tracking-widest">{c.label}</span>
                   <span className={`text-[8px] px-2 py-0.5 rounded font-black ${c.status.includes('DECEASED') ? 'bg-red-500/20 text-red-500' : 'bg-teal/20 text-teal'}`}>{c.status}</span>
                </div>
                <p className="text-xs text-gray-400 font-mono italic uppercase">{c.date}, 2026</p>
             </button>
           ))}
           <div className="mt-8 p-4 bg-black/40 border border-white/5 rounded-xl">
              <p className="text-[9px] text-gray-500 leading-relaxed font-mono italic">
                 PROTECTIVE PROTOCOL: All biological data encrypted. Array scanning active.
              </p>
           </div>
        </div>
        <div className="lg:col-span-2 glass-card h-[600px] relative overflow-hidden bg-gradient-to-b from-transparent to-teal/5">
           <div className="absolute top-6 left-6 z-20">
              <div className="flex items-center gap-2 mb-2">
                 <div className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                 <span className="text-[10px] font-black text-red-500 uppercase tracking-widest">Live Bio-Scan</span>
              </div>
              <h3 className="text-xl font-black text-white italic tracking-tighter">ANATOMICAL ENGAGEMENT</h3>
           </div>
           <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-full h-full pointer-events-none opacity-20 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]" />
           </div>
        </div>
      </div>
    </section>
  );
};

export { BiologicalModel, BiologicalIntelligenceArray };
