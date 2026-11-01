package com.littleweather;

import net.minecraft.world.level.Level;

import java.lang.reflect.Method;

/**
 * Reads the time of day of the Overworld (0..23999, 0 = sunrise, 6000 = noon, 12000 = sunset, 18000 = midnight).
 *
 * Minecraft has been moving its time API around (day time vs. world clocks), so the accessor is looked up by name once
 * instead of being hard-wired. If none of the known accessors exists the game time is used, which matches the day
 * time on any world where the daylight cycle was never changed. Once the project has been compiled against 26.3 this
 * can be replaced by a direct call.
 */
public final class SkyClock {
	private static final String[] CANDIDATES = {"getDayTime", "getOverworldClockTime", "getDefaultClockTime", "getClockTime"};
	private static Method accessor;
	private static boolean searched;

	public static int timeOfDay(Level level) {
		long t = rawTime(level);
		return (int) (((t % 24000L) + 24000L) % 24000L);
	}

	private static long rawTime(Level level) {
		if (!searched) {
			searched = true;
			for (String name : CANDIDATES) {
				try {
					Method m = Level.class.getMethod(name);
					if (m.getReturnType() == long.class) {
						accessor = m;
						break;
					}
				} catch (ReflectiveOperationException | LinkageError ignored) {
					// try the next name
				}
			}
			if (accessor == null) {
				LittleWeatherMod.LOGGER.warn("No day-time accessor found on Level, falling back to game time.");
			}
		}
		if (accessor != null) {
			try {
				return (long) accessor.invoke(level);
			} catch (ReflectiveOperationException | RuntimeException e) {
				accessor = null;
			}
		}
		return level.getGameTime();
	}

	private SkyClock() {
	}
}
