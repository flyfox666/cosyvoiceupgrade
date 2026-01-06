"""
Unified launcher for CosyVoice WebUI + API Server
同时启动 Gradio WebUI 和 FastAPI 服务器
"""
import os
import sys
import signal
import argparse
import multiprocessing
import time
import webbrowser
import threading

def start_webui(port=50000, model_dir="pretrained_models/Fun-CosyVoice3-0.5B"):
    """Start Gradio WebUI"""
    os.environ['WEBUI_PORT'] = str(port)
    os.environ['MODEL_DIR'] = model_dir
    
    import app_local
    # The app_local will handle its own startup
    
def start_api_server(port=81889, model_dir="pretrained_models/Fun-CosyVoice3-0.5B"):
    """Start FastAPI server"""
    import uvicorn
    os.environ['API_PORT'] = str(port)
    os.environ['MODEL_DIR'] = model_dir
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )

def open_browser(webui_port, api_port, delay=3):
    """Open browser after delay"""
    time.sleep(delay)
    print(f"\n🌐 Opening browser...")
    print(f"  WebUI: http://localhost:{webui_port}")
    print(f"  API Docs: http://localhost:{api_port}/docs")
    webbrowser.open(f'http://localhost:{webui_port}')

def main():
    parser = argparse.ArgumentParser(description="Start CosyVoice WebUI + API Server")
    parser.add_argument('--model_dir', type=str, 
                      default='pretrained_models/Fun-CosyVoice3-0.5B',
                      help='Model directory path')
    parser.add_argument('--webui_port', type=int, default=50000,
                      help='WebUI port (default: 50000)')
    parser.add_argument('--api_port', type=int, default=81889,
                      help='API server port (default: 81889)')
    parser.add_argument('--no_browser', action='store_true',
                      help='Do not open browser automatically')
    parser.add_argument('--api_only', action='store_true',
                      help='Start API server only')
    parser.add_argument('--webui_only', action='store_true',
                      help='Start WebUI only')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎙️  CosyVoice All-in-One Launcher")
    print("=" * 70)
    
    processes = []
    
    try:
        # Start API server
        if not args.webui_only:
            print(f"\n🚀 Starting API Server on port {args.api_port}...")
            api_process = multiprocessing.Process(
                target=start_api_server,
                args=(args.api_port, args.model_dir)
            )
            api_process.start()
            processes.append(api_process)
            print(f"   API Docs will be available at: http://localhost:{args.api_port}/docs")
        
        # Start WebUI
        if not args.api_only:
            print(f"\n🚀 Starting WebUI on port {args.webui_port}...")
            webui_process = multiprocessing.Process(
                target=start_webui,
                args=(args.webui_port, args.model_dir)
            )
            webui_process.start()
            processes.append(webui_process)
            print(f"   WebUI will be available at: http://localhost:{args.webui_port}")
        
        # Open browser
        if not args.no_browser and not args.api_only:
            browser_thread = threading.Thread(
                target=open_browser,
                args=(args.webui_port, args.api_port),
                daemon=True
            )
            browser_thread.start()
        
        print("\n" + "=" * 70)
        print("✅ All services started!")
        print("=" * 70)
        
        if not args.api_only:
            print(f"🖥️  WebUI:    http://localhost:{args.webui_port}")
        if not args.webui_only:
            print(f"🔌 API:      http://localhost:{args.api_port}")
            print(f"📚 API Docs: http://localhost:{args.api_port}/docs")
        print("\nPress Ctrl+C to stop all services")
        print("=" * 70 + "\n")
        
        # Wait for processes
        for process in processes:
            process.join()
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        for process in processes:
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
        print("✅ All services stopped")
        sys.exit(0)

if __name__ == "__main__":
    # Required for multiprocessing on Windows
    multiprocessing.set_start_method('spawn', force=True)
    main()
