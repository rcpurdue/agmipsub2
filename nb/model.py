# model.py - Storage access for app
# rcampbel@purdue.edu - 2020-07-14
import os
import csv
import sys
import difflib
import pandas as pd
from nb.log import log
from nb.config import HDR, ITM, YRS, VAL  

FIX_TBL_SUFFIX = 'FixTable'
FIX_COL = 'Fix'

model = sys.modules[__name__]

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
    except OSError:
        model.path = None
        raise
        
    return model.path is not None

def detect_delim():
    try:
        with open(model.path, newline='') as f:
            sample = f.read(1024)
            model.detected_delim = csv.Sniffer().sniff(sample).delimiter
    except csv.Error:
        model.detected_delim = None
        raise

    return model.detected_delim is not None

def read_file(delim=None, skip=0, header='infer', ignore=[]):
    try:

        if not header == 'infer':
            header = skip + 0 if header else None

        model.df = pd.read_csv(model.path, sep=delim, dtype=str, skiprows=skip, header=header, keep_default_na=False)
    except Exception:
        model.df, model.delim = None, None
        raise

    model.num_rows_read = len(model.df)
    model.ignore_scenarios(ignore)
    return model.df is not None

def ignore_scenarios(ignore, scenario_col=None, remove=False):
    
    if len(ignore) > 0:

        if scenario_col is None:
            # Try to find column holding scenario data
            columns_with_values = model.df.isin(ignore).any(axis=0)
            columns_list = columns_with_values[columns_with_values].index.tolist()
            scenario_col = columns_list[0] if len(columns_list) == 1 else None    

        if scenario_col is not None:
            # Filter using scen col & ignore list 
            filtered_df = model.df[~model.df[scenario_col].isin(ignore)]

            # Save count for integrity tab
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
    model.rules = pd.read_excel(os.path.join(project.base, project.rule_file), sheet_name=None, dtype=str, keep_default_na=False)

def all_models():
    return list(model.rules['ModelTable']['Model']) 

def analyze(col_map):
    "Create row counts, bad label list, unknown label list."
    model.num_rows_with_nan = model.df.isna().any(axis=1).sum()  # Row count: Structural problems
    model.duplicate_rows = model.df.duplicated().sum()  # Row count: Duplicate rows
    model.bad_labels, model.unknown_labels = [], []

    # Process output data by column - except values col
    for i, name in enumerate(HDR[1:7]):  # Each column
        data = model.df.iloc[:, col_map[i+1]].unique()  # Unique labels in data (+1 to skip model)
        valid = model.rules[name+'Table'][name]  # Valid labels in rules

        # Check each invalid label
        for label in list(set(data) - set(valid)):  
            loc, row, fix, match = None, None, None, None  

            # Is there a fix from a "fix' table in rules?
            if name+FIX_TBL_SUFFIX in model.rules.keys():   
                loc = model.rules[name+FIX_TBL_SUFFIX][name].str.lower() == label.lower()
                row = model.rules[name+FIX_TBL_SUFFIX][loc]
                fix = list(row[FIX_COL])

            # Fix found: add to "bads"
            if (fix is not None) and (len(fix) > 0): 
                model.bad_labels.append((name, label, fix[0]))  
            
            # No fix found: add to "unkowns"
            else:
                match_list = difflib.get_close_matches(str(label), valid.tolist(), n=1)  # default cutoff=0.6 TODO Validate   
                
                if match_list is not None and len(match_list) > 0:
                    model.unknown_labels.append((name, label, match_list[0]))  
                else:
                    model.unknown_labels.append((name, label, None))  

    # Find fixes for value col

    na_mask = pd.to_numeric(model.df.iloc[:, col_map[7]], errors='coerce').isna()     
    non_num_unique = model.df.iloc[:, col_map[7]][na_mask].unique()

    for label in non_num_unique:
        model.bad_labels.append((VAL, label, '0'))  # NOTE Hardcode zero TODO Verify      

def get_valid(col): 
    return model.rules[col+'Table'][col].tolist()

def get_unique(col_map, out_col_num):
    return model.df.iloc[:, col_map[out_col_num]].unique().tolist()

def fix(col_map, col, lbl, fix, remove_rows):
    col = col_map[HDR.index(col)]  # Convert col hdr text to col index 
    
    if remove_rows:
        model.df = model.df[model.df.iloc[:, col] != lbl]
    else:
        model.df.iloc[:, col] = model.df.iloc[:, col].replace(lbl, fix)

def select(col_map, scn, reg, var):
    scn_col, reg_col, var_col = col_map[1], col_map[2], col_map[3] 
    mask = (model.df.iloc[:, scn_col] == scn) & \
           (model.df.iloc[:, reg_col] == reg) & \
           (model.df.iloc[:, var_col] == var)
    subset = model.df[mask].copy(deep=True)

    # Change year & value cols to numeric
    yrs_col, val_col = col_map[6], col_map[7] 
    subset.iloc[:, yrs_col] = subset.iloc[:, yrs_col].astype(int) 
    subset.iloc[:, val_col] = subset.iloc[:, val_col].astype(float) 
    
    subset.set_index(YRS, inplace=True)
    return subset.groupby(ITM)[VAL]    

