"""All calendar calculations live here. End boundaries are exclusive."""
import calendar
from datetime import date
def add_months(day, count):
    month=day.month-1+count
    year=day.year+month//12
    month=month%12+1
    return date(year,month,min(day.day,calendar.monthrange(year,month)[1]))
def periods(start,mode,count=6):
    if mode not in ('calendar','anniversary'): raise ValueError('Contagem inválida.')
    anchor=start.replace(day=1) if mode=='calendar' else start
    return [(start if n==0 else add_months(anchor,n),add_months(anchor,n+1)) for n in range(count)]

def second_saturday(year,month):
    first=date(year,month,1)
    return date(year,month,1+(5-first.weekday())%7+7)

def distribution_periods(start, count):
    """Monthly service periods anchored to the next available second Saturday."""
    year,month=start.year,start.month
    appointment=second_saturday(year,month)
    if appointment < start:
        month += 1
        if month == 13: year,month=year+1,1
        appointment=second_saturday(year,month)
    dates=[appointment]
    for _ in range(count):
        month += 1
        if month == 13: year,month=year+1,1
        dates.append(second_saturday(year,month))
    return list(zip(dates[:-1],dates[1:]))
