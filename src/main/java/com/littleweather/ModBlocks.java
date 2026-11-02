package com.littleweather;

import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;

import java.util.List;

/** The five filled jars: each is a decorative block with a matching block item. */
public final class ModBlocks {
	public static final WeatherJarBlock STAR_JAR = block(JarKind.STAR);
	public static final WeatherJarBlock RAIN_JAR = block(JarKind.RAIN);
	public static final WeatherJarBlock SUNSET_JAR = block(JarKind.SUNSET);
	public static final WeatherJarBlock SNOW_JAR = block(JarKind.SNOW);
	public static final WeatherJarBlock STORM_JAR = block(JarKind.STORM);

	public static final BlockItem STAR_JAR_ITEM = item(JarKind.STAR, STAR_JAR);
	public static final BlockItem RAIN_JAR_ITEM = item(JarKind.RAIN, RAIN_JAR);
	public static final BlockItem SUNSET_JAR_ITEM = item(JarKind.SUNSET, SUNSET_JAR);
	public static final BlockItem SNOW_JAR_ITEM = item(JarKind.SNOW, SNOW_JAR);
	public static final BlockItem STORM_JAR_ITEM = item(JarKind.STORM, STORM_JAR);

	private static WeatherJarBlock block(JarKind kind) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, LittleWeatherMod.id(kind.blockName));
		BlockBehaviour.Properties props = BlockBehaviour.Properties.of()
			.setId(key)
			.strength(0.3f)
			.sound(SoundType.GLASS)
			.noOcclusion()
			.randomTicks()
			.lightLevel(state -> kind.light);
		return Registry.register(BuiltInRegistries.BLOCK, key, new WeatherJarBlock(props, kind));
	}

	/** Two grey tooltip lines, taken from the lang file (keys lore.littleweather.<name>.1 / .2). */
	static ItemLore lore(String name) {
		Component one = Component.translatable("lore.littleweather." + name + ".1").withStyle(st -> st.withColor(0xB8A8E8).withItalic(false));
		Component two = Component.translatable("lore.littleweather." + name + ".2").withStyle(st -> st.withColor(0x8F84B8).withItalic(false));
		return new ItemLore(List.of(one, two));
	}

	private static BlockItem item(JarKind kind, WeatherJarBlock block) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LittleWeatherMod.id(kind.blockName));
		Item.Properties props = new Item.Properties()
			.setId(key)
			.useBlockDescriptionPrefix()
			.stacksTo(16)
			.rarity(Rarity.UNCOMMON)
			.component(DataComponents.LORE, lore(kind.blockName));
		return Registry.register(BuiltInRegistries.ITEM, key, new BlockItem(block, props));
	}

	/** The filled-jar item for a kind. */
	public static BlockItem itemFor(JarKind kind) {
		return switch (kind) {
			case STAR -> STAR_JAR_ITEM;
			case RAIN -> RAIN_JAR_ITEM;
			case SUNSET -> SUNSET_JAR_ITEM;
			case SNOW -> SNOW_JAR_ITEM;
			case STORM -> STORM_JAR_ITEM;
		};
	}

	public static void init() {
		// touching the class registers every field above
	}

	private ModBlocks() {
	}
}
