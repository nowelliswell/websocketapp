from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.usernames: Dict[WebSocket, str] = {}  # Map WebSocket to username

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.broadcast("A new user has joined the chat!")

    async def disconnect(self, websocket: WebSocket):
        username = self.usernames.get(websocket, "Unknown User")
        self.active_connections.remove(websocket)
        del self.usernames[websocket]
        await self.broadcast(f"{username} has left the chat.")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def set_username(self, websocket: WebSocket, username: str):
        self.usernames[websocket] = username
        await self.broadcast(f"{username} has joined the chat.")

connection_manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("SET_USERNAME:"):
                username = data.split(": ", 1)[1]
                await connection_manager.set_username(websocket, username)
            else:
                username = connection_manager.usernames.get(websocket, "Unknown User")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await connection_manager.broadcast(f"[{timestamp}] {username}: {data}")
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)