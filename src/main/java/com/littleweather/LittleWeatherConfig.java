package com.littleweather;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * config/littleweather.json. All times are ticks of the Overworld day (0 = sunrise, 6000 = noon, 12000 = sunset-ish,
 * 18000 = midnight). Values are sanity-checked on load, so a bad edit never breaks the game.
 */
public final class LittleWeatherConfig {
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static LittleWeatherConfig instance = new LittleWeatherConfig();

	/** First tick of the sunset capture window. */
	public int sunsetStart = 11800;
	/** Last tick of the sunset capture window. */
	public int sunsetEnd = 13600;
	/** First tick at which the sky is dark enough to catch stars. */
	public int nightStart = 13800;
	/** Last tick at which the sky is still dark enough to catch stars. */
	public int nightEnd = 22200;
	/** Ticks the Empty Weather Jar is on cooldown after every use (success or failure). */
	public int cooldownTicks = 20;

	public static LittleWeatherConfig get() {
		return instance;
	}

	public static void load() {
		Path file = FabricLoader.getInstance().getConfigDir().resolve("littleweather.json");
		LittleWeatherConfig loaded = null;
		if (Files.exists(file)) {
			try {
				loaded = GSON.fromJson(Files.readString(file), LittleWeatherConfig.class);
			} catch (IOException | RuntimeException e) {
				LittleWeatherMod.LOGGER.warn("Could not read {}, using defaults: {}", file, e.toString());
			}
		}
		instance = loaded != null ? loaded : new LittleWeatherConfig();
		instance.sanitize();
		try {
			Files.writeString(file, GSON.toJson(instance));
		} catch (IOException e) {
			LittleWeatherMod.LOGGER.warn("Could not write {}: {}", file, e.toString());
		}
	}

	private void sanitize() {
		sunsetStart = clamp(sunsetStart, 0, 23999);
		sunsetEnd = clamp(sunsetEnd, 0, 23999);
		nightStart = clamp(nightStart, 0, 23999);
		nightEnd = clamp(nightEnd, 0, 23999);
		cooldownTicks = clamp(cooldownTicks, 0, 1200);
	}

	private static int clamp(int v, int lo, int hi) {
		return Math.max(lo, Math.min(hi, v));
	}

	/** True when t is inside [from, to], where the range may wrap past midnight (from > to). */
	public static boolean inWindow(int t, int from, int to) {
		return from <= to ? (t >= from && t <= to) : (t >= from || t <= to);
	}
}
