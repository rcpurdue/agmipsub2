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

# Output col order:
#    0)Model, 1)Scenario, 2)Region, 3)Variable, 4)Item, 5)Unit, 6)Year, 7)Value
OUT_COL_NAMES = ['Model', 'Scenario', 'Region', 'Variable', 'Item', 'Unit', 'Year']


class FileError(Exception):
    pass

def start():
    """Prep model."""
    model.df = None  # Pandas DataFrame - all rows read from file
    model.preview_df = None  # Pandas DataFrame - first few rows of model.df that don't have ignoreed scencarios 
    model.detected_delim = None
    model.path = None
    model.suspect_scen_col = None
    model.rules = None
    model.num_rows_read = 0
    model.num_rows_ignored_scens = 0
    model.bad_labels = None
    model.unknown_labels = None

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

    model.num_rows_read = len(model.df)
    model.ignore_scenarios(ignore)
    return model.df is not None

def ignore_scenarios(ignore, scenario_col=None, remove=False):
    logger.debug(f'model.ignore(): ignore={scenario_col}, scenario_col={scenario_col}, remove={remove}')
    
    if len(ignore) > 0:

        if scenario_col is None:
            # Try to find column holding scenario data
            columns_with_values = model.df.isin(ignore).any(axis=0)
            columns_list = columns_with_values[columns_with_values].index.tolist()
            scenario_col = columns_list[0] if len(columns_list) == 1 else None    
            logger.debug(f'model.ignore(): suspect scenario col={scenario_col}')

        if scenario_col is not None:
            # Filter using scen col & ignore list 
            filtered_df = model.df[~model.df[scenario_col].isin(ignore)]

            # Save count for integrity tab
            logger.debug(f'model.ignore(): num_rows_ignored_scens={model.num_rows_ignored_scens}')
            model.num_rows_ignored_scens = len(model.df) - len(filtered_df)

            if remove:
                model.df = filtered_df.reset_index(drop=True)
                model.preview_df = model.df.head(3)
            else:
                model.preview_df = filtered_df.copy().reset_index(drop=True).head(3) 
    
    else:
        model.num_rows_ignored_scens = 0  # Save count for integrity tab
        model.preview_df = model.df.head(3) 

def has_header():
    return isinstance(model.df.columns[0], str)

def load_rules(project):
    """Read all rules from worksheets in project's xlsx file."""
    model.rules = pd.read_excel(os.path.join(project.base, project.rule_file), sheet_name=None, dtype=str)
    logger.debug(f'Rule keys: "{list(model.rules.keys())}"')

def all_models():
    return list(model.rules['ModelTable']['Model']) 

def analyze(col_map):
    logger.debug(f'analyze(): col_map={col_map}') 
    model.num_rows_with_nan = model.df.isna().any(axis=1).sum()  # Structural problems
    model.duplicate_rows = model.df.duplicated().sum()  # Duplicate rows
    model.bad_labels = {}
    model.unknown_labels = []

    # Find invalid labels & suggest fixes
    for i, name in enumerate(model.OUT_COL_NAMES[1:7]):  # Each column
        data = model.df.iloc[:, col_map[i+1]].unique()  # Unique labels in data (+1 to skip model)
        valid = model.rules[name+'Table'][name]  # Valid labels in rules

        for label in list(set(data) - set(valid)):  # Each invalid label
            model.unknown_labels.append(label) # Assume no fix, remove later if fix found
            fix = None

            if name+'FixTable' in model.rules.keys():  # Look for fix 
                fix1 = model.rules[name+'FixTable'].loc[model.rules[name+'FixTable'][name] == label]
                fix2 = fix1['Fix']
                fix = list(fix2)
                logger.debug(f'analyze(): name={name}, label={label}, fix1={fix1}, fix2={fix2}, fix={fix}')

            if (fix is not None) and (len(fix) == 1): 
                model.unknown_labels.remove(label)
                model.bad_labels[label] = fix  # Fix found: add to "bad"s

    logger.debug(f'analyze(): stuct_probs={model.num_rows_with_nan}, dupe={model.duplicate_rows}, bad={model.bad_labels}, unkwn={model.unknown_labels}')
