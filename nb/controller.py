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

def when_upload_copleted(names=None):
    """React to user uploading file."""
    try:
        logger.debug(f'Upload: {names}')
        view.file_info.value = f'Uploaded "{names[0]["name"]}", {names[0]["size"]} bytes'    
        model.read_file(names[0]["name"])
    except Exception as e:
        logger.debug('Exception during upload...\n'+traceback.format_exc())
        view.file_info.value = f'ERROR: "{traceback.format_exception_only(type(e), e)[-1].split(":")[1]}"'    
