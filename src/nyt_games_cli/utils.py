import os

def get_stored_data_dir():
    home_dir = os.path.expanduser('~')
    data_dir = os.path.join(home_dir, '.nyt-cli-data')
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    return data_dir

def get_app_data_dir(app_name):
    dirname = os.path.join(get_stored_data_dir(), app_name)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return dirname



