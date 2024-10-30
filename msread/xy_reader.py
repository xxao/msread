#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# import modules
import re
from .ms_reader import *

# compile basic patterns
COLUMNS_PATTERN = re.compile('^([-0-9\.eE+]+)[ \t]*(;|,)?[ \t]*([-0-9\.eE+]*)$')


class XYReader(MSReader):
    """
    XYReader reads mass spectrum data from simple ASCII XY files.
    
    The file must contain only two columns of numbers. The first column
    represents m/z value, the second column represents intensity value. These
    columns must be separated by tab, semicolon or colon. All the empty lines
    or the lines starting with "#" are skipped automatically.
    """
    
    
    def __init__(self, path, **kwargs):
        """
        Initializes a new instance of msread.XYReader.
        
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
        
        # yield default header
        yield ScanHeader(scan_number=None)
    
    
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
        # read data
        scan_data = self._read_data()
        
        # yield scan
        yield self._make_scan(scan_data, data_type)
    
    
    def scan(self, scan_number=None, data_type=CENTROIDS, **kwargs):
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
        
        # read data
        scan_data = self._read_data()
        
        # return scan
        return self._make_scan(scan_data, data_type)
    
    
    def _read_data(self):
        """Retrieves spectrum data."""
        
        data = []
        
        # read data
        with open(self.path) as f:
            
            # parse lines
            for line in f:
                
                # discard empty lines and comments
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('m/z'):
                    continue
                
                # parse line
                parts = COLUMNS_PATTERN.match(line)
                if parts:
                    mass = float(parts.group(1))
                    intensity = float(parts.group(3) or 0)
                    data.append([mass, intensity])
                else:
                    data = []
                    break
        
        return data
    
    
    def _make_scan(self, scan_data, data_type):
        """Creates msread.Scan object from raw data."""
        
        # create header
        header = ScanHeader(scan_number=0)
        
        # handle data as centroids
        if data_type == CENTROIDS:
            buff = []
            for point in scan_data:
                buff.append(Centroid(mz=point[0], ai=point[1]))
            scan = Scan(centroids=buff, header=header)
        
        # handle data as profile
        elif data_type == PROFILE:
            scan = Scan(profile=scan_data, header=header)
        
        # unknown data type
        else:
            message = "Unknown data type specified! -> '%s'" % data_type
            raise ValueError(message)
        
        return scan
