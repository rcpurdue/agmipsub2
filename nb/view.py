# view.py - User interface for app
# rcampbel@purdue.edu - 2020-07-14
import sys
from IPython.display import display, clear_output
from ipywidgets import \
    Accordion,  Dropdown, GridBox, HBox, BoundedIntText, Label, \
    Layout, Output, HTML, Image, ToggleButtons, Select, Tab, Text, VBox 
import ipyuploads
from nb import controller as ctrl
from nb.log import logger, log_handler

COLS = ['Model', 'Scenario', 'Region', 'Variable', 'Item', 'Unit', 'Year', 'Value']
view = sys.modules[__name__]


def start(show_log):
    """Build the user interface."""
    display(HTML(filename='nb/custom.html'))  # Send CSS code down to browser
    
    # Title
    app_title = HTML('AgMIP GlobalEcon Data Submission')
    app_title.add_class('app_title') 

    # Logo
    with open('nb/logo.png', "rb") as logo_file:
        logo = Image(value=logo_file.read(), format='png', layout={'max_height': '32px'})

    # Tabs

    view.tabs = Tab(children=[upload_tab(), submission_tab(),
                         integrity_tab(), plausibility_tab(),
                         activity_tab()])

    for i, text in enumerate(['1. Upload file', '2. Create submission', '3. Check integrity', 
                                   '4. Check plausibility', 'View activity']):
        view.tabs.set_title(i, text)

    # Show app
    header = HBox([app_title, logo])
    header.layout.justify_content = 'space-between'
    display(VBox([header, view.tabs]))
    logger.info('UI build completed')

    if show_log:
        # Duplicate log lines in log widget (they always show in Jupyter Lab log)
        display(log_handler.log_output_widget)


def section(title, contents, desc=None):
    '''Create collapsible container with title, optional desc.'''
    if desc is not None:
        contents = [HTML(value=desc)] + contents

    ret = Accordion(children=tuple([VBox(contents)]))
    ret.set_title(0, title)
    ret.selected_index = 0
    return ret

def set_width(widgets, width='auto', desc=False):
    """Set width for widgets' layouts or descriptions."""
    for widget in widgets:
    
        if desc:
            widget.style.description_width = width
        else:
            widget.layout = Layout(width=width)

def upload_tab():
    '''Create widgets for upload tab content.'''
    content = []
    view.uploader = ipyuploads.Upload(accept='*', multiple=False, all_files_complete=ctrl.when_upload_completed)
    view.file_info = Label(layout=Layout(margin='0 0 0 50px'))
    content.append(section('a) Select file for upload', [HBox([view.uploader, view.file_info])]))
    view.project = Select(options=[(prj.name, prj) for prj in ctrl.user_projects], value=None, disabled=False)  
    content.append(section('b) Select project', [view.project]))
    return VBox(content)

