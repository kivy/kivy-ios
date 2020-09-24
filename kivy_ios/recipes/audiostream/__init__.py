from kivy_ios.toolchain import CythonRecipe


class AudiostreamRecipe(CythonRecipe):
    version = "master"
    url = "https://github.com/kivy/audiostream/archive/{version}.zip"
    library = "libaudiostream.a"
    depends = ["python", "sdl2", "sdl2_mixer"]
    pre_build_ext = True


recipe = AudiostreamRecipe()
