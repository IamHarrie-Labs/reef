# Reef landing art direction

Original Reef imagery generated with the built-in image-generation tool. Agora informed the use of atmosphere, product detail and varied section scales. No Agora images, marks or financial claims were reused.

## Assets

- `evidence-island.png`: master. Production: `web/public/art/evidence-island.webp`, 1200 pixels wide.
- `research-archive.png`: master. Production: `web/public/art/research-archive.webp`, 1000 pixels wide.

Both use warm stone, forest-green glass, ivory paper and soft directional daylight. The artwork expresses research depth and recorded reasoning. All product labels and figures are live HTML, not generated image text.

## Final prompts

### Evidence island

Original website brand artwork for Reef, an institutional financial research desk. A beautifully crafted sculptural cutaway of a circular island: four organic pale limestone landforms separated by deep winding channels of translucent forest-green glass water, floating above three thin offset horizontal layers of warm stone and smoked glass. Represents looking beneath the surface and inspecting layers of evidence. Premium architectural model photography, extraordinary tactile detail, refined art direction, soft upper-left daylight and long shadows on warm ivory seamless backdrop. Slightly elevated three-quarter camera, entire sculpture visible, landscape 3:2 composition, object occupies central 70 percent. Palette cream #faf8f5, dark forest #2d3a2e, muted sage. No text, numbers, charts, logos, coins, cryptocurrency symbols, people or watermarks. Quiet confidence, precision, editorial financial brand.

### Research archive

Original editorial brand artwork for Reef institutional research software. Macro architectural product photograph of an elegant archive: three offset warm ivory paper sheets with subtle blind-embossed fine horizontal lines, a smoked forest-green glass slab hovering slightly above them, and a small circular pale limestone seal resting on top, seal surface carved into four organic landforms separated by winding river channels. No readable writing, no numbers, no logo lettering. Premium tactile paper grain, polished green glass edge, raking soft daylight from upper left, beautiful precise shadows, warm cream seamless studio background. Slightly overhead three-quarter camera, landscape 3:2 composition with generous margins around object. Quiet refined editorial feel, palette #faf8f5 #2d3a2e muted sage. No digital screens, padlocks, crypto coins, charts, people or watermarks.

## Composition and motion refinement

The hero snapshot card was removed to focus the first screen on the product and entry action. The landscape overlay now protects copy on the left while revealing more detail on the right. The evidence island uses an organic curved crop and thin orbital outline. The archive uses a transparent cutout on white with the same orbital motif; explanatory cards were removed to keep the artwork unobstructed. IntersectionObserver triggers one-time side entrances and text reveals. CSS disables motion for reduced-motion preferences; content stays visible if IntersectionObserver is unavailable. Desktop and 375-pixel mobile layouts were inspected, and animation overflow was corrected with clipping on the landing wrapper.

## Archive transparent cutout

Built-in image-generation edit of `research-archive.png`, with transparent background enabled. Master: `research-archive-cutout.png`. Production: `web/public/art/research-archive-cutout.webp`, 1000 pixels wide, alpha channel preserved.

Final edit prompt:

Remove only the entire beige studio background, surface and background shadows from this original Reef archive artwork. Preserve the complete stack of ivory paper, forest-green glass plate and carved circular limestone seal, original camera angle, lighting, material detail, all object edges and proportions. Create a clean isolated cutout on a genuinely transparent background. Do not crop any object, change the composition, add text or add new objects. Keep natural shadows between the paper layers and glass. Transparent output for placement on a white website section.
