# Benchmark de Multiplicação de Matrizes (Computação Experimental)

Este repositório contém o código-fonte, scripts de automação e ferramentas de análise estatística utilizados para o artigo da disciplina de **Computação Experimental**. 

O objetivo do experimento é analisar o impacto das diferentes flags de otimização do compilador GCC (`-O0`, `-O1`, `-O2`, `-O3`, `-Ofast`) sobre o desempenho da multiplicação de matrizes de diferentes ordens ($N = 256, 512, 1024, 2048$), avaliando métricas de tempo, uso de memória e contadores de desempenho de hardware (via `perf`).

---

## 📂 Estrutura do Repositório

```text
├── matrix_mult.c          # Implementação em C da multiplicação de matrizes
├── run_benchmark.sh       # Script Bash para automação das execuções do benchmark
├── resultados_perf.csv    # Dados brutos das execuções coletados pelo benchmark
├── analise.py             # Script Python para agregação de dados e gráficos básicos
├── anova_perf.py          # Script Python para análise estatística (ANOVA, Tukey HSD e Boxplots)
├── requirements.txt       # Dependências de pacotes Python para análise
├── .gitignore             # Arquivos ignorados pelo controle de versão
└── resultados/            # Diretório contendo os resultados gerados pelos scripts Python
    ├── graficos/          # Gráficos de barras (tempo, cache, IPC) e Boxplots gerados
    └── tabelas/           # CSVs com consolidação estatística, ANOVA e testes Tukey
```

---

## 🛠️ Requisitos

### Para Executar o Benchmark (Coleta de Dados)
* Sistema Operacional Linux (necessário para o utilitário `perf`)
* Compilador `gcc`
* Utilitários `size`, `/usr/bin/time`, `taskset` e `perf`

### Para Analisar os Resultados (Python)
* Python 3.x
* Pacotes listados no `requirements.txt`. Instale-os com:
  ```bash
  pip install -r requirements.txt
  ```

---

## 🚀 Como Executar

### 1. Execução do Benchmark
O script Bash executa a multiplicação de matrizes várias vezes para cada combinação de tamanho $N$ e flag de otimização do GCC, salvando os resultados brutos em um arquivo CSV.

1. Dê permissão de execução ao script:
   ```bash
   chmod +x run_benchmark.sh
   ```
2. Execute o script:
   ```bash
   ./run_benchmark.sh
   ```
Os resultados brutos da execução (tempo, ciclos, instruções, cache misses, etc.) serão salvos em `resultados_perf.csv`.

### 2. Geração dos Gráficos e Agregações de Desempenho
Rode o script de análise para consolidar as médias e desvios padrão, além de gerar gráficos de barras comparativos por tamanho de matriz:
```bash
python3 analise.py
```
* **Saída**:
  * Tabela consolidada em `resultados/tabelas/resumo_benchmark.csv`
  * Gráficos de barras salvos em `resultados/graficos/` (Tempo, Cache Misses, IPC e Taxa de Cache Miss Rate).

### 3. Análise Estatística (ANOVA & Tukey HSD)
Para verificar se as diferenças observadas entre as flags de otimização são estatisticamente significativas, execute o script de análise de variância:
```bash
python3 anova_perf.py
```
* **Saída**:
  * Resumos e dados detalhados dos testes ANOVA e Tukey em `resultados/tabelas/` (`anova_results.csv`, `tukey_results.csv` e `resumo_estatistico.csv`).
  * Boxplots comparativos para cada métrica salvos em `resultados/graficos/`.
