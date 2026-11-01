package com.littleweather;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Right-click to catch the sky. Everything (validation, inventory change, effects) happens on the logical server;
 * the client only swings the arm. Vanilla refuses to call use() while the item is on cooldown, so a held button can
 * never capture twice.
 */
public class EmptyWeatherJarItem extends Item {
	public EmptyWeatherJarItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel server) || !(player instanceof ServerPlayer sp)) {
			return InteractionResult.SUCCESS; // client: just swing; the server decides everything
		}
		ItemStack stack = sp.getItemInHand(hand);
		int cooldown = LittleWeatherConfig.get().cooldownTicks;

		SkyConditions.Result result = SkyConditions.evaluate(server, sp);
		if (!result.ok()) {
			// failed capture: nothing is consumed, only a short action-bar hint and a short cooldown
			sp.sendOverlayMessage(Component.translatable(result.failKey()));
			if (cooldown > 0) {
				sp.getCooldowns().addCooldown(stack, cooldown);
			}
			return InteractionResult.FAIL;
		}

		JarKind kind = result.kind();
		ItemStack filled = new ItemStack(ModBlocks.itemFor(kind));
		if (cooldown > 0) {
			sp.getCooldowns().addCooldown(stack, cooldown);
		}

		if (!sp.getAbilities().instabuild) {
			stack.shrink(1);
			if (stack.isEmpty()) {
				sp.setItemInHand(hand, filled);
			} else {
				giveOrDrop(server, sp, filled);
			}
		} else {
			giveOrDrop(server, sp, filled);
		}

		playCaptureEffects(server, sp, kind);
		sp.sendOverlayMessage(Component.translatable("message.littleweather.captured", new ItemStack(ModBlocks.itemFor(kind)).getHoverName()));
		return InteractionResult.SUCCESS;
	}

	/** Puts the jar into the inventory, or drops it at the player's feet if the inventory is full. */
	private static void giveOrDrop(ServerLevel server, ServerPlayer sp, ItemStack stack) {
		if (!sp.getInventory().add(stack)) {
			server.addFreshEntity(new ItemEntity(server, sp.getX(), sp.getY() + 0.5, sp.getZ(), stack));
		}
	}

	private static void playCaptureEffects(ServerLevel server, ServerPlayer sp, JarKind kind) {
		Vec3 p = sp.getEyePosition().add(sp.getLookAngle().scale(0.7));
		int count = switch (kind) {
			case STAR -> 16;
			case RAIN -> 10;
			case SUNSET -> 18;
		};
		server.sendParticles(kind.particle(), p.x, p.y, p.z, count, 0.25, 0.25, 0.25, 0.02);
		float pitch = switch (kind) {
			case STAR -> 1.5f;
			case RAIN -> 1.2f;
			case SUNSET -> 0.9f;
		};
		server.playSound(null, p.x, p.y, p.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 0.6f, pitch);
		server.playSound(null, p.x, p.y, p.z, SoundEvents.BOTTLE_FILL, SoundSource.PLAYERS, 0.5f, 1.1f);
	}
}
