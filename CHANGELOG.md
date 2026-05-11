
## [1.6.0] - 2026-05-11 (STABLE PRODUCTION BASELINE)
### Added
- **Finalized Stable UI/UX:** Established the definitive baseline for all core modules. **This is the version to revert to for future stable builds.**
- **Individualized FAQ Cards:** Premium knowledge hub with category-specific icons, glowing accents, and fluid drop-down animations.
- **Fear Index Restoration:** Re-integrated the tactical sentiment monitor with historical vote persistence.
- **Vessel Telemetry 2.0:** High-fidelity ship status cards with real-time speed, uplink, and signal stream.
- **Case Progression Analytics:** Log-scale timeline chart comparing current outbreak to historical COVID-19 data.

### Changed
- **Optimized Dashboard Layout:** Reordered hierarchy to Stats -> Fear -> Spread -> News -> Map -> FAQ.
- **Data Migration:** Successfully merged legacy FAQ and sentiment data into the new persistent KV store.
- **Rendering Engine:** Switched to `st.html()` for FAQ cards to ensure perfect visual fidelity across all browsers.

## [1.5.0] - 2026-05-11
### Added
- **Stable Maps & Ship Status Baseline:** Locked in the high-fidelity map architecture and compact vessel telemetry.
- **Mission Control v28.1:** Finalized the "Everyday User" upgrade with simplified terminology and bright readability.
- **Compact Telemetry Grid:** Optimized real-time ship signals card for high-density space efficiency.
- **Methodology Disclosures:** Transparent labeling for Verifiable vs. Non-Verifiable (Proximity-Based) data regions.

### Changed
- **Terminology Refactor:** Replaced technical jargon with accessible terms (e.g., 'Risk' -> 'Chance of Spread', 'Mission Control' -> 'Global Health Monitor').
- **High-Visibility Tooltips:** Enlarged briefing text and calculation formulas for immediate data recognition.

### Removed
- **Expert Discussion Room:** Removed the experimental War Room feature to declutter the user experience.
- **Sentiment Complexity:** Reverted complex fear-index analysis in favor of stable, deterministic risk models.


## [1.4.0] - 2026-05-11
### Added
- **Interactive Relational Map:** Added a high-fidelity global map tracking vessel telemetry and outbreak hotspots.
- **Mobile-Responsive Map Toggle:** Implemented a floating "📡 SHIP DATA" button to toggle overlays on small screens.
- **Live OSINT Signal Feed:** Integrated a real-time news scroller directly into the map interface.

### Changed
- **Journalist Tools Data:** Added `passengers` and `crew` metrics to nationality data to support detailed reporting.
- **Version Branding:** Updated application header to display `v1.4.0`.

### Removed
- **Community Intel Panel:** Removed the experimental "Tactical Intel" / Sentiment Velocity section to streamline the dashboard focus.

## [1.3.1] - 2026-05-09
### Added
- **Ultra-Compact Sentiment Tiles:** Redesigned sentiment selector with high-intensity neon glow and radial hover effects.
- **Mobile-First Vertical Grid:** Dynamic layout engine that forces vertical stacking on mobile browsers for optimal touch engagement.
- **Instant Vote Registration:** Zero-latency voting logic using prioritized session-state updates.
- **Highlighted CTA:** High-visibility cyan glow for the "TAP TILE TO VOTE" prompt with critical importance mention.

### Fixed
- **Ghost Box Artifacts:** Eliminated residual Streamlit button borders and outlines.
- **Skull Icon Backgrounds:** Resolved background artifacts on emoji icons in mobile view.
- **Label Truncation:** Forced 'white-space: nowrap' on sentiment labels to prevent clipping.

## [1.3.0] - 2026-05-09
### Added
- **Sidebar Command Center:** Physical-feel tile grid with Luxury Gold hover animations.
- **Memory Guardrail System:** Incremental ingestion and 30-minute watchdog.
- **Visual Hierarchy 2.0:** Mega-Glow Title and Critical Alert Badge.

## [1.2.0] - 2026-04-20
### Added
- **Intelligence Sharing Suite:** Direct share buttons for X, LinkedIn, and WhatsApp.
- **Situation Reports:** Automated situational summaries in PDF/TXT format.

## [1.1.0] - 2026-03-15
### Added
- **Qdrant Cloud Integration:** Transitioned to hosted vector storage.
- **Contextual Recommendation Engine:** Mapping related research via Qdrant API.
- **Semantic Alerting:** Push notifications for critical research keywords.
