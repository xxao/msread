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
RETENTION_TIME_PATTERN = re.compile('^PT((\d*\.?\d*)M)?((\d*\.?\d*)S)?$')


class MZXMLReader(MSReader):
    """
    MZXMLReader reads mass spectrum data from mzData files.
    """
    
    
    def __init__(self, path, **kwargs):
        """
        Initializes a new instance of msread.MZXMLReader.
        
        Args:
            path: str
                Path of the spectrum file to be read.
        """
        
        super().__init__(path)
        
        # init buffers
        self._spectrum_type = None
        self._scan_hierarchy = []
        
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
        
        # clear scan hierarchy
        self._scan_hierarchy = []
        
        # iterate through file
        for evt, elm in etree.iterparse(self.path, ('start','end')):
            
            # retrieve spectrum type
            if elm.tag == self._prefix+'dataProcessing' and evt == 'start':
                self._retrieve_spectrum_type(elm)
            
            # process spectrum data
            if elm.tag == self._prefix+'scan':
                
                # retain scan hierarchy
                if evt == 'start':
                    self._scan_hierarchy.append(elm.get('num', None))
                    continue
                else:
                    del self._scan_hierarchy[-1]
                
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
        
        # clear scan hierarchy
        self._scan_hierarchy = []
        
        # iterate through file
        for evt, elm in etree.iterparse(self.path, ('start', 'end')):
            
            # retrieve data type
            if elm.tag == self._prefix+'dataProcessing' and evt == 'start':
                self._retrieve_spectrum_type(elm)
            
            # process spectrum data
            if elm.tag == self._prefix+'scan':
                
                # get current scan number
                current_scan_number = elm.get('num', None)
                
                # retain scan hierarchy
                if evt == 'start':
                    self._scan_hierarchy.append(current_scan_number)
                    continue
                else:
                    del self._scan_hierarchy[-1]
                
                # check scan number
                if scan_number is not None and current_scan_number and scan_number != int(current_scan_number):
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
        
        # clear scan hierarchy
        self._scan_hierarchy = []
        
        # iterate through file
        for evt, elm in etree.iterparse(self.path, ('start','end')):
            
            # retrieve data type
            if elm.tag == self._prefix+'dataProcessing' and evt == 'start':
                self._retrieve_spectrum_type(elm)
            
            # process spectrum data
            if elm.tag == self._prefix+'scan':
                
                # retain scan hierarchy
                if evt == 'start':
                    self._scan_hierarchy.append(elm.get('num', None))
                    continue
                else:
                    del self._scan_hierarchy[-1]
                
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
        
        # clear scan hierarchy
        self._scan_hierarchy = []
        
        # iterate through file
        for evt, elm in etree.iterparse(self.path, ('start','end')):
            
            # retrieve data type
            if elm.tag == self._prefix+'dataProcessing' and evt == 'start':
                self._retrieve_spectrum_type(elm)
            
            # process spectrum data
            if elm.tag == self._prefix+'scan':
                
                # get current scan number
                current_scan_number = elm.get('num', None)
                
                # retain scan hierarchy
                if evt == 'start':
                    self._scan_hierarchy.append(current_scan_number)
                    continue
                else:
                    del self._scan_hierarchy[-1]
                
                # check scan number
                if scan_number is not None and current_scan_number and scan_number != int(current_scan_number):
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
            
            'points': None,
            'byte_order': None,
            'compression': None,
            'precision': None,
        }
    
    
    def _make_header(self, scan_data):
        """Creates ScanHeader object from raw data."""
        
        # copy header data
        header_data = scan_data.copy()
        
        # remove some items from raw data
        del header_data['points']
        del header_data['byte_order']
        del header_data['compression']
        del header_data['precision']
        
        # create header
        header = ScanHeader(header_data)
        
        return header
    
    
    def _make_scan(self, scan_data, data_type):
        """Creates Scan object from raw data."""
        
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
    
    
    def _retrieve_header_data(self, scan_elm, scan_data):
        """Retrieves scan header data."""
        
        # retrieve scan number
        attr = scan_elm.get('num', None)
        if attr:
            scan_data['scan_number'] = int(attr)
        
        # set parent scan number
        if self._scan_hierarchy:
            scan_data['parent_scan_number'] = int(self._scan_hierarchy[-1])
        
        # retrieve ms level
        attr = scan_elm.get('msLevel', 1)
        if attr:
            scan_data['ms_level'] = int(attr)
        
        # retrieve points count
        attr = scan_elm.get('peaksCount', None)
        if attr is not None:
            scan_data['points_count'] = int(attr)
        
        # retrieve polarity
        attr = scan_elm.get('polarity', None)
        if attr in ('positive', 'Positive', '+'):
            scan_data['polarity'] = POSITIVE
        elif attr in ('negative', 'Negative', '-'):
            scan_data['polarity'] = NEGATIVE
        
        # retrieve retention time
        attr = scan_elm.get('retentionTime', None)
        if attr is not None:
            scan_data['retention_time'] = self._parse_retention_time(attr)
        
        # retrieve low m/z
        attr = scan_elm.get('lowMz', None)
        if attr is not None:
            scan_data['low_mz'] = float(attr)
        
        # retrieve high m/z
        attr = scan_elm.get('highMz', None)
        if attr is not None:
            scan_data['high_mz'] = float(attr)
        
        # retrieve base peak m/z
        attr = scan_elm.get('basePeakMz', None)
        if attr is not None:
            scan_data['basepeak_mz'] = float(attr)
        
        # retrieve base peak intensity
        attr = scan_elm.get('basePeakIntensity', None)
        if attr is not None:
            scan_data['basepeak_intensity'] = max(0.0, float(attr))
        
        # retrieve total ion current
        attr = scan_elm.get('totalIonCurrent', None)
        if attr is not None:
            scan_data['tic'] = max(0.0, float(attr))
        
        # retrieve activation energy
        attr = scan_elm.get('collisionEnergy', None)
        if attr is not None:
            scan_data['activation_energy'] = float(attr)
        
        # retrieve precursor info
        for precursor_elm in scan_elm.iter(self._prefix+'precursorMz'):
            
            # retrieve precursor mass
            if precursor_elm.text:
                scan_data['precursor_mz'] = float(precursor_elm.text)
            
            # retrieve precursor intensity
            attr = precursor_elm.get('precursorIntensity', None)
            if attr is not None:
                scan_data['precursor_intensity'] = max(0.0, float(attr))
            
            # retrieve precursor charge
            attr = precursor_elm.get('precursorCharge', None)
            if attr is not None:
                scan_data['precursor_charge'] = int(attr)
    
    
    def _retrieve_spectrum_data(self, scan_elm, scan_data):
        """Retrieves spectrum data."""
        
        # retrieve number of points
        scan_data['points_count'] = int(scan_elm.get('peaksCount', 0))
        
        # retrieve data points
        peaks_elm = scan_elm.find(self._prefix+'peaks')
        if peaks_elm:
            scan_data['points'] = peaks_elm.text
            scan_data['byte_order'] = peaks_elm.get('byteOrder', 'network')
            scan_data['precision'] = int(peaks_elm.get('precision', 32))
            
            # retrieve compression
            attr = peaks_elm.get('compressionType', None)
            if attr and attr != 'none':
                scan_data['compression'] = attr
    
    
    def _retrieve_spectrum_type(self, dataProcessing_elm):
        """Retrieves global spectrum type."""
        
        self._spectrum_type = None
        
        attr = dataProcessing_elm.get(CENTROIDS, None)
        if attr and attr == '1':
            self._spectrum_type = CENTROIDS
        elif attr and attr == '0':
            self._spectrum_type = PROFILE
    
    
    def _parse_retention_time(self, string):
        """Converts retention time to seconds."""
        
        # match retention time pattern
        match = RETENTION_TIME_PATTERN.match(string)
        if not match:
            return None
        
        # convert to seconds
        seconds = 0
        if match.group(2):
            seconds += float(match.group(2))*60
        if match.group(4):
            seconds += float(match.group(4))
        
        return seconds
    
    
    def _parse_points(self, scan_data):
        """Parses spectrum data points."""
        
        # check data
        if not scan_data['points']:
            return []
        
        # get precision
        precision = 'f'
        if scan_data['precision'] == 64:
            precision = 'd'
        
        # get endian
        endian = '!'
        if scan_data['byte_order'] == 'little':
            endian = '<'
        elif scan_data['byte_order'] == 'big':
            endian = '>'
        
        # decode data
        data = base64.b64decode(scan_data['points'])
        
        # decompress data
        if scan_data['compression'] == 'zlib':
            data = zlib.decompress(data)
        
        # convert from binary
        count = int(len(data) / struct.calcsize(endian + precision))
        data = struct.unpack(endian + precision * count, data[0:len(data)])
        
        # format
        if scan_data['spectrum_type'] == CENTROIDS:
            points = list(map(list, zip(data[::2], data[1::2])))
        else:
            data = numpy.array(data)
            data.shape = (-1, 2)
            points = data.copy()
        
        return points
