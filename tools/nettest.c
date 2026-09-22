/*
 * nettest.c - the network core, a host and guests in one process.
 *
 *   cc -DSR2_TEST -I net -o nettest tools/nettest.c net/sr2net.c && ./nettest
 *
 * Every net has a real UDP socket on loopback; the clock is simulated and
 * every net is polled each tick, so a run takes milliseconds. A third of
 * the datagrams are dropped through the test hook for the second half,
 * so the reliable class and the timers are exercised, not just the happy
 * path. Prints one line per check; exits 1 on the first failure.
 */
#include "sr2net.h"
#include "sock.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define N 6
static sr2_net *nets[N];
static const char *names[N] = {"Host", "G1", "G2", "G3", "G4", "G5"};
static int alive[N];
static uint32_t now = 100000;
static unsigned lcg = 12345;
static int drop_pct;

static uint16_t dir_port;           /* the directory, when the wrapper started one */
static uint16_t drop_to;            /* a port nothing direct reaches: the relay must carry it */
static uint16_t spy_from, spy_to;   /* the link watched: its socket and last reliable seq kept */
static sock_t spy_sock = SOCK_INVALID;
static uint32_t spy_seq;

static uint16_t local_port(sock_t s)
{
    struct sockaddr_in sa;
    socklen_t salen = sizeof sa;
    if (getsockname(s, (struct sockaddr *)&sa, &salen) != 0)
        return 0;
    return ntohs(sa.sin_port);
}

static int drop(sock_t s, const sock_addr *to, const void *data, int len)
{
    const uint8_t *d = data;
    if (spy_from && to->port == spy_to && len >= 16 && (d[5] & 1) && local_port(s) == spy_from) {
        uint32_t seq = d[8] | d[9] << 8 | d[10] << 16 | (uint32_t)d[11] << 24;
        spy_sock = s;
        if ((int32_t)(seq - spy_seq) > 0)
            spy_seq = seq;
    }
    if (drop_to && to->port == drop_to)
        return 1;
    lcg = lcg * 1103515245u + 12345u;
    return drop_pct && (int)((lcg >> 16) % 100) < drop_pct;
}

static void logline(void *ctx, const char *line)
{
    printf("      [%s] %s\n", (const char *)ctx, line);
}

static void fail(const char *what)
{
    printf("FAIL: %s\n", what);
    exit(1);
}

static void ok(const char *what)
{
    printf("  ok  %s\n", what);
}

/* Time passes: every live net polled each tick. */
static void run(int ms)
{
    int t;
    for (t = 0; t < ms; t += 10) {
        int i;
        now += 10;
        if (dir_port) {                 /* the directory answers in real time */
            struct timespec ts = {0, 300000};
            nanosleep(&ts, NULL);
        }
        for (i = 0; i < N; i++)
            if (alive[i])
                sr2_poll(nets[i], now);
    }
}

static int expect_event(int who, int type, int a)
{
    sr2_event ev;
    while (sr2_pop_event(nets[who], &ev) == SR2_OK) {
        if (ev.type == type && (a < 0 || ev.a == a))
            return 1;
    }
    return 0;
}

static void drain_events(int who)
{
    sr2_event ev;
    while (sr2_pop_event(nets[who], &ev) == SR2_OK)
        ;
}

static int join(int who, const char *what)
{
    sr2_session found[SR2_MAX_SESSIONS];
    int c, r, t;
    for (t = 0; t < 400; t++) {
        c = sr2_enum(nets[who], now, found, SR2_MAX_SESSIONS);
        if (c > 0)
            break;
        run(10);
    }
    if (c <= 0)
        fail("no session found");
    if (strcmp(found[0].name, "TEAM") != 0 || found[0].max_players != 4)
        fail("the record");
    r = sr2_join(nets[who], &found[0], now);
    for (t = 0; t < 1000 && r == SR2_CONNECTING; t++) {
        run(10);
        r = sr2_join_status(nets[who], now);
    }
    if (r == SR2_OK) {
        if (sr2_player_create(nets[who], names[who], now) != sr2_my_index(nets[who]))
            fail("player_create");
        ok(what);
    }
    return r;
}

static int got(int who, int from, const char *text)
{
    char buf[SR2_MAX_PAYLOAD];
    int f, len = sizeof buf;
    int r = sr2_recv(nets[who], &f, buf, &len);
    return r == SR2_OK && f == from && len == (int)strlen(text) + 1 && strcmp(buf, text) == 0;
}

static int empty(int who)
{
    char buf[SR2_MAX_PAYLOAD];
    int f, len = sizeof buf;
    return sr2_recv(nets[who], &f, buf, &len) == SR2_NONE;
}

