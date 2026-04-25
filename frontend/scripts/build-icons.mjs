/**
 * Rasterize `public/brand/bytloop-mark.svg` into app and browser icons.
 *
 * | Output                 | Where used |
 * |------------------------|------------|
 * | `favicon.ico`          | Classic `/favicon.ico` (tab, bookmarks; multi-size 16+32) |
 * | `icon-192.png`         | PWA manifest, `metadata` fallback, some Android |
 * | `icon-512.png`         | PWA install / splash, manifest |
 * | `apple-touch-icon.png` | iOS / Safari "Add to Home", `metadata.apple` |
 * | (keep `bytloop-mark.svg` for crisp rel=icon where supported) — wired in `seo.ts` |
 *
 * Run: `pnpm run build:icons` (from `frontend/`)
 * Commit the generated files so CI/production need not run this unless SVG changes.
 */

import { writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";
import toIco from "to-ico";

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = join(__dirname, "..", "public");
const svgPath = join(publicDir, "brand", "bytloop-mark.svg");

const DENSITY = 400;

/**
 * @param {number} size
 * @param {import('sharp').ResizeOptions} [options]
 */
function pngAt(size, options) {
  return sharp(svgPath, { density: DENSITY })
    .resize(size, size, {
      fit: "contain",
      background: { r: 0, g: 0, b: 0, alpha: 0 },
      ...options,
    })
    .png();
}

async function main() {
  const icon192 = await pngAt(192).toBuffer();
  const icon512 = await pngAt(512).toBuffer();
  const apple180 = await pngAt(180).toBuffer();
  const f32 = await pngAt(32).toBuffer();
  const f16 = await pngAt(16).toBuffer();

  await writeFile(join(publicDir, "icon-192.png"), icon192);
  await writeFile(join(publicDir, "icon-512.png"), icon512);
  await writeFile(join(publicDir, "apple-touch-icon.png"), apple180);

  // ICO: 32 then 16 (largest first)
  const ico = await toIco([f32, f16]);
  await writeFile(join(publicDir, "favicon.ico"), ico);

  console.log(
    "Wrote public/favicon.ico, icon-192.png, icon-512.png, apple-touch-icon.png (from brand/bytloop-mark.svg).",
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
