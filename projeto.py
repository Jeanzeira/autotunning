import subprocess
import sys
import random
import time
import concurrent.futures
import os
from typing import List, Tuple

# =============================================================================
# CONFIGURAÇÃO DE LIMITES
# =============================================================================
MIN_VAL = 1
MAX_VAL = 1000  # Alterado de 100 para 1000

# =============================================================================
# FUNÇÕES GLOBAIS COMUNS
# =============================================================================
def detectar_cfg(exemplo: str) -> Tuple[List, List[str]]:
    """Detecta valores iniciais e tipos automaticamente"""
    partes = exemplo.strip().split()
    cfg, tipos = [], []
    for p in partes:
        try:
            v = int(p); v = 1 if v == 0 else v
            cfg.append(v); tipos.append('int'); continue
        except: pass
        try:
            v = float(p); v = 1.0 if v == 0.0 else v
            cfg.append(v); tipos.append('float'); continue
        except: pass
        cfg.append(p.lower()); tipos.append('str')
    return cfg, tipos

def executar(exe: str, cfg: List) -> float:
    """Roda o executável e retorna o valor numérico"""
    try:
        # Executa o comando e captura a saída
        res = subprocess.run([exe] + [str(x) for x in cfg], 
                           capture_output=True, text=True, timeout=30)
        out = res.stdout.strip()
        # Tenta extrair o valor após ':' ou pega a saída inteira
        valor = float(out.split(":")[-1].strip()) if ":" in out else float(out)
        return valor
    except:
        return float('-inf')

def avaliar_em_massa(exe: str, populacao: List[List]) -> List[float]:
    """Avalia uma lista de configurações EM PARALELO"""
    # Usa o número de núcleos da CPU para definir quantos processos rodar simultaneamente
    workers = os.cpu_count() or 4
    
    # ThreadPoolExecutor é ideal aqui pois o 'gargalo' é esperar o subprocesso terminar (I/O)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Submete todas as execuções para o pool de threads
        futures = [executor.submit(executar, exe, ind) for ind in populacao]
        # Coleta os resultados na ordem em que foram submetidos
        resultados = [f.result() for f in futures]
        
    return resultados

# =============================================================================
# RELATÓRIO
# =============================================================================
def gerar_relatorio(metodo: str, exe: str, cfg_inicial: List, cfg_final: List, melhor: float, tempo: float, tentativas: int):
    with open("relatorio_otimizacao.txt", "a", encoding="utf-8") as arq:
        arq.write("\n" + "="*70 + "\n")
        arq.write(f" MÉTODO: {metodo}\n")
        arq.write(f" Executável: {exe}\n")
        arq.write(f" Tempo decorrido: {tempo:.3f} segundos\n")
        arq.write(f" Total de tentativas: {tentativas}\n")
        arq.write("\nParâmetros iniciais:\n")
        arq.write("  " + " ".join(map(str, cfg_inicial)) + "\n")
        arq.write("\nMelhor configuração encontrada:\n")
        arq.write("  " + " ".join(map(str, cfg_final)) + "\n")
        arq.write(f"\nMelhor resultado: {melhor:.6f}\n")
        arq.write("="*70 + "\n")
    print("\n📄 Relatório salvo em: relatorio_otimizacao.txt")

