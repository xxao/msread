#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# import modules
import base64
import struct
import re
import numpy
import xml.etree.cElementTree as etree
from .ms_reader import *

# compile basic patterns
PREFIX_PATTERN = re.compile('^(\{[^\}]*\}).*')


class MZDataReader(MSReader):
    """
    MZDataReader reads mass spectrum data from mzData files.
    """
    
    
    def __init__(self, path, **kwargs):
        """
        Initializes a new instance of msread.MZDataReader.
        
        Args:
            path: str
                Path of the spectrum file to be read.
        """
        
        super().__init__(path)
        
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
            
            # process spectrum data
            if elm.tag == self._prefix+'spectrum':
                
                # check scan number
                if scan_number is not None:
                    attr = elm.get('id', None)
                    if attr and scan_number != int(attr):
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
            
            # process spectrum data
            if elm.tag == self._prefix+'spectrum':
                
                # check scan number
                if scan_number is not None:
                    attr = elm.get('id', None)
                    if attr and scan_number != int(attr):
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
            'mz_endian': None,
            'mz_precision': None,
            'int_data': None,
            'int_endian': None,
            'int_precision': None,
        }
    
    
    def _make_header(self, scan_data):
        """Creates msread.ScanHeader object from raw data."""
        
        # copy header data
        header_data = scan_data.copy()
        
        # remove some items from raw data
        del header_data['mz_data']
        del header_data['mz_endian']
        del header_data['mz_precision']
        del header_data['int_data']
        del header_data['int_endian']
        del header_data['int_precision']
        
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
                buff.append(Centroid(mz=point[0], ai=point[1]))
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
            scan_data['scan_number'] = int(attr)
        
        # retrieve spectrum description
        spectrumDesc_elm = spectrum_elm.find(self._prefix+'spectrumDesc')
        if spectrumDesc_elm:
            
            # retrieve spectrum settings
            spectrumSettings_elm = spectrumDesc_elm.find(self._prefix+'spectrumSettings')
            if spectrumSettings_elm:
                
                # retrieve spectrum type
                acqSpecification_elm = spectrumSettings_elm.find(self._prefix+'acqSpecification')
                if acqSpecification_elm is not None:
                    attr = acqSpecification_elm.get('spectrumType', None)
                    if attr == 'discrete':
                        scan_data['spectrum_type'] = CENTROIDS
                    elif attr == 'continuous':
                        scan_data['spectrum_type'] = PROFILE
                
                # retrieve scan info
                spectrumInstrument_elm = spectrumSettings_elm.find(self._prefix+'spectrumInstrument')
                if spectrumInstrument_elm is not None:
                    
                    # retrieve ms level
                    scan_data['ms_level'] = int(spectrumInstrument_elm.get('msLevel', 1))
                    
                    # retrieve low m/z
                    attr = spectrumInstrument_elm.get('mzRangeStart', None)
                    if attr is not None:
                        scan_data['low_mz'] = float(attr)
                    
                    # retrieve high m/z
                    attr = spectrumInstrument_elm.get('mzRangeStop', None)
                    if attr is not None:
                        scan_data['high_mz'] = float(attr)
                    
                    # retrieve cv params
                    for cvParam_elm in spectrumInstrument_elm.iter(self._prefix+'cvParam'):
                        key, value = self._parse_cv_param(cvParam_elm, 'spectrum')
                        if key:
                            scan_data[key] = value
            
            # retrieve precursor info
            for precursor_elm in spectrumDesc_elm.iter(self._prefix+'precursor'):
                
                # retrieve parent scan number
                attr = precursor_elm.get('spectrumRef', None)
                if attr:
                    scan_data['parent_scan_number'] = int(attr)
                
                # retrieve cv params
                for cvParam_elm in precursor_elm.iter(self._prefix+'cvParam'):
                    key, value = self._parse_cv_param(cvParam_elm, 'precursor')
                    if key:
                        scan_data[key] = value
    
    
    def _retrieve_spectrum_data(self, spectrum_elm, scan_data):
        """Retrieves spectrum data."""
        
        # retrieve m/z array
        mzArrayBinary_elm = spectrum_elm.find(self._prefix+'mzArrayBinary')
        if mzArrayBinary_elm:
            data_elm = mzArrayBinary_elm.find(self._prefix+'data')
            if data_elm is not None:
                scan_data['points_count'] = int(data_elm.get('length', 0))
                scan_data['mz_data'] = data_elm.text
                scan_data['mz_endian'] = data_elm.get('endian', 'network')
                scan_data['mz_precision'] = int(data_elm.get('precision', 32))
        
        # retrieve intensity array
        intenArrayBinary_elm = spectrum_elm.find(self._prefix+'intenArrayBinary')
        if intenArrayBinary_elm:
            data_elm = intenArrayBinary_elm.find(self._prefix+'data')
            if data_elm is not None:
                scan_data['points_count'] = int(data_elm.get('length', 0))
                scan_data['int_data'] = data_elm.text
                scan_data['int_endian'] = data_elm.get('endian', 'network')
                scan_data['int_precision'] = int(data_elm.get('precision', 32))
    
    
    def _parse_cv_param(self, cvParam_elm, context=None):
        """Parses cvParam tag."""
        
        # get param data
        accession = cvParam_elm.get('accession', '')
        name = cvParam_elm.get('name', '')
        value = cvParam_elm.get('value', '')
        
        # spectrum data
        if not context or context == 'spectrum':
            
            # positive scan
            if accession == 'PSI:1000037' and value == 'Positive':
                return 'polarity', POSITIVE
            
            # negative scan
            if accession == 'PSI:1000037' and value == 'Negative':
                return 'polarity', NEGATIVE
            
            # retention time in minutes
            if accession == 'PSI:1000038' and value:
                return 'retention_time', float(value) * 60
        
        # precursor data
        if not context or context == 'precursor':
            
            # selected ion m/z
            if accession == 'PSI:1000040' and value:
                return 'precursor_mz', float(value)
            
            # peak intensity
            if accession == 'PSI:1000042' and value:
                return 'precursor_intensity', float(value)
            
            # charge state
            if accession == 'PSI:1000041' and value:
                return 'precursor_charge', int(value)
            
            # dissociation method
            if accession == 'PSI:1000044' and value:
                return 'dissociation_method', value
        
        return None, None
    
    
    def _parse_points(self, scan_data):
        """Parses spectrum data points."""
        
        # check data
        if not scan_data['mz_data'] or not scan_data['int_data']:
            return []
        
        # decode data
        mz_data = base64.b64decode(scan_data['mz_data'])
        int_data = base64.b64decode(scan_data['int_data'])
        
        # get endian
        mz_endian = '!'
        if scan_data['mz_endian'] == 'little':
            mz_endian = '<'
        elif scan_data['mz_endian'] == 'big':
            mz_endian = '>'
        
        int_endian = '!'
        if scan_data['int_endian'] == 'little':
            int_endian = '<'
        elif scan_data['int_endian'] == 'big':
            int_endian = '>'
        
        # get precision
        mz_precision = 'f'
        if scan_data['mz_precision'] == 64:
            mz_precision = 'd'
        
        int_precision = 'f'
        if scan_data['int_precision'] == 64:
            int_precision = 'd'
        
        # convert from binary
        count = int(len(mz_data) / struct.calcsize(mz_endian + mz_precision))
        mz_data = struct.unpack(mz_endian + mz_precision * count, mz_data[0:len(mz_data)])
        
        count = int(len(int_data) / struct.calcsize(int_endian + int_precision))
        int_data = struct.unpack(int_endian + int_precision * count, int_data[0:len(int_data)])
        
        # format
        if scan_data['spectrum_type'] == CENTROIDS:
            points = list(map(list, zip(mz_data, int_data)))
        else:
            mz_data = numpy.array(mz_data)
            mz_data.shape = (-1, 1)
            int_data = numpy.array(int_data)
            int_data.shape = (-1, 1)
            data = numpy.concatenate((mz_data,int_data), axis=1)
            points = data.copy()
        
        return points
