import socket
import time

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
BUFFER_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.1)  # Pequeno timeout para checar periodicamente

# Parâmetros de controle de congestionamento
cwnd = 1         # congestion window (janela de congestionamento) inicial
ssthresh = 8     # limiar para mudar de Slow Start para Congestion Avoidance
base_seq = 0     # menor seq que ainda não foi confirmado
next_seq_num = 0 # próximo seq que podemos enviar

# Parâmetros de retransmissão
TIMEOUT_RTT = 1.0  # 1 segundo de timeout para cada pacote
unacked = {}       # { seq_num: (packet, send_time) }

# Janela de recepção do servidor (controle de fluxo)
rwnd = 5  

# Geração de payload
payload_size = BUFFER_SIZE - 10  # Reservando 10 bytes para o seq_num
data = b"x" * payload_size

TOTAL_PACKETS = 10000

def send_packet(seq):
    """Envia um pacote com número de sequência 'seq' e atualiza o dicionário de não confirmados."""
    packet = f"{seq:010}".encode() + data
    sock.sendto(packet, (SERVER_IP, SERVER_PORT))
    unacked[seq] = (packet, time.time())
    print(f"[ENVIO] Pacote seq={seq} cwnd={cwnd}")

while base_seq < TOTAL_PACKETS:
    # 1) Envie novos pacotes (enquanto houver espaço na janela)
    # janela efetiva = min(cwnd, rwnd)
    while next_seq_num < TOTAL_PACKETS and (next_seq_num - base_seq) < min(cwnd, rwnd):
        send_packet(next_seq_num)
        next_seq_num += 1

    # 2) Verifique se houve ACK ou se algum pacote estourou o tempo (timeout)
    try:
        ack_data, _ = sock.recvfrom(BUFFER_SIZE)
        ack_split = ack_data.decode().split()
        
        # ex: "ACK15 5" → ack_num = 15, rwnd = 5
        ack_num = int(ack_split[0][3:])
        rwnd = int(ack_split[1]) if len(ack_split) > 1 else rwnd  # se o servidor mandar a janela

        print(f"[ACK   ] Recebido ACK={ack_num}, rwnd={rwnd}")

        # 2.1) Remover pacotes confirmados
        # Se ack_num = 15, todos seq < 15 foram recebidos
        for seq in list(unacked.keys()):
            if seq < ack_num:
                del unacked[seq]

        # 2.2) Ajustar base_seq
        base_seq = ack_num

        # 2.3) Controle de Congestionamento
        if cwnd < ssthresh:
            # Slow Start
            cwnd *= 2
        else:
            # Congestion Avoidance
            cwnd += 1

    except socket.timeout:
        # 2.4) Não chegou ACK agora; checamos se existe algum pacote que excedeu o tempo limite
        current_time = time.time()
        for seq in list(unacked.keys()):
            packet, last_send_time = unacked[seq]
            if (current_time - last_send_time) > TIMEOUT_RTT:
                # Retransmissão
                print(f"[TIMEOUT] Retransmitindo seq={seq}")
                sock.sendto(packet, (SERVER_IP, SERVER_PORT))
                unacked[seq] = (packet, time.time())

                # Ajuste de congestionamento
                ssthresh = max(cwnd // 2, 1)
                cwnd = 1  # Reinicia para Slow Start
                break  # Importante: retransmitir um pacote por vez e sair do loop

    # (Volta para o início do loop e tenta enviar mais pacotes se houver espaço)

print("Transmissão concluída!")
sock.close()
