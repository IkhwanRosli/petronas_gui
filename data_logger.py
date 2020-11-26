import datetime
import time, random
import csv

class dataLogger():
    def __init__(self):
        self.file_number = 0
        self.line_count = 0
        date_time = str(datetime.datetime.now())
        self.name = date_time.replace(' ', '_')
        self.f = open("logs/{}_{}.csv".format(self.name, str(self.file_number).zfill(5)), "w")
        self.writer = csv.writer(self.f)
        self.prepare_csv_header()

    def prepare_csv_header(self, stop_signal=False):
        columnTitleRow = ['date', 'time']
        columnTitleRow = columnTitleRow + ['x_'+s for s in ['measurement', 'rssi', 'degree']]
        columnTitleRow = columnTitleRow + ['y_'+s for s in ['measurement', 'rssi', 'degree']]
        columnTitleRow = columnTitleRow + ['z_'+s for s in ['measurement', 'rssi', 'growth']]
        if not stop_signal:
            self.writer.writerow(columnTitleRow)
            self.f.flush()

    def check_new_file(self):
        if self.line_count >= 30000:
            self.f.close()
            self.file_number +=1
            self.line_count = 0
            self.f = open("logs/{}_{}.csv".format(self.name, str(self.file_number).zfill(5)), "w")
            self.writer = csv.writer(self.f)
            self.prepare_csv_header()

    def write_csv_row(self, data):
        date_time = str(datetime.datetime.now())
        date, time = date_time.split(' ')
        row = [date, time]
        x = [list(data[i].values()) for i in data]
        flat_list = [item for sublist in x for item in sublist]
        row = row + flat_list

        self.writer.writerow(row)
        self.f.flush()
        self.line_count += 1
        self.check_new_file()
