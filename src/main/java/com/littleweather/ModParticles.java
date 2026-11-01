package com.littleweather;

import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;

/** Little Weather's particle types. Textures: assets/littleweather/textures/particle, animations: .../particles. */
public final class ModParticles {
	/** Tiny four-frame twinkling star. */
	public static final SimpleParticleType STAR_TWINKLE = reg("star_twinkle");
	/** Small blue raindrop. */
	public static final SimpleParticleType RAIN_DROP = reg("rain_drop");
	/** Soft orange/pink mote of sunset light. */
	public static final SimpleParticleType SUNSET_MOTE = reg("sunset_mote");

	private static SimpleParticleType reg(String name) {
		return Registry.register(BuiltInRegistries.PARTICLE_TYPE, LittleWeatherMod.id(name), FabricParticleTypes.simple());
	}

	public static void init() {
		// touching the class registers every field above
	}

	private ModParticles() {
	}
}
