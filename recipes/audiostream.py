from toolchain import Recipe

class AudiostreamRecipe(Recipe):
    version = "master"
    url = "https://github.com/kivy/audiostream/archive/{version}.zip"

recipe = AudiostreamRecipe()
