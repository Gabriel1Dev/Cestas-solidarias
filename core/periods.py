"""All calendar calculations live here. End boundaries are exclusive."""
import calendar
from datetime import date
def add_months(day, count):
    month=day.month-1+count
    year=day.year+month//12
    month=month%12+1
    return date(year,month,min(day.day,calendar.monthrange(year,month)[1]))
def periods(start,mode):
    if mode not in ('calendar','anniversary'): raise ValueError('Contagem inválida.')
    anchor=start.replace(day=1) if mode=='calendar' else start
    return [(start if n==0 else add_months(anchor,n),add_months(anchor,n+1)) for n in range(6)]
