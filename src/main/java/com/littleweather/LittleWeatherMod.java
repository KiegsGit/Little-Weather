package com.littleweather;

import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.api.ModInitializer;

public class LittleWeatherMod implements ModInitializer {
	public static final String MOD_ID = "littleweather";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}

	@Override
	public void onInitialize() {
		LittleWeatherConfig.load();
		ModParticles.init();
		ModSounds.init();
		ModBlocks.init();
		ModItems.init();
		LOGGER.info("Little Weather loaded.");
	}
}
