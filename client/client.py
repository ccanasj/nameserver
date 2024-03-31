import grpc
import filetransfer_pb2
import filetransfer_pb2_grpc


def run():
    # Conectar al servidor
    channel = grpc.insecure_channel("34.123.168.239:50051")
    stub = filetransfer_pb2_grpc.FileServiceStub(channel)

    filename = "Me fui.jpg"

    with open(filename, "rb") as file:
        chunk_number = 0
        data = file.read()
        response = stub.SendChunk(
            filetransfer_pb2.ChunkData(
                filename=filename, chunk_number=chunk_number, chunk_data=data
            )
        )
        print(response)
        print(
            f"Chunk {chunk_number} enviado, respuesta del servidor: {response.message}"
        )

    response = stub.RequestChunk(
        filetransfer_pb2.ChunkRequest(filename=filename, chunk_number=chunk_number)
    )
    print(response)
    with open("Llegue.png", "wb") as f:
        f.write(response.chunk_data)


if __name__ == "__main__":
    run()
