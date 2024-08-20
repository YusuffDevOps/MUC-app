import os
from typing import Optional

"""
Configuration options for running dependencies through "conda run -n".

If any of these environment variables are supplied, then the respective
program will be run through "conda run -n name".
"""
CONDA_BAKTA_NAME: Optional[str] = os.environ.get('CONDA_BAKTA_NAME')
CONDA_RGI_NAME: Optional[str] = os.environ.get('CONDA_RGI_NAME')
CONDA_EXE_NAME: Optional[str] = os.environ.get('CONDA_EXE_NAME', 'conda')
CONDA_BAKTA_DB: Optional[str] = os.environ.get('BAKTA_DB')
