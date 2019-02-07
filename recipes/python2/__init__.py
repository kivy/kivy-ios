from toolchain import Recipe, shprint
from os.path import join
import sh
import os
import logging

logger = logging.getLogger(__name__)

class Python2Recipe(Recipe):
    version = "2.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tar.bz2"
    depends = ["hostpython2", "libffi"]
    optional_depends = ["openssl"]
    library = "libpython2.7.a"
    pbx_libraries = ["libz", "libbz2", "libsqlite3"]

    def init_with_ctx(self, ctx):
        super(Python2Recipe, self).init_with_ctx(ctx)
        self.set_python(self, "2.7")
        ctx.python_ver_dir = "python2.7"
        ctx.python_prefix = join(ctx.dist_dir, "root", "python2")
        ctx.site_packages_dir = join(
            ctx.python_prefix, "lib", ctx.python_ver_dir, "site-packages")

    def prebuild_arch(self, arch):
        # common to all archs
        if  self.has_marker("patched"):
            return
        self.apply_patch("ssize-t-max.patch")
        self.apply_patch("dynload.patch")
        self.apply_patch("static-_sqlite3.patch")
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        self.copy_file("_scproxy.py", "Lib/_scproxy.py")
        self.apply_patch("xcompile.patch")
        self.apply_patch("setuppath.patch")
        self.append_file("ModulesSetup.mobile", "Modules/Setup.local")
        self.apply_patch("ipv6.patch")
        if "openssl.build_all" in self.ctx.state:
             self.append_file("ModulesSetup.openssl", "Modules/Setup.local")
        self.apply_patch("posixmodule.patch")

        self.set_marker("patched")

    def build_arch(self, arch):
        build_env = arch.get_env()
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={} -undefined dynamic_lookup".format(build_env["LDFLAGS"]),
                "--without-pymalloc",
                "--disable-toolbox-glue",
                "--host={}-apple-darwin".format(arch),
                "--prefix=/python",
                "--with-system-ffi",
                "--without-doc-strings",
                "--enable-ipv6",
                _env=build_env)

        self._patch_pyconfig()
        self.apply_patch("ctypes_duplicate.patch")
        self.apply_patch("ctypes_duplicate_longdouble.patch")

        shprint(sh.make, self.ctx.concurrent_make,
                "CROSS_COMPILE_TARGET=yes",
                "HOSTPYTHON={}".format(self.ctx.hostpython),
                "HOSTPGEN={}".format(self.ctx.hostpgen))

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_env = arch.get_env()
        build_dir = self.get_build_dir(arch.arch)
        build_env["PATH"] = os.environ["PATH"]
        shprint(sh.make, self.ctx.concurrent_make,
                "-C", build_dir,
                "install",
                "CROSS_COMPILE_TARGET=yes",
                "HOSTPYTHON={}".format(self.ctx.hostpython),
                "prefix={}".format(join(self.ctx.dist_dir, "root", "python2")),
                _env=build_env)
        self.reduce_python()

    def _patch_pyconfig(self):
        # patch pyconfig to remove some functionnalities
        # (to have uniform build accross all platfors)
        # this was before in a patch itself, but because the different
        # architecture can lead to different pyconfig.h, we would need one patch
        # per arch. Instead, express here the line we don't want / we want.
        pyconfig = join(self.build_dir, "pyconfig.h")
        def _remove_line(lines, pattern):
            for line in lines[:]:
                if pattern in line:
                    lines.remove(line)
        with open(pyconfig, "r") as fd:
            lines = fd.readlines()
        _remove_line(lines, "#define HAVE_BIND_TEXTDOMAIN_CODESET 1")
        _remove_line(lines, "#define HAVE_FINITE 1")
        _remove_line(lines, "#define HAVE_FSEEK64 1")
        _remove_line(lines, "#define HAVE_FTELL64 1")
        _remove_line(lines, "#define HAVE_GAMMA 1")
        _remove_line(lines, "#define HAVE_GETHOSTBYNAME_R 1")
        _remove_line(lines, "#define HAVE_GETHOSTBYNAME_R_6_ARG 1")
        _remove_line(lines, "#define HAVE_GETRESGID 1")
        _remove_line(lines, "#define HAVE_GETRESUID 1")
        _remove_line(lines, "#define HAVE_GETSPENT 1")
        _remove_line(lines, "#define HAVE_GETSPNAM 1")
        _remove_line(lines, "#define HAVE_MREMAP 1")
        _remove_line(lines, "#define HAVE_PLOCK 1")
        _remove_line(lines, "#define HAVE_SEM_TIMEDWAIT 1")
        _remove_line(lines, "#define HAVE_SETRESGID 1")
        _remove_line(lines, "#define HAVE_SETRESUID 1")
        _remove_line(lines, "#define HAVE_TMPNAM_R 1")
        _remove_line(lines, "#define HAVE__GETPTY 1")
        lines.append("#define HAVE_GETHOSTBYNAME 1\n")
        with open(pyconfig, "w") as fd:
            fd.writelines(lines)

    def reduce_python(self):
        logger.info("Reduce python")
        oldpwd = os.getcwd()
        try:
            logger.info("Remove files unlikely to be used")
            os.chdir(join(self.ctx.dist_dir, "root", "python2"))
            sh.rm("-rf", "share")
            sh.rm("-rf", "bin")
            os.chdir(join(self.ctx.dist_dir, "root", "python2", "lib"))
            sh.rm("-rf", "pkgconfig")
            sh.rm("libpython2.7.a")
            os.chdir(join(self.ctx.dist_dir, "root", "python2", "lib", "python2.7"))
            sh.find(".", "-iname", "*.pyc", "-exec", "rm", "{}", ";")
            sh.find(".", "-iname", "*.py", "-exec", "rm", "{}", ";")
            #sh.find(".", "-iname", "test*", "-exec", "rm", "-rf", "{}", ";")
            sh.rm("-rf", "wsgiref", "bsddb", "curses", "idlelib", "hotshot")
            sh.rm("-rf", sh.glob("lib*"))

            # now create the zip.
            logger.info("Create a python27.zip")
            sh.rm("config/libpython2.7.a")
            sh.rm("config/python.o")
            sh.rm("config/config.c.in")
            sh.rm("config/makesetup")
            sh.rm("config/install-sh")
            sh.mv("config", "..")
            sh.mv("site-packages", "..")
            sh.zip("-r", "../python27.zip", sh.glob("*"))
            sh.rm("-rf", sh.glob("*"))
            sh.mv("../config", ".")
            sh.mv("../site-packages", ".")
        finally:
            os.chdir(oldpwd)


recipe = Python2Recipe()
