1. backend - fasapi, websocket, endpoint
2. data models
3. scenario generator
4. opponent agent
5. coach agent
6. post-mortem agent
7. video storage + users
8. library + dashboard
9. frontend
10. frontend + backend connection

user speaks -> capture audio -> send audio chunks via WebSocket -> stt model -> transcrbed text -> agent pipeline - > agent generates a response -> tts model -> audio bytes -> websocket -> frontend -> play audio