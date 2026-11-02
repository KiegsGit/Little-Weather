package com.littleweather;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundEvent;

/** Little Weather's own sounds (assets/littleweather/sounds/*.ogg, declared in sounds.json). */
public final class ModSounds {
	/** Soft rising glass chime when a jar is filled. */
	public static final SoundEvent CAPTURE_CHIME = reg("capture_chime");
	/** Small cork pop that goes with it. */
	public static final SoundEvent CORK_POP = reg("cork_pop");

	private static SoundEvent reg(String name) {
		Identifier id = LittleWeatherMod.id(name);
		return Registry.register(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id));
	}

	public static void init() {
		// touching the class registers every field above
	}

	private ModSounds() {
	}
}
