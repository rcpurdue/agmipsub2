# controller.py - App logic, rcampbel@purdue.edu, Oct 2023
import logging
import os
import sys
import traceback
import difflib
from nb import model
from nb import view
from nb.config import cfg, SCN, REG, VAR, HDR, DEL, OVR, UPLOAD, SUBMISSION, INTEGRITY, PLAUSIBILITY, FINISH
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
        ctrl.col_map = [view.scen_col_ddn, view.reg_col_ddn, view.var_col_ddn, view.item_col_ddn,
                        view.unit_col_ddn, view.year_col_ddn, view.val_col_ddn]
        ctrl.plot_ddns = [view.plot_scen_ddn, view.plot_reg_ddn, view.plot_var_ddn]

        # Setup callbacks NOTE uploader's callback set by view
        view.tabs.observe(when_tab_changes, 'selected_index' , 'change')  # Tabs
        view.project.observe(ctrl.when_project_selected, 'value')  # Upload
        view.skip_txt.observe(ctrl.when_reload, 'value')  # Submission...
        view.delim_ddn.observe(ctrl.when_reload, 'value')
        view.header_ddn.observe(ctrl.when_reload, 'value')
        view.scen_ignore_txt.observe(ctrl.when_reload, 'value')
        view.model_ddn.observe(ctrl.when_refresh_preview, 'value')
        ctrl.observe_activate(True, ctrl.col_map, ctrl.when_refresh_preview)
        ctrl.observe_activate(True, ctrl.plot_ddns, ctrl.when_plot)  # Plausibility

        log.info('App running')
    except Exception:
        log.error('start:\n'+traceback.format_exc())
        raise

def when_tab_changes(change):
    """React to user selecting new tab."""
    try:

        if change['new'] == view.tab_ids[UPLOAD]:
            pass

        if change['new'] == view.tab_ids[SUBMISSION]:
            refresh_upload_sample()
            init_assign_columns()
        
        elif change['new'] == view.tab_ids[INTEGRITY]:
            model.set_columns({i+1:ddn.value for i, ddn in enumerate(ctrl.col_map)})  # +1 to skip model   
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

        elif change['new'] == view.tab_ids[PLAUSIBILITY]:
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

        elif change['new'] == view.tab_ids[FINISH]:
            if ctrl.pending:
                view.submit_desc_lbl.value = f'New data for the "{view.model_ddn.value}" model will be submitted with status: PENDING REVIEW.' 
            else:
                view.submit_desc_lbl.value = f'New data for the "{view.model_ddn.value}" model will be submitted with status: ACCEPTED.' 
    
    except Exception:
        log.error('when_tab_changes, change={change}:\n'+traceback.format_exc())
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
            ctrl.observe_activate(False, ctrl.col_map, ctrl.when_refresh_preview)
            view.model_ddn.options = model.all_models()
            view.model_ddn.value = view.model_ddn.options[0]
            ctrl.observe_activate(True, ctrl.col_map, ctrl.when_refresh_preview)
        
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

    except Exception:
        # TODO set all cells to "ERROR"?
        log.error('when_reload:\n'+traceback.format_exc())

def refresh_upload_sample():
    """Populate upload sample widget w/data from preview data."""
    try:
        # Clear sample view widgets
        for i in range(3*8):
            view.inp_grid.children[i].value = ''

        if model.preview_df is not None:
            num_data_rows = 3  # Assume no header

            # Possible header row
            if model.has_header():
                num_data_rows = 2

                for i, header in enumerate(model.preview_df.columns[:8]):
                    view.inp_grid.children[i].value = header
                    view.inp_grid.children[i].style.font_weight = 'bold'

            # Data rows
            for r, row in model.preview_df.head(num_data_rows).iterrows():

                for c, value in enumerate(row[:8]):
                    view.inp_grid.children[(r+(3-num_data_rows))*8+c].value = str(value)
                    view.inp_grid.children[(r+(3-num_data_rows))*8+c].style.font_weight = 'normal'
        
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

    if model.df is not None:
        # Col mapping dropdowns
        options = [(str(widget.value), i) for i,widget in enumerate(view.inp_grid.children[0:8])]
        text = [tup[0] for tup in options]
        
        for i, ddn in enumerate(ctrl.col_map):
            ddn.options = options 

            # Guess selected value TODO Also guess model 

            ctrl.observe_activate(False, ctrl.col_map, ctrl.when_refresh_preview)

            if model.has_header():
                # Hdr row: match col names 
                match = difflib.get_close_matches(HDR[i+1], text, n=1, cutoff=0.9)  # i+1 to skip model 

                if match is not None and len(match) > 0:
                    ddn.index = text.index(match[0])
            else:
                # No hdr row: match value from rules
                pass  # TODO match cols based on rule file

            ctrl.observe_activate(True, ctrl.col_map, ctrl.when_refresh_preview)

        when_refresh_preview()

def when_refresh_preview(_=None):
    """Populate submission preview widgets w/data."""

    # Clear sample view widgets
    for i in range(3*8):
        
        if i < 8:
            view.out_grid.children[i].value = HDR[i]  
            view.out_grid.children[i].style.font_weight = 'bold'
        else:
            view.out_grid.children[i].value = ' '  

    if model.df is not None:

        # Data rows
        for r in range(1,3):  # Skip header
            view.out_grid.children[r*8+0].value = str(view.model_ddn.value)

            for c in range(0,7):  # Size of col map

                mapped_col = ctrl.col_map[c].value    
                
                if mapped_col is not None and len(model.df.iloc[r].values) > mapped_col:
                    view.out_grid.children[r*8+c+1].value = str(model.df.iloc[r, mapped_col])  # +1 to accnt for model  

def when_plot(_=None):
    """Display plot."""
    try:
        series = model.select(view.plot_scen_ddn.value, view.plot_reg_ddn.value, view.plot_var_ddn.value)
        view.display_plot(series)
    except Exception as e:
        view.display_plot(None, f'(Plot error: "{e}")')
        log.error('when_plot:\n'+traceback.format_exc())

