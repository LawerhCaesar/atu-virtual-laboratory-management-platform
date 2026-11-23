# Yankson public/local version check — 23 November 2026

The owner reports that a client sees follow-up changes briefly and then the former layout returns. The exact client URL and a browser trace have been requested but not yet supplied.

The public static endpoints at `https://atuvirtuallab.com/static/js/yankson/` returned HTTP 200 for practical.js, workbench.mjs and build.js. All three hashes differ from the local follow-up. The public workbench does not include the new Test spoken command control. Requests included Cache-Control: no-cache. Responses advertise max-age=60, public. The comparison is saved at `test-results/yankson-live-version-check/public-vs-local.json`.

This confirms the public static source differs from the unpushed local follow-up. It does not establish the exact cause of the reported visual flash, which still requires the client's exact URL/browser observation. Source inspection also confirms that the template renders the older starting desk and teaching.mjs later mounts workbench.mjs; that progressive rearrangement can create a visual transition while modules load.

The current local branch remains codex/yankson-ui-follow-up, based on f87ed12, with local working-tree changes. No upstream publication or deployment was made: the supplied follow-up explicitly instructed local source or fork only and no push to the owner's upstream repository. A change to that publication constraint is needed before pushing/deploying this release. The local review package and the passing software checks remain available for review; actual human speech acceptance is still pending.
