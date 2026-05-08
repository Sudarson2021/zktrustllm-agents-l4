// SPDX-License-Identifier: MIT
//
// DTLS-wrapped RTP proxy for ZKTrustLLM Level 4 media-plane validation.
//
// server mode:
//   Receives DTLS-protected RTP records on a UDP/DTLS port and forwards
//   recovered RTP packets to a local UDP receiver.
//
// client mode:
//   Receives plain RTP packets on a local UDP port and sends each RTP packet
//   as one DTLS record to the DTLS server.
//
// This is a controlled DTLS tunnel/proxy baseline for media-plane KPI measurement.
// It is not WebRTC DTLS-SRTP.

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

static struct sockaddr_in make_udp_addr(const char *host, int port) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);

    if (inet_pton(AF_INET, host, &addr.sin_addr) != 1) {
        fprintf(stderr, "Invalid IPv4 address: %s\n", host);
        exit(EXIT_FAILURE);
    }

    return addr;
}


#define BUF_SIZE 4096
#define HANDSHAKE_TIMEOUT_SEC 10

static const char *PSK_IDENTITY = "zktrustllm-l4-client";
static const unsigned char PSK_KEY[] = {
    0x5a, 0x4b, 0x54, 0x72, 0x75, 0x73, 0x74, 0x4c,
    0x4c, 0x4d, 0x4c, 0x34, 0x44, 0x54, 0x4c, 0x53,
    0x50, 0x53, 0x4b, 0x31, 0x32, 0x33, 0x34, 0x35,
    0x36, 0x37, 0x38, 0x39, 0x41, 0x42, 0x43, 0x44
};

static void die(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

static void print_ssl_error(const char *where, SSL *ssl, int ret) {
    int err = SSL_get_error(ssl, ret);
    fprintf(stderr, "%s failed: SSL_get_error=%d errno=%d\n", where, err, errno);

    unsigned long e;
    while ((e = ERR_get_error()) != 0) {
        char buf[256];
        ERR_error_string_n(e, buf, sizeof(buf));
        fprintf(stderr, "  OpenSSL: %s\n", buf);
    }
}

static struct sockaddr_in make_addr(const char *host, int port) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));

    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);

    if (inet_pton(AF_INET, host, &addr.sin_addr) != 1) {
        fprintf(stderr, "Invalid IPv4 address: %s\n", host);
        exit(EXIT_FAILURE);
    }

    return addr;
}

static int make_udp_bind_socket(const char *host, int port) {
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) die("socket");

    int yes = 1;
    if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes)) < 0) {
        die("setsockopt SO_REUSEADDR");
    }

    struct sockaddr_in addr = make_addr(host, port);
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        die("bind");
    }

    return fd;
}

static int make_udp_connected_socket(const char *host, int port) {
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) die("socket");

    struct sockaddr_in addr = make_addr(host, port);
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        die("connect");
    }

    return fd;
}

static void learn_and_connect_first_peer(int fd, struct sockaddr_in *peer_out) {
    unsigned char peek_buf[1];
    socklen_t peer_len = sizeof(*peer_out);
    memset(peer_out, 0, sizeof(*peer_out));

    fprintf(stderr, "[server] waiting for first DTLS datagram to learn peer\n");

    ssize_t n = recvfrom(
        fd,
        peek_buf,
        sizeof(peek_buf),
        MSG_PEEK,
        (struct sockaddr *)peer_out,
        &peer_len
    );

    if (n < 0) {
        die("recvfrom MSG_PEEK");
    }

    char ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &peer_out->sin_addr, ip, sizeof(ip));
    fprintf(stderr, "[server] learned peer %s:%d\n", ip, ntohs(peer_out->sin_port));

    if (connect(fd, (struct sockaddr *)peer_out, peer_len) < 0) {
        die("server UDP connect to learned peer");
    }
}

