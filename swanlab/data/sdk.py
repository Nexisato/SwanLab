#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2024-01-01 18:00:04
@File: swanlab/data/sdk.py
@IDE: vscode
@Description:
    在此处封装swanlab在日志记录模式下的各种接口
"""
import os
from typing import Optional, Union, Dict, Tuple
from .modules import DataType
from .run import (
    SwanLabRunState,
    SwanLabRun,
    register,
    get_run,
)
from .callback_cloud import CloudRunCallback
from .callback_local import LocalRunCallback
from .run.operator import SwanLabRunOperator
from swanlab.env import init_env, get_swanlog_dir, SwanLabMode, MODE
from swanlab.log import swanlog
from swanlab.utils import check_load_json_yaml, check_proj_name_format
from swanlab.api import code_login
from swanlab.db import GlomCallback
from swanlab.package import version_limit

"""
Allows users to record experiment configurations through swanlab.config.
Before calling the init() function, config cannot be read or written, even if it is a SwanLabConfig object.
After calling the init() function, swanlab.config is equivalent to run.config.
Configuration information synchronization is achieved through class variables.
When the run object is initialized, it will operate on the SwanLabConfig object to write the configuration.
"""


def _check_proj_name(name: str) -> str:
    """检查项目名称是否合法，如果不合法则抛出ValueError异常
    项目名称必须是一个非空字符串，长度不能超过255个字符

    Parameters
    ----------
    name : str
        待检查的项目名称

    Returns
    -------
    str
        返回项目名称

    Raises
    ------
    ValueError
        项目名称不合法
    """
    _name = check_proj_name_format(name)
    if len(name) != len(_name):
        swanlog.warning(f"project name is too long, auto cut to {_name}")
    return _name


def _is_inited():
    """检查是否已经初始化"""
    return get_run() is not None


def login(api_key: str = None):
    """
    Login to SwanLab Cloud. If you already have logged in, you can use this function to relogin.
    Every time you call this function, the previous login information will be overwritten.
    [Note that] this function should be called before `init`.

    Parameters
    ----------
    api_key : str
        authentication key, if not provided, the key will be read from the key file.
    """
    if _is_inited():
        raise RuntimeError("You must call swanlab.login() before using init()")
    CloudRunCallback.login_info = code_login(api_key) if api_key else CloudRunCallback.get_login_info()


def init(
    project: str = None,
    workspace: str = None,
    experiment_name: str = None,
    description: str = None,
    config: Union[dict, str] = None,
    logdir: str = None,
    suffix: Union[str, None, bool] = "default",
    mode: str = None,
    load: str = None,
    **kwargs,
) -> SwanLabRun:
    """
    Start a new run to track and log. Once you have called this function, you can use 'swanlab.log' to log data to
    the current run. Meanwhile, you can use 'swanlab.finish' to finish the current run and close the current
    experiment. After calling this function, SwanLab will begin to record the console output of the current process,
    and register a callback function to the exit function.

    Parameters
    ----------
    project : str, optional
        The project name of the current experiment, the default is None,
        which means the current project name is the same as the current working directory.
    workspace : str, optional
        Where the current project is located, it can be an organization or a user (currently only supports yourself).
        The default is None, which means the current entity is the same as the current user.
    experiment_name : str, optional
        The experiment name you currently have open. If this parameter is not provided,
        SwanLab will generate one for you by default.
    description : str, optional
        The experiment description you currently have open,
        used for a more detailed introduction or labeling of the current experiment.
        If you do not provide this parameter, you can modify it later in the web interface.
    config : Union[dict, str], optional
        If you provide as a dict, it will be used as the configuration of the current experiment.
        If you provide as a string, SwanLab will read the configuration from the file.
        And the configuration file must be in the format of `json` or `yaml`.
        Anyway, you can modify the configuration later after this function is called.
    logdir : str, optional
        The folder will store all the log information generated during the execution of SwanLab.
        If the parameter is None,
        SwanLab will generate a folder named "swanlog" in the same path as the code execution to store the data.
        If you want to visualize the generated log files,
        simply run the command `swanlab watch` in the same path where the code is executed
        (without entering the "swanlog" folder).
        You can also specify your own folder, but you must ensure that the folder exists and preferably does not contain
        anything other than data generated by Swanlab.
        In this case, if you want to view the logs,
        you must use something like `swanlab watch -l ./your_specified_folder` to specify the folder path.
    suffix : str, optional
        The suffix of the experiment name, the default is 'default'.
        If this parameter is 'default', suffix will be '%b%d-%h-%m-%s'(example:'Feb03_14-45-37'),
        which represents the current time.
        example: experiment_name = 'example', suffix = 'default' -> 'example_Feb03_14-45-37';
        If this parameter is None or False, no suffix will be added.
        If this parameter is a string, the suffix will be the string you provided.
        Attention: experiment_name + suffix must be unique, otherwise the experiment will not be created.
    mode : str, optional
        Allowed values are 'cloud', 'cloud-only', 'local', 'disabled'.
        If the value is 'cloud', the data will be uploaded to the cloud and the local log will be saved.
        If the value is 'cloud-only', the data will only be uploaded to the cloud and the local log will not be saved.
        If the value is 'local', the data will only be saved locally and will not be uploaded to the cloud.
        If the value is 'disabled', the data will not be saved or uploaded, just parsing the data.
    load : str, optional
        If you pass this parameter,SwanLab will search for the configuration file you specified
        (which must be in JSON or YAML format)
        and automatically fill in some explicit parameters of this function for you
        (excluding parameters in `**kwargs` and the parameters if they are None).
        In terms of priority, if the parameters passed to init are `None`,
        SwanLab will attempt to replace them from the configuration file you provided;
        otherwise, it will use the parameters you passed as the definitive ones.
    """
    run = get_run()
    if run is not None:
        swanlog.warning("You have already initialized a run, the init function will be ignored")
        return run
    # ---------------------------------- 一些变量、格式检查 ----------------------------------
    if "cloud" in kwargs:
        swanlog.warning(
            "The `cloud` parameter in swanlab.init is deprecated and will be removed in the future"
            "please use `mode='cloud'` instead."
        )
        mode = "cloud" if kwargs["cloud"] else mode
    if load:
        load_data = check_load_json_yaml(load, load)
        experiment_name = _load_data(load_data, "experiment_name", experiment_name)
        description = _load_data(load_data, "description", description)
        config = _load_data(load_data, "config", config)
        logdir = _load_data(load_data, "logdir", logdir)
        suffix = _load_data(load_data, "suffix", suffix)
        mode = _load_data(load_data, "mode", mode)
        project = _load_data(load_data, "project", project)
        workspace = _load_data(load_data, "workspace", workspace)
    operator, c = _create_operator(mode)
    project = _check_proj_name(project if project else os.path.basename(os.getcwd()))  # 默认实验名称为当前目录名
    exp_num = SwanLabRunOperator.parse_return(
        operator.on_init(project, workspace, logdir=logdir), key=c.__str__() if c else None
    )
    # 初始化confi参数
    config = _init_config(config)
    init_env()
    # 检查logdir内文件的版本，如果<=0.1.4则报错
    version_limit(get_swanlog_dir(), mode="init")
    # ---------------------------------- 实例化实验 ----------------------------------
    # 注册实验
    run = register(
        project_name=project,
        experiment_name=experiment_name,
        description=description,
        run_config=config,
        log_level=kwargs.get("log_level", "info"),
        suffix=suffix,
        exp_num=exp_num,
        operator=operator,
    )
    return run


def log(data: Dict[str, DataType], step: int = None):
    """
    Log a row of data to the current run.
    We recommend that you log data by SwanLabRun.log() method, but you can also use this function to log data.

    Parameters
    ----------
    data : Dict[str, DataType]
        Data must be a dict.
        The key must be a string with 0-9, a-z, A-Z, " ", "_", "-", "/".
        The value must be a `float`, `float convertible object`, `int` or `swanlab.data.BaseType`.
    step : int, optional
        The step number of the current data, if not provided, it will be automatically incremented.
        If step is duplicated, the data will be ignored.
    """
    if not _is_inited():
        raise RuntimeError("You must call swanlab.init() before using log()")
    run = get_run()
    ll = run.log(data, step)
    return ll


def finish(state: SwanLabRunState = SwanLabRunState.SUCCESS, error=None):
    """
    Finish the current run and close the current experiment
    Normally, swanlab will run this function automatically,
    but you can also execute it manually and mark the experiment as 'completed'.
    Once the experiment is marked as 'completed', no more data can be logged to the experiment by 'swanlab.log'.
    If you mark the experiment as 'CRASHED' manually, `error` must be provided.
    """
    run = get_run()
    if not get_run():
        raise RuntimeError("You must call swanlab.data.init() before using finish()")
    if not run.is_running:
        return swanlog.error("After experiment is finished, you can't call finish() again.")
    run.finish(state, error)


def _init_mode(mode: str = None):
    """
    初始化mode参数
    从环境变量中提取默认的mode参数，如果传入的mode参数不为None，则使用环境变量中的mode参数，否则使用传入的mode参数
    传入的mode必须为SwanLabMode枚举中的一个值，否则报错ValueError
    如果环境变量和传入的mode参数都为None，则默认为cloud

    :param mode: str, optional
        传入的mode参数
    :return: str mode
    :raise ValueError: mode参数不合法
    """
    allowed = [m.value for m in SwanLabMode]
    m = os.environ.get(MODE)
    if m is not None and mode is not None:
        swanlog.warning(f"The environment variable {MODE} will be overwritten by the parameter mode")
    mode = m if mode is None else mode
    if mode is not None and mode not in allowed:
        raise ValueError(f"`mode` must be one of {allowed}, but got {mode}")
    mode = "cloud" if mode is None else mode
    os.environ[MODE] = mode
    return mode


def _init_config(config: Union[dict, str]):
    """初始化传入的config参数"""
    if isinstance(config, str):
        swanlog.info("The parameter config is loaded from the configuration file: {}".format(config))
        return check_load_json_yaml(config, "config")

    return config


def _load_data(load_data: dict, key: str, value):
    """
    从load_data中加载数据，如果value不是None，则直接返回value，如果为None，则返回load_data中的key
    """
    if value is not None:
        return value
    d = load_data.get(key, None)
    return d


def _create_operator(mode) -> Tuple[SwanLabRunOperator, Optional[CloudRunCallback]]:
    """
    创建SwanLabRunOperator实例
    如果mode为disabled，则返回一个空的SwanLabRunOperator实例和None

    :param mode: str
        运行模式
    :return: SwanLabRunOperator, CloudRunCallback
    """
    mode = _init_mode(mode)
    if mode == SwanLabMode.DISABLED.value:
        swanlog.warning("SwanLab run disabled, the data will not be saved or uploaded.")
        return SwanLabRunOperator(), None
    c = CloudRunCallback() if mode == SwanLabMode.CLOUD.value else LocalRunCallback()
    callbacks = [c, GlomCallback()]
    return SwanLabRunOperator(callbacks), c
