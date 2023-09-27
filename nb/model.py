# model.py - Storage access for app
# rcampbel@purdue.edu - 2020-07-14
import os
import csv
import glob
import sys
import traceback
import pandas as pd
from nb.log import logger

model = sys.modules[__name__]
pd.set_option('display.width', 1000)  # Prevent data desc line breaking

class FileError(Exception):
    pass

def start():
    """Prep model."""
    model.df = None  # Pandas DataFrame
    model.delim = None
    model.path = None

def set_file(file_path):
    try:
        model.path = file_path if os.path.getsize(file_path) > 0 else None
    except:
        logger.debug('Exception: set_file()...\n'+traceback.format_exc())
        model.path = None
        
    logger.debug(f'Model path: "{model.path}"')
    return model.path is not None
        
def detect_delim():
    try:
        with open(model.path, newline='') as f:
            sample = f.read(1024)
            model.delim = csv.Sniffer().sniff(sample).delimiter
    except:
        logger.debug('Exception: detect_delim()...\n'+traceback.format_exc())
        model.delim = None

    logger.debug(f'Delimiter: "{model.delim}"')
    return model.delim is not None

def read_file():
    try:
        model.df = pd.read_csv(model.path, sep=model.delim, dtype=str)
        logger.debug(f'Records: "{len(model.df)}"')
    except:
        model.df, model.delim = None, None
        logger.debug('Exception: read_file()...\n'+traceback.format_exc())

    return model.df is not None

def has_header():
    return isinstance(model.df.columns[0], str)

# TODO Remove?
def set_disp(data=None, limit=None, wide=False):
    """Prep Pandas to display specific number of data lines."""
    if not limit:
        limit = data.shape[0]

    pd.set_option('display.max_rows', limit + 1)

    if wide:
        pd.set_option('display.float_format', lambda x: format(x, '0,.4f'))


