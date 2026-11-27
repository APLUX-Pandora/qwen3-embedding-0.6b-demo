from pathlib import Path
from shutil import copytree
from sysconfig import get_platform

from setuptools import setup
from setuptools.command.build_py import build_py
from wheel.bdist_wheel import bdist_wheel


class BuildPython(build_py):
    def run(self):
        super().run()
        src = Path(__file__).resolve().parent / "lib"
        if not (src / "libpandora_embedding.so").is_file():
            raise FileNotFoundError("The SDK native library is missing from lib/")
        dst = Path(self.build_lib) / "pandora_qwen3_embedding_0_6b" / "_lib"
        copytree(src, dst, dirs_exist_ok=True)


class PlatformWheel(bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        if get_platform() != "linux-aarch64":
            raise RuntimeError("The SDK native library requires Linux aarch64")
        return "py3", "none", "linux_aarch64"


setup(cmdclass={"build_py": BuildPython, "bdist_wheel": PlatformWheel})