# =============================================================================
# 1) EVOLUÇÃO (Genetic Algorithm)
# =============================================================================
def evolucao(exe: str, cfg0: List, tipos: List[str], modo='max'):
    inicio = time.time()
    TIMEOUT = 1200
    total_evals = 0

    print(f"\n>>> EVOLUÇÃO (GA) INICIADA (Faixa: {MIN_VAL}-{MAX_VAL}) [PARALELO]")
    pop = 40
    ger = 80
    mut = 0.15

    populacao = []
    for _ in range(pop):
        ind = []
        for i,t in enumerate(tipos):
            if t == 'int': ind.append(random.randint(MIN_VAL, MAX_VAL))
            elif t == 'float': ind.append(round(random.uniform(MIN_VAL, MAX_VAL),6))
            else: ind.append(cfg0[i])
        populacao.append(ind)
    populacao[0] = cfg0[:]

    vals_iniciais = avaliar_em_massa(exe, [cfg0])
    total_evals += 1
    melhor_global = vals_iniciais[0]

    for g in range(ger):
        if time.time() - inicio > TIMEOUT:
            print("\n⛔ Tempo máximo atingido!")
            break

        vals = avaliar_em_massa(exe, populacao)
        total_evals += len(populacao)
        
        idx_melhor = max(range(pop), key=lambda i: vals[i]) if modo=='max' else min(range(pop), key=lambda i: vals[i])

        if (modo=='max' and vals[idx_melhor]>melhor_global) or (modo=='min' and vals[idx_melhor]<melhor_global):
            melhor_global = vals[idx_melhor]
            print(f"Geração {g+1} → {melhor_global:.6f}")

        nova = [populacao[idx_melhor][:]] 
        while len(nova) < pop:
            pai = populacao[random.randint(0,pop-1)]
            filho = pai[:]
            for i in range(len(filho)):
                if tipos[i] != 'str' and random.random() < mut:
                    # Ajustado delta para ser proporcional ao range 1000 (+- 120)
                    delta = random.randint(-120,120) if tipos[i]=='int' else random.uniform(-80,80)
                    filho[i] += delta
                    filho[i] = max(MIN_VAL, min(MAX_VAL, filho[i]))
                    filho[i] = int(round(filho[i])) if tipos[i]=='int' else round(filho[i],6)
            nova.append(filho)
        populacao = nova[:]

    cfg_final = populacao[0]
    tempo = time.time() - inicio
    gerar_relatorio("Genetic Algorithm", exe, cfg0, cfg_final, melhor_global, tempo, total_evals)
    return cfg_final, melhor_global

# =============================================================================
# 2) ENXAME OTIMIZADO (PSO com Inércia e Velocity Clamping)
# =============================================================================
def enxame(exe: str, cfg0: List, tipos: List[str], modo='max'):
    inicio = time.time()
    TIMEOUT = 1200
    total_evals = 0

    print(f"\n>>> ENXAME (PSO V2) INICIADO (Faixa: {MIN_VAL}-{MAX_VAL}) [PARALELO]")
    
    # Parâmetros Avançados do PSO
    n_particulas = 40
    iteracoes = 100
    w_max = 0.9  
    w_min = 0.4  
    c1 = 2.05    
    c2 = 2.05    
    v_max_ratio = 0.2 

    # Inicialização
    particulas = []
    velocidades = []
    pbest = []       
    pbest_val = []   

    # Inicializa partículas aleatórias
    for _ in range(n_particulas):
        p = []
        v = []
        for i, t in enumerate(tipos):
            if t == 'int': 
                p.append(random.randint(MIN_VAL, MAX_VAL))
                # Velocidade inicial aumentada para cobrir o range maior
                v.append(random.uniform(-50, 50))
            elif t == 'float': 
                p.append(round(random.uniform(MIN_VAL, MAX_VAL), 6))
                v.append(random.uniform(-50, 50))
            else: 
                p.append(cfg0[i])
                v.append(0)
        particulas.append(p)
        velocidades.append(v)
        pbest.append(p[:]) 
        
    start_val = float('-inf') if modo == 'max' else float('inf')
    pbest_val = [start_val] * n_particulas

    val0 = executar(exe, cfg0)
    total_evals += 1
    melhor_global = val0
    gbest = cfg0[:]
    print(f"Base Inicial: {melhor_global:.6f}")

    for t in range(iteracoes):
        if time.time() - inicio > TIMEOUT:
            print("\n⛔ Tempo máximo atingido!")
            break

        valores = avaliar_em_massa(exe, particulas)
        total_evals += len(particulas)

        for i, val in enumerate(valores):
            melhorou_pessoal = (modo == 'max' and val > pbest_val[i]) or \
                               (modo == 'min' and val < pbest_val[i])
            
            if melhorou_pessoal:
                pbest_val[i] = val
                pbest[i] = particulas[i][:]

                melhorou_global = (modo == 'max' and val > melhor_global) or \
                                  (modo == 'min' and val < melhor_global)
                if melhorou_global:
                    melhor_global = val
                    gbest = particulas[i][:]
                    print(f"Iter {t+1} → {melhor_global:.6f} (Novo Recorde)")

        w = w_max - ((w_max - w_min) * t / iteracoes)

        for i in range(n_particulas):
            for j in range(len(tipos)):
                if tipos[j] == 'str': continue
                
                r1, r2 = random.random(), random.random()
                
                cognitive = c1 * r1 * (pbest[i][j] - particulas[i][j])
                social = c2 * r2 * (gbest[j] - particulas[i][j])
                
                velocidades[i][j] = (w * velocidades[i][j]) + cognitive + social
                
                # Clamp na Velocidade (Baseado no MAX_VAL = 1000)
                limite_v = MAX_VAL * v_max_ratio
                velocidades[i][j] = max(-limite_v, min(limite_v, velocidades[i][j]))
                
                novo_val = particulas[i][j] + velocidades[i][j]
                
                # Tratamento de Fronteiras
                if novo_val < MIN_VAL: 
                    novo_val = MIN_VAL
                    velocidades[i][j] *= -0.5 
                elif novo_val > MAX_VAL:
                    novo_val = MAX_VAL
                    velocidades[i][j] *= -0.5 

                if tipos[j] == 'int':
                    particulas[i][j] = int(round(novo_val))
                else:
                    particulas[i][j] = round(novo_val, 6)

    tempo = time.time() - inicio
    gerar_relatorio("Particle Swarm V2", exe, cfg0, gbest, melhor_global, tempo, total_evals)
    return gbest, melhor_global

