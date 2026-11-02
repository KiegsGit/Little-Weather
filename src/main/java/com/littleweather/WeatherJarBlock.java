package com.littleweather;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A filled weather jar. It can stand on a surface or, when you click the underside of a block, hang from it on a
 * little twine loop (the "hanging" block state, like a lantern). The look comes from the model and animated texture,
 * the glow from the light level and the tiny ambient particles from animateTick (client only).
 */
public class WeatherJarBlock extends Block {
	public static final BooleanProperty HANGING = BlockStateProperties.HANGING;
	private static final VoxelShape STANDING_SHAPE = Block.box(3.5, 0.0, 3.5, 12.5, 15.8, 12.5);
	private static final VoxelShape HANGING_SHAPE = Block.box(4.5, 0.0, 4.5, 11.5, 16.0, 11.5);

	public final JarKind kind;

	public WeatherJarBlock(Properties properties, JarKind kind) {
		super(properties);
		this.kind = kind;
		this.registerDefaultState(this.stateDefinition.any().setValue(HANGING, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(HANGING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		BlockState state = this.defaultBlockState().setValue(HANGING, context.getClickedFace() == Direction.DOWN);
		return state.canSurvive(context.getLevel(), context.getClickedPos()) ? state : null;
	}

	@Override
	public boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
		if (state.getValue(HANGING)) {
			return Block.canSupportCenter(level, pos.above(), Direction.DOWN);
		}
		return Block.canSupportCenter(level, pos.below(), Direction.UP);
	}

	/** Jars drop as items if whatever carried them is gone (checked on random ticks, so it can take a moment). */
	@Override
	public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		if (!state.canSurvive(level, pos)) {
			level.destroyBlock(pos, true);
		}
	}

	@Override
	public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return state.getValue(HANGING) ? HANGING_SHAPE : STANDING_SHAPE;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		double s = state.getValue(HANGING) ? 0.8 : 1.0;   // the hanging model is a little smaller
		double cx = pos.getX() + 0.5;
		double cz = pos.getZ() + 0.5;
		double y0 = pos.getY();
		switch (kind) {
			case STAR -> {
				int n = 1 + random.nextInt(2);
				for (int i = 0; i < n; i++) {
					level.addParticle(ModParticles.STAR_TWINKLE,
						cx + (random.nextDouble() - 0.5) * 0.36 * s, y0 + (0.12 + random.nextDouble() * 0.5) * s, cz + (random.nextDouble() - 0.5) * 0.36 * s,
						0.0, 0.002, 0.0);
				}
			}
			case RAIN -> level.addParticle(ModParticles.RAIN_DROP,
				cx + (random.nextDouble() - 0.5) * 0.34 * s, y0 + 0.62 * s, cz + (random.nextDouble() - 0.5) * 0.34 * s,
				0.0, -0.035, 0.0);
			case SUNSET -> {
				double a = random.nextDouble() * Math.PI * 2.0;
				level.addParticle(ModParticles.SUNSET_MOTE,
					cx + Math.cos(a) * 0.15 * s, y0 + (0.12 + random.nextDouble() * 0.35) * s, cz + Math.sin(a) * 0.15 * s,
					-Math.sin(a) * 0.004, 0.006, Math.cos(a) * 0.004);
			}
			case SNOW -> level.addParticle(ModParticles.SNOW_FLAKE,
				cx + (random.nextDouble() - 0.5) * 0.34 * s, y0 + (0.55 + random.nextDouble() * 0.08) * s, cz + (random.nextDouble() - 0.5) * 0.34 * s,
				(random.nextDouble() - 0.5) * 0.004, -0.006, (random.nextDouble() - 0.5) * 0.004);
			case STORM -> {
				level.addParticle(ModParticles.RAIN_DROP,
					cx + (random.nextDouble() - 0.5) * 0.34 * s, y0 + 0.58 * s, cz + (random.nextDouble() - 0.5) * 0.34 * s,
					0.0, -0.04, 0.0);
				if (random.nextInt(4) == 0) {
					level.addParticle(ModParticles.STORM_SPARK,
						cx + (random.nextDouble() - 0.5) * 0.24 * s, y0 + (0.5 + random.nextDouble() * 0.15) * s, cz + (random.nextDouble() - 0.5) * 0.24 * s,
						0.0, 0.0, 0.0);
				}
			}
		}
	}
}
