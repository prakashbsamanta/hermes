import sys
import os
import argparse
import inspect

# Add parent directory to path so we can import 'engine' and 'strategies'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from engine.loader import DataLoader
from engine.core import BacktestEngine
import strategies

def get_available_strategies():
    """Dynamically find all Strategy subclasses in the strategies module"""
    return {
        name: cls for name, cls in inspect.getmembers(strategies, inspect.isclass)
        # simplistic check, ideally check issubclass(cls, Strategy) but Strategy is in engine
        if name != "Strategy"
    }

def main():
    avail_strategies = get_available_strategies()
    
    parser = argparse.ArgumentParser(description="Hermes Backtest Verification")
    parser.add_argument("--symbol", type=str, required=True, help="Stock Symbol")
    parser.add_argument("--strategy", type=str, default="SMACrossover", 
                        choices=avail_strategies.keys(),
                        help=f"Strategy to run. Options: {list(avail_strategies.keys())}")
    
    args = parser.parse_args()
    
    symbol = args.symbol.upper()
    data_dir = os.path.join(parent_dir, "data/minute")
    
    print(f"--- Hermes Backtest Verification ---")
    print(f"Target: {symbol}")
    print(f"Strategy: {args.strategy}")
    
    # 1. Load Data
    loader = DataLoader(data_dir=data_dir)
    try:
        df = loader.load_data([symbol])
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # 2. Setup Strategy
    strategy_cls = avail_strategies[args.strategy]
    
    # Default params per strategy (simplistic for verification)
    params = {}
    if args.strategy == "SMACrossover":
        params = {"fast_period": 50, "slow_period": 200}
    elif args.strategy == "RSIStrategy":
        params = {"period": 14, "overbought": 70, "oversold": 30}
    elif args.strategy == "BollingerBandsStrategy":
        params = {"period": 20, "std_dev": 2.0}
    elif args.strategy == "MACDStrategy":
        params = {"fast_period": 12, "slow_period": 26, "signal_period": 9}
    elif args.strategy == "MTFTrendFollowingStrategy":
        # No specific params for this demo class, it has hardcoded logic in generate_signals
        params = {}
        
    strategy = strategy_cls(params=params)
    
    # 3. Run Engine
    engine = BacktestEngine(initial_cash=100000.0)
    try:
        result_df = engine.run(strategy, df)
    except Exception as e:
        print(f"CRITICAL ERROR running strategy: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Report
    metrics = engine.calculate_metrics(result_df)
    
    print("\n--- Results ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")
        
    print(f"\nLast 5 Rows:\n{result_df.tail(5)}")

if __name__ == "__main__":
    main()
