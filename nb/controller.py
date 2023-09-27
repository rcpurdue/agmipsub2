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

    # Setup callbacks
    try:
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
            view.delim_ddn.value = model.delim
            
            if model.read_file():
                refresh_upload_sample()
    else:
        view.file_info.value = f'(UPLOAD ERROR)'    

def refresh_upload_sample():
    """Populate upload sample widget w/ data."""
    data_rows = 3

    if model.has_header():
        data_rows = 2

        for i, header in enumerate(model.df.columns):
            view.inp_grid.children[i].value = header

            if i == 7:
                break

    for r, row in model.df.head(data_rows).iterrows():
        
        for c, value in enumerate(row):
            view.inp_grid.children[(r+(3-data_rows))*8+c].value = str(value)        

            if c == 7:
                break
    

