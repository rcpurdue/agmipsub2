# controller.py - Central logic for app
# rcampbel@purdue.edu - 2020-07-14
import logging
import sys
import traceback
from nb import model
from nb import view
from nb.log import logger, log_handler

ctrl = sys.modules[__name__]

def start(debug=False):
    """Begin running the app."""

    if debug:
        log_handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    model.start()  
    view.start(debug)  

    # Setup callbacks NOTE uploader's callback set by view
    try:
        view.skip_txt.observe(ctrl.reload, 'value')
        view.delim_ddn.observe(ctrl.reload, 'value')
        view.header_ddn.observe(ctrl.reload, 'value')
        view.scen_ignore_txt.observe(ctrl.reload, 'value')
        logger.info('App running')
    except Exception:
        logger.debug('Exception while setting up callbacks...\n'+traceback.format_exc())
        raise

def when_upload_completed(names=None):
    """React to user uploading file."""
    logger.debug(f'Upload: {names}')

    if model.set_file(names[0]["name"]):
        view.file_info.value = f'Uploaded "{names[0]["name"]}", {names[0]["size"]} bytes'    
        
        if model.detect_delim():
            view.delim_ddn.value = model.detected_delim
            model.read_file(delim=view.delim_ddn.value)
            refresh_upload_sample()
    else:
        view.file_info.value = f'(UPLOAD ERROR)'    

def reload(_):
    """Due to param change, ask model to relead data, relfect new data in view."""
    if model.path is not None:
        model.read_file(delim=view.delim_ddn.value, skip=view.skip_txt.value, header=view.header_ddn.value, 
                        ignore=[x.strip() for x in view.scen_ignore_txt.value.split(',')])
        refresh_upload_sample()

def refresh_upload_sample():
    """Populate upload sample widget w/ data."""
    num_data_rows = 3

    # Empty data
    if model.df is None:

        for i in range(3*8):
            view.inp_grid.children[i].value = ' ?'        

    else:   
        # Header row
        if model.has_header():
            num_data_rows = 2

            for i, header in enumerate(model.df.columns):
                view.inp_grid.children[i].value = header
                view.inp_grid.children[i].style.font_weight = 'bold'                

                if i == 7:
                    break
        
        # Data rows
        for r, row in model.df.head(num_data_rows).iterrows():
            
            for c, value in enumerate(row):
                view.inp_grid.children[(r+(3-num_data_rows))*8+c].value = str(value)        
                view.inp_grid.children[(r+(3-num_data_rows))*8+c].style.font_weight = 'normal'

                if c == 7:
                    break
    

