import os
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================
# CONFIGURAÇÃO (Alinhado com o CSV gerado pelo Bash)
# =========================================================
ARQUIVO = "resultados_perf.csv"

# =========================================================
# LEITURA DOS DADOS
# =========================================================
df = pd.read_csv(ARQUIVO)

# Colunas brutas presentes no CSV gerado pelo script Bash
colunas_brutas = [
    "Tempo",
    "RSS",
    "Text",
    "Cycles",
    "Instructions",
    "CacheReferences",
    "CacheMisses",
    "Branches",
    "BranchMisses",
    "L1Loads",
    "L1LoadMisses",
    "L2Access",
    "L2Misses",
    "L3Access",
    "L3Misses",
]

# Garantir tipos numéricos (trata os "NA" gerados pela sanitização do Bash como NaN)
for col in colunas_brutas:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Calcular o IPC dinamicamente (Instruções por Ciclo) antes da agregação
df["IPC"] = df["Instructions"] / df["Cycles"]

# =========================================================
# AGREGAÇÃO E MÉTRIQUES ESTATÍSTICAS
# =========================================================
agrupado = df.groupby(["N", "Flag"]).agg(
    {
        "Tempo": ["mean", "std"],
        "RSS": ["mean", "std"],
        "Text": "mean",
        "CacheMisses": ["mean", "std"],
        "CacheReferences": ["mean", "std"],
        "Instructions": ["mean", "std"],
        "Cycles": ["mean", "std"],
        "IPC": ["mean", "std"],
    }
)

# Achatar o índice de colunas multinível (ex: Tempo_mean, Tempo_std)
agrupado.columns = ["_".join(col).strip("_") for col in agrupado.columns.values]
agrupado = agrupado.reset_index()

# =========================================================
# EXPORTAR TABELA CONSOLIDADA
# =========================================================
os.makedirs("resultados/tabelas", exist_ok=True)
os.makedirs("resultados/graficos", exist_ok=True)
agrupado.to_csv("resultados/tabelas/resumo_benchmark.csv", index=False)
print("Resumo salvo com sucesso em resultados/tabelas/resumo_benchmark.csv")

# =========================================================
# GERAÇÃO DOS PLOTS POR TAMANHO N
# =========================================================
flags_ordem = ["-O0", "-O1", "-O2", "-O3", "-Ofast"]

# 1. TEMPO DE EXECUÇÃO
for N in sorted(df["N"].unique()):
    subset = agrupado[agrupado["N"] == N]
    subset = subset.set_index("Flag").loc[flags_ordem].reset_index()

    plt.figure(figsize=(8, 5))
    plt.bar(
        subset["Flag"],
        subset["Tempo_mean"],
        yerr=subset["Tempo_std"],
        capsize=5,
        color="skyblue",
        edgecolor="black",
    )
    plt.ylabel("Tempo (s)")
    plt.xlabel("Flags GCC")
    plt.title(f"Tempo de Execução - N={N}")
    plt.tight_layout()
    plt.savefig(f"resultados/graficos/tempo_N_{N}.png")
    plt.close()

# 2. CACHE MISSES BRUTOS
for N in sorted(df["N"].unique()):
    subset = agrupado[agrupado["N"] == N]
    subset = subset.set_index("Flag").loc[flags_ordem].reset_index()

    plt.figure(figsize=(8, 5))
    plt.bar(
        subset["Flag"],
        subset["CacheMisses_mean"],
        yerr=subset["CacheMisses_std"],
        capsize=5,
        color="salmon",
        edgecolor="black",
    )
    plt.ylabel("Cache Misses")
    plt.xlabel("Flags GCC")
    plt.title(f"Cache Misses - N={N}")
    plt.tight_layout()
    plt.savefig(f"resultados/graficos/cache_misses_N_{N}.png")
    plt.close()

# 3. INSTRUCTIONS PER CYCLE (IPC)
for N in sorted(df["N"].unique()):
    subset = agrupado[agrupado["N"] == N]
    subset = subset.set_index("Flag").loc[flags_ordem].reset_index()

    plt.figure(figsize=(8, 5))
    plt.bar(
        subset["Flag"],
        subset["IPC_mean"],
        yerr=subset["IPC_std"],
        capsize=5,
        color="lightgreen",
        edgecolor="black",
    )
    plt.ylabel("IPC")
    plt.xlabel("Flags GCC")
    plt.title(f"Instructions Per Cycle - N={N}")
    plt.tight_layout()
    plt.savefig(f"resultados/graficos/ipc_N_{N}.png")
    plt.close()

# 4. TAXA DE CACHE MISS RATE (%)
df["MissRate"] = (df["CacheMisses"] / df["CacheReferences"]) * 100
missrate_grouped = (
    df.groupby(["N", "Flag"])["MissRate"].agg(["mean", "std"]).reset_index()
)

for N in sorted(df["N"].unique()):
    subset = missrate_grouped[missrate_grouped["N"] == N]
    subset = subset.set_index("Flag").loc[flags_ordem].reset_index()

    plt.figure(figsize=(8, 5))
    plt.bar(
        subset["Flag"],
        subset["mean"],
        yerr=subset["std"],
        capsize=5,
        color="orchid",
        edgecolor="black",
    )
    plt.ylabel("Cache Miss Rate (%)")
    plt.xlabel("Flags GCC")
    plt.title(f"Taxa de Cache Misses - N={N}")
    plt.tight_layout()
    plt.savefig(f"resultados/graficos/missrate_N_{N}.png")
    plt.close()

print("Todos os gráficos foram gerados.")
