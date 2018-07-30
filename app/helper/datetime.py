from datetime import datetime

class DateHelper:
    @staticmethod
    def parse_date(self, message):
        date = datetime.today()
        matches = DockerHelper.date_pattern.search(message)
        if matches is not None:
            date.replace(hour=int(matches.group('hour')))\
                .replace(minute=int(matches.group('minute')))\
                .replace(second=int(matches.group('second')))
            if matches.group('microsecond'):
                date = date.replace(microsecond=int(matches.group('microsecond'))*1000 if len(matches.group('microsecond')) == 3 else int(matches.group('microsecond')))
        
        return date.strftime("%Y-%m-%dT%H:%M:%S.%f%Z")

    @staticmethod
    def clean_date(self, message):
        return DockerHelper.date_pattern.sub("", message)