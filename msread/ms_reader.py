#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# import modules
import os.path
from .centroid import Centroid
from .masslist import Masslist
from .header import ScanHeader
from .scan import Scan
from .constants import *


class MSReader(object):
    """
    MSReader represents a base class for all the MS readers.
    
    Attributes:
        path: str
            Current document path.
    """
    
    
    def __init__(self, path):
        """
        Initializes a new instance of msread.MSReader.
        
        Args:
            path: str
                Path of the spectrum file to be loaded.
        """
        
        # check path
        if not os.path.exists(path):
            message = "File not found! -> '%s'" % path
            raise IOError(message)
        
        # set path
        self._path = path
    
    
    def __enter__(self):
        """Opens specified path within 'with' statement."""
        
        self.open()
        return self
    
    
    def __exit__(self, exc_ty, exc_val, tb):
        """Closes opened path when 'with' statement ended."""
        
        self.close()
    
    
    @property
    def path(self):
        """
        Gets document path.
        
        Returns:
            str
                Current document path.
        """
        
        return self._path
    
    
    def open(self):
        """Opens the file."""
        
        return self
    
    
    def close(self):
        """Closes the file."""
        
        pass
    
    
    def headers(self, **kwargs):
        """
        Iterates through all available scan headers within document.
        
        This is just an abstract method, which must be overridden in all derived
        classes to get headers.
        
        Yields:
            msread.ScanHeader
                MS scan header.
        """
        
        message = "The 'headers(self)' method is not implemented for this class. -> %s" % self.__class__.__name__
        raise NotImplementedError(message)
    
    
    def scans(self, **kwargs):
        """
        Iterates through all available scans within document.
        
        This is just an abstract method, which must be overridden in all derived
        classes to get scans.
        
        Yields:
            msread.Scan
                MS scan.
        """
        
        message = "The 'scans(self, data_type)' method is not implemented for this class. -> %s" % self.__class__.__name__
        raise NotImplementedError(message)
    
    
    def scan(self, scan_number, **kwargs):
        """
        Retrieves specified scan from document.
        
        This is just an abstract method, which must be overridden in all derived
        classes to get scan.
        
        Args:
            scan_number: int or None
                Specifies the scan number of the scan to be retrieved. If not
                provided or set to None, first scan is returned. The None value
                is typically used for files containing just one scan without
                specific scan number assigned.
        
        Returns:
            msread.Scan
                MS scan.
        """
        
        message = "The 'scan(self, scan_number, data_type)' method is not implemented for this class. -> %s" % self.__class__.__name__
        raise NotImplementedError(message)
    
    
    def summary(self, show=True):
        """
        Gets information summary retrieved from all scans.
        
        Args:
            show: bool
                If set tot True, the summary will be printed immediately.
        
        Returns:
            dict
                Summary dictionary.
        """
        
        # init summary
        summary = {
            'instrument_name': None,
            'instrument_model': None,
            'scan_number_min': None,
            'scan_number_max': None,
            'rt_min': None,
            'rt_max': None,
            'ms_levels': {},
        }
        
        # get all headers
        headers = list(self.headers())
        
        # get instrument names
        names = set(h.instrument_name for h in headers if h.instrument_name is not None)
        if names:
            summary['instrument_name'] = "; ".join(names)
        
        # get instrument models
        models = set(h.instrument_model for h in headers if h.instrument_model is not None)
        if models:
            summary['instrument_model'] = "; ".join(models)
        
        # get scan numbers
        numbers = [h.scan_number for h in headers]
        summary['scan_number_min'] = min(numbers)
        summary['scan_number_max'] = max(numbers)
        
        # get RT range
        times = [h.retention_time for h in headers]
        summary['rt_min'] = min(times)
        summary['rt_max'] = max(times)
        
        # init MS level info
        levels = set(h.ms_level for h in headers)
        for level in levels:
            summary['ms_levels'][level] = {
                'scan_counts': 0,
                'mass_analyzers': set(),
                'mass_ranges': set(),
                'mass_ranges_count': set(),
                'polarities': set(),
                'resolutions': set(),
                'dissociation_methods': set(),
                'activation_energies': set()}
        
        # get MS level info
        for x in headers:
            summary['ms_levels'][x.ms_level]['scan_counts'] += 1
            summary['ms_levels'][x.ms_level]['mass_analyzers'].add(x.mass_analyzer)
            summary['ms_levels'][x.ms_level]['mass_ranges'].add((x.low_mz, x.high_mz))
            summary['ms_levels'][x.ms_level]['polarities'].add({POSITIVE: '+', NEGATIVE: '-', None: None}[x.polarity])
            summary['ms_levels'][x.ms_level]['resolutions'].add(x.resolution)
            summary['ms_levels'][x.ms_level]['dissociation_methods'].add(x.dissociation_method)
            summary['ms_levels'][x.ms_level]['activation_energies'].add(x.activation_energy)
        
        # clean summary
        for value in summary['ms_levels'].values():
            value['mass_analyzers'] = tuple(value['mass_analyzers'])
            value['mass_ranges'] = tuple(value['mass_ranges'])
            value['mass_ranges_count'] = len(value['mass_ranges'])
            value['polarities'] = tuple(value['polarities'])
            value['resolutions'] = tuple(value['resolutions'])
            value['dissociation_methods'] = tuple(value['dissociation_methods'])
            value['activation_energies'] = tuple(set(map(lambda x:int(round(x)), filter(None, value['activation_energies']))))
        
        # show summary
        if show:
            
            print("Instrument: %s | %s" % (summary['instrument_name'], summary['instrument_model']))
            print("RT Range: %.2f - %.2f [min]" % (summary['rt_min']/60.0, summary['rt_max']/60.0))
            print("Scan Range: %d - %d" % (summary['scan_number_min'], summary['scan_number_max']))
            
            for level, info in summary['ms_levels'].items():
                print("\nMS%d Info:" % level)
                print("\tScan Counts: %d" % info['scan_counts'])
                print("\tPolarities: %s" % str(info['polarities']))
                print("\tMass Analyzers: %s" % str(info['mass_analyzers']))
                print("\tMass Ranges: %s" % (info['mass_ranges_count'] if info['mass_ranges_count'] > 2 else str(info['mass_ranges'])))
                print("\tResolutions: %s" % str(info['resolutions']))
                print("\tDissociation Methods: %s" % str(info['dissociation_methods']))
                print("\tActivation Energies: %s" % str(info['activation_energies']))
        
        return summary
