import React, { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import MainHub from './ui/MainHub'
import SurveillanceHub from './ui/SurveillanceHub'
import IntelHub from './ui/IntelHub'
import OceanXEngine from './components/OceanXEngine'
import { BiologicalModel, BiologicalIntelligenceArray } from './components/BiologicalIntelligenceArray'
import './index.css'

const BackgroundCanvas = () => {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none">
      <Canvas
        camera={{ position: [0, 5, 20], fov: 75 }}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <OceanXEngine />
          <group position={[10, -5, 0]} rotation={[0, -Math.PI / 4, 0]}>
             <BiologicalModel activeCase={1} />
          </group>
        </Suspense>
      </Canvas>
    </div>
  )
}

function App() {
  return (
    <div className="relative h-screen w-full bg-navy text-white selection:bg-teal selection:text-navy overflow-hidden">
      
      <BackgroundCanvas />

      <main className="absolute inset-0 z-10 pointer-events-none">
        <div className="w-full h-full relative pointer-events-auto">
            <MainHub />
            
            <div className="absolute top-6 right-6 flex flex-col gap-4 w-96">
              <BiologicalIntelligenceArray />
              <div className="h-[300px]">
                  <SurveillanceHub />
              </div>
            </div>

            <div className="absolute bottom-6 left-6 w-[500px]">
              <IntelHub vibe="os" />
            </div>
        </div>
      </main>

      {/* TOP DECORATIVE BAR */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-teal to-transparent opacity-50 z-50" />
      
      {/* STATUS FOOTER */}
      <div className="absolute bottom-0 right-0 p-2 z-50">
        <p className="text-[8px] font-mono text-gray-600 uppercase tracking-widest">Standalone Engine v1.0.0 // Andes RTS</p>
      </div>
    </div>
  )
}

export default App
