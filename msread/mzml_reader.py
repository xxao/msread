#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# import modules
import base64
import zlib
import struct
import re
import numpy
import xml.etree.cElementTree as etree
from .ms_reader import *

# compile basic patterns
PREFIX_PATTERN = re.compile('^(\{[^\}]*\}).*')
SCAN_NUMBER_PATTERN = re.compile('scan=([0-9]+)')


class MZMLReader(MSReader):
    """
    MZMLReader reads mass spectrum data from mzML files.
    """
    
    def __init__(self, path, **kwargs):
        """
        Initializes a new instance of msread.MZMLReader.
        
        Args:
            path: str
                Path of the spectrum file to be read.
        """
        
        super().__init__(path)
        
        # init buffers
        self._instrument_configs = {}
        
        # set namespace prefix
        self._prefix = ''
        for evt, elm in etree.iterparse(self.path, ('start',)):
            match = PREFIX_PATTERN.match(elm.tag)
            self._prefix = match.group(1) if match else ''
            break
    
    
    def headers(self, min_rt=None, max_rt=None, ms_level=None, polarity=None, **kwargs):
        
        """
        Iterates through all available scan headers within document.
        
        Args:
            min_rt: float or None
                Minimum retention time in seconds.
            
            max_rt: float or None
                Maximum retention time in seconds.
            
            ms_level: int or None
                Specific MS level.
            
            polarity: int or None
                Polarity mode.
                    msread.POSITIVE - positive mode
                    msread.NEGATIVE - negative mode
        
        Yields:
            msread.ScanHeader
                MS scan header.
        """
        
        # iterate through file
        for evt, elm in etree.iterparse(self.path, ('end',)):
            
            # retrieve instrument configs
            if elm.tag == self._prefix+'instrumentConfigurationList':
                self._retrieve_instrument_configurations(elm)
            
            # process spectrum data
            if elm.tag == self._prefix+'spectrum':
                
                # init scan data container
                scan_data = self._make_template()
                
                # retrieve raw header data
                self._retrieve_header_data(elm, scan_data)
                
                # check raw header data
                if not self._check_header_data(scan_data, min_rt, max_rt, ms_level, polarity):
                    elm.clear()
                    continue
                
                # free memory
                elm.clear()
                
                # create scan header
                yield self._make_header(scan_data)
    
    
    def header(self, scan_number, **kwargs):
        """
        Retrieves specified scan header from document.
        
        Args:
            scan_number: int or None
                Specifies the scan number of the header to be retrieved. If not
                provided or set to None, first header is returned. The None value
                is typically used for files containing just one scan without
                specific scan number assigned.
        
        Returns:
            msread.ScanHeader
                MS scan header.
        """
        
        # iterate through file
        for evt, elm in etree.iterparse(self.path, ('end',)):
            
            # retrieve instrument configs
            if elm.tag == self._prefix+'instrumentConfigurationList':
                self._retrieve_instrument_configurations(elm)
            
            # process spectrum data
            if elm.tag == self._prefix+'spectrum':
                
                # check scan number
                if scan_number is not None:
                    attr = elm.get('id', None)
                    if attr and scan_number != self._parse_scan_number(attr):
                        continue
                
                # init scan data container
                scan_data = self._make_template()
                
                # retrieve raw header data
                self._retrieve_header_data(elm, scan_data)
                
                # free memory
                elm.clear()
                
                # create scan
                return self._make_header(scan_data)
    
    
    def scans(self, min_rt=None, max_rt=None, ms_level=None, polarity=None, data_type=CENTROIDS, **kwargs):
        """
        Iterates through all available scans within document.
        
        Args:
            min_rt: float or None
                Minimum retention time in seconds.
            
            max_rt: float or None
                Maximum retention time in seconds.
            
            ms_level: int or None
                Specific MS level.
            
            polarity: int or None
                Polarity mode.
                    msread.POSITIVE - positive mode
                    msread.NEGATIVE - negative mode
            
            data_type: str
                Specifies how data points should be handled if this value is not
                available from the file.
                    msread.CENTROIDS - points will be handled as centroids
                    msread.PROFILE - points will be handled as profile
        
        Yields:
            msread.Scan
                MS scan.
        """
        
        # iterate through file
        for evt, elm in etree.iterparse(self.path, ('end',)):
            
            # retrieve instrument configs
            if elm.tag == self._prefix+'instrumentConfigurationList':
                self._retrieve_instrument_configurations(elm)
            
            # process spectrum data
            if elm.tag == self._prefix+'spectrum':
                
                # init scan data container
                scan_data = self._make_template()
                
                # retrieve raw header data
                self._retrieve_header_data(elm, scan_data)
                
                # check raw header data
                if not self._check_header_data(scan_data, min_rt, max_rt, ms_level, polarity):
                    elm.clear()
                    continue
                
                # retrieve raw spectrum data
                self._retrieve_spectrum_data(elm, scan_data)
                
                # free memory
                elm.clear()
                
                # create scan
                yield self._make_scan(scan_data, data_type)
    
    
    def scan(self, scan_number, data_type=CENTROIDS, **kwargs):
        """
        Retrieves specified scan from document.
        
        Args:
            scan_number: int or None
                Specifies the scan number of the scan to be retrieved. If not
                provided or set to None, first scan is returned. The None value
                is typically used for files containing just one scan without
                specific scan number assigned.
            
            data_type: str
                Specifies how data points should be handled if this value is not
                available from the file.
                    msread.CENTROIDS - points will be handled as centroids
                    msread.PROFILE - points will be handled as profile
        
        Returns:
            msread.Scan
                MS scan.
        """
        
        # iterate through file
        for evt, elm in etree.iterparse(self.path, ('end',)):
            
            # retrieve instrument configs
            if elm.tag == self._prefix+'instrumentConfigurationList':
                self._retrieve_instrument_configurations(elm)
            
            # process spectrum data
            if elm.tag == self._prefix+'spectrum':
                
                # check scan number
                if scan_number is not None:
                    attr = elm.get('id', None)
                    if attr and scan_number != self._parse_scan_number(attr):
                        continue
                
                # init scan data container
                scan_data = self._make_template()
                
                # retrieve raw header data
                self._retrieve_header_data(elm, scan_data)
                
                # retrieve raw spectrum data
                self._retrieve_spectrum_data(elm, scan_data)
                
                # free memory
                elm.clear()
                
                # create scan
                return self._make_scan(scan_data, data_type)
    
    
    def _make_template(self):
        """Creates scan template."""
        
        return {
            'scan_number': None,
            'parent_scan_number': None,
            'ms_level': None,
            'spectrum_type': None,
            'mass_analyzer': None,
            'ionization_source': None,
            'resolution': None,
            'points_count': None,
            'polarity': None,
            'retention_time': None,
            'low_mz': None,
            'high_mz': None,
            'basepeak_mz': None,
            'basepeak_intensity': None,
            'tic': None,
            'precursor_mz': None,
            'precursor_intensity': None,
            'precursor_charge': None,
            'precursor_low_mz': None,
            'precursor_high_mz': None,
            'dissociation_method': None,
            'activation_energy': None,
            
            'mz_data': None,
            'mz_precision': None,
            'mz_compression': None,
            'int_data': None,
            'int_precision': None,
            'int_compression': None,
            'sn_data': None,
            'sn_precision': None,
            'sn_compression': None,
            'precursor_target_mz': None,
            'precursor_lower_offset': None,
            'precursor_upper_offset': None,
            'precursor_width': None,
        }
    
    
    def _make_header(self, scan_data):
        """Creates msread.ScanHeader object from raw data."""
        
        # copy header data
        header_data = scan_data.copy()
        
        # set precursor target
        if header_data['precursor_target_mz'] is None:
            header_data['precursor_target_mz'] = header_data['precursor_mz']
        
        # set precursor offsets
        if header_data['precursor_width'] is not None:
            header_data['precursor_lower_offset'] = 0.5 * header_data['precursor_width']
            header_data['precursor_upper_offset'] = 0.5 * header_data['precursor_width']
        
        # set precursor window
        if header_data['precursor_target_mz'] is not None:
            header_data['precursor_low_mz'] = header_data['precursor_target_mz'] - header_data['precursor_lower_offset']
            header_data['precursor_high_mz'] = header_data['precursor_target_mz'] + header_data['precursor_upper_offset']
        
        # remove some items from raw data
        del header_data['mz_data']
        del header_data['mz_precision']
        del header_data['mz_compression']
        del header_data['int_data']
        del header_data['int_precision']
        del header_data['int_compression']
        del header_data['sn_data']
        del header_data['sn_precision']
        del header_data['sn_compression']
        del header_data['precursor_target_mz']
        del header_data['precursor_lower_offset']
        del header_data['precursor_upper_offset']
        del header_data['precursor_width']
        
        # create header
        return ScanHeader(header_data)
    
    
    def _make_scan(self, scan_data, data_type):
        """Creates msread.Scan object from raw data."""
        
        # make scan header
        header = self._make_header(scan_data)
        
        # parse points
        points = self._parse_points(scan_data)
        
        # set data type
        if scan_data['spectrum_type'] is not None:
            data_type = scan_data['spectrum_type']
        
        # parse data as centroids
        if data_type == CENTROIDS:
            buff = []
            for point in points:
                noise = point[1] / point[2] if point[2] else None
                buff.append(Centroid(mz=point[0], ai=point[1], noise=noise))
            scan = Scan(centroids=buff, header=header)
        
        # parse data as profile
        elif data_type == PROFILE:
            scan = Scan(profile=points, header=header)
        
        # unknown data type
        else:
            message = "Unknown data type specified! -> '%s'" % data_type
            raise ValueError(message)
        
        return scan
    
    
    def _check_header_data(self, scan_data, min_rt=None, max_rt=None, ms_level=None, polarity=None):
        """Checks whether scan header passes filter criteria."""
        
        if min_rt is not None and scan_data['retention_time'] < min_rt:
            return False
        
        if max_rt is not None and scan_data['retention_time'] > max_rt:
            return False
        
        if ms_level is not None and scan_data['ms_level'] != ms_level:
            return False
        
        if polarity is not None and scan_data['polarity'] != polarity:
            return False
        
        return True
    
    
    def _retrieve_header_data(self, spectrum_elm, scan_data):
        """Retrieves scan header data."""
        
        # retrieve scan number
        attr = spectrum_elm.get('id', None)
        if attr:
            scan_data['scan_number'] = self._parse_scan_number(attr)
        
        # retrieve points count
        attr = spectrum_elm.get('defaultArrayLength', None)
        if attr:
            scan_data['points_count'] = int(attr)
        
        # retrieve cv params
        for cvParam_elm in spectrum_elm.findall(self._prefix+'cvParam'):
            key, value = self._parse_cv_param(cvParam_elm, 'spectrum')
            if key:
                scan_data[key] = value
        
        # retrieve scan info
        for scan_elm in spectrum_elm.iter(self._prefix+'scan'):
            
            # retrieve instrument config
            attr = scan_elm.get('instrumentConfigurationRef', None)
            if attr and attr in self._instrument_configs:
                scan_data['ionization_source'] = self._instrument_configs[attr]['ionization_source']
                scan_data['mass_analyzer'] = self._instrument_configs[attr]['mass_analyzer']
                scan_data['resolution'] = self._instrument_configs[attr]['resolution']
            
            # retrieve cv params
            for cvParam_elm in scan_elm.iter(self._prefix+'cvParam'):
                key, value = self._parse_cv_param(cvParam_elm, 'spectrum')
                if key:
                    scan_data[key] = value
        
        # retrieve precursor info
        for precursor_elm in spectrum_elm.iter(self._prefix+'precursor'):
            
            # retrieve parent scan number
            attr = precursor_elm.get('spectrumRef', None)
            if attr:
                scan_data['parent_scan_number'] = self._parse_scan_number(attr)
            
            # retrieve cv params
            for cvParam_elm in precursor_elm.iter(self._prefix+'cvParam'):
                key, value = self._parse_cv_param(cvParam_elm, 'precursor')
                if key:
                    scan_data[key] = value
    
    
    def _retrieve_spectrum_data(self, spectrum_elm, scan_data):
        """Retrieves spectrum data."""
        
        # retrieve binary data
        for binaryDataArray_elm in spectrum_elm.iter(self._prefix+'binaryDataArray'):
            
            # init containers
            binary_data = []
            precision = None
            compression = None
            array_type = None
            
            # retrieve data
            binary_elm = binaryDataArray_elm.find(self._prefix+'binary')
            if binary_elm is not None:
                binary_data = binary_elm.text
            
            # retrieve cv params
            for cvParam_elm in binaryDataArray_elm.iter(self._prefix+'cvParam'):
                key, value = self._parse_cv_param(cvParam_elm, 'binary')
                
                if key == 'precision':
                    precision = value
                elif key == 'compression':
                    compression = value
                elif key == 'array_type':
                    array_type = value
            
            # store mz array
            if array_type == 'mz_array':
                scan_data['mz_data'] = binary_data
                scan_data['mz_precision'] = precision
                scan_data['mz_compression'] = compression
            
            # store intensity array
            elif array_type == 'int_array':
                scan_data['int_data'] = binary_data
                scan_data['int_precision'] = precision
                scan_data['int_compression'] = compression
            
            # store s/n array
            elif array_type == 'sn_array':
                scan_data['sn_data'] = binary_data
                scan_data['sn_precision'] = precision
                scan_data['sn_compression'] = compression
    
    
    def _retrieve_instrument_configurations(self, instrumentConfigurationList_elm):
        """Retrieves available instrument configurations."""
        
        for instrumentConfiguration_elm in instrumentConfigurationList_elm.findall(self._prefix+'instrumentConfiguration'):
            
            # retrieve configuration id
            config_id = instrumentConfiguration_elm.get('id', None)
            if not config_id:
                continue
            
            # init buffer
            self._instrument_configs[config_id] = {
                'ionization_source': None,
                'mass_analyzer': None,
                'resolution': None}
            
            # retrieve all cv params
            for cvParam_elm in instrumentConfiguration_elm.iter(self._prefix+'cvParam'):
                key, value = self._parse_cv_param(cvParam_elm, 'instrument')
                if key:
                    self._instrument_configs[config_id][key] = value
    
    
    def _parse_cv_param(self, cvParam_elm, context=None):
        """Parses cvParam tag."""
        
        # get param data
        accession = cvParam_elm.get('accession', '')
        name = cvParam_elm.get('name', '')
        value = cvParam_elm.get('value', '')
        unit_accession = cvParam_elm.get('unitAccession', '')
        unit_name = cvParam_elm.get('unitName', '')
        
        # binary data
        if not context or context == 'binary':
            
            # 64-bit float
            if accession == 'MS:1000523':
                return 'precision', 64
            
            # 32-bit float
            if accession == 'MS:1000521':
                return 'precision', 32
            
            # 16-bit float
            if accession == 'MS:1000520':
                return 'precision', 16
            
            # zlib compression
            if accession == 'MS:1000574':
                return 'compression', 'zlib'
            
            # no compression
            if accession == 'MS:1000576':
                return 'compression', False
            
            # m/z array
            if accession == 'MS:1000514':
                return 'array_type', 'mz_array'
            
            # intensity array
            elif accession == 'MS:1000515':
                return 'array_type', 'int_array'
            
            # s/n array
            elif accession == 'MS:1000517':
                return 'array_type', 'sn_array'
        
        # spectrum data
        if not context or context == 'spectrum':
            
            # centroid spectrum
            if accession == 'MS:1000127':
                return 'spectrum_type', CENTROIDS
            
            # profile spectrum
            if accession == 'MS:1000128':
                return 'spectrum_type', PROFILE
            
            # ms level
            if accession == 'MS:1000511' and value:
                return 'ms_level', int(value)
            
            # positive scan
            if accession == 'MS:1000130':
                return 'polarity', POSITIVE
            
            # negative scan
            if accession == 'MS:1000129':
                return 'polarity', NEGATIVE
            
            # total ion current
            if accession == 'MS:1000285' and value:
                return 'tic', max(0.0, float(value))
            
            # base peak m/z
            if accession == 'MS:1000504' and value:
                return 'basepeak_mz', float(value)
            
            # base peak intensity
            if accession == 'MS:1000505' and value:
                return 'basepeak_intensity', max(0.0, float(value))
            
            # scan window lower limit
            if accession == 'MS:1000501' and value:
                return 'low_mz', float(value)
            
            # scan window upper limit
            if accession == 'MS:1000500' and value:
                return 'high_mz', float(value)
            
            # scan start time (in minutes)
            if accession == 'MS:1000016' and value and unit_accession == 'UO:0000031':
                return 'retention_time', float(value)*60
            
            # scan start time (in seconds)
            if accession == 'MS:1000016' and value and unit_accession == 'UO:0000010':
                return 'retention_time', float(value)
            
            # scan start time (no units)
            if accession == 'MS:1000016' and value:
                return 'retention_time', float(value)*60
            
            # resolution
            if accession == 'MS:1000800' and value:
                return 'resolution', int(value)
            
            # scan filter
            if accession == 'MS:1000512' and value:
                return 'scan_filter', value
            
            # injection time (in milliseconds)
            if accession == 'MS:1000927' and value and unit_accession == 'UO:0000028':
                return 'injection_time', float(value)
        
        # precursor data
        if not context or context == 'precursor':
            
            # selected ion m/z
            if accession == 'MS:1000744' and value:
                return 'precursor_mz', float(value)
            
            # isolation window target m/z
            if accession == 'MS:1000827' and value:
                return 'precursor_target_mz', float(value)
            
            # isolation window lower limit
            if accession == 'MS:1000793' and value:
                return 'precursor_low_mz', float(value)
            
            # isolation window upper limit
            if accession == 'MS:1000794' and value:
                return 'precursor_high_mz', float(value)
            
            # isolation window lower offset
            if accession == 'MS:1000828' and value:
                return 'precursor_lower_offset', float(value)
            
            # isolation window upper offset
            if accession == 'MS:1000829' and value:
                return 'precursor_upper_offset', float(value)
            
            # isolation width
            if accession == 'MS:1000023' and value and unit_accession == 'MS:1000040':
                return 'precursor_width', float(value)
            
            # peak intensity
            if accession == 'MS:1000042' and value and unit_accession == 'MS:1000131':
                return 'precursor_intensity', float(value)
            
            # charge state
            if accession == 'MS:1000041' and value:
                return 'precursor_charge', int(value)
            
            # possible charge state
            if accession == 'MS:1000633' and value:
                return 'precursor_charge', int(value)
            
            # activation energy
            if accession == 'MS:1000509' and value and unit_accession == 'UO:0000266':
                return 'activation_energy', float(value)
            
            if accession == 'MS:1000045' and value and unit_accession == 'UO:0000266':
                return 'activation_energy', float(value)
            
            # collision induced dissociation
            if accession == 'MS:1000133':
                return 'dissociation_method', 'CID'
            
            # plasma desorption
            if accession == 'MS:1000134':
                return 'dissociation_method', 'PD'
            
            # post-source decay
            if accession == 'MS:1000135':
                return 'dissociation_method', 'PSD'
            
            # surface-induced dissociation
            if accession == 'MS:1000136':
                return 'dissociation_method', 'SID'
            
            # blackbody infrared radiative dissociation
            if accession == 'MS:1000242':
                return 'dissociation_method', 'BIRD'
            
            # electron capture dissociation
            if accession == 'MS:1000250':
                return 'dissociation_method', 'ECD'
            
            # infrared multi-photon dissociation
            if accession == 'MS:1000262':
                return 'dissociation_method', 'IRMPD'
            
            # sustained off-resonance irradiation
            if accession == 'MS:1000282':
                return 'dissociation_method', 'SORI'
            
            # high-energy collision-induced dissociation
            if accession == 'MS:1000422':
                return 'dissociation_method', 'HCD'
            
            # low-energy collision-induced dissociation
            if accession == 'MS:1000433':
                return 'dissociation_method', 'LCD'
        
        # instrument data
        if not context or context == 'instrument':
            
            # resolution
            if accession == 'MS:1000028' and value:
                return 'resolution', int(value)
            
            # chemical ionization
            if accession == 'MS:1000071':
                return 'ionization_source', 'CI'
            
            # electrospray ionization
            if accession == 'MS:1000073':
                return 'ionization_source', 'ESI'
            
            # fast atom bombardment ionization
            if accession == 'MS:1000074':
                return 'ionization_source', 'FAB'
            
            # multi-photon ionization
            if accession == 'MS:1000227':
                return 'ionization_source', 'MPI'
            
            # atmospheric pressure ionization
            if accession == 'MS:1000240':
                return 'ionization_source', 'API'
            
            # desorption ionization
            if accession == 'MS:1000247':
                return 'ionization_source', 'DI'
            
            # fast ion bombardment
            if accession == 'MS:1000446':
                return 'ionization_source', 'FIB'
            
            # field ionization
            if accession == 'MS:1000258':
                return 'ionization_source', 'FI'
            
            # photo-ionization
            if accession == 'MS:1000273':
                return 'ionization_source', 'PI'
            
            # resonance enhanced multi-photon ionization
            if accession == 'MS:1000276':
                return 'ionization_source', 'REMPI'
            
            # fourier transform ion cyclotron resonance mass spectrometer
            if accession == 'MMS:1000079':
                return 'mass_analyzer', 'FTICR'
            
            # magnetic sector
            if accession == 'MS:1000080':
                return 'mass_analyzer', 'Sector'
            
            # quadrupole
            if accession == 'MS:1000081':
                return 'mass_analyzer', 'Quadrupole'
            
            # time-of-flight
            if accession == 'MS:1000084':
                return 'mass_analyzer', 'TOF'
            
            # ion trap
            if accession == 'MS:1000264':
                return 'mass_analyzer', 'IT'
            
            # stored waveform inverse fourier transform
            if accession == 'MS:1000284':
                return 'mass_analyzer', 'SWIFT'
            
            # orbitrap
            if accession == 'MS:1000484':
                return 'mass_analyzer', 'Orbitrap'
        
        return None, None
    
    
    def _parse_scan_number(self, string):
        """Parses real scan number from id tag."""
        
        # match scan number pattern
        match = SCAN_NUMBER_PATTERN.search(string)
        if not match:
            return None
        
        # return as int
        return int(match.group(1))
    
    
    def _parse_points(self, scan_data):
        """Parses spectrum data points."""
        
        # check data
        if not scan_data['mz_data'] or not scan_data['int_data']:
            return []
        
        if not scan_data['sn_data']:
            scan_data['sn_data'] = ""
        
        # decode data
        mz_data = base64.b64decode(scan_data['mz_data'])
        int_data = base64.b64decode(scan_data['int_data'])
        sn_data = base64.b64decode(scan_data['sn_data'])
        
        # decompress data
        if scan_data['mz_compression'] == 'zlib':
            mz_data = zlib.decompress(mz_data)
        
        if scan_data['int_compression'] == 'zlib':
            int_data = zlib.decompress(int_data)
        
        if scan_data['sn_compression'] == 'zlib':
            sn_data = zlib.decompress(sn_data)
        
        # get precision
        mz_precision = 'f'
        if scan_data['mz_precision'] == 64:
            mz_precision = 'd'
        
        int_precision = 'f'
        if scan_data['int_precision'] == 64:
            int_precision = 'd'
        
        sn_precision = 'f'
        if scan_data['sn_precision'] == 64:
            sn_precision = 'd'
        
        # convert from binary
        count = int(len(mz_data) / struct.calcsize('<' + mz_precision))
        mz_data = struct.unpack('<' + mz_precision * count, mz_data[0:len(mz_data)])
        
        count = int(len(int_data) / struct.calcsize('<' + int_precision))
        int_data = struct.unpack('<' + int_precision * count, int_data[0:len(int_data)])
        
        count = int(len(sn_data) / struct.calcsize('<' + sn_precision))
        sn_data = struct.unpack('<' + sn_precision * count, sn_data[0:len(sn_data)])
        
        # format
        if scan_data['spectrum_type'] == CENTROIDS:
            data = zip(mz_data, int_data, sn_data) if sn_data else zip(mz_data, int_data, [0]*len(mz_data))
            points = list(map(list, data))
        else:
            mz_data = numpy.array(mz_data)
            mz_data.shape = (-1, 1)
            int_data = numpy.array(int_data)
            int_data.shape = (-1, 1)
            data = numpy.concatenate((mz_data,int_data), axis=1)
            points = data.copy()
        
        return points
