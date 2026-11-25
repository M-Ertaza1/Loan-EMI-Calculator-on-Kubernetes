import random, sys
n_sessions = int(sys.argv[1])
random.seed(42)
with open("sessions.txt", "w") as f:
    for _ in range(n_sessions):
        P = random.randint(50000, 2000000)
        rate = round(random.uniform(5, 30), 1)
        n = random.randint(6, 60)
        f.write("/api/emi method=POST contents='{\"principal\":%d,\"rate\":%s,\"months\":%d}'\n\n" % (P, rate, n))
