#!/bin/bash

arm64_set_path_and_python_version(){
  python_version="$1"
  if [[ $(/usr/bin/arch) = arm64 ]]; then
      echo $PATH
      export PATH=/usr/local/bin:$PATH
      export PATH=/opt/homebrew/bin:$PATH
      eval "$(pyenv init --path)"
      pyenv install $python_version -s
      pyenv global $python_version
      export PATH=$(pyenv prefix)/bin:$PATH
  fi
}
