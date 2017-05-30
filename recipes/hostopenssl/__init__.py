from toolchain import Recipe, shprint
from os.path import join, exists, basename, dirname
from os import makedirs
import sh
import shutil

def ensure_dir(filename):
    if not exists(filename):
        makedirs(filename)

class HostOpenSSLRecipe(Recipe):
    version = "1.0.2k"
    url = "http://www.openssl.org/source/openssl-{version}.tar.gz"
    archs = ["x86_64"]
    libraries = ["libssl.a", "libcrypto.a"]
    include_dir = "include"

    def build_x86_64(self):
	arch = self.archs[0]
        sdk_path = sh.xcrun("--sdk", "macosx", "--show-sdk-path").strip()
        dist_dir = join(self.ctx.dist_dir,"hostopenssl")
        print("OpenSSL for host to be installed at: {}").format(dist_dir)
        sh.perl(join(self.build_dir, "Configure"), "darwin64-x86_64-cc", 
                     "--openssldir={}".format(dist_dir),
                     "--prefix={}".format(dist_dir))

        shprint(sh.make, "clean")
        shprint(sh.make, "-j4", "build_libs")

    def install_include(self):
	arch = self.archs[0]
	print("Custom include file install...")
	print("Dist dir = {}".format(self.ctx.dist_dir))
        dest_dir = join(self.ctx.dist_dir,"hostopenssl","include")
        if exists(dest_dir):
            shutil.rmtree(dest_dir)
        src_dir = join(self.ctx.build_dir,"hostopenssl",arch,"openssl-{}".format(self.version),"include")
        shutil.copytree(src_dir,dest_dir)

    def build_all(self):
        filtered_archs = self.filtered_archs
        print("Build {} for {} (filtered)".format(
            self.name,
            ", ".join([x.arch for x in filtered_archs])))
        for arch in self.filtered_archs:
            self.build(arch)

        name = self.name
        if self.library:
            print("Create lipo library for {}".format(name))
            if not name.startswith("lib"):
                name = "lib{}".format(name)
            static_fn = join(self.ctx.dist_dir, "hostopenssl", "lib", "{}.a".format(name))
            ensure_dir(dirname(static_fn))
            print("Lipo {} to {}".format(self.name, static_fn))
            self.make_lipo(static_fn)
        if self.libraries:
            print("Create multiple lipo for {}".format(name))
            for library in self.libraries:
                static_fn = join(self.ctx.dist_dir, "hostopenssl", "lib", basename(library))
                ensure_dir(dirname(static_fn))
                print("  - Lipo-ize {}".format(library))
                self.make_lipo(static_fn, library)
        print("Install include files for {}".format(self.name))
        self.install_include()
        print("Install frameworks for {}".format(self.name))
        self.install_frameworks()
        print("Install sources for {}".format(self.name))
        self.install_sources()
        print("Install {}".format(self.name))
        self.install()

recipe = HostOpenSSLRecipe()
