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
        
        self.setup_routes()
        
    def setup_routes(self):
        # Serve static files
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        @self.app.get("/")
        async def get():
            from fastapi.responses import FileResponse
            return FileResponse(os.path.join(static_dir, "index.html"))

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.clients.add(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    if msg.get('type') == 'config_update':
                        for key, value in msg.get('data', {}).items():
                            self.config_manager.set(key, value)
                        self.config_manager.save()
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
        data = {
            "type": "visualization",
            "bars": bars.tolist() if hasattr(bars, 'tolist') else bars
        }
        self.queue.put(data)
