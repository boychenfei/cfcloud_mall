import os
from pathlib import Path
from environs import Env


BASE_DIR = Path(__file__).resolve().parent.parent

def get_app_root()->Path:
    """
    获取应用程序的根目录路径。

    该函数返回一个Path对象，该对象表示应用程序的根目录。
    这对于在应用程序中定位文件和目录非常有用。

    Returns:
        Path: 表示应用程序根目录的Path对象。
    """
    return BASE_DIR

def load_env(env_file_suffix:str = None)->Env:
    """
    根据指定的环境变量文件后缀加载环境变量。

    参数:
    env_file_suffix (str): 环境变量文件的后缀名。如果未提供，则使用默认的环境变量文件。

    Returns:
    Env: 加载的环境变量对象。
    """
    conf_dir = get_app_root() / 'conf'
    if env_file_suffix is None:
        env_file_path = conf_dir / '.env'
    else:
        env_file_path = conf_dir / f'.env.{env_file_suffix}'
    env = Env()
    # recurse 递归查找路径下的env文件
    env.read_env(str(env_file_path), recurse=True)
    return env

def in_main_process() -> bool:
    """
    判断当前进程是否为主进程。

    Returns:
        bool: 如果当前进程为主进程，则返回True；否则返回False。
    """
    return os.environ.get("RUN_IN_MAIN_PROCESS", "False") == "True"

