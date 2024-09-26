from kivy_ios.toolchain import Recipe, shprint
from kivy_ios.context_managers import cd
from os.path import join
import sh
import os
import logging

logger = logging.getLogger(__name__)


class Python3Recipe(Recipe):
    version = "3.11.6"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    depends = ["hostpython3", "libffi", "openssl"]
    library = "libpython3.11.a"
    pbx_libraries = ["libz", "libbz2", "libsqlite3"]

    def init_with_ctx(self, ctx):
        super().init_with_ctx(ctx)
        self.set_python(self, "3.11")
        ctx.python_ver_dir = "python3.11"
        ctx.python_prefix = join(ctx.dist_dir, "root", "python3")
        ctx.site_packages_dir = join(
            ctx.python_prefix, "lib", ctx.python_ver_dir, "site-packages")

    def prebuild_platform(self, plat):
        # common to all archs
        if self.has_marker("patched"):
            return
        self.apply_patch("configure.patch")
        self.apply_patch("dynload_shlib.patch")
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        self.append_file("ModulesSetup.mobile", "Modules/Setup.local")
        self.set_marker("patched")

    def postbuild_platform(self, plat):
        # We need to skip remove_junk, because we need to keep few files.
        # A cleanup will be done in the final step.
        return

    def get_build_env(self, plat):
        build_env = plat.get_env()
        build_env["PATH"] = "{}:{}".format(
            join(self.ctx.dist_dir, "hostpython3", "bin"),
            os.environ["PATH"])
        build_env["CFLAGS"] += " --sysroot={}".format(plat.sysroot)
        return build_env

    def build_platform(self, plat):
        build_env = self.get_build_env(plat)
        configure = sh.Command(join(self.build_dir, "configure"))
        py_arch = plat.arch
        if py_arch == "arm64":
            py_arch = "aarch64"
        prefix = join(self.ctx.dist_dir, "root", "python3")
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={} -undefined dynamic_lookup".format(build_env["LDFLAGS"]),
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
                "ac_cv_func_rtpSpawn=no",
                "ac_cv_func_fdwalk=no",
                "ac_cv_func_futimesat=no",
                "ac_cv_func_copy_file_range=no",
                "ac_cv_func_fexecve=no",
                "ac_cv_func_execve=no",
                "ac_cv_func_sched_rr_get_interval=no",
                "ac_cv_func_explicit_bzero=no",
                "ac_cv_func_explicit_memset=no",
                "ac_cv_func_close_range=no",
                "ac_cv_search_crypt_r=no",
                "ac_cv_func_fork1=no",
                "ac_cv_func_system=no",
                "ac_cv_func_clock_nanosleep=no",
                "ac_cv_func_splice=no",
                "ac_cv_func_mremap=no",
                "--host={}-apple-ios".format(py_arch),
                "--build=x86_64-apple-darwin",
                "--with-build-python={}".format(join(self.ctx.dist_dir, "hostpython3", "bin", "python3")),
                "--prefix={}".format(prefix),
                "--without-ensurepip",
                "--with-system-ffi",
                "--enable-ipv6",
                "PYTHON_FOR_BUILD=_PYTHON_PROJECT_BASE=$(abs_builddir) \
                    _PYTHON_HOST_PLATFORM=$(_PYTHON_HOST_PLATFORM) \
                    PYTHONPATH=$(shell test -f pybuilddir.txt && echo $(abs_builddir)/`cat pybuilddir.txt`:)$(srcdir)/Lib\
                    _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata_$(ABIFLAGS)_$(MACHDEP)_$(MULTIARCH)\
                    {}".format(sh.Command(self.ctx.hostpython)),
                _env=build_env)
        shprint(sh.make, self.ctx.concurrent_make, "CFLAGS={}".format(build_env["CFLAGS"]))

    def install(self):
        plat = list(self.platforms_to_build)[0]
        build_env = self.get_build_env(plat)
        build_dir = self.get_build_dir(plat)
        shprint(sh.make, self.ctx.concurrent_make,
                "-C", build_dir,
                "install",
                "prefix={}".format(join(self.ctx.dist_dir, "root", "python3")),
                _env=build_env)
        self.reduce_python()

    def reduce_python(self):
        logger.info("Reduce python")
        logger.info("Remove files unlikely to be used")
        with cd(join(self.ctx.dist_dir, "root", "python3")):
            sh.rm("-rf", "bin", "share")
        # platform binaries and configuration
        with cd(join(
                self.ctx.dist_dir, "root", "python3", "lib",
                "python3.11", "config-3.11-darwin")):
            sh.rm(
                "libpython3.11.a",
                "python.o",
                "config.c.in",
                "makesetup",
                "install-sh",
            )

        # cleanup pkgconfig and compiled lib
        with cd(join(self.ctx.dist_dir, "root", "python3", "lib")):
            sh.rm("-rf", "pkgconfig", "libpython3.11.a")

        # cleanup python libraries
        with cd(join(
                self.ctx.dist_dir, "root", "python3", "lib", "python3.11")):
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
            logger.info("Create a python3.11.zip")
            sh.mv("config-3.11-darwin", "..")
            sh.mv("site-packages", "..")
            sh.zip("-r", "../python311.zip", sh.glob("*"))
            sh.rm("-rf", sh.glob("*"))
            sh.mv("../config-3.11-darwin", ".")
            sh.mv("../site-packages", ".")


recipe = Python3Recipe()
