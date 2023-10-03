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
    model.detected_delim = None
    model.path = None
    model.suspect_scen_col = None
    model.rules = None

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
            model.detected_delim = csv.Sniffer().sniff(sample).delimiter
    except:
        logger.debug('Exception: detect_delim()...\n'+traceback.format_exc())
        model.detected_delim = None

    logger.debug(f'Delimiter: "{model.detected_delim}"')
    return model.detected_delim is not None

def read_file(delim=None, skip=0, header='infer', ignore=[]):

    if not header == 'infer':
        header = skip + 0 if header else None

    try:
        model.df = pd.read_csv(model.path, sep=delim, dtype=str, skiprows=skip, header=header)
        logger.debug(f'Records: "{len(model.df)}"')
    except:
        model.df, model.delim = None, None
        logger.debug('Exception: read_file()...\n'+traceback.format_exc())

    if len(ignore) > 0:
        # Try to find column holding scenario data
        columns_with_values = model.df.isin(ignore).any(axis=0)
        columns_list = columns_with_values[columns_with_values].index.tolist()
        
        if len(columns_list) == 1:
            # Filter using suspected scen col & ignore list 
            model.suspect_scen_col = columns_list[0]
            logger.debug(f'Suspected sceanrio column: "{model.suspect_scen_col}"')
            filtered_df = model.df[~model.df[model.suspect_scen_col].isin(ignore)]
            model.df = filtered_df.reset_index(drop=True)

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

def load_rules(project):
    """Read all rules from worksheets in project's xlsx file."""
    model.rules = pd.read_excel(os.path.join(project.base, project.rule_file), sheet_name=None)
    logger.debug(f'Rule keys: "{list(model.rules.keys())}"')

def all_models():
    return list(model.rules['ModelTable']['Model']) 
