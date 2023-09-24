# view.py - User interface for app
# rcampbel@purdue.edu - 2020-07-14

import sys
import ipywidgets as widgets
from IPython.display import HTML, display, clear_output

from nb.log import logger, log_handler


"""Store app-wide constants, including values and language text."""

# NOTE Simple language string definiitions below: for better features, consider using the following:
# - Multilingual internationalization: https://docs.python.org/2/library/gettext.html
# - Data classes: https://docs.python.org/3/library/dataclasses.html
# - Bound attributes: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch05s16.html

# General
APP_TITLE = 'AgMIP GlobalEcon Data Submission'
CSS_JS_HTML = 'nb/custom.html'
LOGO_IMAGE = 'nb/logo.png'
ALL = 'All'
EMPTY = ''
NO_DATA_MSG = '''<br>(There's no data to display.)'''
TAB_TITLES = ['1. Upload File', '2. Specify Data', '3. Check Integrity', '4. Check Plausibility', 'View Activity']
PLOT_TITLE = 'Land-Ocean Temperature Index'
COLS = ['Model', 'Scenario', 'Region', 'Variable', 'Item', 'Unit', 'Year', 'Value']

# Data tab
PREVIEW_SECTION_TITLE = 'Data'
EXPORT_LINK_PROMPT = "Click here to save file: "

# Selection tab
CRITERIA_TITLE = 'Selection Criteria'
CRITERIA_APPLY = 'Select'
OUTPUT_TITLE = 'Results'
OUTPUT_PRE = 'Limit to '
OUTPUT_POST = 'lines'
EXPORT_TITLE = 'Export'
EXPORT_BUTTON = 'Create Download Link'
START_YEAR = 'From Year'
END_YEAR = 'To Year'

# Visualize tab
NOTE_TITLE = 'Note'
NOTE_TEXT = 'The plot is based on results from the Selection tab.'
PLOT_TITLE = 'Plot'
PLOT_LABEL = 'Select data field'

# Setting tab
PLOT_SETTINGS_SECTION_TITLE = 'Plot Settings'
THEME = 'Theme'
THEMES = ['onedork', 'grade3', 'oceans16', 'chesterish', 'monokai', 'solarizedl', 'solarizedd']
CONTEXT = 'Context'
CONTEXTS = ['paper', 'notebook', 'talk', 'poster']
FONT_SCALE = 'Font Scale'
SPINES = 'Spines'
GRIDLINES = 'Gridlines'
TICKS = 'Ticks'
GRID = 'Grid'
FIG_WIDTH = 'Width'
FIG_HEIGHT = 'Height'
APPLY = 'Apply'

LO10 = widgets.Layout(width='10%')
LO15 = widgets.Layout(width='15%')
LO20 = widgets.Layout(width='20%')

view = sys.modules[__name__]

# The view's "public" attributes are listed here, with type hints, for quick reference

# Filer ("Selection" tab) controls
select_txt_startyr: widgets.Text
select_txt_endyr: widgets.Text
select_btn_apply: widgets.Button
select_ddn_ndisp: widgets.Dropdown
select_output: widgets.Output
select_btn_refexp: widgets.Button
select_out_export: widgets.Output

# Plot ("Visualize" tab) controls
plot_ddn: widgets.Dropdown
plot_output: widgets.Output

# Settings controls
theme: widgets.Dropdown
context: widgets.Dropdown
fscale: widgets.FloatSlider
spines: widgets.Checkbox
gridlines: widgets.Text
ticks: widgets.Checkbox
grid: widgets.Checkbox
figsize1: widgets.FloatSlider
figsize2: widgets.FloatSlider
apply: widgets.Button


