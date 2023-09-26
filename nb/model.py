# model.py - Storage access for app
# rcampbel@purdue.edu - 2020-07-14
import os
import csv
import glob
import sys
import pandas as pd
from nb.log import logger

model = sys.modules[__name__]
pd.set_option('display.width', 1000)  # Prevent data desc line breaking

class FileError(Exception):
    pass

def start():
    """Prep model."""
    model.df = None  # Pandas DataFrame

def read_file(file_path):
    """React to new file upload."""

    # Check for upload error
    if os.path.getsize(file_path) == 0:
        raise FileError("Upload failed (size=0)")
        
    # Detect delimiter, header
    try:
        with open(file_path, newline='') as f:
            sample = f.read(1024)
            model.delim = csv.Sniffer().sniff(sample).delimiter
            model.has_header = csv.Sniffer().has_header(sample)
    except:
        model.delim = None
        model.has_header = None

    logger.debug(f'Delimiter/header: "{model.delim}"/{model.has_header}')


def set_disp(data=None, limit=None, wide=False):
    """Prep Pandas to display specific number of data lines."""
    if not limit:
        limit = data.shape[0]

    pd.set_option('display.max_rows', limit + 1)

    if wide:
        pd.set_option('display.float_format', lambda x: format(x, '0,.4f'))


