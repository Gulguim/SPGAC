import os
import random
from itertools import permutations
from time import time, sleep
from multiprocessing import Process, Queue, cpu_count
from math import factorial
from eth_account import Account

# Habilita as funções de mnemônica do Ethereum
Account.enable_unaudited_hdwallet_features()

# Configurações
TARGET_ADDRESS = "0x2468e3576D94009F0Bd23795161E55d122d07dB6"  # Endereço alvo
RESULT_FILE = "found_keys.txt"
NUM_PROCESSES = 4  # Número de processos em paralelo
FIXED_WORD = "avocado"  # Palavra fixa na posição 3

# Palavras conhecidas para gerar as combinações:
KNOWN_WORDS = ["switch", "peanut", "avocado", "green", "health", "exchange", "girl", "brown", "fly", "produce", "amazing", "sight"]

def hash_function(seed_phrase):
    """Gera um endereço Ethereum a partir da frase mnemônica."""
    try:
        acct = Account.from_mnemonic(seed_phrase)
        return acct.address
    except Exception:
        return None

def save_result(seed_phrase, address):
    """Salva a seed phrase encontrada e o endereço alvo em um arquivo."""
    with open(RESULT_FILE, "a") as f:
        f.write(f"Seed Phrase: {seed_phrase}\nAddress: {address}\n\n")
    print(f"\n[SUCESSO] Seed Phrase salva no arquivo: {RESULT_FILE}")
    print(f"Seed Phrase: {seed_phrase}")
    print(f"Endereço Alvo: {address}")

def generate_combinations(words):
    """Gera todas as combinações possíveis das palavras, mantendo a palavra fixa na terceira posição."""
    words_without_fixed = [word for word in words if word != FIXED_WORD]
    for combination in permutations(words_without_fixed):
        yield combination[:2] + (FIXED_WORD,) + combination[2:]

def search_combinations_in_range(start, end, words, target_address, progress_queue):
    """Busca pela combinação correta em um intervalo específico."""
    combinations_checked = 0
    start_time = time()

    for i, combination in enumerate(generate_combinations(words)):
        if i < start:
            continue
        if i >= end:
            break

        seed_phrase = " ".join(combination)
        derived_address = hash_function(seed_phrase)

        if derived_address and derived_address.lower() == target_address.lower():
            save_result(seed_phrase, derived_address)
            progress_queue.put(None)  # Sinaliza que a combinação foi encontrada
            return

        combinations_checked += 1
        if combinations_checked % 1000 == 0:
            elapsed_time = time() - start_time
            progress_queue.put((combinations_checked, elapsed_time))

    progress_queue.put((combinations_checked, time() - start_time))

def monitor_progress(progress_queue):
    """Monitoramento do progresso geral."""
    combinations_checked = 0
    start_time = time()

    while True:
        message = progress_queue.get()
        if message is None:
            print("\n[SUCESSO] Combinação encontrada. Encerrando os processos.")
            break

        checked, elapsed = message
        combinations_checked += checked
        speed = combinations_checked / elapsed if elapsed > 0 else 0
        elapsed_total = (time() - start_time) / 60

        print(
            f"\rTestadas: {combinations_checked} | Velocidade: {speed:.2f} combinações/s | "
            f"Tempo decorrido: {elapsed_total:.2f} min",
            end=""
        )

    print("\nBusca finalizada.")

def parallel_search():
    """Executa a busca paralela e troca as palavras automaticamente ao final de cada rodada."""
    attempt_count = 1  # Contador de tentativas

    while True:
        words = KNOWN_WORDS.copy()
        total_combinations = factorial(11)  # 11! = 39.916.800

        print(f"\nNova tentativa com palavras: {words}")

        chunk_size = total_combinations // NUM_PROCESSES
        processes = []
        progress_queue = Queue()

        for i in range(NUM_PROCESSES):
            start = i * chunk_size
            end = start + chunk_size if i < NUM_PROCESSES - 1 else total_combinations
            process = Process(target=search_combinations_in_range, args=(start, end, words, TARGET_ADDRESS, progress_queue))
            processes.append(process)
            process.start()

        monitor_process = Process(target=monitor_progress, args=(progress_queue,))
        monitor_process.start()

        for process in processes:
            process.join()

        monitor_process.terminate()  # Encerra monitoramento quando os processos terminam

        attempt_count += 1  # Incrementa o contador de tentativas
        print(f"\n[INFO] Tentativa {attempt_count} concluída. Gerando novas palavras...")

        # Condição de parada após um número específico de tentativas
        if attempt_count >= 1:  # Por exemplo, parar após 10 tentativas
            print("\n[INFO] Número máximo de tentativas alcançado. Encerrando a busca.")
            break

        sleep(2)  # Pequena pausa antes de reiniciar a busca

if __name__ == "__main__":
    parallel_search()