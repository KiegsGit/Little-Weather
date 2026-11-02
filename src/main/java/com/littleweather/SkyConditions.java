package com.littleweather;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;

import java.lang.reflect.Method;

/** Decides, on the logical server, which sky moment (if any) the player can catch right now. */
public final class SkyConditions {
	/** Either a kind to capture, or the translation key of the reason why nothing can be captured. */
	public record Result(JarKind kind, String failKey) {
		public boolean ok() {
			return kind != null;
		}

		static Result of(JarKind kind) {
			return new Result(kind, null);
		}

		static Result fail(String key) {
			return new Result(null, key);
		}
	}

	public static Result evaluate(ServerLevel level, ServerPlayer player) {
		if (level.dimension() != Level.OVERWORLD) {
			return Result.fail("message.littleweather.need_overworld");
		}
		BlockPos head = BlockPos.containing(player.getEyePosition());
		if (!level.canSeeSky(head)) {
			return Result.fail("message.littleweather.need_sky");
		}

		// 1) Precipitation: rain (or a thunderstorm) that really falls on this spot, or snowfall in a cold biome.
		if (level.isRaining()) {
			if (level.isRainingAt(head)) {
				return Result.of(level.isThundering() ? JarKind.STORM : JarKind.RAIN);
			}
			if (isSnowingAt(level, head)) {
				return Result.of(JarKind.SNOW);
			}
			return Result.fail("message.littleweather.not_clear");
		}

		LittleWeatherConfig cfg = LittleWeatherConfig.get();
		int t = SkyClock.timeOfDay(level);

		// 2) Sunset: inside the configured capture window.
		if (LittleWeatherConfig.inWindow(t, cfg.sunsetStart, cfg.sunsetEnd)) {
			return Result.of(JarKind.SUNSET);
		}
		// 3) Stars: clear sky and dark enough.
		if (LittleWeatherConfig.inWindow(t, cfg.nightStart, cfg.nightEnd)) {
			return Result.of(JarKind.STAR);
		}

		// Nothing to catch: explain what to wait for.
		if (LittleWeatherConfig.inWindow(t, cfg.sunsetEnd, cfg.nightStart)) {
			return Result.fail("message.littleweather.stars_rising");
		}
		if (LittleWeatherConfig.inWindow(t, cfg.nightEnd, cfg.sunsetStart)) {
			return Result.fail("message.littleweather.daytime");
		}
		return Result.fail("message.littleweather.wrong_time");
	}

	// ---- snow detection -----------------------------------------------------------------------------------------
	// Biome/precipitation accessors changed between releases, so they are looked up by name once. When it is raining
	// but not at this spot, snow counts if the level reports SNOW precipitation, or else if the biome is cold.

	private static Method precipitationAt;
	private static Method baseTemperature;
	private static boolean searched;

	private static void search() {
		searched = true;
		try {
			precipitationAt = Level.class.getMethod("getPrecipitationAt", BlockPos.class);
		} catch (ReflectiveOperationException | LinkageError ignored) {
			precipitationAt = null;
		}
		try {
			baseTemperature = net.minecraft.world.level.biome.Biome.class.getMethod("getBaseTemperature");
		} catch (ReflectiveOperationException | LinkageError ignored) {
			baseTemperature = null;
		}
		if (precipitationAt == null && baseTemperature == null) {
			LittleWeatherMod.LOGGER.warn("No snow detection accessor found, Snow Jars cannot be caught.");
		}
	}

	static boolean isSnowingAt(ServerLevel level, BlockPos pos) {
		if (!searched) {
			search();
		}
		if (precipitationAt != null) {
			try {
				Object p = precipitationAt.invoke(level, pos);
				if (p != null) {
					return p.toString().equals("SNOW");
				}
			} catch (ReflectiveOperationException | RuntimeException ignored) {
				precipitationAt = null;
			}
		}
		if (baseTemperature != null) {
			try {
				Object biome = level.getBiome(pos).value();
				return ((Float) baseTemperature.invoke(biome)) <= 0.15f;
			} catch (ReflectiveOperationException | RuntimeException ignored) {
				baseTemperature = null;
			}
		}
		return false;
	}

	private SkyConditions() {
	}
}
