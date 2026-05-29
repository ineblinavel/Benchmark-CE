
#define _POSIX_C_SOURCE 199309L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef N
#define N 1024
#endif

#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 199901L
#define RESTRICT restrict
#else
#define RESTRICT
#endif

double *allocate_matrix() { return (double *)malloc(N * N * sizeof(double)); }

int main() {
    srand(1337);

    double *RESTRICT A = allocate_matrix();
    double *RESTRICT B = allocate_matrix();
    double *RESTRICT C = allocate_matrix();

    if (!A || !B || !C) {
        fprintf(stderr, "Erro de alocação.\n");
        return 1;
    }

    for (int i = 0; i < N * N; i++) {
        A[i] = (double)(rand() % 100) / 10.0;
        B[i] = (double)(rand() % 100) / 10.0;
        C[i] = 0.0;
    }

    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    /*
     * Loop order i-j-k:
     * propositalmente desfavorável para localidade espacial
     * da matriz B, permitindo observar impactos de cache.
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

    /*
     * volatile impede otimizações agressivas
     * e eliminações indevidas.
     */
    volatile double checksum = 0.0;

    for (int i = 0; i < N * N; i++) {
        checksum += C[i];
    }

    printf("TEMPO: %.6f\n", time_spent);
    fprintf(stderr, "CHECKSUM: %.4f\n", checksum);

    free(A);
    free(B);
    free(C);

    return 0;
}
