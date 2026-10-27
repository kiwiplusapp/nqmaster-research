import sys, os, json, time
sys.path.insert(0, "/home/user/nqmaster-research/research/mine"); os.chdir("/home/user/nqmaster-research/research/mine")
import exp03_eval_size as E
E.HERE = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r3"   # salida fuera del repo
t0 = time.time(); E.main(1000); print("DONE", round(time.time() - t0))