static void header(uint8_t *p, int type, int flags, int from, int to, uint32_t seq)
{
    memset(p, 0, 16);
    memcpy(p, "SR2N", 4);
    p[4] = type;
    p[5] = flags;
    p[6] = from;
    p[7] = to;
    p[8] = seq; p[9] = seq >> 8; p[10] = seq >> 16; p[11] = seq >> 24;
}

static void send_from(sock_t s, uint16_t port, const void *data, int len)
{
    struct sockaddr_in sa;
    memset(&sa, 0, sizeof sa);
    sa.sin_family = AF_INET;
    sa.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    sa.sin_port = htons(port);
    sendto(s, data, len, 0, (struct sockaddr *)&sa, sizeof sa);
}

/* Guest 1's own socket sends the host a reliable message ahead of the
 * next one and longer than any held slot. Its tail is laid out as the
 * next slot's header and a game message "boo", which the host would
 * deliver in place of the guest's own if the length went unchecked. */
static void oversized(void)
{
    uint8_t pkt[16 + SR2_MAX_PAYLOAD + 36];
    uint32_t seq;
    int i;
    spy_from = sr2_port(nets[1]);
    spy_to = sr2_port(nets[0]);
    sr2_send(nets[1], 0, "x", 2, 1, now);
    run(300);
    if (spy_sock == SOCK_INVALID || !got(0, 1, "x"))
        fail("the watched link");
    seq = spy_seq + 2;
    if (seq % 64 == 63)
        seq++;
    memset(pkt, 0, sizeof pkt);
    header(pkt, 13, 1, 1, 0xff, seq);                  /* T_GAME, reliable */
    i = 16 + SR2_MAX_PAYLOAD;                           /* past a held slot's data: the next slot */
    pkt[i] = (seq + 1); pkt[i + 1] = (seq + 1) >> 8; pkt[i + 2] = (seq + 1) >> 16; pkt[i + 3] = (seq + 1) >> 24;
    pkt[i + 12] = 20;                                   /* its len: a header and "boo" */
    header(pkt + i + 16, 13, 0, 1, 0xff, 0);
    memcpy(pkt + i + 32, "boo", 4);
    send_from(spy_sock, spy_to, pkt, sizeof pkt);
    run(100);
    sr2_send(nets[1], 0, "r1", 3, 1, now);
    sr2_send(nets[1], 0, "r2", 3, 1, now);
    sr2_send(nets[1], 0, "r3", 3, 1, now);
    run(1000);
    if (!got(0, 1, "r1") || !got(0, 1, "r2") || !got(0, 1, "r3") || !empty(0))
        fail("an oversized reliable datagram got past the length check");
    spy_from = 0;
    ok("an oversized reliable datagram is dropped; the link after it intact");
}

/* A host that answers a join by itself: the welcome carries `index`. */
static int fake_host(int who, int index)
{
    sr2_session s;
    sock_t fs = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in sa;
    uint8_t buf[256];
    int r, t, welcomed = 0;
    memset(&sa, 0, sizeof sa);
    sa.sin_family = AF_INET;
    sa.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (fs < 0 || bind(fs, (struct sockaddr *)&sa, sizeof sa) != 0)
        fail("fake host socket");
    fcntl(fs, F_SETFL, O_NONBLOCK);
    memset(&s, 0, sizeof s);
    memset(s.guid, 0x5a, 16);
    s.addr = htonl(INADDR_LOOPBACK);
    s.port = local_port(fs);
    s.max_players = 4;
    strcpy(s.name, "FAKE");
    r = sr2_join(nets[who], &s, now);
    for (t = 0; t < 700 && r == SR2_CONNECTING; t++) {
        struct sockaddr_in from;
        socklen_t flen = sizeof from;
        int n = (int)recvfrom(fs, buf, sizeof buf, 0, (struct sockaddr *)&from, &flen);
        if (n >= 16 && buf[4] == 3 && !welcomed) {     /* T_JOIN: T_WELCOME, reliable seq 1 */
            uint8_t w[16 + 7];
            header(w, 4, 1, 0, index, 1);
            w[16] = index;
            w[17] = 0;
            memset(w + 18, 0, 5);                       /* nothing reserved, an empty roster */
            sendto(fs, w, sizeof w, 0, (struct sockaddr *)&from, flen);
            welcomed = 1;
        }
        run(10);
        r = sr2_join_status(nets[who], now);
    }
    close(fs);
    if (!welcomed)
        fail("the fake host never saw the join");
    return r;
}

