# config.py - Configuration info, rcampbel@purdue.edu, Oct 2023
from dataclasses import dataclass

UPLOAD = 'Step 1: Upload file'
SUBMISSION = 'Step 2: Create submission'
INTEGRITY = 'Step 3: Check integrity'
PLAUSIBILITY = 'Step 4: Check plausibility'
FINISH = 'Finish up'

MOD = 'Model'  
SCN = 'Scenario'
REG = 'Region'  
VAR = 'Variable'
ITM = 'Item'    
UNI = 'Unit'    
YRS = 'Year'    
VAL = 'Value'   

#       0    1    2    3    4    5    6    7    
HDR = [MOD, SCN, REG, VAR, ITM, UNI, YRS, VAL]

DEL = '-DELETE-RECORDS-'
OVR = '-OVERRIDE-'

NUM_PREVIEW_ROWS = 3
COL_DDN_WIDTH = '140px'

@dataclass
class Project:
    name: str
    group: str
    base: str
    rule_file: str
    submit_dir: str
    pending_dir: str
    merge_file: str


@dataclass
class Config:
    all_projects: list


cfg = Config(
    all_projects=[Project(name='agclim50iv',
                          group='pr-agmipglobaleconagclim50iv',
                          base='/data/projects/agmipglobaleconagclim50iv/files/',
                          rule_file='.rules/RuleTables.xlsx',
                          submit_dir='.submissions/',
                          pending_dir='.submissions/.pending/',
                          merge_file='AgClim50IV.csv'),
                  Project(name='data',
                          group='pr-agmipglobalecondata',
                          base='/data/projects/agmipglobalecondata/files/',
                          rule_file='.rules/RuleTables.xlsx',
                          submit_dir='.submissions/',
                          pending_dir='.submissions/.pending/',
                          merge_file='Data.csv')])
