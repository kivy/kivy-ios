from toolchain import Recipe, shprint
from os.path import join
import sh
import os
import fnmatch


class PillowRecipe(Recipe):
    version = "2.7.0"
    url = "https://github.com/python-pillow/Pillow/archive/{}.zip".format(version)
    library = "libpil.a"
    depends = ["libz", "freetype", "libjpeg", "python", "ios"]
    include_per_arch = True

    def get_pil_env(self, arch):
        build_env = arch.get_env()
        build_env["IOSROOT"] = self.ctx.root_dir
        build_env["IOSSDKROOT"] = arch.sysroot
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        build_env["ARM_LD"] = build_env["LD"]
        build_env["ARCH"] = arch.arch
        #build_env["C_INCLUDE_PATH"] = join(arch.sysroot, "usr", "include")
        #build_env["LIBRARY_PATH"] = join(arch.sysroot, "usr", "lib")
        build_env["CFLAGS"] = " ".join([
            "-I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "freetype")) +
            "   -I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "libjpeg")) +
            "   -I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "libz"))
            ])
        return build_env

    def _patch_setup(self):
        # patch setup to remove some functionnalities
        pyconfig = join(self.build_dir, "setup.py")
        self.lines = []
        def _remove_line(pattern, pattern2 = '', replace=False):
            _lines = []
            for line in self.lines:
                if pattern in line:
                    if replace:
                        _lines.append(pattern2)
                        #print 'replacing:\n {}\nwith:\n {} '.format(line, pattern2)
                    continue
                _lines.append(line)
            self.lines = _lines

        with open(pyconfig) as fd:
            self.lines = fd.readlines()

        self.lines.insert(201, '        elif True:\n')
        self.lines.insert(202, '            pass\n')

        _remove_line(
            "    import _tkinter",
            pattern2="    _tkinter = None\n",
            replace=True)
        _remove_line('_add_directory(library_dirs, "/usr/local/lib")')
        _remove_line('_add_directory(include_dirs, "/usr/local/include")')
        _remove_line(
            'prefix = sysconfig.get_config_var("prefix")', 
            pattern2='        prefix = False\n',
            replace=True)

        _remove_line('import mp_compile')
        _remove_line('_add_directory(library_dirs, "/usr/lib")')
        _remove_line('_add_directory(include_dirs, "/usr/include")')
        _remove_line('if sys.platform == "darwin":',
            pattern2 = '        if False:\n', replace=True)
        _remove_line('zlib = jpeg = tiff = freetype = tcl = tk = lcms = webp = webpmux = None',
            pattern2 = '        zlib = jpeg = tiff = freetype = tcl = tk = lcms = webp = webpmux = None\n',
            replace=True)
        with open(pyconfig, "wb") as fd:
            fd.writelines(self.lines)

    def _prebuild_pil(self, hostpython):
        sh.curl("-O",  "https://bootstrap.pypa.io/ez_setup.py")
        shprint(hostpython, "./ez_setup.py")

    def build_arch(self, arch):
        self._patch_setup()
        build_env = self.get_pil_env(arch)
        #build_dir = self.get_build_dir(arch.arch)
        hostpython = sh.Command(self.ctx.hostpython)
        #build_env["PYTHONHOME"] = hostpython
        self._prebuild_pil(hostpython)
        # first try to generate .h
        try:
            shprint(hostpython, "setup.py", "build_ext", "-g",
                    _env=build_env)
        except:
            pass
        shprint(hostpython, "setup.py", "build_ext", "-g",
                _env=build_env)
        self.biglink()

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = self.get_pil_env(arch)
        shprint(hostpython, "setup.py", "install", "-O2",
                "--prefix", join(build_dir, "iosbuild"),
                _env=build_env)
        dest_dir = join(self.ctx.dist_dir, "root", "python", "lib", "python2.7",
                "site-packages", "pil")
        if exists(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.copytree(
            join(build_dir, "iosbuild", "lib",
                 "python2.7", "site-packages", "pil"),
            dest_dir)

    def biglink(self):
        dirs = []
        for root, dirnames, filenames in os.walk(self.build_dir):
            if fnmatch.filter(filenames, "*.so.libs"):
                dirs.append(root)
        cmd = sh.Command(join(self.ctx.root_dir, "tools", "biglink"))
        shprint(cmd, join(self.build_dir, "libpil.a"), *dirs)

recipe = PillowRecipe()