# =============================================================================
# 3) HÍBRIDO GA + SWARM OTIMIZADO
# =============================================================================
def hibrido_ga_swarm(exe: str, cfg0: List, tipos: List[str], modo='max'):
    print(f"\n>>> HÍBRIDO OTIMIZADO INICIADO (Faixa: {MIN_VAL}-{MAX_VAL}) [PARALELO]")
    
    inicio = time.time()
    TIMEOUT = 1200 
    total_evals = 0

    # --- FASE 1: GA ---
    pop = 40
    ger_ga = 30 
    mut = 0.2 

    populacao = []
    for _ in range(pop):
        ind = []
        for i, t in enumerate(tipos):
            if t == 'int': ind.append(random.randint(MIN_VAL, MAX_VAL))
            elif t == 'float': ind.append(round(random.uniform(MIN_VAL, MAX_VAL), 6))
            else: ind.append(cfg0[i])
        populacao.append(ind)

    melhor_global = executar(exe, cfg0)
    total_evals += 1
    gbest = cfg0[:]
    
    print("--- FASE 1: GENÉTICO ---")
    for g in range(ger_ga):
        if time.time() - inicio > TIMEOUT: break

        valores = avaliar_em_massa(exe, populacao)
        total_evals += len(populacao)
        
        idx_best = max(range(pop), key=lambda i: valores[i]) if modo == 'max' else \
                   min(range(pop), key=lambda i: valores[i])

        if (modo=='max' and valores[idx_best] > melhor_global) or (modo=='min' and valores[idx_best] < melhor_global):
            melhor_global = valores[idx_best]
            gbest = populacao[idx_best][:]
            print(f"[GA] Geração {g+1} → {melhor_global:.6f}")

        nova = [gbest[:]] 
        while len(nova) < pop:
            pai = populacao[random.randint(0, pop-1)]
            filho = pai[:]
            for i in range(len(filho)):
                if tipos[i] != 'str' and random.random() < mut:
                    # Delta aumentado para +- 100
                    delta = random.uniform(-100, 100)
                    filho[i] = max(MIN_VAL, min(MAX_VAL, filho[i] + delta))
                    filho[i] = int(round(filho[i])) if tipos[i]=='int' else round(filho[i], 6)
            nova.append(filho)
        populacao = nova

    # --- FASE 2: PSO ---
    print("\n--- FASE 2: SWARM (REFINO) ---")
    
    particulas = [ind[:] for ind in populacao]
    velocidades = [[0]*len(cfg0) for _ in range(pop)]
    pbest = [ind[:] for ind in populacao]
    
    # Avaliação inicial do PSO (necessária para definir pbest_val)
    pbest_val = avaliar_em_massa(exe, pbest)
    total_evals += len(pbest)

    it_swarm = 60
    w = 0.5 
    c1, c2 = 2.0, 2.0

    for t in range(it_swarm):
        if time.time() - inicio > TIMEOUT: break

        valores = avaliar_em_massa(exe, particulas)
        total_evals += len(particulas)

        for i, val in enumerate(valores):
            melhorou_pessoal = (modo == 'max' and val > pbest_val[i]) or \
                               (modo == 'min' and val < pbest_val[i])
            if melhorou_pessoal:
                pbest_val[i] = val
                pbest[i] = particulas[i][:]
                
                melhorou_global = (modo == 'max' and val > melhor_global) or \
                                  (modo == 'min' and val < melhor_global)
                if melhorou_global:
                    melhor_global = val
                    gbest = particulas[i][:]
                    print(f"[SWARM] Iter {t+1} → {melhor_global:.6f}")

        for i in range(pop):
            for j in range(len(tipos)):
                if tipos[j] == 'str': continue
                
                r1, r2 = random.random(), random.random()
                
                cog = c1 * r1 * (pbest[i][j] - particulas[i][j])
                soc = c2 * r2 * (gbest[j] - particulas[i][j])
                
                velocidades[i][j] = (w * velocidades[i][j]) + cog + soc
                
                # Clamp Velocidade aumentado (x10)
                velocidades[i][j] = max(-150, min(150, velocidades[i][j]))

                novo = particulas[i][j] + velocidades[i][j]
                
                # Clamp Posição
                if novo < MIN_VAL: novo = MIN_VAL; velocidades[i][j] = 0
                if novo > MAX_VAL: novo = MAX_VAL; velocidades[i][j] = 0
                
                if tipos[j]=='int': particulas[i][j] = int(round(novo))
                else: particulas[i][j] = round(novo, 6)

    tempo = time.time() - inicio
    gerar_relatorio("Hybrid GA + Swarm V2", exe, cfg0, gbest, melhor_global, tempo, total_evals)

    print("\n>>> FIM DO HÍBRIDO")
    print(f"Melhor resultado: {melhor_global:.6f}")
    print("Config final:", " ".join(map(str, gbest)))

    return gbest, melhor_global

