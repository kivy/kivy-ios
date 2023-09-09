#!/bin/bash

# Enforce Python Version
python_version=$(python3 --version)
if ! [[ $python_version == *"3.10."* ]]; then
    echo "Requires Python version of 3.10.x"
    exit 1
fi

version="$1"

if [ -z $version ]; then
    echo "Must pass in PE version as argument."
    exit 1
fi

# Clean up Toolchain Dist
# echo "Cleaning up Toolchain Dist"
# python3 toolchain.py distclean

# Clone PE
git clone --branch ${version} git@github.com:diamondkinetics/dk-python.git ./temp/dk-python/

# Get required dependency versions from patch-data.txt
# NOTE: the versions in requirements.txt should correspond to what dk-python built and uploaded to aws
#       and also can be found in dk-python/requirements.txt
# NOTE: these versions are used to patch recipes and create version folders for setup.py
echo "Patching Recipes"
dkextensions_version_line=$(grep 'dkextensions==' ./temp/dk-python/requirements.txt)
dkextensions_version="${dkextensions_version_line//dkextensions==}"
sed -i '' "s/{version}/${dkextensions_version}/" ./kivy_ios/recipes/dkextensions/__init__.py

ppcommon_version_line=$(grep 'python_ppcommon_wrapper==' ./temp/dk-python/requirements.txt)
ppcommon_version="${ppcommon_version_line//python_ppcommon_wrapper==}"
sed -i '' "s/{version}/${ppcommon_version}/" ./kivy_ios/recipes/python_ppcommon_wrapper/__init__.py

peak_finding_utils_version_line=$(grep 'peak_finding_utils==' ./temp/dk-python/requirements.txt)
peak_finding_utils_version="${peak_finding_utils_version_line//peak_finding_utils==}"
sed -i '' "s/{version}/${peak_finding_utils_version}/" ./kivy_ios/recipes/peak_finding_utils/__init__.py

rotation_version_line=$(grep 'rotation==' ./temp/dk-python/requirements.txt)
rotation_version="${rotation_version_line//rotation==}"
sed -i '' "s/{version}/${rotation_version}/" ./kivy_ios/recipes/rotation/__init__.py

echo "Patch Versions: "
echo "dkextensions: $dkextensions_version"
echo "python_ppcommon_wrapper: $ppcommon_version"
echo "peak_finding_utils: $peak_finding_utils_version"
echo "rotation: $rotation_version"

# Clone Pose Engine
git clone git@github.com:diamondkinetics/pose_engine.git ./temp/pose_engine/

# Build default libraries using the kivy toolchain
# Could run a clean if desired, python3 toolchain.py clean

python3 toolchain.py build python3 numpy

# Patch numpy
# NOTE: numpy_init.py is hardcoded to numpy version and cython version
cp ./patch_files/numpy/_numpyconfig.h ./dist/include/common/numpy/numpy/_numpyconfig.h
cp ./patch_files/numpy/__multiarray_api.h ./dist/include/common/numpy/numpy/__multiarray_api.h
cp ./patch_files/numpy/__ufunc_api.h ./dist/include/common/numpy/numpy/__ufunc_api.h
sed -i '' "s/import platform/# import platform/" ./dist/root/python3/lib/python3.10/site-packages/numpy/core/_internal.py
sed -i '' "s/IS_PYPY = /IS_PYPY = False #/" ./dist/root/python3/lib/python3.10/site-packages/numpy/core/_internal.py

# Patch PE
sed -i '' "s/from dk.pe.swing.options.options import SwingOptions/# you've been patched/" ./temp/dk-python/dk/pe/lib/options/__init__.py
sed -i '' "s/from dk.pe.pitch.options import PitchOptions/# you've been patched/" ./temp/dk-python/dk/pe/lib/options/__init__.py

echo "Copying setup.py to version folders for each recipe"
# Patch dkextensions
python3 toolchain.py download dkextensions
tar -xvzf ./.cache/dkextensions-dkextensions.tar.gz -C ./temp/
rm ./.cache/dkextensions-dkextensions.tar.gz
rm ./temp/dkextensions-${dkextensions_version}/setup.py
cp ./patch_files/dkextensions/setup.py ./temp/dkextensions-${dkextensions_version}/
cd temp/
tar czf ./../.cache/dkextensions-dkextensions.tar.gz dkextensions-${dkextensions_version}
cd ..

# Patch peak_finding_utils
python3 toolchain.py download peak_finding_utils
tar -xvzf ./.cache/peak_finding_utils-peak_finding_utils.tar.gz -C ./temp/
rm ./.cache/peak_finding_utils-peak_finding_utils.tar.gz
rm ./temp/peak_finding_utils-${peak_finding_utils_version}/setup.py
cp ./patch_files/peak_finding_utils/setup.py ./temp/peak_finding_utils-${peak_finding_utils_version}/
cd temp/
tar czf ./../.cache/peak_finding_utils-peak_finding_utils.tar.gz peak_finding_utils-${peak_finding_utils_version}
cd ..

# Patch rotation
python3 toolchain.py download rotation
tar -xvzf ./.cache/rotation-rotation.tar.gz -C ./temp/
rm ./.cache/rotation-rotation.tar.gz
rm ./temp/rotation-${rotation_version}/setup.py
cp ./patch_files/rotation/setup.py ./temp/rotation-${rotation_version}/
cd temp/
tar czf ./../.cache/rotation-rotation.tar.gz rotation-${rotation_version}
cd ..

# Build custom libraries
echo "=== Build Custom Libraries ==="
python3 toolchain.py build dkextensions python_ppcommon_wrapper peak_finding_utils rotation

# Copy into artifact directory
rsync -av --delete ./dist/root/python3/include ./artifact/
rsync -av ./dist/root/python3/lib ./artifact/
rsync -av ./dist/lib/ ./artifact/static_libs/
rsync -av ./temp/dk-python/dk ./artifact/lib/python3.10/site-packages/
rsync -av ./temp/pose_engine/pose ./artifact/lib/python3.10/site-packages/
rsync -av ./temp/pose_engine/keypoints_detection ./artifact/lib/python3.10/site-packages/
rsync -av ./temp/pose_engine/utils ./artifact/lib/python3.10/site-packages/

# Compile Python!
./dist/hostpython3/bin/python -OO -m compileall -f -b ./artifact/lib/

# Remove all file types that Apple will reject
find ./artifact/lib/ -regex '.*\.py' -delete
find ./artifact/lib/ -regex '.*\.sh' -delete
find ./artifact/lib/ -regex '.*\.a' -delete
find ./artifact/lib/ -regex '.*\.pyi' -delete
find ./artifact/lib/ -regex '.*\.pyx' -delete
find ./artifact/lib/ -regex '.*\.md' -delete
find ./artifact/lib/ -regex '.*\.ipynb' -delete

# zip up artifact!
mkdir -p artifacts/
zip -r artifacts/ios-dk-physics-engine-artifact-${version}.zip artifact

# Clean up
rm -r ./artifact
rm -rf ./temp
# This resets the recipes from changes above
git checkout -- ./kivy_ios/recipes/dkextensions/__init__.py
git checkout -- ./kivy_ios/recipes/python_ppcommon_wrapper/__init__.py
git checkout -- ./kivy_ios/recipes/peak_finding_utils/__init__.py
git checkout -- ./kivy_ios/recipes/rotation/__init__.py
