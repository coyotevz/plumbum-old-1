# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime


# date/time utilities
if os.name == 'nt':
    raise NotImplementedError("Not yet implemented for this platform")
else:
    time_now, datetime_now = time.time, datetime.now
