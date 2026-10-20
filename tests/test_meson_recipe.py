import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from kivy_ios.toolchain import MesonRecipe, ToolchainCL
from kivy_ios.recipes.libcairo import LibcairoRecipe
from kivy_ios.recipes.pycairo import PycairoRecipe


class TestMesonRecipe(unittest.TestCase):

    def setUp(self):
        self.ctx = MagicMock()
        self.ctx.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kivy_ios"))
        self.ctx.hostpython = "/dist/hostpython3/bin/python"
        self.ctx.include_dir = "/dist/include"
        self.ctx.dist_dir = "/dist"
        self.ctx.build_dir = "/build"
        self.ctx.python_prefix = "/dist/root/python3"
        self.ctx.python_ver = "3.11"
        self.ctx.so_suffix = ".cpython-311-darwin.so"
        self.ctx.site_packages_dir = "/dist/root/python3/lib/python3.11/site-packages"
        self.ctx.state = MagicMock()
        self.ctx.state.get.return_value = None

        self.plat_arm64 = MagicMock()
        self.plat_arm64.arch = "arm64"
        self.plat_arm64.sdk = "iphoneos"
        self.plat_arm64.name = "iphoneos-arm64"
        self.plat_arm64.get_env.return_value = {
            "CC": "/tmp/cc_arm64.sh",
            "CXX": "/tmp/cxx_arm64.sh",
            "AR": "/usr/bin/ar",
            "STRIP": "/usr/bin/strip",
        }

        self.plat_x86_64 = MagicMock()
        self.plat_x86_64.arch = "x86_64"
        self.plat_x86_64.sdk = "iphonesimulator"
        self.plat_x86_64.name = "iphonesimulator-x86_64"
        self.plat_x86_64.get_env.return_value = {
            "CC": "/tmp/cc_x86.sh",
            "CXX": "/tmp/cxx_x86.sh",
            "AR": "/usr/bin/ar",
            "STRIP": "/usr/bin/strip",
        }

    def test_meson_recipe_defaults(self):
        from kivy_ios.toolchain import Recipe

        class DummyMeson(MesonRecipe):
            pass

        recipe = DummyMeson()
        self.assertIn("meson", recipe.hostpython_prerequisites)
        self.assertIn("ninja", recipe.hostpython_prerequisites)
        self.assertFalse(recipe.skip_python)
        self.assertEqual(recipe.meson_options, [])
        self.assertEqual(recipe.patches, [])
        self.assertTrue(recipe.strip_main)
        self.assertFalse(Recipe().strip_main)

    def test_generate_crossfile_arm64(self):
        recipe = MesonRecipe()
        recipe.skip_python = True
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            cross_file = recipe.generate_crossfile(self.plat_arm64)
            self.assertTrue(os.path.exists(cross_file))
            with open(cross_file) as f:
                content = f.read()

            self.assertIn("[binaries]", content)
            self.assertIn("c = '/tmp/cc_arm64.sh'", content)
            self.assertIn("cpp = '/tmp/cxx_arm64.sh'", content)
            self.assertIn(f"python = '{self.ctx.hostpython}'", content)
            self.assertIn("[host_machine]", content)
            self.assertIn("system = 'darwin'", content)
            self.assertIn("cpu_family = 'aarch64'", content)
            self.assertIn("cpu = 'arm64'", content)
            self.assertIn("endian = 'little'", content)

    def test_python_wrapper_generation(self):
        recipe = MesonRecipe()
        recipe.skip_python = False
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            wrapper_path = recipe.get_python_wrapper(self.plat_arm64)
            self.assertTrue(os.path.exists(wrapper_path))
            self.assertTrue(os.access(wrapper_path, os.X_OK))
            with open(wrapper_path) as f:
                content = f.read()
            self.assertIn("TARGET_PYTHON_PREFIX", content)
            self.assertIn("handle_python_info", content)

            cross_file = recipe.generate_crossfile(self.plat_arm64)
            with open(cross_file) as f:
                cross_content = f.read()
            self.assertIn(f"python = '{wrapper_path}'", cross_content)

    def test_python_wrapper_execution_intercept(self):
        recipe = MesonRecipe()
        recipe.skip_python = False
        recipe.ctx = self.ctx
        recipe.ctx.hostpython = sys.executable
        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            wrapper_path = recipe.get_python_wrapper(self.plat_arm64)
            self.assertTrue(os.path.exists(wrapper_path))

            # Test 1: Intercept python_info.py call
            cmd = [wrapper_path, "/path/to/mesonbuild/scripts/python_info.py"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["version"], "3.11")
            self.assertEqual(data["suffix"], ".cpython-311-darwin.so")
            self.assertEqual(data["platform"], "darwin")
            self.assertEqual(data["paths"]["purelib"], "/dist/root/python3/lib/python3.11/site-packages")

    def test_python_wrapper_execution_passthrough(self):
        recipe = MesonRecipe()
        recipe.skip_python = False
        recipe.ctx = self.ctx
        recipe.ctx.hostpython = sys.executable
        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            wrapper_path = recipe.get_python_wrapper(self.plat_arm64)
            cmd = [wrapper_path, "-c", "import sys; print('PASSTHROUGH_OK')"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout.strip(), "PASSTHROUGH_OK")

    def test_meson_invokes_python_wrapper(self):
        meson_bin = shutil.which("meson")
        cc_bin = shutil.which("cc")
        if not meson_bin or not cc_bin:
            self.skipTest("meson or cc executable not found in PATH")

        mini_meson = """project('test_wrapper', 'c', meson_version: '>= 0.64.0')
pymod = import('python')
py = pymod.find_installation()
message('FOUND PYTHON VERSION: ' + py.language_version())
"""
        recipe = MesonRecipe()
        recipe.skip_python = False
        recipe.ctx = self.ctx
        recipe.ctx.hostpython = sys.executable

        plat = MagicMock()
        plat.arch = "arm64"
        plat.sdk = "iphoneos"
        plat.name = "iphoneos-arm64"
        plat.get_env.return_value = {
            "CC": cc_bin,
            "CXX": shutil.which("c++") or cc_bin,
            "AR": "ar",
            "STRIP": "strip",
        }

        with tempfile.TemporaryDirectory() as td:
            src_dir = os.path.join(td, "src")
            os.makedirs(src_dir)
            with open(os.path.join(src_dir, "meson.build"), "w") as f:
                f.write(mini_meson)

            build_dir = os.path.join(td, "build")
            recipe.build_dir = build_dir
            cross_file = recipe.generate_crossfile(plat)
            wrapper_path = recipe.get_python_wrapper(plat)

            log_file = os.path.join(td, "wrapper_called.log")
            with open(wrapper_path) as f:
                content = f.read()
            instrumented = content.replace(
                "def handle_python_info():",
                f'def handle_python_info():\n    with open("{log_file}", "a") as lf: lf.write("called\\n")'
            )
            with open(wrapper_path, "w") as f:
                f.write(instrumented)

            res = subprocess.run([
                meson_bin, "setup", os.path.join(build_dir, "builddir"),
                "--cross-file", cross_file
            ], cwd=src_dir, capture_output=True, text=True)

            self.assertEqual(res.returncode, 0, f"Meson setup failed:\n{res.stderr}\n{res.stdout}")
            self.assertIn("FOUND PYTHON VERSION: 3.11", res.stdout)
            self.assertTrue(os.path.exists(log_file), "Wrapper log file was not created; wrapper was not called")
            with open(log_file) as f:
                self.assertIn("called", f.read())

    def test_config_wrappers(self):
        recipe = MesonRecipe()
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            p_wrap = recipe.get_config_wrappers(self.plat_arm64, "pybind11")
            self.assertTrue(os.path.exists(p_wrap))
            self.assertTrue(os.access(p_wrap, os.X_OK))
            with open(p_wrap) as f:
                content = f.read()
            self.assertIn("pybind11", content)

    def test_generate_crossfile_x86_64(self):
        recipe = MesonRecipe()
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            cross_file = recipe.generate_crossfile(self.plat_x86_64)
            self.assertTrue(os.path.exists(cross_file))
            with open(cross_file) as f:
                content = f.read()

            self.assertIn("cpu_family = 'x86_64'", content)
            self.assertIn("cpu = 'x86_64'", content)

    def test_prebuild_platform_applies_patches(self):
        recipe = MesonRecipe()
        recipe.patches = ["test.patch"]
        recipe.has_marker = MagicMock(return_value=False)
        recipe.apply_patch = MagicMock()
        recipe.set_marker = MagicMock()

        recipe.prebuild_platform(self.plat_arm64)
        recipe.apply_patch.assert_called_once_with("test.patch")
        recipe.set_marker.assert_called_once_with("patched")

    def test_libcairo_recipe_config(self):
        recipe = LibcairoRecipe()
        recipe.ctx = self.ctx

        self.assertEqual(recipe.name, "libcairo")
        self.assertEqual(recipe.version, "1.18.4")
        self.assertTrue(recipe.skip_python)
        self.assertIn("hostpython3", recipe.depends)
        self.assertIn("libpng", recipe.depends)
        self.assertEqual(recipe.patches, ["meson.patch"])
        self.assertEqual(recipe.include_name, "cairo")

        opts = recipe.get_recipe_meson_options(self.plat_arm64)
        self.assertTrue(any(opt.startswith("-Dpng=") for opt in opts))
        self.assertTrue(any(opt.startswith("-Dpng_include_dir=") for opt in opts))
        self.assertIn("-Dfreetype=disabled", opts)
        self.assertIn("-Dtests=disabled", opts)
        self.assertNotIn("-Ddemos=disabled", opts)
        self.assertIn("-Dpixman:tests=disabled", opts)
        self.assertIn("-Dpixman:demos=disabled", opts)

    def test_pycairo_recipe_config(self):
        recipe = PycairoRecipe()
        recipe.ctx = self.ctx

        self.assertEqual(recipe.name, "pycairo")
        self.assertEqual(recipe.version, "1.28.0")
        self.assertFalse(recipe.skip_python)
        self.assertEqual(recipe.site_packages_name, "cairo")
        self.assertIn("hostpython3", recipe.depends)
        self.assertIn("python3", recipe.depends)
        self.assertIn("libcairo", recipe.depends)
        self.assertEqual(recipe.patches, ["meson.patch"])
        self.assertEqual(recipe.library, "libpycairo.a")

        opts = recipe.get_recipe_meson_options(self.plat_arm64)
        self.assertTrue(any(opt.startswith("-Dcairo_include=") for opt in opts))
        self.assertTrue(any(opt.startswith("-Dcairo_lib=") for opt in opts))
        self.assertIn("-Dtests=false", opts)

    def test_install_site_packages_copying(self):
        recipe = MesonRecipe()
        recipe.skip_python = False
        recipe.name = "testpkg"
        self.ctx.selected_platforms = [self.plat_arm64]

        with tempfile.TemporaryDirectory() as build_td, tempfile.TemporaryDirectory() as sp_td:
            recipe.get_build_dir = MagicMock(return_value=build_td)
            recipe.ctx = self.ctx
            recipe.ctx.site_packages_dir = sp_td

            install_sp = os.path.join(build_td, "builddir", "install", "lib", "python3.11", "site-packages", "testpkg")
            os.makedirs(install_sp)
            with open(os.path.join(install_sp, "__init__.py"), "w") as f:
                f.write("# testpkg")
            with open(os.path.join(install_sp, "_testpkg.cpython-311m-darwin.so"), "w") as f:
                f.write("so")

            recipe.install()

            dest_init = os.path.join(sp_td, "testpkg", "__init__.py")
            self.assertTrue(os.path.exists(dest_init))
            with open(dest_init) as f:
                self.assertEqual(f.read(), "# testpkg")

            dest_so_clean = os.path.join(sp_td, "testpkg", "_testpkg.cpython-311-darwin.so")
            dest_so_old = os.path.join(sp_td, "testpkg", "_testpkg.cpython-311m-darwin.so")
            self.assertTrue(os.path.exists(dest_so_clean))
            self.assertFalse(os.path.exists(dest_so_old))

    def test_hostpython3_so_suffix(self):
        from kivy_ios.recipes.hostpython3 import Hostpython3Recipe
        recipe = Hostpython3Recipe()
        recipe.init_with_ctx(self.ctx)
        self.assertEqual(self.ctx.so_suffix, ".cpython-311-darwin.so")
        self.assertNotIn("311m", self.ctx.so_suffix)

    def test_python_wrapper_sanitizes_m_suffix(self):
        recipe = MesonRecipe()
        recipe.skip_python = False
        recipe.ctx = self.ctx
        recipe.ctx.so_suffix = ".cpython-311m-darwin.so"
        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            wrapper_path = recipe.get_python_wrapper(self.plat_arm64)
            with open(wrapper_path) as f:
                content = f.read()
            self.assertIn("PYTHON_SUFFIX = '.cpython-311-darwin.so'", content)
            self.assertNotIn("311m", content)

    def test_get_meson_command_hostpython_bin(self):
        recipe = MesonRecipe()
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            hp_bin = os.path.join(td, "python")
            meson_bin = os.path.join(td, "meson")
            with open(hp_bin, "w") as f:
                f.write("#!/bin/sh\n")
            with open(meson_bin, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(hp_bin, 0o755)
            os.chmod(meson_bin, 0o755)

            recipe.ctx.hostpython = hp_bin
            cmd = recipe.get_meson_command()
            self.assertEqual(str(cmd[0]), hp_bin)
            self.assertEqual(cmd[1], meson_bin)

    def test_get_meson_command_module_fallback(self):
        recipe = MesonRecipe()
        recipe.ctx = self.ctx
        recipe.ctx.dist_dir = None
        recipe.ctx.hostpython = sys.executable

        with patch("shutil.which", return_value=None):
            cmd = recipe.get_meson_command()
            self.assertEqual(str(cmd[0]), sys.executable)
            self.assertEqual(cmd[1:], ["-m", "mesonbuild.mesonmain"])

    def test_get_ninja_command_hostpython_bin(self):
        recipe = MesonRecipe()
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            hp_bin = os.path.join(td, "python")
            ninja_bin = os.path.join(td, "ninja")
            with open(hp_bin, "w") as f:
                f.write("#!/bin/sh\n")
            with open(ninja_bin, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(hp_bin, 0o755)
            os.chmod(ninja_bin, 0o755)

            recipe.ctx.hostpython = hp_bin
            cmd = recipe.get_ninja_command()
            self.assertEqual(str(cmd[0]), ninja_bin)

    def test_get_ninja_command_system_or_module(self):
        recipe = MesonRecipe()
        recipe.ctx = self.ctx
        recipe.ctx.dist_dir = None
        with tempfile.TemporaryDirectory() as td:
            recipe.ctx.hostpython = os.path.join(td, "python")
            sys_ninja = os.path.join(td, "sys_ninja")
            with open(sys_ninja, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(sys_ninja, 0o755)

            with patch("shutil.which", return_value=sys_ninja):
                cmd = recipe.get_ninja_command()
                self.assertEqual(str(cmd[0]), sys_ninja)

    def test_get_recipe_env_includes_path(self):
        recipe = MesonRecipe()
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            env = recipe.get_recipe_env(self.plat_arm64)
            self.assertIn("PATH", env)
            path_val = env["PATH"]
            self.assertIn(os.path.dirname(self.ctx.hostpython), path_val)
            self.assertIn(recipe.get_wrapper_dir(self.plat_arm64), path_val)

    def test_setup_ssl_certificates(self):
        recipe = MesonRecipe()
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            dummy_cert = os.path.join(td, "cert.pem")
            with open(dummy_cert, "w") as f:
                f.write("-----BEGIN CERTIFICATE-----\n-----END CERTIFICATE-----\n")
            with patch.dict(os.environ, {"SSL_CERT_FILE": dummy_cert}):
                env = {}
                recipe.setup_ssl_certificates(env)
                self.assertEqual(env.get("SSL_CERT_FILE"), dummy_cert)
                self.assertEqual(env.get("SSL_CERT_DIR"), td)

    def test_strip_main_from_library_darwin_format(self):
        recipe = LibcairoRecipe()
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            lib_path = os.path.join(td, "libcairo.a")
            with open(lib_path, "wb") as f:
                f.write(b"!<arch>\n")

            mock_nm_output = (
                "/path/libcairo.a[scaling-test.c.o]: 0000000000000000 T _main\n"
                "/path/libcairo.a[cairo.c.o]: 0000000000000000 T _cairo_create\n"
                "/path/libcairo.a[trap-crasher.c.o]: 0000000000000000 T _main\n"
                "/path/libcairo.a[SDL_uikit_main.o]: 0000000000000000 T _main\n"
            )

            with patch("kivy_ios.toolchain.sh.Command") as mock_cmd, \
                 patch("kivy_ios.toolchain.shprint") as mock_shprint:
                mock_nm = MagicMock(return_value=mock_nm_output)
                mock_cmd.return_value = mock_nm

                recipe.strip_main_from_library(self.plat_arm64, lib_path)

                deleted_objs = []
                for call_args in mock_shprint.call_args_list:
                    args = call_args[0]
                    if len(args) >= 4 and args[1] == "d" and args[2] == lib_path:
                        deleted_objs.append(args[3])
                self.assertEqual(sorted(deleted_objs), ["scaling-test.c.o", "trap-crasher.c.o"])
                self.assertNotIn("SDL_uikit_main.o", deleted_objs)

    def test_strip_main_skipped_for_sdl2(self):
        from kivy_ios.toolchain import Recipe
        recipe = Recipe()
        recipe.name = "sdl2"
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            lib_path = os.path.join(td, "libSDL2.a")
            with open(lib_path, "wb") as f:
                f.write(b"!<arch>\n")

            with patch("kivy_ios.toolchain.sh.Command") as mock_cmd:
                recipe.strip_main_from_library(self.plat_arm64, lib_path)
                mock_cmd.assert_not_called()

    def test_strip_main_from_library_gnu_format(self):
        recipe = LibcairoRecipe()
        recipe.ctx = self.ctx
        with tempfile.TemporaryDirectory() as td:
            lib_path = os.path.join(td, "libcairo.a")
            with open(lib_path, "wb") as f:
                f.write(b"!<arch>\n")

            mock_nm_output = (
                "/path/libcairo.a:scaling-test.c.o:0000000000000000 T main\n"
                "/path/libcairo.a:cairo.c.o:0000000000000000 T cairo_create\n"
            )

            with patch("kivy_ios.toolchain.sh.Command") as mock_cmd, \
                 patch("kivy_ios.toolchain.shprint") as mock_shprint:
                mock_nm = MagicMock(return_value=mock_nm_output)
                mock_cmd.return_value = mock_nm

                recipe.strip_main_from_library(self.plat_arm64, lib_path)

                deleted_objs = []
                for call_args in mock_shprint.call_args_list:
                    args = call_args[0]
                    if len(args) >= 4 and args[1] == "d" and args[2] == lib_path:
                        deleted_objs.append(args[3])
                self.assertEqual(deleted_objs, ["scaling-test.c.o"])

    def test_build_platform_skips_test_objects(self):
        recipe = LibcairoRecipe()
        recipe.ctx = self.ctx
        recipe.get_recipe_env = MagicMock(return_value={"AR": "ar"})
        recipe.generate_crossfile = MagicMock(return_value="/tmp/cross")
        recipe.get_meson_command = MagicMock(return_value=["meson"])
        recipe.get_ninja_command = MagicMock(return_value=["ninja"])
        recipe.strip_main_from_library = MagicMock()

        with tempfile.TemporaryDirectory() as td:
            recipe.build_dir = td
            builddir = os.path.join(td, "builddir")
            subprojects_dir = os.path.join(builddir, "subprojects", "pixman")
            test_dir = os.path.join(subprojects_dir, "test")
            good_obj = os.path.join(subprojects_dir, "pixman.o")
            test_obj1 = os.path.join(test_dir, "scaling-test.c.o")
            test_obj2 = os.path.join(subprojects_dir, "pixman-test.o")
            expected_lib = os.path.join(td, recipe.library.format(plat=self.plat_arm64))

            def fake_shprint(*args, **kwargs):
                if args and "install" in args:
                    os.makedirs(test_dir, exist_ok=True)
                    with open(good_obj, "w") as f:
                        f.write("obj")
                    with open(test_obj1, "w") as f:
                        f.write("obj")
                    with open(test_obj2, "w") as f:
                        f.write("obj")
                    os.makedirs(os.path.dirname(expected_lib), exist_ok=True)
                    if not os.path.exists(expected_lib):
                        with open(expected_lib, "w") as f:
                            f.write("lib")

            with patch("kivy_ios.toolchain.shprint", side_effect=fake_shprint) as mock_shprint:
                recipe.build_platform(self.plat_arm64)

                ar_calls = [c[0] for c in mock_shprint.call_args_list if len(c[0]) > 1 and c[0][1] == "-rcs"]
                self.assertTrue(len(ar_calls) > 0)
                added_files = ar_calls[0][3:]
                self.assertIn(good_obj, added_files)
                self.assertNotIn(test_obj1, added_files)
                self.assertNotIn(test_obj2, added_files)
                recipe.strip_main_from_library.assert_called_once_with(self.plat_arm64, expected_lib)

    def test_toolchain_clean_dist(self):
        with tempfile.TemporaryDirectory() as td:
            ctx = self.ctx
            ctx.state = MagicMock()
            ctx.dist_dir = os.path.join(td, "dist")
            ctx.build_dir = os.path.join(td, "build")
            ctx.include_dir = os.path.join(ctx.dist_dir, "include")

            ios_lib = os.path.join(ctx.dist_dir, "lib", "iphoneos", "libcairo.a")
            sim_lib = os.path.join(ctx.dist_dir, "lib", "iphonesimulator", "libcairo.a")
            xcframework = os.path.join(ctx.dist_dir, "xcframework", "libcairo.xcframework")
            inc_common = os.path.join(ctx.include_dir, "common", "cairo")
            inc_arm = os.path.join(ctx.include_dir, "iphoneos-arm64", "cairo")
            recipe_build = os.path.join(ctx.build_dir, "libcairo")

            for p in (ios_lib, sim_lib):
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w") as f:
                    f.write("lib")
            os.makedirs(xcframework, exist_ok=True)
            os.makedirs(inc_common, exist_ok=True)
            os.makedirs(inc_arm, exist_ok=True)
            os.makedirs(recipe_build, exist_ok=True)

            with patch("sys.argv", ["toolchain", "clean", "libcairo"]), \
                 patch("kivy_ios.toolchain.Context", return_value=ctx):
                toolchain = ToolchainCL()
                toolchain.clean()

            self.assertFalse(os.path.exists(ios_lib))
            self.assertFalse(os.path.exists(sim_lib))
            self.assertFalse(os.path.exists(xcframework))
            self.assertFalse(os.path.exists(inc_common))
            self.assertFalse(os.path.exists(inc_arm))
            self.assertFalse(os.path.exists(recipe_build))


if __name__ == "__main__":
    unittest.main()
