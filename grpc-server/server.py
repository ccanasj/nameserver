from concurrent import futures
import grpc
import os
import shutil
import logging

from dotenv import load_dotenv
import httpx
import filetransfer_pb2
import filetransfer_pb2_grpc

load_dotenv()

FILES_LOCATION = os.getenv("FILES_LOCATION")
MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL")


class FileService(filetransfer_pb2_grpc.FileServiceServicer):
    def SendChunk(self, request, context):
        logging.info(f"Recibido chunk {request.chunk_number} del archivo '{request.filename}'")

        # Crear la carpeta si no existe
        folder_path = os.path.join(FILES_LOCATION, request.filename)
        os.makedirs(folder_path, exist_ok=True)

        # Construir la ruta del archivo donde se guardará el chunk
        chunk_path = os.path.join(folder_path, str(request.chunk_number))

        # Guardar el chunk en el archivo correspondiente
        with open(chunk_path, "wb") as chunk_file:
            chunk_file.write(request.chunk_data)

        free_disk = shutil.disk_usage("/").free / (1024**2)

        response = httpx.post(
            f"{MAIN_SERVER_URL}/add-chunk/",
            json={
                "chunkId": request.chunk_number,
                "fileName": request.filename,
                "newFreeStorage": free_disk,
            },
        )
        response.raise_for_status()

        return filetransfer_pb2.TransferStatus(
            success=True,
            message="Chunk recibido exitosamente",
            new_free_storage=free_disk,
        )

    def RequestChunk(self, request, context):
        # Construir la ruta al archivo de chunk basado en el filename y chunk_number
        chunk_file_path = os.path.join(
            FILES_LOCATION, request.filename, str(request.chunk_number)
        )

        try:
            # Intentar abrir y leer el archivo de chunk
            with open(chunk_file_path, "rb") as file:
                chunk_data = file.read()
                return filetransfer_pb2.ChunkData(
                    filename=request.filename,
                    chunk_number=request.chunk_number,
                    chunk_data=chunk_data,
                )
        except FileNotFoundError:
            # Si el archivo no se encuentra, retornar un error gRPC
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Chunk {request.chunk_number} for file '{request.filename}' not found.",
            )
        except Exception as e:
            # Manejar cualquier otro error de lectura de archivo
            context.abort(
                grpc.StatusCode.INTERNAL,
                f"Error reading chunk {request.chunk_number} for file '{request.filename}': {str(e)}",
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    filetransfer_pb2_grpc.add_FileServiceServicer_to_server(FileService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    logging.info("Servidor iniciado en el puerto 50051.")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
