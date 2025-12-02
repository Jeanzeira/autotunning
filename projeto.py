import subprocess
import sys
import random
import time
import concurrent.futures
import os
from typing import List, Tuple

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
        res = subprocess.run([exe] + [str(x) for x in cfg], 
                           capture_output=True, text=True, timeout=30)
        out = res.stdout.strip()
        valor = float(out.split(":")[-1].strip()) if ":" in out else float(out)
        return valor
    except:
        return float('-inf')

def avaliar_em_massa(exe: str, populacao: List[List]) -> List[float]:
    """Avalia uma lista de configurações em paralelo usando Threads"""
    max_workers = min(32, (os.cpu_count() or 4) * 4) 
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        func = lambda p: executar(exe, p)
        resultados = list(executor.map(func, populacao))
    return resultados

# =============================================================================
# RELATÓRIO
# =============================================================================
def gerar_relatorio(metodo: str, exe: str, cfg_inicial: List, cfg_final: List, melhor: float, tempo: float):
    with open("relatorio_otimizacao.txt", "a", encoding="utf-8") as arq:
        arq.write("\n" + "="*70 + "\n")
        arq.write(f" MÉTODO: {metodo}\n")
        arq.write(f" Executável: {exe}\n")
        arq.write(f" Tempo decorrido: {tempo:.3f} segundos\n")
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

    print("\n>>> EVOLUÇÃO (GA) INICIADA (PARALELIZADO)")
    pop = 40
    ger = 80
    mut = 0.15

    populacao = []
    for _ in range(pop):
        ind = []
        for i,t in enumerate(tipos):
            if t == 'int': ind.append(random.randint(1,100))
            elif t == 'float': ind.append(round(random.uniform(1,100),6))
            else: ind.append(cfg0[i])
        populacao.append(ind)
    populacao[0] = cfg0[:]

    vals_iniciais = avaliar_em_massa(exe, [cfg0])
    melhor_global = vals_iniciais[0]

    for g in range(ger):
        if time.time() - inicio > TIMEOUT:
            print("\n⛔ Tempo máximo atingido!")
            break

        vals = avaliar_em_massa(exe, populacao)
        
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
                    delta = random.randint(-12,12) if tipos[i]=='int' else random.uniform(-8,8)
                    filho[i] += delta
                    filho[i] = max(1, min(100, filho[i]))
                    filho[i] = int(round(filho[i])) if tipos[i]=='int' else round(filho[i],6)
            nova.append(filho)
        populacao = nova[:]

    cfg_final = populacao[0]
    tempo = time.time() - inicio
    gerar_relatorio("Genetic Algorithm", exe, cfg0, cfg_final, melhor_global, tempo)
    return cfg_final, melhor_global