int main(void)
{
    int i, r, max, cur;
    sr2_player pl;
    sr2_session s;
    sock_test_drop = drop;
    for (i = 0; i < N; i++) {
        nets[i] = sr2_create();
        sr2_set_log(nets[i], logline, (void *)names[i]);
        if (sr2_open(nets[i], SR2_KIND_LAN, "", now) != SR2_OK)
            fail("open");
        sr2_set_search(nets[i], htonl(INADDR_LOOPBACK), SR2_PORT);
        alive[i] = 1;
    }

    /* the host */
    if (sr2_host(nets[0], "TEAM", 4, now) != SR2_OK || sr2_player_create(nets[0], "Host", now) != 0)
        fail("host");
    if (!expect_event(0, SR2_EV_HOST, 0) || !expect_event(0, SR2_EV_CREATED, 0))
        fail("host events");
    ok("host: session and player 0, events HOST and CREATED");

    /* three guests */
    if (join(1, "guest 1 finds, joins, is index 1") != SR2_OK || sr2_my_index(nets[1]) != 1)
        fail("guest 1");
    if (!expect_event(1, SR2_EV_HOST, 0) || !expect_event(1, SR2_EV_CREATED, 0) || !expect_event(1, SR2_EV_CREATED, 1))
        fail("guest 1 events");
    if (!expect_event(0, SR2_EV_CREATED, 1))
        fail("host: guest 1 created");
    ok("events on both sides");
    if (join(2, "guest 2 joins as 2") != SR2_OK || sr2_my_index(nets[2]) != 2)
        fail("guest 2");
    if (join(3, "guest 3 joins as 3") != SR2_OK || sr2_my_index(nets[3]) != 3)
        fail("guest 3");
    run(500);
    if (!expect_event(1, SR2_EV_CREATED, 2) || !expect_event(1, SR2_EV_CREATED, 3))
        fail("guest 1 sees 2 and 3");
    if (sr2_player_info(nets[0], 2, &pl) != SR2_OK || strcmp(pl.name, "G2") != 0)
        fail("host has guest 2's name");
    if (sr2_player_info(nets[1], 3, &pl) != SR2_OK || strcmp(pl.name, "G3") != 0 || pl.host)
        fail("guest 1 has guest 3's name");
    if (sr2_player_info(nets[3], 0, &pl) != SR2_OK || !pl.host || strcmp(pl.name, "Host") != 0)
        fail("guest 3 knows the host");
    sr2_player_count(nets[2], &max, &cur);
    if (max != 4 || cur != 4)
        fail("counts");
    ok("names and counts everywhere");

    oversized();
    if (fake_host(5, 1) != SR2_OK || sr2_my_index(nets[5]) != 1)
        fail("a welcome with seat 1");
    sr2_leave(nets[5], now);
    if (fake_host(5, 200) == SR2_OK || sr2_my_index(nets[5]) >= 0)
        fail("a welcome with seat 200 taken");
    ok("a welcome with a seat past the table is not taken; one in it is");

    /* a fifth: full */
    if (join(4, "") != SR2_REFUSED)
        fail("fifth not refused");
    ok("a fifth player is refused: full");

    /* messages, with loss from here on */
    drop_pct = 33;
    drain_events(0); drain_events(1); drain_events(2); drain_events(3);
    if (sr2_send(nets[1], -1, "hello", 6, 1, now) != SR2_OK)
        fail("send");
    run(2000);
    if (!got(0, 1, "hello") || !got(2, 1, "hello") || !got(3, 1, "hello") || !empty(1))
        fail("reliable broadcast");
    ok("a reliable broadcast from guest 1 reaches the host and the others, under 33% loss");
    sr2_send(nets[0], 2, "psst", 5, 1, now);
    run(2000);
    if (!got(2, 0, "psst") || !empty(1) || !empty(3) || !empty(0))
        fail("unicast");
    ok("a reliable unicast from the host reaches guest 2 only");
    sr2_send(nets[3], 1, "hey1", 5, 1, now);
    run(2000);
    if (!got(1, 3, "hey1") || !empty(2) || !empty(0))
        fail("guest to guest");
    ok("guest 3 to guest 1 through the host");
    {
        int k, seen = 0;
        for (k = 0; k < 20; k++)
            sr2_send(nets[2], -1, "car", 4, 0, now);
        run(200);
        while (got(0, 2, "car"))
            seen++;
        if (seen < 5 || seen > 20)
            fail("unreliable");
        ok("unreliable broadcasts arrive when they do");
        while (got(1, 2, "car")) ;
        while (got(3, 2, "car")) ;
    }
    {
        char order[64];
        int k, seq_ok = 1;
        for (k = 0; k < 40; k++) {
            snprintf(order, sizeof order, "m%d", k);
            sr2_send(nets[0], -1, order, (int)strlen(order) + 1, 1, now);
        }
        run(6000);
        for (k = 0; k < 40 && seq_ok; k++) {
            snprintf(order, sizeof order, "m%d", k);
            seq_ok = got(1, 0, order) && got(2, 0, order) && got(3, 0, order);
        }
        if (!seq_ok)
            fail("ordering");
        ok("forty reliable messages arrive in order at every guest");
    }
    drop_pct = 0;

    /* closed */
    sr2_set_open(nets[0], 0, now);
    run(100);
    if (join(4, "") != SR2_REFUSED)
        fail("closed not refused");
    sr2_session_info(nets[0], &s);
    if (!s.closed)
        fail("closed flag");
    sr2_set_open(nets[0], 1, now);
    ok("a closed session refuses; the record says so");

    /* a slot closed under guest 3 */
    drain_events(0); drain_events(1); drain_events(2); drain_events(3);
    if (sr2_slot_reserve(nets[0], 3, 1, now) != SR2_OK)
        fail("reserve");
    run(1000);
    if (!expect_event(0, SR2_EV_DESTROYED, 3) || !expect_event(1, SR2_EV_DESTROYED, 3) || !expect_event(3, SR2_EV_LOST, -1))
        fail("kick");
    if (!sr2_slot_reserved(nets[1], 3) || sr2_player_info(nets[2], 3, &pl) == SR2_OK)
        fail("slot table");
    if (join(4, "") != SR2_REFUSED)
        fail("reserved slot taken");
    alive[3] = 0;
    ok("closing slot 3 drops guest 3, the others see it, a newcomer finds no room");
    sr2_slot_reserve(nets[0], 3, 0, now);
    run(500);
    if (join(4, "guest 4 takes slot 3 once it is open again") != SR2_OK || sr2_my_index(nets[4]) != 3)
        fail("reopen");

    /* leaving and silence */
    drain_events(0); drain_events(1); drain_events(2); drain_events(4);
    sr2_leave(nets[2], now);
    alive[2] = 0;
    run(500);
    if (!expect_event(0, SR2_EV_DESTROYED, 2) || !expect_event(1, SR2_EV_DESTROYED, 2))
        fail("leave");
    ok("guest 2 leaves: DESTROYED 2 at the host and guest 1");
    alive[1] = 0;                       /* guest 1 stops polling */
    run(8000);
    if (!expect_event(0, SR2_EV_DESTROYED, 1) || !expect_event(4, SR2_EV_DESTROYED, 1))
        fail("silence");
    ok("guest 1 goes silent: dropped after the timeout");
    alive[1] = 1;
    run(100);
    if (!expect_event(1, SR2_EV_LOST, -1))
        fail("the dropped guest hears it");
    ok("and hears it is out when it comes back");

    /* the directory: found through it, joined direct, then through the relay */
    if (getenv("SR2_DIR_PORT")) {
        char dir[64];
        int k;
        dir_port = (uint16_t)atoi(getenv("SR2_DIR_PORT"));
        snprintf(dir, sizeof dir, "127.0.0.1:%u", dir_port);
        for (k = 0; k < N; k++) {
            sr2_leave(nets[k], now);
            if (sr2_open(nets[k], SR2_KIND_INTERNET, dir, now) != SR2_OK)
                fail("open internet");
            alive[k] = 1;
        }
        drain_events(0);
        if (sr2_host(nets[0], "TEAM", 4, now) != SR2_OK || sr2_player_create(nets[0], "Host", now) != 0)
            fail("host internet");
        run(1200);                      /* registered */
        if (join(1, "internet: guest 1 finds the session at the directory and joins direct") != SR2_OK)
            fail("internet join");
        drop_to = sr2_port(nets[2]);
        if (join(2, "internet: guest 2, no direct road, joins through the relay") != SR2_OK)
            fail("relay join");
        run(1500);
        drain_events(0); drain_events(1); drain_events(2);
        sr2_send(nets[2], -1, "via", 4, 1, now);
        sr2_send(nets[0], 2, "back", 5, 1, now);
        run(1500);
        if (!got(0, 2, "via") || !got(1, 2, "via") || !got(2, 0, "back"))
            fail("relay traffic");
        ok("internet: relayed traffic both ways, and on to the direct guest");
        if (sr2_player_count(nets[1], &max, &cur) != SR2_OK || cur != 3)
            fail("the direct guest still there");
        drop_to = 0;
        for (k = 3; k < N; k++)
            alive[k] = 0;
    }

    /* the host leaves */
    drain_events(4); drain_events(1);
    sr2_leave(nets[0], now);
    alive[0] = 0;
    run(100);
    i = dir_port ? 1 : 4;
    if (!expect_event(i, SR2_EV_LOST, -1) || sr2_poll(nets[i], now) != SR2_ERR)
        fail("host leaves");
    ok("the host leaves: the guest's session is lost");

    for (i = 0; i < N; i++)
        sr2_destroy(nets[i]);
    printf("OK\n");
    (void)r;
    return 0;
}
