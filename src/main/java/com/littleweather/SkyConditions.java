package com.littleweather;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;

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

		// 1) Rain: needs rain that really falls on this spot (biomes without rain never qualify).
		if (level.isRaining()) {
			if (level.isRainingAt(head)) {
				return Result.of(JarKind.RAIN);
			}
			return Result.fail("message.littleweather.not_clear");
		}

		LittleWeatherConfig cfg = LittleWeatherConfig.get();
		int t = SkyClock.timeOfDay(level);

		// 2) Sunset: inside the configured capture window.
		if (LittleWeatherConfig.inWindow(t, cfg.sunsetStart, cfg.sunsetEnd)) {
			return Result.of(JarKind.SUNSET);
		}
		// 3) Stars: clear (no rain, no thunder) and dark enough.
		if (LittleWeatherConfig.inWindow(t, cfg.nightStart, cfg.nightEnd)) {
			if (level.isThundering()) {
				return Result.fail("message.littleweather.not_clear");
			}
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

	private SkyConditions() {
	}
}
