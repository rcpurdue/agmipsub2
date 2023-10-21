# controller.py - App logic, rcampbel@purdue.edu, Oct 2023
import logging
import os
import sys
import traceback
from fuzzywuzzy import fuzz, process
from nb import model, view
from nb.config import cfg, SCN, REG, VAR, HDR, DEL, OVR, UPLOAD, SUBMISSION, \
                      INTEGRITY, PLAUSIBILITY, FINISH, NUM_PREVIEW_ROWS, COL_DDN_WIDTH 
from nb.log import log, log_handler

ctrl = sys.modules[__name__]

def start(debug=False):
    """Begin running the app."""
    try:
        if debug:
            log_handler.setLevel(logging.DEBUG)
            log.setLevel(logging.DEBUG)

        # Find user's projects

        ctrl.user_projects = []

        for user_group in os.popen('groups').read().strip('\n').split(' '):

            for project in cfg.all_projects:

                if user_group == project.group:
                    ctrl.user_projects.append(project)

        # Build UI & data access objects
        model.start()
        view.start(debug, when_upload_completed, ctrl.user_projects)
        
        # Keep lists of some UI widgets 
        ctrl.col_ddns = [view.scen_col_ddn, view.reg_col_ddn, view.var_col_ddn, view.item_col_ddn,
                        view.unit_col_ddn, view.year_col_ddn, view.val_col_ddn]
        ctrl.plot_ddns = [view.plot_scen_ddn, view.plot_reg_ddn, view.plot_var_ddn]

        # Setup callbacks NOTE uploader's callback set by view
        view.stack.observe(when_stack_changes, 'selected_index' , 'change')  # Tabs
        view.project.observe(ctrl.when_project_selected, 'value')  # Upload
        view.skip_txt.observe(ctrl.when_reload, 'value')  # Submission...
        view.delim_ddn.observe(ctrl.when_reload, 'value')
        view.header_ddn.observe(ctrl.when_reload, 'value')
        view.scen_ignore_txt.observe(ctrl.when_reload, 'value')
        view.model_ddn.observe(ctrl.when_refresh_preview, 'value')
        ctrl.observe_activate(True, ctrl.col_ddns, ctrl.when_refresh_preview)
        ctrl.observe_activate(True, ctrl.plot_ddns, ctrl.when_plot)  # Plausibility
        view.next.on_click(when_next)

        log.info('App running')
    except Exception:
        log.error('start:\n'+traceback.format_exc())
        raise

def when_next(_=None):
    """React to user pressing Next button."""

    if view.stack.selected_index < len(view.steps)-1:
        view.stack.selected_index += 1
        view.progress.value = view.stack.selected_index
        view.progress.description = view.steps[view.stack.selected_index]

