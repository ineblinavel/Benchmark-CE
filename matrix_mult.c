#define _POSIX_C_SOURCE 199309L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef N
#define N 1024
#endif

/* Define restrict de forma segura baseada na conformidade com o padrão C99+ */
#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 199901L
#define RESTRICT restrict
#else
#define RESTRICT
#endif

/* Alocação contígua em heap (flat array) */
double *allocate_matrix() { return (double *)malloc(N * N * sizeof(double)); }

int main() {
    /* Forçar semente determinística para reprodutibilidade dos dados
     * aritméticos */
    srand(1337);

    double *RESTRICT A = allocate_matrix();
    double *RESTRICT B = allocate_matrix();
    double *RESTRICT C = allocate_matrix();

    if (!A || !B || !C) {
        fprintf(stderr, "Erro de alocação de memória.\n");
        return 1;
    }

    /* Inicialização */
    for (int i = 0; i < N * N; i++) {
        A[i] = (double)(rand() % 100) / 10.0;
        B[i] = (double)(rand() % 100) / 10.0;
        C[i] = 0.0;
    }

    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);
    /*
     * Algoritmo Convencional (i-j-k):
     * Apresenta sérios gargalos de cache L1/L2 devido ao acesso não contíguo
     * (stride longo) à matriz B.
     */
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            double sum = 0.0;
            for (int k = 0; k < N; k++) {
                sum += A[i * N + k] * B[k * N + j];
            }
            C[i * N + j] = sum;
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double time_spent =
        (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;

    /* Checksum robusto para impedir que o compilador ignore a malha (DCE) */
    double checksum = 0.0;
    for (int i = 0; i < N * N; i++) {
        checksum += C[i];
    }

    /* Saída padronizada de dados */
    printf("TEMPO: %.6f\n", time_spent);
    fprintf(stderr, "CHECKSUM: %.4f\n", checksum);

    free(A);
    free(B);
    free(C);

    return 0;
}   