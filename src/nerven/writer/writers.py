from datetime import datetime
from edflib import _edflib as edf
from numpy import array, ndarray

from consts import *

class EpocWriter(object):
    '''Abstract class.'''
    def __init__(self, outpath, epoc):
        self.path = outpath
        self.start_time = datetime.now()

    def write_packet(self, pkt):
        pass

    def close(self):
        pass

    def running(self):
        return datetime.now() - self.start_time

class RawWriter(EpocWriter):
    '''Just dumps the raw EPOC packets to disk.'''
    def __init__(self, outpath, epoc):
        EpocWriter.__init__(self, outpath, epoc)
        self.stream = open(outpath, 'wb')

    def write_packet(self, pkt):
        buf = map(chr, pkt.raw)
        self.stream.write(''.join(buf))

    def close(self):
        self.stream.close()

class EdfWriter(EpocWriter):
    '''Writes European Data Format (EDF) files. Requires python-edflib.'''
    def __init__(self, outpath, epoc, extra={}):
        EpocWriter.__init__(self, outpath, epoc)
        self.handle = edf.open_file_writeonly(self.path, 1, N_CHANNELS)
        self.sensors = epoc.sensors
        self.pkt_buffer = dict([(s, []) for s in self.sensors])
        self.pkt_buffer['gyrox'] = []
        self.pkt_buffer['gyroy'] = []
        self._init_channels()
        if extra.get('patient', None):
            patient = extra['patient']
            if len(patient) > 80:
                patient = patient[:80]
            edf.set_patientname(self.handle, patient)
        if extra.get('gender', None):
            gender = extra['gender']
            if len(gender) > 15:
                gender = gender[:15]
            edf.set_gender(self.handle, gender)
        if extra.get('patient_additional', None):
            additional = extra['patient_additional']
            if len(additional) > 80:
                additional = additional[:80]
            edf.set_patient_additional(self.handle, additional)
        if extra.get('birthdate', None):
            birthdate = extra['birthdate']
            edf.set_birthdate(self.handle, birthdate.year, birthdate.month, birthdate.day)
        
    def write_packet(self, pkt):
        sensor_data = []
        for s in self.sensors:
            self.pkt_buffer[s].append(pkt.digital[s])
            if len(self.pkt_buffer[s]) == SAMPLE_FREQ:
                self._write_sample(s)
        for s in ('gyrox', 'gyroy'):
            self.pkt_buffer[s].append(pkt.gyro.x if s == 'gyrox' else pkt.gyro.y)
            if len(self.pkt_buffer[s]) == SAMPLE_FREQ:
                self._write_sample(s)

    def close(self):
        edf.close_file(self.handle)

    def _write_sample(self, sensor):
        sensor_data = array(self.pkt_buffer[sensor], dtype='int16')
        edf.write_digital_samples(self.handle, sensor_data)
        self.pkt_buffer[sensor] = []
        
    def _init_channels(self):
        hdl = self.handle
        for i in range(N_CHANNELS):
            edf.set_samplefrequency(hdl, i, SAMPLE_FREQ)
        for i in range(EEG_CHANNELS):
            edf.set_physical_maximum(hdl, i, EEG_PHYS_MAX)
        for i in range(EEG_CHANNELS, N_CHANNELS):
            edf.set_physical_maximum(hdl, i, GYRO_PHYS_MAX)
        for i in range(EEG_CHANNELS):
            edf.set_digital_maximum(hdl, i, EEG_DIG_MAX)
        for i in range(EEG_CHANNELS, N_CHANNELS):
            edf.set_digital_maximum(hdl, i, GYRO_DIG_MAX)
        for i in range(EEG_CHANNELS):
            edf.set_digital_minimum(hdl, i, EEG_DIG_MIN)
        for i in range(EEG_CHANNELS, N_CHANNELS):
            edf.set_digital_minimum(hdl, i, GYRO_DIG_MIN)
        for i in range(EEG_CHANNELS):
            edf.set_physical_minimum(hdl, i, EEG_PHYS_MIN)
        for i in range(EEG_CHANNELS, N_CHANNELS):
            edf.set_physical_minimum(hdl, i, GYRO_PHYS_MIN)
            
        for i, s in enumerate(self.sensors):
            edf.set_label(hdl, i, s)
        edf.set_label(hdl, EEG_CHANNELS, "gyroX")
        edf.set_label(hdl, EEG_CHANNELS+1, "gyroY")

        for i in range(EEG_CHANNELS):
            edf.set_physical_dimension(hdl, i, EEG_DIM)
        for i in range(EEG_CHANNELS, N_CHANNELS):
            edf.set_physical_dimension(hdl, i, GYRO_DIM)
        

        
