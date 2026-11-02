package com.littleweather;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

public final class ModItems {
	public static final EmptyWeatherJarItem EMPTY_WEATHER_JAR = registerEmptyJar();

	private static EmptyWeatherJarItem registerEmptyJar() {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LittleWeatherMod.id("empty_weather_jar"));
		Item.Properties props = new Item.Properties().setId(key).stacksTo(16)
			.component(DataComponents.LORE, ModBlocks.lore("empty_weather_jar"));
		return Registry.register(BuiltInRegistries.ITEM, key, new EmptyWeatherJarItem(props));
	}

	private static final ResourceKey<CreativeModeTab> FALLBACK_TAB =
		ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.fromNamespaceAndPath("minecraft", "functional_blocks"));
	private static final ResourceKey<CreativeModeTab> LITTLE_WEATHER_TAB =
		ResourceKey.create(Registries.CREATIVE_MODE_TAB, LittleWeatherMod.id("littleweather"));

	/** Every item of the mod, in tab order. */
	private static Item[] all() {
		return new Item[] {EMPTY_WEATHER_JAR, ModBlocks.STAR_JAR_ITEM, ModBlocks.SUNSET_JAR_ITEM, ModBlocks.RAIN_JAR_ITEM,
			ModBlocks.SNOW_JAR_ITEM, ModBlocks.STORM_JAR_ITEM};
	}

	/**
	 * Fabric's tab-builder class has been renamed between versions, so it is looked up by name (same approach as the
	 * Skybreaker reference). If none of the known names exists the items go into the Functional Blocks tab instead.
	 */
	private static CreativeModeTab.Builder fabricTabBuilder() {
		String[] classes = {
			"net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab",
			"net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup"
		};
		for (String name : classes) {
			try {
				return (CreativeModeTab.Builder) Class.forName(name).getMethod("builder").invoke(null);
			} catch (ReflectiveOperationException | LinkageError | ClassCastException ignored) {
				// try the next name
			}
		}
		return null;
	}

	public static void init() {
		CreativeModeTab.Builder builder = fabricTabBuilder();
		if (builder != null) {
			CreativeModeTab tab = builder
				.title(Component.translatable("itemGroup.littleweather"))
				.icon(() -> new ItemStack(ModBlocks.SUNSET_JAR_ITEM))
				.displayItems((params, output) -> {
					for (Item item : all()) {
						output.accept(item);
					}
				})
				.build();
			Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, LITTLE_WEATHER_TAB, tab);
		} else {
			LittleWeatherMod.LOGGER.warn("Fabric creative-tab builder not found, adding Little Weather items to Functional Blocks instead.");
			CreativeModeTabEvents.modifyOutputEvent(FALLBACK_TAB).register(output -> {
				for (Item item : all()) {
					output.accept(item);
				}
			});
		}
	}

	private ModItems() {
	}
}
