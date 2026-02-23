from orderbook_simulator import OrderBookSimulator
from visualization import LiquidityHeatmapVisualizer

if __name__ == "__main__":
    # Simulation parameters
    n_levels = 40
    n_steps = 300
    simulator = OrderBookSimulator(n_levels=n_levels, n_steps=n_steps)
    simulator.run_simulation()

    visualizer = LiquidityHeatmapVisualizer(simulator)
    visualizer.animate()
