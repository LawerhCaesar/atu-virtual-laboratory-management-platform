# Yankson follow-up release — 23 November 2026

The owner explicitly authorized pushing and deploying the local follow-up, superseding the original local-only publication constraint. The client uses the Render URL. The owner confirmed Atrax-R Workspace for this deployment.

Target: `atu-virtual-laboratory-staging`, service `srv-db81c4qvcj2c73fqrsc0`, workspace `tea-d09udfidbo4c73e46er0`, branch `main`, base commit `f87ed124198628c9d33f77cc418086f17fbc1ffd`. Render URL: https://atu-virtual-laboratory-staging.onrender.com . Automatic deployment is enabled after CI checks pass.

The release includes the simplified/resizable three-step workspace, current Start default, measured timer/reset fixes, separate real-time controller source labels, microphone visibility, visible Test spoken command diagnostic, practice-aware identity guidance, updated learning guide and separate reported historical evidence. The controller equations and authentication/CAN/starter supervision remain unchanged. Actual new human Start recognition is not yet verified.

The deployment-readiness change adds content fingerprints to nested module imports and guide JSON/PDF URLs using the generated source manifest. Top-level CSS/scripts already use Django static manifests in production. Nested browser imports previously used stable paths and could reuse an older workbench during a new release. Cold/reload checks verify the resolved URLs and persistent new layout. This is a cache-consistency safeguard; the exact cause of the client's flash was not independently observed.

Before release, all 333 non-browser tests passed, asset generation reproduced tracked bundles, Django system and migration checks passed, and whitespace checks passed. The complete affected browser suite and new release smoke tests are recorded separately in local test logs. A successful code push or deploy trigger alone is not proof that Render is live: verification requires the specific deploy reaching live and public readiness/source checks.

Earlier local review reports describe their then-current no-publication state; this document records the owner's subsequent publication authorization. Original historical trial exports are not rewritten.

Production static collection succeeded and produced hashed top-level CSS/JS. The release-version cold/reload test and both desktop/mobile binary/guide accessibility checks passed (3 cases in 47.68 s) after correcting legacy test expectations. Initial failures and their corrections are retained in local logs. The separate complete affected browser run was already collected with the earlier assertions and continues for the remaining regressions; CI will run the corrected suite from the published commit.

## CI findings and release correction

The first published run (45158681118, commit 601c62e) completed with 303 browser passes and three failures after a serial 65-minute browser stage. Render did not deploy that failed run. The generic all-module reset audit was not opening Yankson's newly collapsed controls; its navigation now waits for module readiness and opens those sections. The staff/student exercise test exposed delayed workspace initialization behind guide/GPU loading; the critical workspace now mounts first, hides legacy source HTML until ready and reports initialization errors without exposing a fallback layout. Guide loading and 3D initialization follow asynchronously. The BrakeLab preference test now uses the normal browser render clock so native media-query change delivery is checked without fake-clock scheduling interference. No BrakeLab equations or control policy changed.

The three failing cases and the relevant Yankson behaviors passed in a 20-case local rerun (131.19 s). Three additional boot/reload/error-path cases passed (16.52 s), including a deliberately delayed guide and aborted module load. The updated workflow runs all 308 collected browser cases in eight isolated PostgreSQL-backed jobs. Collection manifests prove eight disjoint partitions of 38–39 cases each, with no omissions or duplicates. The unit and production-profile checks remain required, and Render still waits for all CI checks to pass.
