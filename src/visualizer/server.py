from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import json
import threading
import queue
import os
from utils.logger import logger

class VisualizerServer:
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
                logger.error(f"Error in broadcast_worker: {e}")

    def start(self):
        logger.info(f"Browser visualizer starting at http://{self.host}:{self.port}")
        if self.host == '0.0.0.0':
            logger.info(f"You can also try http://localhost:{self.port}")
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Start the broadcast worker
        self.loop.create_task(self.broadcast_worker())
        
        # 1. Set loop="asyncio" to prevent auto-detection errors
        # 2. Set log_level="warning" to reduce noise
        config = uvicorn.Config(
            self.app, 
            host=self.host, 
            port=self.port, 
            log_level="warning", 
            loop="asyncio"
        )
        self.server = uvicorn.Server(config)
        
        # --- CRITICAL FIX ---
        # Disable signal handlers so Uvicorn doesn't crash in a thread
        self.server.install_signal_handlers = lambda: None 
        # --------------------

        try:
            self.loop.run_until_complete(self.server.serve())
        except Exception as e:
            logger.error(f"SERVER CRASHED: {e}")

    def stop(self):
        """Stops the server and the broadcast worker."""
        logger.info("Stopping VisualizerServer")
        if hasattr(self, 'queue'):
            self.queue.put(None) # Signal worker to stop
            
        # We don't have a direct reference to the 'server' instance here 
        # but we can try to stop the loop or set a flag if we had one.
        # Given how it's started in _run, we'll need to store the server instance.
        if hasattr(self, 'server'):
            self.server.should_exit = True

    def send_data(self, bars, audio_data=None, is_beat=False):
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
            "recording": self.is_recording(),
            "is_beat": is_beat
        }
        self.queue.put(data)
