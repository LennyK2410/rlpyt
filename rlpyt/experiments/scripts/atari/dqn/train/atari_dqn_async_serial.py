
import sys

from rlpyt.utils.launching.affinity import get_affinity
# from rlpyt.samplers.cpu.parallel_sampler import CpuParallelSampler
from rlpyt.samplers.async_.async_serial_sampler import AsyncSerialSampler
# from rlpyt.samplers.cpu.collectors import WaitResetCollector
from rlpyt.samplers.async_.collectors import DbCpuResetCollector
from rlpyt.envs.atari.atari_env import AtariEnv, AtariTrajInfo
from rlpyt.algos.dqn.dqn import DQN
from rlpyt.agents.dqn.atari.atari_dqn_agent import AtariDqnAgent
# from rlpyt.runners.minibatch_rl_eval import MinibatchRlEval
from rlpyt.runners.async_rl import AsyncRlEval
from rlpyt.utils.logging.context import logger_context
from rlpyt.utils.launching.variant import load_variant, update_config

from rlpyt.experiments.configs.atari.dqn.atari_dqn import configs


def build_and_train(slot_affinity_code, log_dir, run_ID, config_key):
    affinity = get_affinity(slot_affinity_code)
    config = configs[config_key]
    variant = load_variant(log_dir)
    config = update_config(config, variant)
    config["eval_env"]["game"] = config["env"]["game"]

    CollectorCls = config["sampler"].pop("CollectorCls", None)
    sampler = AsyncSerialSampler(
        EnvCls=AtariEnv,
        env_kwargs=config["env"],
        CollectorCls=CollectorCls or DbCpuResetCollector,
        TrajInfoCls=AtariTrajInfo,
        eval_env_kwargs=config["eval_env"],
        **config["sampler"]
    )
    algo = DQN(optim_kwargs=config["optim"], **config["algo"])
    agent = AtariDqnAgent(model_kwargs=config["model"], **config["agent"])
    runner = AsyncRlEval(
        algo=algo,
        agent=agent,
        sampler=sampler,
        affinity=affinity,
        **config["runner"]
    )
    name = "async_serial_" + config["env"]["game"]
    with logger_context(log_dir, run_ID, name, config):
        runner.train()


if __name__ == "__main__":
    build_and_train(*sys.argv[1:])
