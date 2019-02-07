from toolchain import Recipe, shprint
from os.path import join
import sh
import shutil
import os
import logging

logger = logging.getLogger(__name__)


class Python3Recipe(Recipe):
    version = "3.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    depends = ["hostpython3", "libffi", "openssl"]
    library = "libpython3.7m.a"
    pbx_libraries = ["libz", "libbz2", "libsqlite3"]

    def init_with_ctx(self, ctx):
        super(Python3Recipe, self).init_with_ctx(ctx)
        self.set_python(self, "3.7")
        ctx.python_ver_dir = "python3.7"
        ctx.python_prefix = join(ctx.dist_dir, "root", "python3")
        ctx.site_packages_dir = join(
            ctx.python_prefix, "lib", ctx.python_ver_dir, "site-packages")

    def prebuild_arch(self, arch):
        # common to all archs
        if  self.has_marker("patched"):
            return
        self.apply_patch("dynload.patch")
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        self.append_file("ModulesSetup.mobile", "Modules/Setup.local")
        self.apply_patch("xcompile.patch")
        self.set_marker("patched")

    def get_build_env(self, arch):
        build_env = arch.get_env()
        build_env["PATH"] = "{}:{}".format(
            join(self.ctx.dist_dir, "hostpython3", "bin"),
            os.environ["PATH"])
        return build_env

    def build_arch(self, arch):
        build_env = self.get_build_env(arch)
        configure = sh.Command(join(self.build_dir, "configure"))
        py_arch = arch.arch
        if py_arch == "armv7":
            py_arch = "arm"
        elif py_arch == "arm64":
            py_arch = "aarch64"
        prefix = join(self.ctx.dist_dir, "root", "python3")
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={} -undefined dynamic_lookup".format(build_env["LDFLAGS"]),
                # "--without-pymalloc",
                "ac_cv_file__dev_ptmx=yes",
                "ac_cv_file__dev_ptc=no",
                "ac_cv_little_endian_double=yes",
                "ac_cv_func_memrchr=no",
                "ac_cv_func_getentropy=no",
                "ac_cv_func_getresuid=no",
                "ac_cv_func_getresgid=no",
                "ac_cv_func_setresgid=no",
                "ac_cv_func_setresuid=no",
                "ac_cv_func_plock=no",
                "ac_cv_func_dup3=no",
                "ac_cv_func_pipe2=no",
                "ac_cv_func_preadv=no",
                "ac_cv_func_pwritev=no",
                "ac_cv_func_preadv2=no",
                "ac_cv_func_pwritev2=no",
                "ac_cv_func_mkfifoat=no",
                "ac_cv_func_mknodat=no",
                "ac_cv_func_posix_fadvise=no",
                "ac_cv_func_posix_fallocate=no",
                "ac_cv_func_sigwaitinfo=no",
                "ac_cv_func_sigtimedwait=no",
                "ac_cv_func_clock_settime=no",
                "ac_cv_func_pthread_getcpuclockid=no",
                "ac_cv_func_sched_setscheduler=no",
                "ac_cv_func_sched_setparam=no",
                "ac_cv_func_clock_gettime=no",
                "--host={}-apple-ios".format(py_arch),
                "--build=x86_64-apple-darwin",
                "--prefix={}".format(prefix),
                "--without-ensurepip",
                "--with-system-ffi",
                # "--without-doc-strings",
                "--enable-ipv6",
                _env=build_env)

        self.apply_patch("ctypes_duplicate.patch")
        shprint(sh.make, self.ctx.concurrent_make)

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_env = self.get_build_env(arch)
        build_dir = self.get_build_dir(arch.arch)
        shprint(sh.make, self.ctx.concurrent_make,
                "-C", build_dir,
                "install",
                "prefix={}".format(join(self.ctx.dist_dir, "root", "python3")),
                _env=build_env)
        # os.execve("/bin/bash", ["/bin/bash"], os.environ)
        self.reduce_python()

    def reduce_python(self):
        logger.info("Reduce python")
        oldpwd = os.getcwd()
        try:
            logger.info("Remove files unlikely to be used")
            os.chdir(join(self.ctx.dist_dir, "root", "python3"))
            # os.execve("/bin/bash", ["/bin/bash"], env=os.environ)
            sh.rm("-rf", "bin", "share")

            # platform binaries and configuration
            os.chdir(join(
                self.ctx.dist_dir, "root", "python3", "lib",
                "python3.7", "config-3.7m-darwin"))
            sh.rm("libpython3.7m.a")
            sh.rm("python.o")
            sh.rm("config.c.in")
            sh.rm("makesetup")
            sh.rm("install-sh")

            # cleanup pkgconfig and compiled lib
            os.chdir(join(self.ctx.dist_dir, "root", "python3", "lib"))
            sh.rm("-rf", "pkgconfig")
            sh.rm("-f", "libpython3.7m.a")

            # cleanup python libraries
            os.chdir(join(
                self.ctx.dist_dir, "root", "python3", "lib", "python3.7"))
            sh.rm("-rf", "wsgiref", "curses", "idlelib", "lib2to3",
                  "ensurepip", "turtledemo", "lib-dynload", "venv",
                  "pydoc_data")
            sh.find(".", "-path", "*/test*/*", "-delete")
            sh.find(".", "-name", "*.exe", "-type", "f", "-delete")
            sh.find(".", "-name", "test*", "-type", "d", "-delete")
            sh.find(".", "-iname", "*.pyc", "-delete")
            sh.find(".", "-path", "*/__pycache__/*", "-delete")
            sh.find(".", "-name", "__pycache__", "-type", "d", "-delete")

            # now precompile to Python bytecode
            hostpython = sh.Command(self.ctx.hostpython)
            shprint(hostpython, "-m", "compileall", "-f", "-b")
            # sh.find(".", "-iname", "*.py", "-delete")

            # some pycache are recreated after compileall
            sh.find(".", "-path", "*/__pycache__/*", "-delete")
            sh.find(".", "-name", "__pycache__", "-type", "d", "-delete")

            # create the lib zip
            logger.info("Create a python3.7.zip")
            sh.mv("config-3.7m-darwin", "..")
            sh.mv("site-packages", "..")
            sh.zip("-r", "../python37.zip", sh.glob("*"))
            sh.rm("-rf", sh.glob("*"))
            sh.mv("../config-3.7m-darwin", ".")
            sh.mv("../site-packages", ".")
        finally:
            os.chdir(oldpwd)


recipe = Python3Recipe()