# =============================================================================
# 2) ENXAME OTIMIZADO (PSO com Inércia e Velocity Clamping)
# =============================================================================
def enxame(exe: str, cfg0: List, tipos: List[str], modo='max'):
    inicio = time.time()
    TIMEOUT = 1200

    print("\n>>> ENXAME (PSO V2) INICIADO (PARALELIZADO)")
    
    # Parâmetros Avançados do PSO
    n_particulas = 40
    iteracoes = 100
    w_max = 0.9  # Inércia inicial (Exploração)
    w_min = 0.4  # Inércia final (Explotação)
    c1 = 2.05    # Influência Cognitiva (Melhor Pessoal)
    c2 = 2.05    # Influência Social (Melhor Global)
    v_max_ratio = 0.2 # Limite de velocidade (20% do espaço de busca)

    # Inicialização
    particulas = []
    velocidades = []
    pbest = []       # Melhor posição pessoal de cada partícula
    pbest_val = []   # Melhor valor pessoal de cada partícula

    # Inicializa partículas aleatórias
    for _ in range(n_particulas):
        p = []
        v = []
        for i, t in enumerate(tipos):
            if t == 'int': 
                p.append(random.randint(1, 100))
                v.append(random.uniform(-5, 5))
            elif t == 'float': 
                p.append(round(random.uniform(1, 100), 6))
                v.append(random.uniform(-5, 5))
            else: 
                p.append(cfg0[i])
                v.append(0)
        particulas.append(p)
        velocidades.append(v)
        pbest.append(p[:]) # Cópia
        
    # Inicializa valores de pbest com infinito negativo/positivo
    start_val = float('-inf') if modo == 'max' else float('inf')
    pbest_val = [start_val] * n_particulas

    # Avaliação Inicial do cfg0 fornecido pelo usuário para garantir que ele entre na disputa
    val0 = executar(exe, cfg0)
    melhor_global = val0
    gbest = cfg0[:]
    print(f"Base Inicial: {melhor_global:.6f}")

    for t in range(iteracoes):
        if time.time() - inicio > TIMEOUT:
            print("\n⛔ Tempo máximo atingido!")
            break

        # 1. Avaliação em Massa
        valores = avaliar_em_massa(exe, particulas)

        # 2. Atualizar Personal Best e Global Best
        for i, val in enumerate(valores):
            # Atualiza PBest (Melhor Pessoal)
            melhorou_pessoal = (modo == 'max' and val > pbest_val[i]) or \
                               (modo == 'min' and val < pbest_val[i])
            
            if melhorou_pessoal:
                pbest_val[i] = val
                pbest[i] = particulas[i][:]

                # Atualiza GBest (Melhor Global)
                melhorou_global = (modo == 'max' and val > melhor_global) or \
                                  (modo == 'min' and val < melhor_global)
                if melhorou_global:
                    melhor_global = val
                    gbest = particulas[i][:]
                    print(f"Iter {t+1} → {melhor_global:.6f} (Novo Recorde)")

        # 3. Decaimento da Inércia (Linear)
        w = w_max - ((w_max - w_min) * t / iteracoes)

        # 4. Atualizar Velocidade e Posição
        for i in range(n_particulas):
            for j in range(len(tipos)):
                if tipos[j] == 'str': continue
                
                # Sorteia r1 e r2
                r1, r2 = random.random(), random.random()
                
                # --- FÓRMULA CANÔNICA DO PSO ---
                # Velocidade = Inércia + Cognitivo + Social
                cognitive = c1 * r1 * (pbest[i][j] - particulas[i][j])
                social = c2 * r2 * (gbest[j] - particulas[i][j])
                
                velocidades[i][j] = (w * velocidades[i][j]) + cognitive + social
                
                # Clamp na Velocidade (Evita explosão)
                limite_v = 100 * v_max_ratio
                velocidades[i][j] = max(-limite_v, min(limite_v, velocidades[i][j]))
                
                # Atualiza Posição
                novo_val = particulas[i][j] + velocidades[i][j]
                
                # Tratamento de Fronteiras (Parede Refletora simples ou Clamp)
                if novo_val < 1: 
                    novo_val = 1
                    velocidades[i][j] *= -0.5 # Inverte velocidade (quica)
                elif novo_val > 100:
                    novo_val = 100
                    velocidades[i][j] *= -0.5 # Inverte velocidade (quica)

                # Arredondamento conforme tipo
                if tipos[j] == 'int':
                    particulas[i][j] = int(round(novo_val))
                else:
                    particulas[i][j] = round(novo_val, 6)

    tempo = time.time() - inicio
    gerar_relatorio("Particle Swarm V2", exe, cfg0, gbest, melhor_global, tempo)
    return gbest, melhor_global

