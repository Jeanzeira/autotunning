### 1. Como o Código Funciona (A Lógica)

O script atua como um **gerente** que comanda um **trabalhador** (o seu arquivo `.exe`). O ciclo básico é ilustrado abaixo:



#### **A. O "Cérebro" (Python)**
1.  **Detecção Automática (`detectar_cfg`):**
    * O usuário digita um exemplo de comando.
    * O script analisa cada parâmetro: se parece um número inteiro, trata como `int`; se tem ponto, é `float`; se é texto, é `str`. Isso permite otimizar qualquer programa sem precisar reescrever o código Python.
2.  **A "Ponte" (`executar`):**
    * Esta função usa a biblioteca `subprocess`. Ela pega os números que o algoritmo escolheu, transforma em texto, chama o seu `.exe`, espera ele terminar e captura o que ele escreveu na tela (`stdout`).
    * Ela procura pelo último número que o programa imprimiu para usar como "pontuação" (score).

#### **B. As Estratégias (Os Algoritmos)**
O código oferece 5 maneiras diferentes de buscar o melhor resultado:

1.  **Busca Axial (Pattern Search):**
    * Muda um parâmetro de cada vez. Se melhorar, mantém; se não, tenta o outro lado. É metódico e bom para ajustes finos.
    * *Diferencial:* É o único que sabe lidar bem com opções de texto (ex: trocar "sim" por "nao", "alto" por "medio").
2.  **Genetic Algorithm (Evolução):**
    * Cria uma "população" de soluções aleatórias.
    * As melhores "sobrevivem" e se "reproduzem" (misturam valores) com pequenas mutações. Ótimo para explorar grandes espaços de busca.
3.  **Particle Swarm (Enxame):**
    * Simula um bando de pássaros. Cada solução (partícula) "voa" pelo espaço de busca.
    * Ela é atraída pela sua própria melhor posição histórica e pela melhor posição do grupo inteiro. Tende a convergir rápido.
4.  **Simplex (Poliedro):**
    * Usa uma forma geométrica (triângulo em 2D, tetraedro em 3D) que "rola" morro acima (ou abaixo). Ele reflete, expande ou contrai o poliedro para cercar o ponto ótimo.
5.  **Híbrido GA + Swarm (O Novo Método):**
    * **Fase 1 (Exploração):** Começa rodando o Algoritmo Genético para espalhar bem a busca e evitar ficar preso em soluções ruins locais.
    * **Fase 2 (Refinamento):** Pega a população final do Genético e a transforma em um Enxame (Swarm) para fazer o ajuste fino e convergir rapidamente para o melhor valor.

---

### 2. Como Rodar o Código

Para usar este otimizador, você precisa ter o Python instalado e o programa alvo (o `.exe` que você quer otimizar) na mesma pasta ou acessível.

#### **Passo a Passo:**

1.  **Prepare o Ambiente:**
    * Salve o código Python (ex: `otimizador.py`).
    * Tenha o seu programa alvo pronto (ex: `simulador.exe`). O `simulador.exe` deve receber os parâmetros por linha de comando e imprimir o resultado na tela.

2.  **Inicie o Script:**
    * Abra o terminal (cmd ou PowerShell).
    * Digite: `python otimizador.py`

3.  **Interaja com o Menu:**
    * O menu mostrará as 5 opções. Escolha uma (digite 1 a 5).
    * **O "Pulo do Gato" (Input):** O programa pedirá: `Exe + exemplo`.
    * Você deve digitar o nome do programa seguido de uma configuração inicial válida.
    * *Exemplo:* `meu_programa.exe baixo 10 50.5`
        * O Python entenderá que o 1º parâmetro é texto (`baixo`), o 2º é inteiro (`10`) e o 3º é decimal (`50.5`).

4.  **Defina o Objetivo:**
    * O script perguntará: `1=Max 2=Min`.
    * Escolha `1` se você quer o **maior** valor possível (lucro, pontuação).
    * Escolha `2` se quer o **menor** valor (erro, custo, tempo).

5.  **Aguarde e Acompanhe:**
    * O script mostrará o progresso na tela ("Novo máx: ...", "Geração X...").
    * Se demorar mais de 20 minutos (1200 segundos), ele para automaticamente (timeout).

6.  **Resultado:**
    * Ao final, ele cria um arquivo `relatorio_otimizacao.txt` com a melhor configuração encontrada e o melhor resultado numérico.

### Resumo Técnico

* **Entrada:** Argumentos de linha de comando.
* **Saída Esperada do .exe:** Um número (float) impresso no console (stdout).
* **Controle de Tempo:** Todas as funções têm um `TIMEOUT = 1200` (20 minutos) para evitar loops infinitos.
* **Tratamento de Erros:** Se o `.exe` falhar, o Python assume o valor `-inf` (infinito negativo) para ignorar aquela tentativa.