def submission_tab():
    '''Create widgets for data tab content.'''

    # Upload parsing options
    view.skip_txt = BoundedIntText(description='Num. lines to skip', min=0)
    view.delim_ddn = Dropdown(description='Delimiter', options=[('Comma (,)',','), ('Tab (\t)','\t'), ('Semicolon (;)',';'),
                                                                ('Pipe (|)','|'), ('Space ( )',' '), ("Single Quote (')","'"), 
                                                                ('Double Quote (")','"'), ('Tilde (~)','~'), ('Colon (:)',':')])
    view.header_ddn = Dropdown(description='Has header row?', options=[('Yes', True), ('No', False)])
    view.scen_ignore_txt = Text(
        description='Ignore scenarios',
        placeholder="(Optional) Enter comma-separated scenario values",
        layout=Layout(width='50%'))
    widgets = [view.skip_txt, view.delim_ddn, view.header_ddn, view.scen_ignore_txt]
    set_width(widgets, width='110px', desc=True)
        
    # Input preview "grid"
    labels = [Label(layout=Layout(border='1px solid lightgray', padding='0px', margin='0px')) for _ in range(24)]
    view.inp_grid = GridBox(children=labels, layout=Layout(grid_template_columns='repeat(8, 1fr)', grid_gap='0px'))

    content = [section('a) Adjust upload parsing options', widgets + [Label('Sample of parsed data:'), view.inp_grid])]

    # Assign model (incl. spacer)
    view.model_ddn = Dropdown()
    cols = [Label(value=COLS[0])]
    widgets = [view.model_ddn]

    # Assign columns
    view.scen_col_ddn, view.reg_col_ddn, view.var_col_ddn = Dropdown(), Dropdown(), Dropdown()
    view.item_col_ddn, view.unit_col_ddn, view.year_col_ddn, view.val_col_ddn = Dropdown(), Dropdown(), Dropdown(), Dropdown()
    cols += [Label(value=col) for col in COLS[1:]]
    widgets += [view.scen_col_ddn, view.reg_col_ddn, view.var_col_ddn,
               view.item_col_ddn, view.unit_col_ddn, view.year_col_ddn,view.val_col_ddn]
    set_width(cols, '140px')
    set_width(widgets, '140px')

    cols.insert(1, Label(layout=Layout(width='50px')))
    widgets.insert(1, Label(layout=Layout(width='50px')))
    
    # Output preview "grid"
    labels = [Label(layout=Layout(border='1px solid lightgray', padding='0px', margin='0px')) for _ in range(3*8)]
    view.out_grid = GridBox(children=labels, layout=Layout(grid_template_columns='repeat(8, 1fr)', grid_gap='0px'))

    content += [section('b) Assign model and columns for submission', 
                        [VBox([HBox(cols), HBox(widgets), Label('Submission preview:'), view.out_grid])])]

    return VBox(content)

def integrity_tab():
    "Create widgets for integrity tab content."

    # Analysis
    view.struct_probs_int = Text(description='Structural problems (e.g. missing fields)', disabled=True)
    view.ignored_scens_int = Text(description='Ignored scenarios', disabled=True)
    view.dupes_int = Text(description='Duplicate records', disabled=True)
    view.accepted_int = Text(description='Accepted records', disabled=True)
    widgets = [view.struct_probs_int, view.ignored_scens_int, view.dupes_int, view.accepted_int]
    set_width(widgets, '460px')
    set_width(widgets, '300px',  desc=True)
    content =[section('a) Review analysis', widgets, 'Classifications and row counts:')]

    # Bad labels
    view.bad_lbls_out = Output()
    content += [section('b) Review bad labels', [view.bad_lbls_out], 'Non-standard labels that will be fixed automatically: ')]
    
    # Unknonw labels
    view.unknown_lbls_out = Output()    
    content += [section('c) Address unknow labels', [view.unknown_lbls_out],
                        'NOTE: Records with labels left as-is will be DELETED. \
                         (Fixed labels will be updated. Overriden labels place submission in "pending" status.)')]    
    
    return VBox(content)

def plausibility_tab():
    "Create widgets for plausibility tab content."
    view.plot_scen_ddn = Dropdown(description='Scenario')
    view.plot_reg_ddn = Dropdown(description='Region')
    view.plot_var_ddn = Dropdown(description='Variable')
    widgets = [view.plot_scen_ddn, view.plot_reg_ddn, view.plot_var_ddn]
    set_width(widgets, '200px')
    set_width(widgets, '75px', desc=True)
    view.plot_type_rb = ToggleButtons(options=['Value trends', 'Growth trends'],
                                     layout=Layout(margin='0 0 0 100px'))
    widgets.append(view.plot_type_rb)
    view.plot_area = Output()
    return(section('a) Review plots', [VBox([HBox(widgets), view.plot_area])], 'Visualize uploaded data to verify its plausibility.'))

def activity_tab():
    "Create widgets for activity tab content."
    view.activity_out = Output()
    return(section('Review Submissions', [view.activity_out]))
