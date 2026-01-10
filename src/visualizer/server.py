from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import json
import threading
import queue
import os

class VisualizerServer:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.app = FastAPI()
        self.clients = set()
        self.host = config_manager.get('browser.host', '0.0.0.0')
        self.port = config_manager.get('browser.port', 8000)
        self.loop = None
        self.queue = queue.Queue()
        self.on_toggle_recording = None
        self.is_recording_callback = None
        
        self.setup_routes()

    def is_recording(self):
        if self.is_recording_callback:
            return self.is_recording_callback()
        return False
        
    def load_color_profiles(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'colors.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                import yaml
                return yaml.safe_load(f).get('profiles', {})
        return {}

    def setup_routes(self):
        # Serve static files
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        @self.app.get("/")
        async def get():
            from fastapi.responses import FileResponse
            return FileResponse(os.path.join(static_dir, "index.html"))

        @self.app.get("/files")
        async def list_files():
            import glob
            extensions = ('**/*.mp3', '**/*.wav', '**/*.flac')
            files = []
            for ext in extensions:
                files.extend(glob.glob(ext, recursive=True))
            
            # Filter out files in .venv or my_venv or .git
            files = [f for f in files if not any(x in f for x in ['.venv', 'my_venv', '.git'])]
            return {"files": sorted(files)}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.clients.add(websocket)
            
            # Send initial config and color profiles
            await websocket.send_text(json.dumps({
                "type": "init",
                "profiles": self.load_color_profiles(),
                "config": self.config_manager.config
            }))

            try:
                while True:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    if msg.get('type') == 'config_update':
                        for key, value in msg.get('data', {}).items():
                            self.config_manager.set(key, value)
                        self.config_manager.save()
                        
                        # Broadcast config update to others
                        update_msg = json.dumps({
                            "type": "config_update",
                            "config": self.config_manager.config
                        })
                        for client in self.clients:
                            if client != websocket:
                                await client.send_text(update_msg)
                    elif msg.get('type') == 'toggle_recording':
                        if self.on_toggle_recording:
                            self.on_toggle_recording()
                    elif msg.get('type') == 'get_status':
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "recording": self.is_recording() if hasattr(self, 'is_recording') else False
                        }))
            except WebSocketDisconnect:
                self.clients.remove(websocket)

    async def broadcast_worker(self):
        while True:
            try:
                # Use a small timeout to allow checking for shutdown if needed
                data = self.queue.get(timeout=0.1)
                if data is None: break
                
                if self.clients:
                    message = json.dumps(data)
                    tasks = [client.send_text(message) for client in self.clients]
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in broadcast_worker: {e}")

    def start(self):
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Start the broadcast worker in the background
        self.loop.create_task(self.broadcast_worker())
        
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="error")
        server = uvicorn.Server(config)
        self.loop.run_until_complete(server.serve())

    def send_data(self, bars, audio_data=None):
        """
        Queue FFT data and optionally audio data to all connected clients.
        """
        if isinstance(bars, list):
            bars_data = [b.tolist() if hasattr(b, 'tolist') else b for b in bars]
        else:
            bars_data = bars.tolist() if hasattr(bars, 'tolist') else bars
            
        data = {
            "type": "visualization",
            "bars": bars_data,
            "recording": self.is_recording()
        }
        self.queue.put(data)
