#!/bin/sh

. /etc/profile
. ~/.bash_profile

pyenv activate venv-ffxivbot
supervisorctl restart all
pyenv deactivate venv-ffxivbot
