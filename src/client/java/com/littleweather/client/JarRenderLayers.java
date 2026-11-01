package com.littleweather.client;

import com.littleweather.LittleWeatherMod;
import net.minecraft.world.level.block.Block;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/**
 * Puts the jars on the translucent chunk layer so the glass shows its contents.
 *
 * Fabric's BlockRenderLayerMap and Minecraft's ChunkSectionLayer have changed shape between releases, so both are
 * looked up by name and the call is wrapped: if the lookup fails the game still starts (the jars would just render
 * with an opaque glass shell) and the problem is logged. Once the project has been compiled against 26.3 this can be
 * replaced with a direct BlockRenderLayerMap.putBlock(block, ChunkSectionLayer.TRANSLUCENT) call.
 */
final class JarRenderLayers {
	private static final String[] MAP_CLASSES = {
		"net.fabricmc.fabric.api.client.rendering.v1.BlockRenderLayerMap"
	};
	private static final String[] LAYER_CLASSES = {
		"net.minecraft.client.renderer.chunk.ChunkSectionLayer",
		"net.minecraft.client.renderer.ChunkSectionLayer",
		"net.minecraft.client.renderer.chunk.ChunkSectionLayers"
	};

	static void register(Block... blocks) {
		try {
			Class<?> layerClass = firstClass(LAYER_CLASSES);
			Class<?> mapClass = firstClass(MAP_CLASSES);
			if (layerClass == null || mapClass == null) {
				throw new ClassNotFoundException("render layer classes not found");
			}
			Object translucent = null;
			for (Object constant : layerClass.getEnumConstants()) {
				if (constant.toString().equals("TRANSLUCENT")) {
					translucent = constant;
				}
			}
			if (translucent == null) {
				throw new NoSuchFieldException("TRANSLUCENT");
			}
			Object target = null;
			Method put = null;
			for (Method m : mapClass.getMethods()) {
				if (m.getName().equals("putBlock") && m.getParameterCount() == 2
					&& m.getParameterTypes()[0] == Block.class && m.getParameterTypes()[1] == layerClass) {
					put = m;
				}
			}
			if (put == null) {
				throw new NoSuchMethodException("putBlock(Block, ChunkSectionLayer)");
			}
			if (!Modifier.isStatic(put.getModifiers())) {
				target = mapClass.getField("INSTANCE").get(null);
			}
			for (Block block : blocks) {
				put.invoke(target, block, translucent);
			}
		} catch (ReflectiveOperationException | RuntimeException | LinkageError e) {
			LittleWeatherMod.LOGGER.warn("Could not set the jar render layer, glass may look opaque: {}", e.toString());
		}
	}

	private static Class<?> firstClass(String[] names) {
		for (String n : names) {
			try {
				return Class.forName(n);
			} catch (ClassNotFoundException | LinkageError ignored) {
				// try next
			}
		}
		return null;
	}

	private JarRenderLayers() {
	}
}
