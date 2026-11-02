package com.littleweather.client;

import com.littleweather.ModBlocks;
import net.fabricmc.api.ClientModInitializer;

public class LittleWeatherClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		ParticleSetup.register();
		JarRenderLayers.register(ModBlocks.STAR_JAR, ModBlocks.RAIN_JAR, ModBlocks.SUNSET_JAR, ModBlocks.SNOW_JAR, ModBlocks.STORM_JAR);
	}
}
