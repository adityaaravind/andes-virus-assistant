# 🧬 Andes Virus Research Assistant `v1.3.0 Stable`

**Real-time AI Outbreak Intelligence for the MV Hondius Hantavirus Incident.**

[![Deployment](https://img.shields.io/badge/Deploy-Streamlit%20Cloud-FF4B4B?logo=streamlit)](https://andes-virus-assistant.streamlit.app/)
[![Stable Version](https://img.shields.io/badge/Release-v1.3.0-00b4d8?logo=github)](https://github.com/adityaaravind/andes-virus-assistant/releases/tag/v1.3.0)

---

## 🚀 The Intelligence Platform

Andes Virus Assistant is a high-performance RAG (Retrieval-Augmented Generation) application designed to bridge the gap between technical epidemiology and real-time news monitoring. Built for researchers, journalists, and public health officials tracking the **MV Hondius Outbreak**.

### 🛡️ Core Capabilities

<table style="width: 100%; border-collapse: collapse;">
<tr>
<td width="50%" style="border: none; padding: 10px;">
<div style="background: rgba(0, 180, 216, 0.08); border: 1px solid #00b4d844; border-radius: 12px; padding: 1.5rem; height: 160px;">
<p style="color: #00b4d8; font-weight: 800; font-size: 0.9rem; margin-top: 0; text-transform: uppercase;">🤖 RESEARCH RAG ENGINE</p>
<p style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5;">Ask complex questions. Get answers cited directly from WHO SITREPs, CDC guidance, and PubMed abstracts.</p>
</div>
</td>
<td width="50%" style="border: none; padding: 10px;">
<div style="background: rgba(255, 215, 0, 0.08); border: 1px solid #ffd70044; border-radius: 12px; padding: 1.5rem; height: 160px;">
<p style="color: #ffd700; font-weight: 800; font-size: 0.9rem; margin-top: 0; text-transform: uppercase;">🧭 COMMAND CENTER (v1.3)</p>
<p style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5;">Luxury-gold sidebar interface with touch-optimized, animated tiles for rapid navigation through intelligence blocks.</p>
</div>
</td>
</tr>
<tr>
<td width="50%" style="border: none; padding: 10px;">
<div style="background: rgba(239, 68, 68, 0.08); border: 1px solid #ef444444; border-radius: 12px; padding: 1.5rem; height: 160px;">
<p style="color: #ef4444; font-weight: 800; font-size: 0.9rem; margin-top: 0; text-transform: uppercase;">📈 RISK & FEAR INDEX</p>
<p style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5;">Real-time epidemiologic weighting blended with AI-driven media sentiment analysis and community voting.</p>
</div>
</td>
<td width="50%" style="border: none; padding: 10px;">
<div style="background: rgba(34, 197, 94, 0.08); border: 1px solid #22c55e44; border-radius: 12px; padding: 1.5rem; height: 160px;">
<p style="color: #22c55e; font-weight: 800; font-size: 0.9rem; margin-top: 0; text-transform: uppercase;">🧠 STABILITY WATCHDOG</p>
<p style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5;">Memory-aware guardrails preventing crashes in low-RAM (1GB) environments via incremental ingestion.</p>
</div>
</td>
</tr>
</table>

---

---

## 📜 v1.3.0: The "Command & Stability" Update

Our most significant leap in UX and performance to date.

- **[NEW] Sidebar Command Center:** A physical-feel tile grid with `Luxury Gold` hover animations and smooth-scrolling anchors.
- **[NEW] Memory Guardrail System:**
    *   **Incremental Ingestion:** Source processing (PubMed → WHO → News) is now sequential and memory-cleared, eliminating cold-start RAM spikes.
    *   **30-Minute Watchdog:** A background system monitor that detects high RAM usage and forces global garbage collection.
    *   **Analytics Cap:** Aggressive local file management for `streamlit-analytics2` to maintain sub-3MB memory footprint.
- **[NEW] Visual Hierarchy 2.0:** 
    *   **Mega-Glow Title:** Bioluminescent pulsing branding for maximum user engagement.
    *   **Critical Alert Badge:** Pulsing red "Outbreak Active" indicator with neon bloom effects.
- **[NEW] Liquid Mobile Responsiveness:** Dynamic layout logic that reconfigures the UI for iPhone/Android (3-column tile grids, fluid typography).

---

## 📜 Historical Milestones

### v1.2.0: User Engagement Update
- **Intelligence Sharing Suite:** Direct share buttons for Twitter/X, LinkedIn, and WhatsApp.
- **Situation Reports:** Automated PDF/TXT situational summaries for journalists.
- **Visual Polish:** Implementation of the "Active Outbreak" aesthetic and initial glowing title classes.

### v1.1.0: Active Intelligence Update
- **Qdrant Cloud Integration:** Transitioned to hosted vector storage for 24/7 reliability.
- **Contextual Recommendation Engine:** Leveraging Qdrant’s Recommendation API to map related research.
- **Semantic Alerting:** Automatic push notifications via `ntfy.sh` when critical research keywords are indexed.

---

## 🛠️ Technology Stack

- **Framework:** Streamlit (Custom Navy/Teal Design System)
- **AI Orchestration:** LangChain + OpenAI GPT-4o-mini
- **Vector Database:** Qdrant Cloud (v1.1 with Recommendation Engine)
- **Memory Management:** psutil + Garbage Collection (GC) watchdog
- **Analytics:** streamlit-analytics2 (Persistent Qdrant-backed KV storage)

---

## ⚠️ Disclaimer
*This tool is for research and informational purposes only. It is not a substitute for professional medical advice. For emergencies, contact your local health authorities.*

---

**Developed with ❤️ by [Aditya Aravind Medepalli](https://www.linkedin.com/in/adityaaravindm/)**
