---
schemaVersion: 1
scope: workspace
updatedAt: "2026-05-12T18:27:30.605Z"
workspaceName: "andes-virus-assistant"
---

# Project Memory

## Project Overview
- Website redesign project for Andes Virus Assistant / Hanta virus tracking public-health dashboard.
- User wants UI-only improvements to increase retention and make the site feel top-tier for Hanta virus tracking.
- Features must not be updated, deleted, or functionally changed.
- The existing map must remain unchanged.
- Target areas remain: stat cards, Public Worry Index, Global Pandemic Tracker, news filter, FAQ, and overall dashboard hierarchy.
- Streamlit compatibility is an important project constraint because the live site is a Streamlit app.

## Current State
- Active source candidate is `App.jsx`.
- `App.jsx` is a previewable React mockup for design verification, not confirmed as the production Streamlit source.
- A second alternate redesign has been created in a “public-health Signal Desk” direction.
- Latest alternate preview verification passed with no syntax, console, asset, or runtime issues.
- `DESIGN.md` exists again as a minimal design-system/design-direction baton for the alternate Streamlit-safe direction.
- Prior `streamlit_app.py` was referenced as a possible Streamlit implementation but has not been found in the available workspace.
- Production Streamlit implementation should still wait until the actual deployed source/entrypoint is located.

## Artifacts
- `App.jsx`: Current previewable React mockup for the alternate Hanta tracking dashboard UI; used for design verification, not yet confirmed as production source.
- `DESIGN.md`: Authoritative design-system/design-direction artifact for this project.
- `UI_REDESIGN_PLAN.md`: UI-only audit and redesign plan focused on retention, hierarchy, trust, and Streamlit-compatible execution.
- `ui-tweak-controls.js`: Tweakable UI token/control file from earlier iteration.
- `.streamlit/config.toml`: Streamlit configuration present in repo.
- `.streamlit/secrets.toml`: Present but must not be copied or exposed.
- `streamlit_app.py`: Previously referenced as a main Streamlit implementation, but not found in the latest available workspace.

## Design Direction
- Current approved-for-preview direction is an alternate “public-health Signal Desk” layout.
- Emphasizes anchored navigation, strong worry-index/status summary, protected unchanged map framing, regional tracker cards, news filters, and FAQ modules.
- Professional, calm, trustworthy public-health dashboard style with stronger editorial hierarchy and decision-support framing.
- Preserve all existing features and the map behavior/appearance.
- Improve retention through clearer hierarchy, stronger first impression, better scanability, and credible dashboard modules.
- Favor Streamlit-compatible CSS/layout wrappers around existing widgets, containers, and outputs.
- Keep the map visually isolated/framed as a protected area rather than redesigning or changing it.

## User Feedback
- “Please check through the website for the UI related issues and make a plan to fix them.”
- “I need high user retention for my site.”
- “I do not need any updates or deletion on the features.”
- “I just want a redesign of the UI.”
- User wants the site positioned as a top Hanta virus tracking experience.
- Earlier explicit constraint: redesign UI but do not change the map.
- User asked to see designs for verification and whether changes can be made if approved.
- Latest request: inspect the site and redesign again in a different way, ensuring it is Streamlit compatible.

## Decisions
- Scope remains UI-only: no feature deletion, no data-model changes, no functional changes, and no map changes.
- Treat `DESIGN.md` as the authoritative design-system source.
- React `App.jsx` is acceptable as a visual verification artifact, but not yet confirmed as the live app source.
- Use preview mockups for approval before applying to production Streamlit code.
- Alternate “Signal Desk” design direction is now the latest verified preview direction.
- Streamlit production implementation should use CSS/layout wrappers around existing Streamlit features rather than replacing logic.

## Open Questions
- Exact Streamlit production source file for the deployed site still needs to be located in the repo or restored if missing.
- Exact existing map implementation/integration point still needs to be identified before UI wrapper work.
- Whether `App.jsx` should be retained as a preview artifact, replaced, or ignored depends on the repo’s actual deployment path.
- Final live data sources for pandemic stats, news, tracker data, and FAQ content are not confirmed.
- User approval or requested revisions are still needed after reviewing the alternate preview.

## Next Steps
- Wait for the user to review the latest `App.jsx` alternate dashboard preview and confirm preferred direction or revisions.
- If approved, locate the actual Streamlit entrypoint used by `https://andes-virus-assistant.streamlit.app`.
- Apply the approved UI redesign to the Streamlit app without changing features, data logic, or map behavior.
- Keep the map component/render unchanged and only adjust surrounding layout/framing if needed.
- Test locally with the correct Streamlit command after source is located.
- Keep `DESIGN.md` updated only with stable visual/system decisions.

## Promotion Candidates For DESIGN.md
- “Signal Desk” layout direction: anchored navigation, status summary, protected map, regional tracker, news filters, and FAQ modules.
- Protected map region pattern: map remains unchanged and visually framed as its own trusted surface.
- Streamlit-safe implementation pattern: CSS/layout wrappers around existing widgets and containers.
- Public-health tone: calm, trustworthy, readable, decision-support oriented.
- Retention-focused hierarchy: strong status summary, scannable metrics, clear section ladder, accessible controls.

## Recent History
- 2026-05-12: User requested site/repo review and a UI-only plan for improving retention without changing or deleting features.
- 2026-05-12: Created `UI_REDESIGN_PLAN.md`, `DESIGN.md`, and `ui-tweak-controls.js`.
- 2026-05-12: User asked to see designs for verification and asked if changes can be made if approved.
- 2026-05-12: Added a previewable Hanta virus tracking dashboard concept in `App.jsx`.
- 2026-05-12: Preview verification completed successfully with no console, asset, syntax, or runtime issues.
- 2026-05-12: User asked where they can preview it; rendered the `App.jsx` preview successfully.
- 2026-05-12: User requested a different redesign and Streamlit compatibility.
- 2026-05-12: Inspected workspace and current `App.jsx`; `DESIGN.md` was missing in that workspace state.
- 2026-05-12: Reworked `App.jsx` into an alternate “public-health Signal Desk” preview direction.
- 2026-05-12: Recreated minimal `DESIGN.md` for the alternate Streamlit-safe direction.
- 2026-05-12: Fixed duplicate component/runtime issue, reduced tweak controls to five, and verified final preview successfully.