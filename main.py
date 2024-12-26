# -*- coding: utf-8 -*-
"""
Created on Wed Dec 25 23:32:40 2024

@author: replica
"""
import streamlit as st
import plotly.express as px
import requests
import time
from PIL import Image
from io import BytesIO
import numpy as np
import os.path

import streamlit.web.cli as stcli
import sys
import streamlit.runtime.scriptrunner.magic_funcs

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py", "--server.port=8523", "--global.developmentMode=false"]
    sys.exit(stcli.main())