import os
import shutil
import tempfile


def before_scenario(context, *args, **kwargs):
    context.starting_dir = os.getcwd()
    context.temp_dir = tempfile.mkdtemp()
    os.chdir(context.temp_dir)


def after_scenario(context, *args, **kwargs):
    os.chdir(context.starting_dir)
    shutil.rmtree(context.temp_dir)
