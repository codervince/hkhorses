#utiltiies2
from fractions import Fraction
from datetime import date, time, datetime, timedelta
from dateutil.relativedelta import relativedelta
# from dateutil import tz
import re
import operator
import math

'''
yearofbirth
if NH -> 01/01
SH -> 08/01
'''

def getdateofbirth(referencedate, age, countryoforigin):
    d1 = referencedate - relativedelta(years=age)
    print(d1)
    if countryoforigin in ['AUS', 'NZ', 'RSA']:
        d2 = d1.replace(month=8, day=1)
    else:
        d2 = d1.replace(month=1, day=1)
    return d2.date()
