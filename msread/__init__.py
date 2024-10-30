#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# set version
version = (0, 5, 1)

# import modules
import os.path

# import objects
from .centroid import Centroid
from .masslist import Masslist
from .header import ScanHeader
from .scan import Scan

# import readers
from .ms_reader import MSReader
from .xy_reader import XYReader
from .mgf_reader import MGFReader
from .mzml_reader import MZMLReader
from .mzxml_reader import MZXMLReader
from .mzdata_reader import MZDataReader
from .thermo_reader import ThermoReader
from .constants import *


def read(path, file_format=None):
    """
    Returns specific file reader for given file type.
    
    Args:
        path: str
            File path.
        
        file_format: str
        
            File format to be used or None to try to get respective format
            directly from file and its content. Supported formats are 'XY'
            (simple ASCII XY), 'mzML', 'mzXML', 'mzData', 'MGF' and 'Thermo'.
    
    Returns:
        msread.MSReader
            Initialized reader for specific file format.
    """
    
    # check path
    if not os.path.exists(path):
        message = "File not found! -> '%s'" % path
        raise IOError(message)
    
    # get format
    if not file_format:
        file_format = resolve_format(path)
    
    # init relevant parser
    if file_format == 'XY':
        return XYReader(path)
    
    if file_format == 'MGF':
        return MGFReader(path)
    
    if file_format == 'mzML':
        return MZMLReader(path)
    
    if file_format == 'mzXML':
        return MZXMLReader(path)
    
    if file_format == 'mzData':
        return MZDataReader(path)
    
    if file_format == 'Thermo':
        return ThermoReader(path)
    
    # unknown format
    message = "Unknown file format! -> '%s'" % file_format
    raise ValueError(message)


def resolve_format(path):
    """
    Resolves file format.
    
    Args:
        path: str
            File path.
    
    Returns:
        str
            File format.
    """
    
    # check path
    if not os.path.exists(path):
        message = "File not found! -> " + path
        raise IOError(message)
    
    # get filename and extension
    dirname, filename = os.path.split(path)
    basename, extension = os.path.splitext(filename)
    filename = filename.lower()
    basename = basename.lower()
    extension = extension.lower()
    
    # get format from file extension
    if not extension:
        return 'XY'
    
    if extension in ('.xy', '.txt', '.asc', '.csv'):
        return 'XY'
    
    if extension == '.mzml':
        return 'mzML'
    
    if extension == '.mzxml':
        return 'mzXML'
    
    if extension == '.mzdata':
        return 'mzData'
    
    if extension == '.mgf':
        return 'MGF'
    
    if extension == '.raw':
        return 'Thermo'
    
    # get format from xml files
    if extension == '.xml':
        
        document = open(path, 'r')
        data = document.read(500)
        document.close()
        
        if '<mzData' in data:
            return 'mzData'
        if '<mzXML' in data:
            return 'mzXML'
        if '<mzML' in data:
            return 'mzML'
    
    # unknown file format
    return None
