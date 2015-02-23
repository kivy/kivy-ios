from toolchain import Recipe, shprint
from os.path import join
import sh
import os


class PythonRecipe(Recipe):
    version = "2.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tar.bz2"
    depends = ["hostpython", "libffi", ]
    library = "libpython2.7.a"
    pbx_libraries = ["libz", "libbz2", "libsqlite3"]

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

        self.set_marker("patched")

    def build_arch(self, arch):
        build_env = arch.get_env()
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={}".format(build_env["LDFLAGS"]),
                "--without-pymalloc",
                "--disable-toolbox-glue",
                "--host={}-apple-darwin".format(arch),
                "--prefix=/python",
                "--with-system-ffi",
                "--without-doc-strings",
                _env=build_env)

        self._patch_pyconfig()
        self.apply_patch("ctypes_duplicate.patch")
        self.apply_patch("ctypes_duplicate_longdouble.patch")

        shprint(sh.make, "-j4",
                "CROSS_COMPILE_TARGET=yes",
                "HOSTPYTHON={}".format(self.ctx.hostpython),
                "HOSTPGEN={}".format(self.ctx.hostpgen))

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_env = arch.get_env()
        build_dir = self.get_build_dir(arch.arch)
        build_env["PATH"] = os.environ["PATH"]
        shprint(sh.make,
                "-C", build_dir,
                "install",
                "CROSS_COMPILE_TARGET=yes",
                "HOSTPYTHON={}".format(self.ctx.hostpython),
                "prefix={}".format(join(self.ctx.dist_dir, "root", "python")),
                _env=build_env)

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
        with open(pyconfig) as fd:
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
        with open(pyconfig, "wb") as fd:
            fd.writelines(lines)


recipe = PythonRecipe()
