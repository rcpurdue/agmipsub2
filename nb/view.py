# view.py - User interface, rcampbel@purdue.edu, Oct 2023
import sys
from IPython.display import display
from ipywidgets import Accordion,  Dropdown, GridBox, HBox, BoundedIntText, Label, \
                       Layout, Output, HTML, Image, Select, Tab, Text, VBox, Button 
import ipyuploads
import matplotlib.pyplot as plt
from IPython.core.display import clear_output
from nb.log import log, log_handler
from nb.config import MOD, YRS, VAL, HDR, OVR, UPLOAD, SUBMISSION, INTEGRITY, PLAUSIBILITY, FINISH, NUM_PREVIEW_ROWS

view = sys.modules[__name__]

def start(show_log, when_upload_completed, user_projects):
    """Build the user interface."""
    display(HTML(filename='nb/custom.html'))  # Send CSS code down to browser    
    app_title = HTML('AgMIP GlobalEcon Data Submission')
    app_title.add_class('app_title') 

    with open('nb/logo.png', "rb") as logo_file:
        logo = Image(value=logo_file.read(), format='png', layout={'max_height': '32px'})

    # Create tabs - NOTE Maintain corresponding order of IDs & children! 
    view.tab_ids = {UPLOAD:0, SUBMISSION:1, INTEGRITY:2, PLAUSIBILITY:3, FINISH:4}
    view.tabs = Tab(children=[upload_tab(when_upload_completed, user_projects), submission_tab(), 
                              integrity_tab(), plausibility_tab(), submit_tab()],
                    titles=[f'{view.tab_ids[title]+1}. {title}' for title in view.tab_ids])
    
    header = HBox([app_title, logo])
    header.layout.justify_content = 'space-between'
    display(VBox([header, view.tabs]))  # Show app
    log.info('UI build completed')

    if show_log:  # Duplicate log lines in log widget (will always show in Jupyter Lab log)
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

def upload_tab(when_upload_completed, user_projects):
    '''Create widgets for upload tab content.'''
    content = []
    view.uploader = ipyuploads.Upload(accept='*', multiple=False, all_files_complete=when_upload_completed)
    view.file_info = Label(layout=Layout(margin='0 0 0 50px'))
    content.append(section('a) Select file for upload', [HBox([view.uploader, view.file_info])]))
    view.project = Select(options=[(prj.name, prj) for prj in user_projects], value=None, disabled=False)  
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
    view.inp_grid = GridBox(children=labels, layout=Layout(grid_template_columns=f'repeat({len(HDR)}, 1fr)', grid_gap='0px'))

    content = [section('a) Adjust upload parsing options', widgets + [Label('Sample of parsed data:'), view.inp_grid])]

    # Assign model (incl. spacer)
    view.model_ddn = Dropdown()
    cols = [Label(value=MOD)]
    widgets = [view.model_ddn]

    # Assign columns
    view.scen_col_ddn, view.reg_col_ddn, view.var_col_ddn = Dropdown(), Dropdown(), Dropdown()
    view.item_col_ddn, view.unit_col_ddn, view.year_col_ddn, view.val_col_ddn = Dropdown(), Dropdown(), Dropdown(), Dropdown()
    cols += [Label(value=col) for col in HDR[1:]]
    widgets += [view.scen_col_ddn, view.reg_col_ddn, view.var_col_ddn,
               view.item_col_ddn, view.unit_col_ddn, view.year_col_ddn,view.val_col_ddn]
    set_width(cols, '140px')
    set_width(widgets, '140px')

    cols.insert(1, Label(layout=Layout(width='50px')))
    widgets.insert(1, Label(layout=Layout(width='50px')))
    
    # Output preview "grid"
    labels = [Label(layout=Layout(border='1px solid lightgray', padding='0px', margin='0px')) for _ in range(NUM_PREVIEW_ROWS*len(HDR))]
    view.out_grid = GridBox(children=labels, layout=Layout(grid_template_columns=f'repeat({len(HDR)}, 1fr)', grid_gap='0px'))

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
    content = [section('a) Review analysis', widgets, 'Classifications and row counts:')]

    # Bad labels
    view.bad_grid = GridBox(children=[], layout=Layout(grid_template_columns='repeat(3, 200px)', grid_gap='0px'))
    content += [section('b) Review bad labels', [view.bad_grid], 'Non-standard labels with known repalcement values: ')]
    
    # Unknonw labels
    view.unknown_grid = GridBox(children=[], layout=Layout(grid_template_columns='repeat(3, 200px)', grid_gap='0px'))  
    content += [section('c) Address unknown labels', [view.unknown_grid],
                        f"""Non-standrads labels with no known replacement values:\n
                            NOTE: Selecting "{OVR}" causes submission to be reviewed before acceptance.)""")]    
    
    return VBox(content)

def plausibility_tab():
    "Create widgets for plausibility tab content."
    view.plot_scen_ddn = Dropdown(description='Scenario')
    view.plot_reg_ddn = Dropdown(description='Region')
    view.plot_var_ddn = Dropdown(description='Variable')
    widgets = [view.plot_scen_ddn, view.plot_reg_ddn, view.plot_var_ddn]  
    set_width(widgets, '400px')
    set_width(widgets, '75px', desc=True)
    view.plot_area = Output(layout=Layout(border='1px solid lightgray', padding='2px', margin='30px'))
    return(section('a) Review plots', [VBox([HBox(widgets), view.plot_area])], 'Visualize processed data to verify plausibility.'))

def submit_tab():
    "Create widgets for submit data tab content."
    view.submit_desc_lbl = Label(value='-')
    view.submit_btn = Button(description='Submit')
    content = [section('a) Confirm submission', [VBox([view.submit_desc_lbl, view.submit_btn])], 'Press the button below to complete the submission process.')]
    view.activity_out = Output()
    content += [section('b) Review submission activity', [view.activity_out], 'Completed submissions are listed below.')]
    return VBox(content)

def cell(text):
    """Create label for use within grid."""
    return Label(value=text, layout=Layout(border='1px solid lightgray', padding='2px', margin='0px'))

def cell_ddn(selected, choices):
    """Create dropdown menu for use within grid."""
    return Dropdown(value=selected, options=choices, layout=Layout(border='1px solid lightgray', padding='2px', margin='0px'))

def title(text):
    """Create header text for use within grid."""
    return Label(value=text)

def display_plot(df, error=None):
    """Ask data to plot itself then show that plot."""
    with view.plot_area:
        clear_output(wait=True)

        if error is None:
            _, ax = plt.subplots()
            df.plot(title='Value Trends', xlabel=YRS, ylabel=VAL, legend=True, grid=True, figsize=(10, 5))
            ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5)) # Move legend outside plot area
            plt.show()
        else:
            display(Label(error))



