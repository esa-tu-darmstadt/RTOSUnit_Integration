#!/usr/bin/python3
import os
import subprocess
import concurrent.futures
from generate_tapasco_folders import configs, top_dir, tapasco_dir

def run_explore(dirname):
    cudir = os.path.abspath(os.path.join(top_dir, dirname))
    with open(os.path.join(cudir, "output.log"), "w") as logfile:
        print(f"now running: {dirname}")
        
        command = f". ./tapasco-setup.sh && tapasco --maxTasks 3 explore [ { 'cv32e40p_ctx_pe' if dirname != 'vanilla' else 'cv32e40p_pe' } x 1 ] @ 195 MHz in frequency -p AU280 --deleteProjects false"
        return subprocess.run(command, shell=True, cwd=cudir, stdout=logfile, stderr=logfile).returncode
        
def run_compose(dirname):
    cudir = os.path.abspath(os.path.join(top_dir, dirname))
    with open(os.path.join(cudir, "compose.log"), "w") as logfile:
        print(f"now running: {dirname}")
        
        command = f". ./tapasco-setup.sh && tapasco compose [ { 'cv32e40p_ctx_pe' if dirname != 'vanilla' else 'cv32e40p_pe' } x 1 ] @ 100 MHz -p AU280 --deleteProjects false"
        return subprocess.run(command, shell=True, cwd=cudir, stdout=logfile, stderr=logfile).returncode

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_explore, dirname) for dirname, config in configs.items()]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_compose, dirname) for dirname, config in configs.items()]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