def start(show_log):
    """Build the user interface."""

    # Send app's custom styles (CSS code) down to the browser
    display(HTML(filename=CSS_JS_HTML))

    # Create large title for app
    app_title = widgets.HTML(APP_TITLE)
    app_title.add_class('app_title')  # Example of custom widget style via CSS, see custom.html

    # Create app logo - example of using exposed layout properties
    with open(LOGO_IMAGE, "rb") as logo_file:
        logo = widgets.Image(value=logo_file.read(), format='png', layout={'max_height': '32px'})

    # Create tabs and fill with UI content (widgets)

    tabs = widgets.Tab()

    # Build conent (widgets) for each tab
    tab_content = []
    tab_content.append(view.build_upload_tab())
    tab_content.append(view.build_data_tab())
    tab_content.append(view.build_selection_tab())
    tab_content.append(view.build_visualize_tab())
    tab_content.append(view.build_settings_tab())

    tabs.children = tuple(tab_content)  # Fill tabs with content

    # Add title text for each tab
    for i, tab_title in enumerate(TAB_TITLES):
        tabs.set_title(i, tab_title)

    # Show the app
    header = widgets.HBox([app_title, logo])
    header.layout.justify_content = 'space-between'  # Example of custom widget layout
    display(widgets.VBox([header, tabs]))
    logger.info('UI build completed')

    # Optionally, display a widget that shows the log items
    # Log items always appear in Jupyter Lab's log.
    # However, this addl. log widget is useful in some contexts (e.g. HUBzero tools)
    if show_log:
        display(log_handler.log_output_widget)


def new_section(title, contents):
    '''Utility method that create a collapsible widget container'''

    if type(contents) == str:
        contents = [widgets.HTML(value=contents)]

    ret = widgets.Accordion(children=tuple([widgets.VBox(contents)]))
    ret.set_title(0, title)
    ret.selected_index = 0
    return ret


def build_upload_tab():
    '''Create widgets for upload tab content.'''
    content = []
    # See https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20List.html#file-upload
    view.uploader = widgets.FileUpload()
    view.project = widgets.Select(options=['Linux', 'Windows', 'macOS'], disabled=False)  # TODO poopulate projects./,mn
    content.append(view.new_section('a) Upload a file', [view.uploader]))
    content.append(view.new_section('b) Select a project', [view.project]))
    return widgets.VBox(content)

def desc_width_auto(widget_list):
    for widget in widget_list:
        widget.style.description_width = 'auto'

def set_width(widget_list, pixels):
    for widget in widget_list:
        widget.layout = widgets.Layout(width=f"{pixels}px")

def build_data_tab():
    '''Create widgets for data tab content.'''
    content = []

    # Specify...
    view.model_ddn = widgets.Dropdown(description='Model')
    view.header_ckb = widgets.Checkbox(description='Header row')
    view.skip_txt = widgets.IntText(description='Num. lines to skip')
    view.delim_ddn = widgets.Dropdown(description='Delimiter')
    view.scen_ignore_txt = widgets.Textarea(
        description='Ignore scenarios',
        placeholder="(Optional) Enter comma-separated scenario values"
    )
    widget_list = [view.model_ddn, view.header_ckb, view.skip_txt, view.delim_ddn, view.scen_ignore_txt]
    view.desc_width_auto(widget_list)
    content.append(view.new_section('Assign columns from input data to output data', widget_list))
    
    # Assign...
    cols = [widgets.Label(value=col) for col in COLS]
    view.set_width(cols, pixels=140)
    view.model_lbl = widgets.Label(value='TODO')
    view.scen_col_ddn = widgets.Dropdown()
    view.reg_col_ddn = widgets.Dropdown()
    view.var_col_ddn = widgets.Dropdown()
    view.item_col_ddn = widgets.Dropdown()
    view.unit_col_ddn = widgets.Dropdown()
    view.year_col_ddn = widgets.Dropdown()
    view.val_col_ddn = widgets.Dropdown()
    widget_list = [view.model_lbl, view.scen_col_ddn, view.reg_col_ddn, view.var_col_ddn,
                   view.item_col_ddn, view.unit_col_ddn, view.year_col_ddn,view.val_col_ddn]
    view.set_width(widget_list, pixels=140)
    content.append(view.new_section('Assign columns from input data to output data', [widgets.VBox([widgets.HBox(cols), 
                                                                                                   widgets.HBox(widget_list)])]))
    
    # Input preview
    labels = [widgets.Label(value='TODO', layout=widgets.Layout(border='1px solid', padding='0px', margin='0px')) for _ in range(24)]
    view.input_preview_grid = widgets.GridBox(children=labels, layout=widgets.Layout(grid_template_columns='repeat(8, 1fr)', grid_gap='0px'))
    content.append(view.new_section('Input preview', [view.input_preview_grid]))

    # Output preview
    labels = [widgets.Label(value='TODO', layout=widgets.Layout(border='1px solid', padding='0px', margin='0px')) for _ in range(24)]
    view.output_preview_grid = widgets.GridBox(children=labels, layout=widgets.Layout(grid_template_columns='repeat(8, 1fr)', grid_gap='0px'))
    content.append(view.new_section('Output preview', [view.output_preview_grid]))

    return widgets.VBox(content)

