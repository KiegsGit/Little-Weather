package com.littleweather;

import net.minecraft.core.particles.SimpleParticleType;

/** The five sky moments that can be kept in a jar. */
public enum JarKind {
	STAR("star_jar", 9),
	RAIN("rain_jar", 3),
	SUNSET("sunset_jar", 6),
	SNOW("snow_jar", 5),
	STORM("storm_jar", 4);

	public final String blockName;
	/** Block light emitted by the placed jar (Star is the brightest, Rain the dimmest). */
	public final int light;

	JarKind(String blockName, int light) {
		this.blockName = blockName;
		this.light = light;
	}

	/** The particle used for the capture burst of this kind. */
	public SimpleParticleType particle() {
		return switch (this) {
			case STAR -> ModParticles.STAR_TWINKLE;
			case RAIN -> ModParticles.RAIN_DROP;
			case SUNSET -> ModParticles.SUNSET_MOTE;
			case SNOW -> ModParticles.SNOW_FLAKE;
			case STORM -> ModParticles.STORM_SPARK;
		};
	}
}
