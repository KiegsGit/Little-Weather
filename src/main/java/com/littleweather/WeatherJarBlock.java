package com.littleweather;

import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A filled weather jar. It is a plain, stateless block: the look comes from its model and animated texture, the
 * glow from its light level and the tiny ambient particles from animateTick (client only, never touches the server).
 */
public class WeatherJarBlock extends Block {
	private static final VoxelShape SHAPE = Block.box(3.0, 0.0, 3.0, 13.0, 15.0, 13.0);

	public final JarKind kind;

	public WeatherJarBlock(Properties properties, JarKind kind) {
		super(properties);
		this.kind = kind;
	}

	@Override
	public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		double cx = pos.getX() + 0.5;
		double cz = pos.getZ() + 0.5;
		switch (kind) {
			case STAR -> {
				// a few twinkles hanging inside the jar
				int n = 1 + random.nextInt(2);
				for (int i = 0; i < n; i++) {
					level.addParticle(ModParticles.STAR_TWINKLE,
						cx + (random.nextDouble() - 0.5) * 0.36, pos.getY() + 0.12 + random.nextDouble() * 0.5, cz + (random.nextDouble() - 0.5) * 0.36,
						0.0, 0.002, 0.0);
				}
			}
			case RAIN -> {
				// drops fall from under the little cloud
				level.addParticle(ModParticles.RAIN_DROP,
					cx + (random.nextDouble() - 0.5) * 0.34, pos.getY() + 0.62, cz + (random.nextDouble() - 0.5) * 0.34,
					0.0, -0.035, 0.0);
			}
			case SUNSET -> {
				// warm motes drift slowly upwards in a lazy swirl
				double a = random.nextDouble() * Math.PI * 2.0;
				level.addParticle(ModParticles.SUNSET_MOTE,
					cx + Math.cos(a) * 0.15, pos.getY() + 0.12 + random.nextDouble() * 0.35, cz + Math.sin(a) * 0.15,
					-Math.sin(a) * 0.004, 0.006, Math.cos(a) * 0.004);
			}
		}
	}
}
