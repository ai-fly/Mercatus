from fastapi import FastAPI
import uvicorn

from app.controllers import blackboard_controller

app = FastAPI()
app.include_router(blackboard_controller.router)



if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)