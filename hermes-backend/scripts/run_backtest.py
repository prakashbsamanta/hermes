import sys
import os
import argparse

# Add parent directory to path so we can import 'engine' and 'strategies'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from engine.loader import DataLoader
from engine.core import BacktestEngine
from strategies.sma_cross import SMACrossover

def main():
    parser = argparse.ArgumentParser(description="Hermes Backtest Verification")
    parser.add_argument("--symbol", type=str, required=True, help="Stock Symbol")
    args = parser.parse_args()
    
    symbol = args.symbol.upper()
    data_dir = os.path.join(parent_dir, "data/minute")
    
    print(f"--- Hermes Backtest Verification ---")
    print(f"Target: {symbol}")
    print(f"Strategy: SMA Crossover (50/200)")
    
    # 1. Load Data
    loader = DataLoader(data_dir=data_dir)
    try:
        df = loader.load_data([symbol])
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # 2. Setup Strategy
    strategy = SMACrossover(params={"fast_period": 50, "slow_period": 200})
    
    # 3. Run Engine
    engine = BacktestEngine(initial_cash=100000.0)
    result_df = engine.run(strategy, df)
    
    # 4. Report
    metrics = engine.calculate_metrics(result_df)
    
    print("\n--- Results ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")
        
    print(f"\nLast 5 Rows:\n{result_df.tail(5)}")

if __name__ == "__main__":
    main()
