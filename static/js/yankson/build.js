window.YanksonBuild = {
  "scope": "Reviewed source assets; runtime deployment commit is reported separately.",
  "baseCommit": "05d72ec5a4a626f35060b7ab0b334eed799b5b66",
  "sha256": {
    "boot.mjs": "7a0f347c03d95db6a11f3340ad4aaea07e420d7c21edf3020b4f63e36674ee93",
    "engine.js": "7e34037a0d2c797f9594d8a9cca8dcb43ca1e8f60336bac74da27dfdb1360279",
    "ui.js": "455193994ad72e09aa4fce943c563a3fbae68d55af05cdacc30b31e28556f8cd",
    "practical.js": "979215be7922205ea587a1bf84e6402e95f6b9612b18fac08326098a808ab707",
    "speech.js": "2bb85bb5377d8fb5ee6f93dcefd3e76ed6627e133e9203e0bc1c0927a1f75f1f",
    "evidence.js": "8df8a4aa5ba801283c1a5c26e8e892b2703660b0bce9afad313f8169e3e0666e",
    "teaching.mjs": "0959ad8a6105027b71a56d47790e75c1326b198b81378a53befabfcd4122499d",
    "workbench.mjs": "caeee144bd506e4977036f05140c3111c4e2b0e238c2aae9e1a1df19988fb56f",
    "microphone.mjs": "4368d970e77d009c2a4b012160a5d97394eb56fd6b4e3bdc1be3b3feb8e99beb",
    "devices.js": "b260381f0c850d0b0a9d4c881b957678118b8dc90f32eff518cf141e2812d3df",
    "experiments.mjs": "ffd1b26d2bc86fe3a9680adefc596357452c30da0d2b8ed0782f81661cdde1f1",
    "layout.mjs": "089e006686dbc16915c622ae99d7156af1151274a32938e1b896270412140c8c",
    "electrical.mjs": "12b7c5b4a7ba4ae0cd269faa0dbe3890d1733bd261e4d19cdc260619b61c8afd",
    "guide.mjs": "986f627ae0c5ae65eab6e919913279288471171076cfe41138f51e4403d86d5c",
    "engine-stand.bundle.mjs": "92552819274ddfbbbfe1a9a5fa6b1f8677f5381636d49b00d26089239753e8db",
    "learning-guide.json": "feb822f2adfa032ba5dc3a9845ee309edd215d216f83a5a4fb62016ba6271d19",
    "authenticated-starting-learning-guide.pdf": "63b8f3455ac2415a7d3671bd4e3bad5ed6cec430eb577f49d1578bfac18a4dd8"
  }
};
// Nested ES modules and guide data must use this release's content fingerprints too.
window.YanksonAssetURL = (name, base) => {
  const url = new URL(name, base);
  const hash = window.YanksonBuild.sha256[url.pathname.split('/').pop()];
  if (hash) url.searchParams.set('v', hash);
  return url.href;
};
