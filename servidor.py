import socket
import random

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
BUFFER_SIZE = 1024
LOSS_PROBABILITY = 0.02  # 2% de chance de perda

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

print(f"Servidor rodando em {SERVER_IP}:{SERVER_PORT}")

expected_seq = 0
window_size = 5  # Tamanho fixo da janela de recepção (rwnd)

while True:
    data, addr = sock.recvfrom(BUFFER_SIZE)
    seq_num = int(data[:10])  # Extrai número de sequência

    # Simulação de perda de pacotes
    if random.random() < LOSS_PROBABILITY:
        print(f"[PERDA ] Pacote seq={seq_num} descartado!")
        continue

    print(f"[RECEB] Pacote seq={seq_num}")

    # Se a sequência for exatamente a esperada, incrementamos
    if seq_num == expected_seq:
        expected_seq += 1

    # Envia ACK acumulativo + tamanho da janela
    ack_msg = f"ACK{expected_seq} {window_size}".encode()
    sock.sendto(ack_msg, addr)
    print(f"[ENVIO] {ack_msg.decode()} → {addr}")
