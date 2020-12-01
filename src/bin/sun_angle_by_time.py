#!/usr/bin/env python

# Ranges from -80 to 80 from 08:00 to 18:00
# For example, 08:00 should be -80, and 16:30 should be 56.

import sys
import math

hours = int(sys.argv[1])
minutes = int(sys.argv[2])

total_minutes = (hours * 60 + minutes) - 780

print(int((total_minutes / 30) * 8))
