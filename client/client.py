import grpc
import filetransfer_pb2
import filetransfer_pb2_grpc


def run():
    # Conectar al servidor
    channel = grpc.insecure_channel("localhost:50051")
    stub = filetransfer_pb2_grpc.FileServiceStub(channel)

    filename = "archivo_ejemplo.txt"
    chunk_size = 1024  # Tamaño de chunk en bytes

    with open(filename, "rb") as file:
        chunk_number = 0
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            response = stub.SendChunk(
                filetransfer_pb2.ChunkData(
                    filename=filename, chunk_number=chunk_number, chunk_data=data
                )
            )
            print(response)
            print(
                f"Chunk {chunk_number} enviado, respuesta del servidor: {response.message}"
            )
            chunk_number += 1

    response = stub.RequestChunk(
        filetransfer_pb2.ChunkRequest(filename=filename, chunk_number=chunk_number)
    )
    print(response)


if __name__ == "__main__":
    run()
