#!/bin/bash

# Exigir declaração de variáveis e falhar em caso de erros simples
set -u

# 1. Verificar dependências de sistema necessárias
for cmd in gcc size /usr/bin/time taskset; do
    if ! command -v "$cmd" &> /dev/null && [ ! -f "$cmd" ]; then
        echo "Erro: O comando '$cmd' não está disponível no sistema." >&2
        exit 1
    fi
done

# Parâmetros de execução
FLAGS=("-O0" "-O1" "-O2" "-O3" "-Ofast")
SIZES=(256 512 1024 2048)
REPETICOES_PEQUENAS=30
REPETICOES_GRANDES=10

ARQUIVO_C="matrix_mult.c"
SAIDA_DADOS="resultados_benchmark.csv"

# Inicializar cabeçalho do arquivo de saída
echo "Flag,N,Repeticao,Tempo(s),MemoriaRSS(KB),SegmentoText(Bytes)" > "$SAIDA_DADOS"

for N in "${SIZES[@]}"; do

    # Redução estatística controlada para tamanhos maiores
    if [ "$N" -ge 2048 ]; then
        REP=$REPETICOES_GRANDES
    else
        REP=$REPETICOES_PEQUENAS
    fi

    echo "========================================="
    echo "Iniciando rodada para N=$N | Amostras: $REP"
    echo "========================================="

    for flag in "${FLAGS[@]}"; do

        echo "Compilando com $flag..."

        # Compilação forçando o padrão C99 para compatibilidade do modificador restrict
        gcc -std=c99 $flag -DN=$N "$ARQUIVO_C" -o prog_exec

        if [ $? -ne 0 ]; then
            echo "Erro crítico na compilação com $flag para N=$N. Pulando." >&2
            continue
        fi

        # Extração isolada do segmento .text do executável binário
        TAMANHO_TEXT=$(size prog_exec | awk 'NR==2 {print $1}')

        for i in $(seq 1 "$REP"); do
            echo " -> Executando $i/$REP ($flag | N=$N)"

            # Randomização eficiente de ambiente em puro Bash (sem forks de processo)
            # Cria uma string de espaços vazios de tamanho aleatório entre 1 e 4096 bytes
            PAD_LEN=$((RANDOM % 4096 + 1))
            printf -v RANDOM_PAD '%*s' "$PAD_LEN" ""

            # Execução fixada na CPU 0 e captura de saídas
            RESUMO_TIME=$(env PADDING="$RANDOM_PAD" \
                /usr/bin/time -v taskset -c 0 ./prog_exec 2>&1)

            # Parsing robusto utilizando âncoras textuais estruturadas do awk
            TEMPO_C=$(echo "$RESUMO_TIME" | awk '/TEMPO:/ {print $2}')
            MEMORIA_RSS=$(echo "$RESUMO_TIME" | awk -F': ' '/Maximum resident set size/ {print $2}')

            # Validação defensiva de dados coletados
            if [ -z "$TEMPO_C" ] || [ -z "$MEMORIA_RSS" ]; then
                echo "Aviso: Coleta corrompida na rodada $i de $flag (N=$N). Descartando amostra." >&2
                continue
            fi

            # Exportação de resultados seguros
            echo "$flag,$N,$i,$TEMPO_C,$MEMORIA_RSS,$TAMANHO_TEXT" >> "$SAIDA_DADOS"
        done

        echo "Concluído: $flag para N=$N"
        echo "-----------------------------------------"
    done
done

# Limpeza do executável temporário
rm -f prog_exec

echo "========================================="
echo "Experimento finalizado com sucesso!"
echo "Resultados consolidados em: $SAIDA_DADOS"
echo "========================================="