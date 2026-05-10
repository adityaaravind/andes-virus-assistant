import React, { useRef, useMemo, Suspense, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF, Environment, Stars, useScroll, MeshDistortMaterial, ContactShadows, Sky } from '@react-three/drei';
import * as THREE from 'three';

// Locally hosted OceanX ship model
const OCEANX_SHIP_URL = "/models/ship.glb";

const MVHondiusModel = () => {
  const { scene } = useGLTF(OCEANX_SHIP_URL);
  const clonedScene = useMemo(() => scene.clone(), [scene]);

  useEffect(() => {
    clonedScene.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        if (child.material) {
          child.material.metalness = 0.8;
          child.material.roughness = 0.2;
        }
      }
    });
  }, [clonedScene]);

  return <primitive object={clonedScene} scale={0.015} rotation={[0, Math.PI, 0]} />;
};

const OceanXEngine = () => {
  const shipContainerRef = useRef();
  // Safe access to useScroll - if not in ScrollControls context, it returns an empty object
  let scroll = {};
  try {
    scroll = useScroll();
  } catch (e) {
    // Ignore context error
  }

  useFrame((state) => {
    const offset = scroll.offset || 0;
    
    // Command Center fixed camera if no scroll
    if (!scroll.offset) {
      state.camera.position.set(12, 8, 12);
      state.camera.lookAt(0, 0, 0);
    } else {
      // Cinematic camera path for scrolling vibes
      const angle = offset * Math.PI * 0.4;
      const radius = 22 - (offset * 18); 
      state.camera.position.x = Math.sin(angle) * radius;
      state.camera.position.z = Math.cos(angle) * radius;
      state.camera.position.y = 10 - (offset * 8.5); 
      state.camera.lookAt(0, 0.5, 0);
    }

    // Ship buoyancy
    if (shipContainerRef.current) {
       const t = state.clock.getElapsedTime();
       shipContainerRef.current.position.y = Math.sin(t * 1.0) * 0.12;
       shipContainerRef.current.rotation.z = Math.cos(t * 0.7) * 0.03;
    }
  });

  return (
    <group>
      {/* Tactical Dark Sky */}
      <Stars radius={100} depth={50} count={5000} factor={2} saturation={0} fade speed={0.5} />
      <Environment preset="night" />
      
      <ambientLight intensity={0.05} />
      <pointLight position={[10, 10, 10]} intensity={1} color="#00b4d8" />
      <spotLight position={[-10, 20, 10]} angle={0.15} penumbra={1} intensity={1} color="#ffffff" castShadow />

      <group ref={shipContainerRef}>
         <Suspense fallback={null}>
            <MVHondiusModel />
         </Suspense>
         <ContactShadows resolution={1024} scale={20} blur={2} opacity={0.5} far={10} color="#000000" />
      </group>

      {/* Tactical Grid Sea */}
      <mesh rotation-x={-Math.PI / 2} position={[0, -0.05, 0]} receiveShadow>
        <planeGeometry args={[200, 200, 64, 64]} />
        <meshStandardMaterial
          color="#050505"
          metalness={1}
          roughness={0.1}
          wireframe={false}
        />
      </mesh>
      
      {/* Radar Circles */}
      {[5, 10, 15, 20].map((r, i) => (
        <mesh key={i} rotation-x={-Math.PI / 2} position={[0, 0.01, 0]}>
          <ringGeometry args={[r, r + 0.05, 64]} />
          <meshBasicMaterial color="#00b4d8" transparent opacity={0.1} />
        </mesh>
      ))}
    </group>
  );
};

export default OceanXEngine;