# =============================================================================
# 3) HÍBRIDO GA + SWARM OTIMIZADO
# =============================================================================
def hibrido_ga_swarm(exe: str, cfg0: List, tipos: List[str], modo='max'):
    print("\n>>> MÉTODO HÍBRIDO OTIMIZADO INICIADO")
    
    inicio = time.time()
    TIMEOUT = 1200 

    # --- FASE 1: GA (Exploração Global Rápida) ---
    pop = 40
    ger_ga = 30 # Menos gerações, deixa o refino pro PSO
    mut = 0.2   # Mutação um pouco mais alta para espalhar bem

    populacao = []
    for _ in range(pop):
        ind = []
        for i, t in enumerate(tipos):
            if t == 'int': ind.append(random.randint(1, 100))
            elif t == 'float': ind.append(round(random.uniform(1, 100), 6))
            else: ind.append(cfg0[i])
        populacao.append(ind)

    melhor_global = executar(exe, cfg0)
    gbest = cfg0[:]
    
    print("--- FASE 1: GENÉTICO ---")
    for g in range(ger_ga):
        if time.time() - inicio > TIMEOUT: break

        valores = avaliar_em_massa(exe, populacao)
        
        idx_best = max(range(pop), key=lambda i: valores[i]) if modo == 'max' else \
                   min(range(pop), key=lambda i: valores[i])

        if (modo=='max' and valores[idx_best] > melhor_global) or (modo=='min' and valores[idx_best] < melhor_global):
            melhor_global = valores[idx_best]
            gbest = populacao[idx_best][:]
            print(f"[GA] Geração {g+1} → {melhor_global:.6f}")

        # Elitismo + Cruzamento Simples
        nova = [gbest[:]] 
        while len(nova) < pop:
            pai = populacao[random.randint(0, pop-1)]
            filho = pai[:]
            for i in range(len(filho)):
                if tipos[i] != 'str' and random.random() < mut:
                    delta = random.uniform(-10, 10)
                    filho[i] = max(1, min(100, filho[i] + delta))
                    filho[i] = int(round(filho[i])) if tipos[i]=='int' else round(filho[i], 6)
            nova.append(filho)
        populacao = nova

    # --- FASE 2: PSO (Refino Local com Momentum) ---
    print("\n--- FASE 2: SWARM (REFINO) ---")
    
    # Converte população final do GA em partículas
    particulas = [ind[:] for ind in populacao]
    # Reinicializa velocidades zeradas
    velocidades = [[0]*len(cfg0) for _ in range(pop)]
    # O PBest inicial é a posição atual que veio do GA
    pbest = [ind[:] for ind in populacao]
    # Precisamos avaliar para pegar os valores de pbest
    pbest_val = avaliar_em_massa(exe, pbest)

    it_swarm = 60
    w = 0.5    # Inércia média constante para refino
    c1, c2 = 2.0, 2.0

    for t in range(it_swarm):
        if time.time() - inicio > TIMEOUT: break

        valores = avaliar_em_massa(exe, particulas)

        for i, val in enumerate(valores):
            # Atualiza PBest
            melhorou_pessoal = (modo == 'max' and val > pbest_val[i]) or \
                               (modo == 'min' and val < pbest_val[i])
            if melhorou_pessoal:
                pbest_val[i] = val
                pbest[i] = particulas[i][:]
                
                # Atualiza GBest
                melhorou_global = (modo == 'max' and val > melhor_global) or \
                                  (modo == 'min' and val < melhor_global)
                if melhorou_global:
                    melhor_global = val
                    gbest = particulas[i][:]
                    print(f"[SWARM] Iter {t+1} → {melhor_global:.6f}")

        # Atualiza Velocidade e Posição
        for i in range(pop):
            for j in range(len(tipos)):
                if tipos[j] == 'str': continue
                
                r1, r2 = random.random(), random.random()
                
                cog = c1 * r1 * (pbest[i][j] - particulas[i][j])
                soc = c2 * r2 * (gbest[j] - particulas[i][j])
                
                velocidades[i][j] = (w * velocidades[i][j]) + cog + soc
                
                # Clamp Velocidade (mais restrito na fase híbrida)
                velocidades[i][j] = max(-15, min(15, velocidades[i][j]))

                novo = particulas[i][j] + velocidades[i][j]
                
                # Clamp Posição
                if novo < 1: novo = 1; velocidades[i][j] = 0
                if novo > 100: novo = 100; velocidades[i][j] = 0
                
                if tipos[j]=='int': particulas[i][j] = int(round(novo))
                else: particulas[i][j] = round(novo, 6)

    tempo = time.time() - inicio
    gerar_relatorio("Hybrid GA + Swarm V2", exe, cfg0, gbest, melhor_global, tempo)

    print("\n>>> FIM DO HÍBRIDO")
    print(f"Melhor resultado: {melhor_global:.6f}")
    print("Config final:", " ".join(map(str, gbest)))

    return gbest, melhor_global

# =============================================================================
# MENU PRINCIPAL
# =============================================================================
def menu():
    print("\n" + "="*50)
    print("  1) Genetic Algorithm")
    print("  2) Particle Swarm V2 (Inércia + Velocity)")
    print("  3) Hybrid GA + Swarm V2")
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
            linha = "modelo10.exe baixo 1 1 1 1 1 1 1 1 1"
        
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
