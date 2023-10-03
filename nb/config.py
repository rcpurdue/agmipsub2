from dataclasses import dataclass

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
    all_projects = [
        Project(name='agclim50iv', 
                group='pr-agmipglobaleconagclim50iv',
                base='/data/projects/agmipglobaleconagclim50iv/files/',
                rule_file='.rules/RuleTables.xlsx', 
                submit_dir='.submissions/', 
                pending_dir='.submissions/.pending/', 
                merge_file='AgClim50IV.csv', 
               ),
        Project(name='data', 
                group='pr-agmipglobalecondata',
                base='/data/projects/agmipglobalecondata/files/',
                rule_file='.rules/RuleTables.xlsx', 
                submit_dir='.submissions/', 
                pending_dir='.submissions/.pending/', 
                merge_file='Data.csv', 
               ), 
    ]
)
