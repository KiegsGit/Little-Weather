# Changelog

Newest first. Every update gets a new version number, an entry here, and its own release notes file
(`.github/changes/<number>.md`), written as NEW / FIXED / CHANGES.

## v2

### NEW
- **Snow Jar**: catch real snowfall in a cold biome. A tiny cloud with drifting flakes and a little snowy ground.
- **Storm Jar**: catch a thunderstorm. A dark cloud, driving rain and a flash of lightning inside the jar.
- **Hanging jars**: click the underside of a block to hang any jar from a twine loop, like a lantern. Click the top or side of a block to stand it up as before.
- **New art**: all jars were redrawn at higher resolution with soft lighting. Real glass with an edge, reflections and bubbles, a cork, a satin bow, and smoothly animated contents: twinkling stars with a moon and shooting star, a drifting rain cloud, a sunset over silhouetted hills, falling snow, lightning.
- **Custom sounds**: a soft glass chime and a cork pop when you catch the sky.
- **Tooltips**: every jar tells you what it is.
- **Advancements**: *A Jar for the Sky*, *Caught Something* and *Sky Collector* (own all five jars).
- New ambient particles for snow and storms.

### FIXED
- Fixed the v1 build error: a jar is now dropped at your feet when your inventory is full instead of calling a method that no longer exists in 26.3.
- Jars now need support: they can no longer float, and they drop as an item if the block under or above them is removed (this can take a moment).

### CHANGES
- Rain jars: a thunderstorm now gives a Storm Jar. Ordinary rain still gives a Rain Jar.
- Jar models are slimmer and taller, with a shoulder, neck, lip, cork and ribbon.
- Placed jars can only be put on or under a block that can carry them.
- Capture sounds are now Little Weather's own.

## v1

### NEW
- **Empty Weather Jar**: right-click to catch the sky. Craftable from glass panes, planks and one amethyst shard.
- **Star Jar**: catch a clear, dark night sky with open sky above you. Twinkling animated stars, the brightest glow of the three.
- **Rain Jar**: catch real rain that falls on your spot. A tiny cloud with animated raindrops.
- **Sunset Jar**: catch the evening glow. A swirl of orange, gold and pink that slowly shifts tone.
- Every filled jar is a placeable decorative block with its own glass model, animated contents, soft light and ambient particles (twinkles, droplets, drifting sunset motes). Breaking one drops it again.
- Failed captures keep your jar and tell you what is missing in the action bar.
- `config/littleweather.json`: sunset window, night window and use cooldown.

### FIXED
- Nothing yet. This is the first release.

### CHANGES
- First public version. Every update gets its own release (v1, v2, v3, ...). Old releases are kept.
