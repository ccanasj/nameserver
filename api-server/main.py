from contextlib import asynccontextmanager
import shutil
import os

from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx


load_dotenv()


def get_files_in_directory(
    directory: str,
) -> dict[str, dict[str, dict[str, list[str]]]]:
    files = {
        file: {
            "availableChunks": [
                filename for filename in os.listdir(os.path.join(directory, file))
            ]
        }
        for file in os.listdir(directory)
    }
    return files


FILES_LOCATION = os.getenv("FILES_LOCATION")
MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):

    free_disk = shutil.disk_usage("/").free
    files = get_files_in_directory(FILES_LOCATION)
    data = {
        "storageCapacityInMb": free_disk / (1024**2),
        "files": files,
    }
    try:
        response = httpx.post(f"{MAIN_SERVER_URL}/add-node/", json=data)

        if response.status_code == 200:
            print("Node registrado exitosamente.")
        else:
            print(
                f"Error al registrar el nodo. Código de estado: {response.status_code}"
            )
            print(response.content)
    except httpx.RequestError as e:
        print(f"Error en la solicitud: {e}")
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping", response_class=JSONResponse)
async def ping():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "pong"})
