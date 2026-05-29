#!/bin/bash

set -u

# ================================
# Verificação de dependências
# ================================
for cmd in gcc size /usr/bin/time taskset perf; do
    if ! command -v "$cmd" &> /dev/null && [ ! -f "$cmd" ]; then
        echo "Erro: comando '$cmd' não encontrado." >&2
        exit 1
    fi
done

# ================================
# Configurações
# ================================
FLAGS=("-O0" "-O1" "-O2" "-O3" "-Ofast")
SIZES=(256 512 1024 2048)

REPETICOES_PEQUENAS=30
REPETICOES_GRANDES=10

ARQUIVO_C="matrix_mult.c"
EXEC="prog_exec"

# Alinhado com o arquivo de leitura do script Python
CSV_OUT="resultados_perf.csv"

# ================================
# Eventos PERF (L3 mapeado como LLC)
# ================================
EVENTS="\
cycles,\
instructions,\
cache-references,\
cache-misses,\
branches,\
branch-misses,\
L1-dcache-loads,\
L1-dcache-load-misses,\
l2_cache_accesses_from_dc_misses,\
l2_cache_misses_from_dc_misses,\
LLC-loads,\
LLC-load-misses"

# ================================
# Cabeçalho CSV
# ================================
echo "Flag,N,Rep,Tempo,RSS,Text,\
Cycles,Instructions,\
CacheReferences,CacheMisses,\
Branches,BranchMisses,\
L1Loads,L1LoadMisses,\
L2Access,L2Misses,\
L3Access,L3Misses" > "$CSV_OUT"

# ================================
# Benchmark
# ================================
for N in "${SIZES[@]}"; do

    if [ "$N" -ge 2048 ]; then
        REP=$REPETICOES_GRANDES
    else
        REP=$REPETICOES_PEQUENAS
    fi

    echo "======================================"
    echo "N=$N | Repetições=$REP"
    echo "======================================"

    for FLAG in "${FLAGS[@]}"; do

        echo "[COMPILANDO] $FLAG"

        gcc -std=c99 -march=native $FLAG -DN=$N "$ARQUIVO_C" -o "$EXEC"

        if [ $? -ne 0 ]; then
            echo "Erro compilando $FLAG" >&2
            continue
        fi

        TEXT_SIZE=$(size "$EXEC" | awk 'NR==2 {print $1}')

        for ((i=1; i<=REP; i++)); do

            echo " -> Execução $i/$REP"

            PAD_LEN=$((RANDOM % 4096 + 1))
            printf -v RANDOM_PAD '%*s' "$PAD_LEN" ""

            OUTPUT=$(env PADDING="$RANDOM_PAD" \
                /usr/bin/time -v \
                perf stat \
                -e "$EVENTS" \
                taskset -c 0 ./"$EXEC" \
                2>&1)

            # ============================
            # Extração tempo/RSS
            # ============================
            TEMPO=$(echo "$OUTPUT" | awk '/TEMPO:/ {print $2}')
            RSS=$(echo "$OUTPUT" | awk -F': ' '/Maximum resident set size/ {print $2}')

            # ============================
            # PERF counters
            # ============================
            extract_perf () {
                echo "$OUTPUT" | \
                grep "$1" | \
                head -n1 | \
                awk '{print $1}' | \
                tr -d ','
            }

            CYCLES=$(extract_perf "cycles")
            INSTR=$(extract_perf "instructions")
            CACHE_REF=$(extract_perf "cache-references")
            CACHE_MISS=$(extract_perf "cache-misses")
            BRANCHES=$(extract_perf "branches")
            BRANCH_MISS=$(extract_perf "branch-misses")

            L1_LOADS=$(extract_perf "L1-dcache-loads")
            L1_MISS=$(extract_perf "L1-dcache-load-misses")

            L2_ACCESS=$(extract_perf "l2_cache_accesses_from_dc_misses")
            L2_MISS=$(extract_perf "l2_cache_misses_from_dc_misses")

            # Mapeamento atualizado para aliases genéricos do LLC (L3)
            L3_ACCESS=$(extract_perf "LLC-loads")
            L3_MISS=$(extract_perf "LLC-load-misses")

            # ============================
            # Sanitização
            # ============================
            sanitize () {
                local val="$1"

                if [[ -z "$val" || "$val" == "<not"* ]]; then
                    echo "NA"
                else
                    echo "$val"
                fi
            }

            CYCLES=$(sanitize "$CYCLES")
            INSTR=$(sanitize "$INSTR")
            CACHE_REF=$(sanitize "$CACHE_REF")
            CACHE_MISS=$(sanitize "$CACHE_MISS")
            BRANCHES=$(sanitize "$BRANCHES")
            BRANCH_MISS=$(sanitize "$BRANCH_MISS")
            L1_LOADS=$(sanitize "$L1_LOADS")
            L1_MISS=$(sanitize "$L1_MISS")
            L2_ACCESS=$(sanitize "$L2_ACCESS")
            L2_MISS=$(sanitize "$L2_MISS")
            L3_ACCESS=$(sanitize "$L3_ACCESS")
            L3_MISS=$(sanitize "$L3_MISS")

            # ============================
            # Validação
            # ============================
            if [ -z "$TEMPO" ] || [ -z "$RSS" ]; then
                echo "Amostra inválida. Ignorando..." >&2
                continue
            fi

            # ============================
            # CSV
            # ============================
            echo "$FLAG,$N,$i,$TEMPO,$RSS,$TEXT_SIZE,\
$CYCLES,$INSTR,\
$CACHE_REF,$CACHE_MISS,\
$BRANCHES,$BRANCH_MISS,\
$L1_LOADS,$L1_MISS,\
$L2_ACCESS,$L2_MISS,\
$L3_ACCESS,$L3_MISS" >> "$CSV_OUT"

        done

        echo "[OK] $FLAG concluído"
        echo "--------------------------------------"

    done
done

rm -f "$EXEC"

echo "======================================"
echo "Benchmark finalizado!"
echo "Saída: $CSV_OUT"
echo "======================================"
