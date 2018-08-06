from datetime import datetime

# class DateHelper:
#     date_pattern = re.compile('\[?(\d{4}[-/]\d{2}[-/]\d{2})?T?\s*((?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(?:[,.]+(?P<microsecond>\d{3}(?:\d{3})?))?)(\s*\+\d{4})?Z?\]?\s*')

#     # Does the message contains a date ?
#     @staticmethod
#     def has_date(message):
#         matches = DateHelper.date_pattern.search( message )
#         return False if matches is None else True

#     # Extract date from message
#     @staticmethod
#     def parse_date(message):
#         date = datetime.today()
#         matches = DateHelper.date_pattern.search( message )
#         if matches is not None:
#             date.replace(hour=int(matches.group('hour')))\
#                 .replace(minute=int(matches.group('minute')))\
#                 .replace(second=int(matches.group('second')))
#             if matches.group('microsecond'):
#                 date = date.replace(microsecond=int(matches.group('microsecond'))*1000 if len(matches.group('microsecond')) == 3 else int(matches.group('microsecond')))
        
#         return date.strftime("%Y-%m-%dT%H:%M:%S.%f%Z")

#     # Delete date from message
#     @staticmethod
#     def clean_date(message):
#         return DateHelper.date_pattern.sub("", message)

DATE_HELPER_PATTERN = re.compile('\[?(\d{4}[-/]\d{2}[-/]\d{2})?T?\s*((?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(?:[,.]+(?P<microsecond>\d{3}(?:\d{3})?))?)(\s*\+\d{4})?Z?\]?\s*')

# Does the message contains a date ?
def has_date(message):
    matches = DATE_HELPER_PATTERN.search( message )
    return False if matches is None else True

# Extract date from message
def parse_date(message):
    date = datetime.today()
    matches = DATE_HELPER_PATTERN.search( message )
    if matches is not None:
        date.replace(hour=int(matches.group('hour')))\
            .replace(minute=int(matches.group('minute')))\
            .replace(second=int(matches.group('second')))
        if matches.group('microsecond'):
            date = date.replace(microsecond=int(matches.group('microsecond'))*1000 if len(matches.group('microsecond')) == 3 else int(matches.group('microsecond')))
    
    return date.strftime("%Y-%m-%dT%H:%M:%S.%f%Z")

# Delete date from message
def clean_date(message):
    return DATE_HELPER_PATTERN.sub("", message)