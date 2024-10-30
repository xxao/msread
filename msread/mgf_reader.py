#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# import modules
import re
from .ms_reader import *

# compile basic patterns
HEADER_PATTERN = re.compile('^([A-Z]+)=(.+)')
POINT_PATTERN = re.compile('^([0-9eE\-\+\.]+)[ \t]*([0-9eE\-\+\.]*)')


class MGFReader(MSReader):
    """
    MGFReader reads mass spectrum data from MGF (Mascot Generic File) files.
    
    This reader currently doesn't support any specific values added by
    different software. It only supports attributes of the original format.
    """
    
    
    def __init__(self, path, **kwargs):
        """
        Initializes a new instance of msread.MGFReader.
        
        Args:
            path: str
                Path of the spectrum file to be read.
        """
        
        super().__init__(path)
    
    
    def headers(self, **kwargs):
        """
        Iterates through all available scan headers within document.
        
        Yields:
            msread.ScanHeader
                MS scan header.
        """
        
        scan_data = None
        
        # read data
        with open(self.path) as f:
            
            # parse data
            for line in f:
                
                # discard empty lines and comments
                line = line.strip()
                if not line or line[0] in ('#', ';', '!', '/'):
                    continue
                
                # init new scan
                if line == 'BEGIN IONS':
                    scan_data = self._make_template()
                    continue
                
                # scan ended
                elif line == 'END IONS' and scan_data is not None:
                    yield self._make_header(scan_data)
                    scan_data = None
                    continue
                
                # check scan data
                if scan_data is None:
                    continue
                
                # parse header data
                self._parse_header(line, scan_data)
    
    
    def scans(self, data_type=CENTROIDS, **kwargs):
        """
        Iterates through all available scans within document.
        
        Args:
            data_type: str
                Specifies how data points should be handled if this value is not
                available from the file.
                    msread.CENTROIDS - points will be handled as centroids
                    msread.PROFILE - points will be handled as profile
        
        Yields:
            msread.Scan
                MS scan.
        """
        
        scan_data = None
        
        # read data
        with open(self.path) as f:
            
            # parse data
            for line in f:
                
                # discard empty lines and comments
                line = line.strip()
                if not line or line[0] in ('#', ';', '!', '/'):
                    continue
                
                # init new scan
                if line == 'BEGIN IONS':
                    scan_data = self._make_template()
                    continue
                
                # scan ended
                elif line == 'END IONS' and scan_data is not None:
                    yield self._make_scan(scan_data, data_type)
                    scan_data = None
                    continue
                
                # check scan data
                if scan_data is None:
                    continue
                
                # parse header data
                self._parse_header(line, scan_data)
                
                # parse spectrum point
                self._parse_point(line, scan_data)
    
    
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
        
        scan_data = None
        
        # read data
        with open(self.path) as f:
            
            # parse data
            for line in f:
                
                # discard empty lines and comments
                line = line.strip()
                if not line or line[0] in ('#', ';', '!', '/'):
                    continue
                
                # init new scan
                if line == 'BEGIN IONS':
                    scan_data = self._make_template()
                    continue
                
                # scan ended
                elif line == 'END IONS' and scan_data is not None:
                    if not scan_number or scan_number == scan_data['scan_number']:
                        return self._make_scan(scan_data, data_type)
                    scan_data = None
                    continue
                
                # check scan data
                if scan_data is None:
                    continue
                
                # parse header data
                self._parse_header(line, scan_data)
                
                # read data only for matched scan
                if not scan_number or scan_number == scan_data['scan_number']:
                    self._parse_point(line, scan_data)
    
    
    def _make_template(self):
        """Creates scan template."""
        
        return {
            'title': '',
            'scan_number': None,
            'points_count': 0,
            'retention_time': None,
            'precursor_mz': None,
            'precursor_charge': None,
            'data': [],
        }
    
    
    def _make_header(self, scan_data):
        """Creates msread.ScanHeader object from raw data."""
        
        # copy header data
        header_data = scan_data.copy()
        
        # remove some items from raw data
        del header_data['data']
        
        # create header
        return ScanHeader(header_data)
    
    
    def _make_scan(self, scan_data, data_type):
        """Creates msread.Scan object from raw data."""
        
        # create header
        header = self._make_header(scan_data)
        
        # handle data as centroids
        if data_type == CENTROIDS:
            buff = []
            for point in scan_data['data']:
                buff.append(Centroid(mz=point[0], ai=point[1]))
            scan = Scan(centroids=buff, header=header)
        
        # handle data as profile
        elif data_type == PROFILE:
            scan = Scan(profile=scan_data['data'], header=header)
        
        # unknown data type
        else:
            message = "Unknown data type specified! -> %s" % data_type
            raise ValueError(message)
        
        return scan
    
    
    def _parse_header(self, line, scan_data):
        """Retrieves scan header data."""
        
        # parse line
        parts = HEADER_PATTERN.match(line)
        if not parts:
            return
        
        # retrieve title
        if parts.group(1) == 'TITLE':
            scan_data['title'] = parts.group(2).strip()
        
        # retrieve scan number
        elif parts.group(1) == 'SCANS':
            scan_data['scan_number'] = int(parts.group(2).split('-')[0])
        
        # retrieve retention time
        elif parts.group(1) == 'RTINSECONDS':
            scan_data['retention_time'] = float(parts.group(2).split('-')[0])
        
        # retrieve precursor m/z
        elif parts.group(1) == 'PEPMASS':
            scan_data['precursor_mz'] = float(parts.group(2).split()[0])
        
        # retrieve precursor charge
        elif parts.group(1) == 'CHARGE':
            charge = parts.group(2).strip()
            if charge[-1] in ('+', '-'):
                charge = charge[-1]+charge[:-1]
            scan_data['precursor_charge'] = int(charge)
    
    
    def _parse_point(self, line, scan_data):
        """Retrieves spectrum point."""
        
        # parse line
        parts = POINT_PATTERN.match(line)
        if not parts:
            return
        
        # init point
        point = [0, 100.]
        point[0] = float(parts.group(1).strip())
        
        # try to get intensity if available
        if parts.group(2):
            point[1] = float(parts.group(2).strip())
        
        scan_data['data'].append(point)
        scan_data['points_count'] += 1
