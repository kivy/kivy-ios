from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import os
import fnmatch
import shutil


class ZlibRecipe(Recipe):
    version = "1.2.8"
    url = "http://liquidtelecom.dl.sourceforge.net/project/libpng/zlib/{version}/zlib-{version}.tar.gz".format(version=version)
    library = "libz.a"
    include_dir = [
        ("zlib.h", ""),
        ("crc32.h", ""),
        ("deflate.h", ""),
        ("gzguts.h", ""),
        ("inffast.h", ""),
        ("inffixed.h", ""),
        ("inflate.h", ""),
        ("inftrees.h", ""),
        ("trees.h", ""),
        ("zconf.h", ""),
        ("zutil.h", ""),
        ("contrib/iostream/zfstream.h", "contrib/iostream/"),
        ("contrib/iostream2/zstream.h", "contrib/iostream/"),
        ("contrib/iostream3/zfstream.h", "contrib/iostream/"),
        ("contrib/puff/puff.h", "contrib/puff"),
        ("contrib/minizip/crypt.h", "contrib/minizip"),
        ("contrib/minizip/ioapi.h", "contrib/minizip"),
        ("contrib/minizip/mztools.h", "contrib/minizip"),
        ("contrib/minizip/unzip.h", "contrib/minizip"),
        ("contrib/minizip/zip.h", "contrib/minizip")
        ]
    include_per_arch = True


    def build_arch(self, arch):
        build_env = arch.get_env()
        build_env['prefix'] = '/'
        build_env['CHOST'] = arch.triple
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "--static",
                _env=build_env)
        shprint(sh.make, "clean")
        shprint(sh.make)

recipe = ZlibRecipe()