static unsigned int psk_server_cb(
    SSL *ssl,
    const char *identity,
    unsigned char *psk,
    unsigned int max_psk_len
) {
    (void)ssl;

    if (!identity) {
        fprintf(stderr, "[server] missing PSK identity\n");
        return 0;
    }

    fprintf(stderr, "[server] PSK identity: %s\n", identity);

    if (strcmp(identity, PSK_IDENTITY) != 0) {
        fprintf(stderr, "[server] unexpected PSK identity\n");
        return 0;
    }

    if (max_psk_len < sizeof(PSK_KEY)) {
        fprintf(stderr, "[server] PSK buffer too small\n");
        return 0;
    }

    memcpy(psk, PSK_KEY, sizeof(PSK_KEY));
    return (unsigned int)sizeof(PSK_KEY);
}

static unsigned int psk_client_cb(
    SSL *ssl,
    const char *hint,
    char *identity,
    unsigned int max_identity_len,
    unsigned char *psk,
    unsigned int max_psk_len
) {
    (void)ssl;
    (void)hint;

    if (max_identity_len <= strlen(PSK_IDENTITY)) {
        fprintf(stderr, "[client] PSK identity buffer too small\n");
        return 0;
    }

    if (max_psk_len < sizeof(PSK_KEY)) {
        fprintf(stderr, "[client] PSK buffer too small\n");
        return 0;
    }

    strcpy(identity, PSK_IDENTITY);
    memcpy(psk, PSK_KEY, sizeof(PSK_KEY));
    return (unsigned int)sizeof(PSK_KEY);
}

static SSL_CTX *make_ctx(bool is_server) {
    SSL_CTX *ctx = SSL_CTX_new(DTLS_method());
    if (!ctx) {
        fprintf(stderr, "SSL_CTX_new failed\n");
        exit(EXIT_FAILURE);
    }

    SSL_CTX_set_min_proto_version(ctx, DTLS1_2_VERSION);
    SSL_CTX_set_max_proto_version(ctx, DTLS1_2_VERSION);

    if (!SSL_CTX_set_cipher_list(ctx, "PSK-AES128-GCM-SHA256:PSK-AES256-GCM-SHA384")) {
        fprintf(stderr, "Failed to set PSK cipher list\n");
        exit(EXIT_FAILURE);
    }

    if (is_server) {
        SSL_CTX_set_psk_server_callback(ctx, psk_server_cb);
    } else {
        SSL_CTX_set_psk_client_callback(ctx, psk_client_cb);
    }

    return ctx;
}

static SSL *make_ssl_with_dgram_bio(SSL_CTX *ctx, int fd, struct sockaddr_in *peer) {
    SSL *ssl = SSL_new(ctx);
    if (!ssl) {
        fprintf(stderr, "SSL_new failed\n");
        exit(EXIT_FAILURE);
    }

    BIO *bio = BIO_new_dgram(fd, BIO_NOCLOSE);
    if (!bio) {
        fprintf(stderr, "BIO_new_dgram failed\n");
        exit(EXIT_FAILURE);
    }

    if (peer) {
        BIO_ctrl(bio, BIO_CTRL_DGRAM_SET_CONNECTED, 0, peer);
    }

    struct timeval timeout;
    timeout.tv_sec = 2;
    timeout.tv_usec = 0;
    BIO_ctrl(bio, BIO_CTRL_DGRAM_SET_RECV_TIMEOUT, 0, &timeout);

    SSL_set_bio(ssl, bio, bio);
    return ssl;
}

static int do_handshake(SSL *ssl, bool is_server) {
    time_t start = time(NULL);

    while (time(NULL) - start < HANDSHAKE_TIMEOUT_SEC) {
        int ret = is_server ? SSL_accept(ssl) : SSL_connect(ssl);

        if (ret == 1) {
            fprintf(stderr, "[%s] DTLS handshake complete\n", is_server ? "server" : "client");
            return 1;
        }

        int err = SSL_get_error(ssl, ret);

        if (err == SSL_ERROR_WANT_READ || err == SSL_ERROR_WANT_WRITE) {
            continue;
        }

        print_ssl_error(is_server ? "SSL_accept" : "SSL_connect", ssl, ret);
        return 0;
    }

    fprintf(stderr, "[%s] DTLS handshake timeout\n", is_server ? "server" : "client");
    return 0;
}

