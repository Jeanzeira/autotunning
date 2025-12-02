🤖 Otimizador de Programas (Black-Box Optimizer)

Este é um "robô inteligente" feito em Python. O objetivo dele é descobrir a melhor configuração para o seu programa .exe automaticamente, sem que você precise testar milhões de combinações na mão.

Ele roda o seu programa várias vezes, lê o resultado e usa matemática para decidir quais números testar em seguida.

🚀 Como funciona?

Imagine que você tem um programa que simula algo (ex: um motor, um investimento financeiro, um jogo) e ele aceita vários números de entrada. O processo segue este ciclo:

O Python escolhe números aleatórios ou baseados em lógica.

Ele manda esses números para o seu .exe.

Ele lê a resposta (o "score") que o seu .exe mostrou na tela.

Se o resultado for bom, ele aprende e tenta melhorar ainda mais.

📋 O que você precisa?

🐍 Python instalado no seu computador.

💻 O seu programa .exe:

Ele deve aceitar os números via linha de comando (ex: meu_programa.exe 10 20.5).

Ele deve escrever o resultado (um número) na tela (ex: Resultado: 95.5).

🛠️ Como rodar

Coloque o script (otimizador.py) na mesma pasta do seu executável.

Abra o terminal (cmd ou PowerShell) e digite:

python otimizador.py


Escolha uma das estratégias no menu:

🧬 1) Genetic Algorithm: Bom para começar, testa muitas opções variadas (evolução).

🐦 2) Particle Swarm: Simula um enxame, tenta convergir rápido para o melhor resultado.

🔥 3) Híbrido: O mais poderoso. Começa explorando tudo (Genético) e depois faz o ajuste fino (Swarm).

✍️ Exemplo de Uso

Quando o programa pedir "Exe + exemplo", você deve digitar o nome do seu executável seguido de um teste qualquer, para o Python entender o formato.

Exemplo:

simulador.exe baixo 10 50.5


O que o Python entende:

baixo → É texto (não será otimizado).

10 → É número inteiro (será otimizado).

50.5 → É número decimal (será otimizado).

Depois, escolha se você quer Maximizar (lucro, pontos) ou Minimizar (erro, tempo, custo).

⚡ Funcionalidades Especiais

🚀 Multitarefa (Threads): Ele roda vários testes ao mesmo tempo para ser mais rápido, usando todo o poder do seu processador.

🧠 Inteligente: Se o parâmetro for texto (ex: sim/nao), ele mantém fixo. Ele foca em otimizar apenas os números.

📄 Relatório: No final, ele cria um arquivo relatorio_otimizacao.txt com a melhor configuração que encontrou.

⚠️ Dicas Importantes

Travamentos: Se o seu .exe travar ou demorar muito, o Python espera até 30 segundos e depois pula para o próximo teste.

Tempo Limite: O otimizador para automaticamente após 20 minutos (1200 segundos) para não rodar para sempre.
