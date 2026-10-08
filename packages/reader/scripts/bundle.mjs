// Builds the self-contained browser bundle that the renderer/publisher inline
// into exported HTML (window.DocMorphReader).
import { build } from "esbuild";

await build({
  entryPoints: ["src/browser.ts"],
  outfile: "dist/reader.global.js",
  bundle: true,
  format: "iife",
  minify: true,
  target: ["es2020"],
  legalComments: "none",
});