# =============================================================================
# MENU PRINCIPAL
# =============================================================================
def menu():
    print("\n" + "="*50)
    print("  1) Genetic Algorithm (Paralelo)")
    print("  2) Particle Swarm V2 (Paralelo)")
    print("  3) Hybrid GA + Swarm V2 (Paralelo)")
    print("  0) Sair")
    print("="*50)

def principal():
    while True:
        menu()
        op = input("\nEscolha → ").strip()
        if op == '0':
            print("Tchau!")
            break
        if op not in '123':
            print("Opção inválida!")
            continue

        linha = input("\nExe + exemplo (ex: modelo.exe baixo 1 2 3): ").strip()
        if not linha:
            # Exemplo padrão ajustado para o novo range se quiser testar
            linha = "modelo10.exe baixo 500 500 500 500 500" 
        
        partes = linha.split()
        exe = partes[0]
        exemplo = " ".join(partes[1:])

        cfg0, tipos = detectar_cfg(exemplo)
        print(f"\nDetectado: {len(cfg0)} params → {tipos}")

        m = input("1=Max 2=Min [1]: ").strip()
        modo = 'min' if m == '2' else 'max'

        if op == '1':
            evolucao(exe, cfg0, tipos, modo)
        elif op == '2':
            enxame(exe, cfg0, tipos, modo)
        elif op == '3':
            hibrido_ga_swarm(exe, cfg0, tipos, modo)

        input("\nENTER para continuar...")

if __name__ == "__main__":
    principal()
