from toolchain import Recipe


class MoodstocksRecipe(Recipe):
    version = "4.1.5"
    url = "https://moodstocks.com/static/releases/moodstocks-ios-sdk-{version}.zip"
    frameworks = ["Moodstocks.framework"]
    archs = ["i386"]
    pbx_frameworks = [
        "Moodstocks", "AVFoundation", "CoreMedia", "CoreVideo", "CFNetwork"]


recipe = MoodstocksRecipe()


