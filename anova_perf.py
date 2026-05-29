import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# Garantir existência dos diretórios de saída
os.makedirs("resultados/graficos", exist_ok=True)
os.makedirs("resultados/tabelas", exist_ok=True)

CSV_FILE = "resultados_perf.csv"

# =========================================
# LOAD
# =========================================

df = pd.read_csv(CSV_FILE)

print("ANTES:")
print(df.shape)

# =========================================
# COLUNAS NUMÉRICAS
# =========================================

numeric_cols = [
    "N",
    "Tempo",
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

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove linhas inválidas apenas da métrica principal
df = df.dropna(subset=["Tempo"])

print("DEPOIS:")
print(df.shape)

print(df.head())

# =========================================
# MÉTRICAS
# =========================================

metricas = [
    "Tempo",
    "Cycles",
    "Instructions",
    "CacheMisses",
    "BranchMisses",
    "L1LoadMisses",
    "L2Misses",
]

# =========================================
# DATAFRAMES DE RESULTADO
# =========================================

anova_results = []
tukey_results = []

# =========================================
# ANOVA + TUKEY
# =========================================

for metrica in metricas:

    print("\n====================================")
    print(f"ANÁLISE -> {metrica}")
    print("====================================")

    for n in sorted(df["N"].unique()):

        subset = df[df["N"] == n]

        # Remove NaN da métrica atual
        subset = subset.dropna(subset=[metrica])

        # Precisa ter pelo menos 2 grupos
        if subset["Flag"].nunique() < 2:
            continue

        print(f"\n===== N={n} =====")

        # =====================================
        # ANOVA
        # =====================================

        model = ols(f"{metrica} ~ C(Flag)", data=subset).fit()

        tabela = anova_lm(model, typ=2)

        print("\nANOVA:")
        print(tabela)

        # Salvar ANOVA
        anova_results.append(
            {
                "Metrica": metrica,
                "N": n,
                "F": tabela.loc["C(Flag)", "F"],
                "p-value": tabela.loc["C(Flag)", "PR(>F)"],
            }
        )

        # =====================================
        # TUKEY HSD
        # =====================================

        print("\nTukey HSD:")

        tukey = pairwise_tukeyhsd(
            endog=subset[metrica], groups=subset["Flag"], alpha=0.05
        )

        print(tukey)

        # Converter resultados Tukey
        tukey_df = pd.DataFrame(
            data=tukey._results_table.data[1:], columns=tukey._results_table.data[0]
        )

        tukey_df["Metrica"] = metrica
        tukey_df["N"] = n

        tukey_results.append(tukey_df)

        # =====================================
        # BOXPLOT
        # =====================================

        plt.figure(figsize=(10, 6))

        subset.boxplot(column=metrica, by="Flag")

        plt.title(f"{metrica} | N={n}")
        plt.suptitle("")
        plt.xlabel("Flag")
        plt.ylabel(metrica)

        plt.tight_layout()

        filename = f"resultados/graficos/boxplot_{metrica}_N{n}.png"

        plt.savefig(filename)

        plt.close()

        print(f"\n[OK] Boxplot salvo: {filename}")

# =========================================
# EXPORTAR CSVs
# =========================================

anova_df = pd.DataFrame(anova_results)

anova_df.to_csv("resultados/tabelas/anova_results.csv", index=False)

print("\n[OK] anova_results.csv salvo")

if len(tukey_results) > 0:

    tukey_final = pd.concat(tukey_results, ignore_index=True)

    tukey_final.to_csv("resultados/tabelas/tukey_results.csv", index=False)

    print("[OK] tukey_results.csv salvo")

# =========================================
# RESUMO ESTATÍSTICO
# =========================================

summary = df.groupby(["Flag", "N"])[metricas].agg(["mean", "std", "median"])
summary.columns = ["_".join(col).strip() for col in summary.columns.values]
summary = summary.reset_index()

summary.to_csv("resultados/tabelas/resumo_estatistico.csv", index=False)

print("[OK] resumo_estatistico.csv salvo")