def build_selection_tab():
    '''Create widgets for selection tab content'''
    view.select_txt_startyr = widgets.Text(description=START_YEAR, value='', placeholder='')
    view.select_txt_endyr = widgets.Text(description=END_YEAR, value='', placeholder='')
    view.select_btn_apply = widgets.Button(description=CRITERIA_APPLY, icon='select', layout=view.LO20)
    view.select_ddn_ndisp = widgets.Dropdown(options=['25', '50', '100', ALL], layout=view.LO10)
    view.select_output = widgets.Output()
    view.select_btn_refexp = widgets.Button(description=EXPORT_BUTTON, icon='download',
                                            layout=view.LO20)
    view.select_out_export = widgets.Output(layout={'border': '1px solid black'})
    content = []

    # Section: Selection criteria
    section_list = []
    section_list.append(view.select_txt_startyr)
    section_list.append(view.select_txt_endyr)
    section_list.append(view.select_btn_apply)
    content.append(view.new_section(CRITERIA_TITLE, section_list))

    # Section: Output (with apply button)
    section_list = []
    row = []
    row.append(widgets.HTML('<div style="text-align: right;">'+OUTPUT_PRE+'</div>', layout=view.LO15))
    row.append(view.select_ddn_ndisp)
    row.append(widgets.HTML('<div style="text-align: left;">' + OUTPUT_POST + '</div>', layout=view.LO10))
    section_list.append(widgets.HBox(row))
    section_list.append(widgets.HBox([view.select_output]))  # NOTE Use "layout={'width': '90vw'}" to widen
    content.append(view.new_section(OUTPUT_TITLE, section_list))

    # Section: Export (download)
    section_list = []
    section_list.append(widgets.VBox([view.select_btn_refexp, view.select_out_export]))
    content.append(view.new_section(EXPORT_TITLE, section_list))

    return widgets.VBox(content)


def build_visualize_tab():
    '''Create widgets for visualize tab content'''
    content = []
    content.append(view.new_section(NOTE_TITLE, NOTE_TEXT))
    view.plot_ddn = widgets.Dropdown(options=[EMPTY], value=None, disabled=True)
    view.plot_output = widgets.Output()
    section_list = []

    row = []
    row.append(widgets.HTML(value=PLOT_LABEL))
    row.append(widgets.Label(value='', layout=widgets.Layout(width='60%')))  # Cheat: spacer
    section_list.append(widgets.HBox(row))
    section_list.append(view.plot_ddn)
    section_list.append(view.plot_output)
    content.append(view.new_section(PLOT_TITLE, section_list))

    return widgets.VBox(content)


def build_settings_tab():
    """Create widgets for settings tab."""
    view.theme = widgets.Dropdown(description=THEME, options=THEMES)
    view.context = widgets.Dropdown(description=CONTEXT, options=CONTEXTS)
    view.fscale = widgets.FloatSlider(description=FONT_SCALE, value=1.4)
    view.spines = widgets.Checkbox(description=SPINES, value=False)
    view.gridlines = widgets.Text(description=GRIDLINES, value='--')
    view.ticks = widgets.Checkbox(description=TICKS, value=True)
    view.grid = widgets.Checkbox(description=GRID, value=False)
    view.figsize1 = widgets.FloatSlider(description=FIG_WIDTH, value=6)
    view.figsize2 = widgets.FloatSlider(description=FIG_HEIGHT, value=4.5)
    view.apply = widgets.Button(description=APPLY)

    return(view.new_section(PLOT_SETTINGS_SECTION_TITLE,
                            [view.theme, view.context, view.fscale, view.spines, view.gridlines,
                             view.ticks, view.grid, view.figsize1, view.figsize2, view.apply]))


def set_no_data():
    """Indicate there are no results."""
    # NOTE While the other view methods build the UI, this one acts an example of a helper method

    with view.select_output:
        clear_output(wait=True)
        display(widgets.HTML(NO_DATA_MSG))