static void run_server(const char *listen_host, int listen_port, const char *out_host, int out_port) {
    SSL_CTX *ctx = make_ctx(true);

    int dtls_fd = make_udp_bind_socket(listen_host, listen_port);

    int out_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (out_fd < 0) {
        perror("socket output");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in out_addr = make_udp_addr(out_host, out_port);

    struct sockaddr_in peer;
    learn_and_connect_first_peer(dtls_fd, &peer);

    SSL *ssl = make_ssl_with_dgram_bio(ctx, dtls_fd, &peer);
    SSL_set_accept_state(ssl);

    if (!do_handshake(ssl, true)) {
        SSL_free(ssl);
        SSL_CTX_free(ctx);
        close(dtls_fd);
        close(out_fd);
        exit(EXIT_FAILURE);
    }

    unsigned char buf[BUF_SIZE];

    while (1) {
        int n = SSL_read(ssl, buf, sizeof(buf));

        if (n > 0) {
            ssize_t sent = sendto(
            out_fd,
            buf,
            (size_t)n,
            0,
            (struct sockaddr *)&out_addr,
            sizeof(out_addr)
        );
            if (sent < 0) {
                perror("[server] send recovered RTP");
                break;
            }
            continue;
        }

        int err = SSL_get_error(ssl, n);

        if (err == SSL_ERROR_WANT_READ || err == SSL_ERROR_WANT_WRITE) {
            continue;
        }

        if (err == SSL_ERROR_ZERO_RETURN) {
            fprintf(stderr, "[server] DTLS connection closed\n");
            break;
        }

        print_ssl_error("SSL_read", ssl, n);
        break;
    }

    SSL_free(ssl);
    SSL_CTX_free(ctx);
    close(dtls_fd);
    close(out_fd);
}

static void run_client(const char *server_host, int server_port, const char *rtp_host, int rtp_port) {
    SSL_CTX *ctx = make_ctx(false);

    int dtls_fd = make_udp_connected_socket(server_host, server_port);
    int rtp_fd = make_udp_bind_socket(rtp_host, rtp_port);

    struct sockaddr_in peer = make_addr(server_host, server_port);

    SSL *ssl = make_ssl_with_dgram_bio(ctx, dtls_fd, &peer);
    SSL_set_connect_state(ssl);

    fprintf(stderr, "[client] connecting DTLS to %s:%d\n", server_host, server_port);

    if (!do_handshake(ssl, false)) {
        SSL_free(ssl);
        SSL_CTX_free(ctx);
        close(dtls_fd);
        close(rtp_fd);
        exit(EXIT_FAILURE);
    }

    fprintf(stderr, "[client] waiting for local RTP on %s:%d\n", rtp_host, rtp_port);

    unsigned char buf[BUF_SIZE];

    while (1) {
        ssize_t n = recvfrom(rtp_fd, buf, sizeof(buf), 0, NULL, NULL);

        if (n < 0) {
            if (errno == EINTR) continue;
            perror("[client] recvfrom RTP");
            break;
        }

        int written = SSL_write(ssl, buf, (int)n);

        if (written <= 0) {
            int err = SSL_get_error(ssl, written);

            if (err == SSL_ERROR_WANT_READ || err == SSL_ERROR_WANT_WRITE) {
                continue;
            }

            print_ssl_error("SSL_write", ssl, written);
            break;
        }
    }

    SSL_free(ssl);
    SSL_CTX_free(ctx);
    close(dtls_fd);
    close(rtp_fd);
}

int main(int argc, char **argv) {
    if (argc != 6) {
        fprintf(stderr, "Usage:\n");
        fprintf(stderr, "  %s server <listen_host> <listen_port> <out_host> <out_port>\n", argv[0]);
        fprintf(stderr, "  %s client <server_host> <server_port> <rtp_input_host> <rtp_input_port>\n", argv[0]);
        return EXIT_FAILURE;
    }

    SSL_library_init();
    SSL_load_error_strings();
    OpenSSL_add_ssl_algorithms();

    const char *mode = argv[1];

    if (strcmp(mode, "server") == 0) {
        run_server(argv[2], atoi(argv[3]), argv[4], atoi(argv[5]));
    } else if (strcmp(mode, "client") == 0) {
        run_client(argv[2], atoi(argv[3]), argv[4], atoi(argv[5]));
    } else {
        fprintf(stderr, "Unknown mode: %s\n", mode);
        return EXIT_FAILURE;
    }

    EVP_cleanup();
    return EXIT_SUCCESS;
}
