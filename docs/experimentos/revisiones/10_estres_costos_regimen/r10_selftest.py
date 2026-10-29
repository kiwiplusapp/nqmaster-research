import os, sys, time
os.chdir("/home/user/nqmaster-research/research/mine"); sys.path.insert(0, os.getcwd())
import exp10_stress as X10
t0 = time.time(); bad = X10.selftest(); print("bad", bad, "time", round(time.time() - t0))
