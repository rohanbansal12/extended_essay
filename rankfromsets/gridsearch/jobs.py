import os
import time
import itertools
import subprocess


def get_keys_for_dir_name(grid):
    """Only add a key for directory creation if it is being changed."""
    keys = []
    for key in grid:
        if isinstance(grid[key], list) and len(grid[key]) > 1:
            keys.append(key)
    return keys


def make_output_dir(log_dir, experiment_name, cfg, keys):
    name = "_".join(["%s=%s" % (key, str(cfg[key])) for key in keys])
    date = time.strftime("%Y-%m-%d") + "-rankfromsets"
    output_dir = log_dir / date / experiment_name / name
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def param_grid(grid):
    """Generator of parameter grid."""
    all_combos = []
    for key in grid:
        if isinstance(grid[key], list):
            all_combos.append([(key, value) for value in grid[key]])
        else:
            all_combos.append([(key, grid[key])])
    for params_tuples in itertools.product(*all_combos):
        cfg = dict(params_tuples)
        yield cfg


def submit(command_list, cfg, get_slurm_script):
    """Submit a job to slurm, specified by a command and cfg.
    cfg is a dict where every key is a command line flag, and the value
    is the argument for the command line flag.
    """
    param_tuples = list(cfg.items())
    args = " ".join(["--%s=%s" % tup for tup in param_tuples])
    command = "\n".join([" ".join([command, args]) for command in command_list])
    file_contents = get_slurm_script(cfg["output_dir"], command)
    print(file_contents)
    fname = cfg["output_dir"] / "job.cmd"
    with open(fname, "w") as f:
        f.write(file_contents)
    print("wrote file to: %s" % fname)
    print("contents:")
    print(file_contents)
    subprocess.call(["sbatch", fname])
    time.sleep(0.1)