def when_stack_changes(change):
    """React to user selecting new tab."""
    try:

        if change['new'] == view.steps.index(UPLOAD):
            pass

        if change['new'] == view.steps.index(SUBMISSION) and model.df is not None:
            refresh_upload_sample()
            init_assign_columns()
            when_refresh_preview()
        
        elif change['new'] == view.steps.index(INTEGRITY) and model.df is not None:
            model.set_columns({i+1:ddn.value for i, ddn in enumerate(ctrl.col_ddns)})  # +1 to skip model   
            model.analyze()  

            # Display analysis results

            # Row counts
            view.struct_probs_int.value = str(model.num_rows_with_nan )
            view.ignored_scens_int.value = str(model.num_rows_ignored_scens)
            view.dupes_int.value = str(model.duplicate_rows)
            view.accepted_int.value = str(model.num_rows_read - model.num_rows_with_nan - 
                                          model.num_rows_ignored_scens - model.duplicate_rows )

            # Bad labels

            bad_grid_widgets = [view.title('Column'), view.title('Label'), view.title('Fix (applied automatically)')] 

            for col, lbl, fix in model.bad_labels:
                bad_grid_widgets += [view.cell(col), view.cell(lbl), view.cell(fix)]

            view.bad_grid.children = bad_grid_widgets

            # Unknown labels

            unknown_grid_widgets = [view.title('Column'), view.title('Label'), view.title('Fix (select from menu)')]

            for col, lbl, match in model.unknown_labels:
                ddn = view.cell_ddn(DEL if match is None else match, [DEL, OVR] + model.get_valid(col))
                unknown_grid_widgets += [view.cell(col), view.cell(lbl), ddn]

            view.unknown_grid.children = unknown_grid_widgets 

        elif change['new'] == view.steps.index(PLAUSIBILITY) and model.df is not None:
            # Apply fixes TODO Remove records with struct problems

            widgets = view.bad_grid.children[3:] + view.unknown_grid.children[3:]  # 3: skips col headers 
            ctrl.pending = False

            for i in range(len(widgets)//3):   
                col, lbl, fix = widgets[i*3].value, widgets[i*3+1].value, widgets[i*3+2].value
                
                if fix == OVR:
                    ctrl.pending = True
                else:
                    model.fix(col, lbl, fix, fix==DEL)

            log.debug(f'AFTER FIX:\n{model.df}')                    

            # Refresh_plot_menus
            observe_activate(False, ctrl.plot_ddns, ctrl.when_plot)
            view.plot_scen_ddn.options = model.get_unique(SCN)
            view.plot_reg_ddn.options = model.get_unique(REG)
            view.plot_var_ddn.options = model.get_unique(VAR)
            view.plot_scen_ddn.index, view.plot_reg_ddn.index, view.plot_var_ddn.index = 0, 0, 0
            observe_activate(True, ctrl.plot_ddns, ctrl.when_plot)
            ctrl.when_plot()

        elif change['new'] == view.steps.index(FINISH) and model.df is not None:
            if ctrl.pending:
                view.submit_desc_lbl.value = f'New data for the "{view.model_ddn.value}" model will be submitted with status: PENDING REVIEW.' 
            else:
                view.submit_desc_lbl.value = f'New data for the "{view.model_ddn.value}" model will be submitted with status: ACCEPTED.' 
    
    except Exception:
        log.error('when_stack_changes, change={change}:\n'+traceback.format_exc())
        raise

def when_upload_completed(names=None):
    """React to user uploading file."""
    # NOTE Callback to this method registered in view
    try:
        model.set_file(names[0]["name"])
        view.file_info.value = f'Uploaded "{names[0]["name"]}", {names[0]["size"]} bytes'

        if model.detect_delim():
            view.delim_ddn.value = model.detected_delim
            model.read_file(delim=view.delim_ddn.value)
    
    except Exception:
        view.file_info.value = '(UPLOAD ERROR)'
        log.error('when_upload_completed:\n'+traceback.format_exc())

def when_project_selected(_=None):
    try:

        if view.project.value is not None:
            model.load_rules(view.project.value)  # Read rules file

            # Set model dropdown menu
            ctrl.observe_activate(False, ctrl.col_ddns, ctrl.when_refresh_preview)
            view.model_ddn.options = model.all_models()
            view.model_ddn.value = view.model_ddn.options[0]  # TODO Guess model 
            ctrl.observe_activate(True, ctrl.col_ddns, ctrl.when_refresh_preview)
        
    except Exception:
        log.error('when_project_selected:\n'+traceback.format_exc())
        raise

def when_reload(_=None):
    """Due to param change, ask model to relead data, relfect new data in view."""
    try:

        if model.path is not None:            
            model.read_file(delim=view.delim_ddn.value, skip=view.skip_txt.value, header=view.header_ddn.value,
                            ignore=[x.strip() for x in view.scen_ignore_txt.value.split(',')])
            refresh_upload_sample()
            init_assign_columns()
            when_refresh_preview()

    except Exception:
        # TODO set all cells to "ERROR"?
        log.error('when_reload:\n'+traceback.format_exc())

def refresh_upload_sample():
    """Populate upload sample widget w/data from preview data."""
    try:
        # Clear sample view widgets
        for i in range(NUM_PREVIEW_ROWS*len(HDR)):
            view.inp_grid.children[i].value = ''

        if model.preview_df is not None:
            num_data_rows = NUM_PREVIEW_ROWS  # Assume no header

            # Possible header row
            if model.has_header():
                num_data_rows = NUM_PREVIEW_ROWS - 1

                for i, header in enumerate(model.preview_df.columns[:len(HDR)]):
                    view.inp_grid.children[i].value = header
                    view.inp_grid.children[i].style.font_weight = 'bold'

            # Data rows
            for r, row in model.preview_df.head(num_data_rows).iterrows():

                for c, value in enumerate(row[:len(HDR)]):
                    view.inp_grid.children[(r+(NUM_PREVIEW_ROWS-num_data_rows))*len(HDR)+c].value = str(value)
                    view.inp_grid.children[(r+(NUM_PREVIEW_ROWS-num_data_rows))*len(HDR)+c].style.font_weight = 'normal'
        
    except Exception:
        log.error('when_upload_completed:\n'+traceback.format_exc())
        raise

def observe_activate(activate, widgets, callback):
    """Turn on/off value callbacks for widgets in given list."""
    for widget in widgets:
        
        if activate:
            widget.observe(callback, 'value')
        else:
            widget.unobserve(callback, 'value')

def init_assign_columns():
    """Set options and selected value of column mapping dropdown menus. """    
    
    if model.df is not None:
        options = [(str(widget.value), i) for i,widget in enumerate(view.inp_grid.children[0:len(HDR)])]
        text = [tup[0] for tup in options]
        ctrl.observe_activate(False, ctrl.col_ddns, ctrl.when_refresh_preview)
        
        for i, ddn in enumerate(ctrl.col_ddns):
            ddn.options = options 

            # Guess selected value  
            if model.has_header():
                # Hdr row: match col names 
                match = process.extractOne(HDR[i+1], text, scorer=fuzz.token_sort_ratio)  # i+1 to skip model

                if match is not None and len(match) > 0:
                    ddn.index = text.index(match[0])

            else:  # TODO Match cols based on rule file
                ddn.index = i+1

        view.set_width(ctrl.col_ddns, COL_DDN_WIDTH)
        ctrl.observe_activate(True, ctrl.col_ddns, ctrl.when_refresh_preview)

def when_refresh_preview(_=None):
    """Populate submission preview widgets w/data."""

    # Clear sample view widgets
    for i in range(NUM_PREVIEW_ROWS*len(HDR)):
        
        if i < len(HDR):
            view.out_grid.children[i].value = HDR[i]  
            view.out_grid.children[i].style.font_weight = 'bold'
        else:
            view.out_grid.children[i].value = ' '  

    if model.df is not None:

        # Data rows
        for r in range(1, NUM_PREVIEW_ROWS):  # 1 to skip header
            view.out_grid.children[r*len(HDR)+0].value = str(view.model_ddn.value)  # Model

            for c in range(len(HDR[1:])):  # +1 to skip model  
                view.out_grid.children[r*len(HDR)+c+1].value = str(model.df.iloc[r, c+1])  

def when_plot(_=None):
    """Display plot."""
    try:
        view.display_plot('Generating plot...')
        series = model.select(view.plot_scen_ddn.value, view.plot_reg_ddn.value, view.plot_var_ddn.value)
        view.display_plot(series)
    except Exception as e:
        view.display_plot(f'Plot error: "{e}"')
        log.error('when_plot:\n'+traceback.format_exc())

