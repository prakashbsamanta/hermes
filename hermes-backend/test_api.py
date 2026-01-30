import requests
import time
import subprocess
import sys
import os
import signal

def test_api():
    print("--- Starting API Verification ---")
    
    # 1. Start Server
    # We use Popen to start it in background
    cwd = os.path.join(os.getcwd(), "hermes-backend")
    # use correct venv python
    python_bin = os.path.join(cwd, "venv", "bin", "python3")
    
    # Start process: uvicorn main:app
    proc = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "main:app", "--port", "8001"], # Use different port to avoid conflicts
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"Server started with PID {proc.pid}. Waiting for startup...")
    
    # 2. Wait for Health Check
    base_url = "http://localhost:8001"
    ready = False
    for i in range(10):
        try:
            r = requests.get(f"{base_url}/")
            if r.status_code == 200:
                print("Server is UP!")
                ready = True
                break
        except:
            pass
        time.sleep(1)
        print(f"Waiting... {i+1}")
        
    if not ready:
        print("Server failed to start.")
        proc.kill()
        out, err = proc.communicate()
        print(f"STDOUT: {out.decode()}")
        print(f"STDERR: {err.decode()}")
        sys.exit(1)

    # 3. Test Backtest Endpoint
    payload = {
        "symbol": "AARTIIND", 
        "strategy": "RSIStrategy", 
        "params": {"period": 14}
    }
    
    print(f"Sending POST /backtest with {payload}...")
    try:
        r = requests.post(f"{base_url}/backtest", json=payload)
        
        if r.status_code == 200:
            data = r.json()
            print("✅ Response 200 OK")
            print(f"Symbol: {data.get('symbol')}")
            print(f"Strategy: {data.get('strategy')}")
            print(f"Metrics: {data.get('metrics')}")
            
            eq_len = len(data.get('equity_curve', []))
            sig_len = len(data.get('signals', []))
            print(f"Equity Curve Points: {eq_len}")
            print(f"Signals Generated: {sig_len}")
            
            if eq_len > 0 and sig_len > 0:
                print("✅ Data validation successful.")
            else:
                print("⚠️ Warning: Empty data returned.")
        else:
            print(f"❌ Request Failed: {r.status_code}")
            print(r.text)
            
    except Exception as e:
        print(f"Exception during request: {e}")
    finally:
        print("Shutting down server...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()
        print("Done.")

if __name__ == "__main__":
    test_api()
