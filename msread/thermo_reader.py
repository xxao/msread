#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# import modules
import re
import numpy
import ctypes
import datetime

try:
    import comtypes
    import comtypes.client
    import comtypes.automation
except ImportError:
    pass

from .ms_reader import *

# compile basic patterns
SCAN_FILTER_POLARITY_PATTERN = re.compile('^(?P<analyzer>\w+ )?((?P<polarity>\+|\-) )(?P<profile>\w )?(?P<source>\w+ )(?P<dda>\w )?')
SCAN_FILTER_DISSOCIATION_PATTERN = re.compile('(([0-9\.]+)@([a-z]+)([0-9\.]+))')
STEPPED_ENERGIES = re.compile('(?P<activation>\w+) Collision Energies \(%\) = (?P<values>[\d,]+)')

# set enums
ANALYZERS = ('ITMS', 'TQMS', 'SQMS', 'TOFMS', 'FTMS', 'Sector', 'Unknown', 'Astral')
DISSOCIATION_METHODS = ('CID', 'MPD', 'ECD', 'PQD', 'ETD', 'HCD', 'Any', 'SA', 'PTR', 'NETD', 'NPTR', 'Unknown')

# define constants
OLD_BASE = False
VALIDATE_MS_LEVEL = True
FOLLOW_PRECURSOR = True


class ThermoReader(MSReader):
    """
    ThermoReader reads mass spectrum data from ThermoFisher RAW files.
    
    Note that for this reader to work you have to have the Thermo MSFileReader
    installed on your machine. However, this is available on Windows platform
    only.
    """
    
    
    def __init__(self, path, **kwargs):
        """
        Initializes a new instance of msread.ThermoReader.
        
        Args:
            path: str
                Path of the spectrum file to be read.
        """
        
        super().__init__(path)
        
        # init raw file reader
        comtypes.CoInitialize()
        self._raw_reader = comtypes.client.CreateObject('MSFileReader.XRawfile')
        
        # set open flag
        self._is_opened = False
        
        # init buffs
        self._master_scan_numbers = {}
        self._inst_methods = None
    
    
    def open(self):
        """
        Opens the file.
        
        Returns:
            bool
                Returns True if the file is newly opened. False if the file was
                already open.
        """
        
        if self._is_opened:
            return False
        
        self._raw_reader.open(self.path)
        self._is_opened = True
        
        return True
    
    
    def close(self):
        """Closes the file."""
        
        if self._is_opened:
            self._is_opened = False
            self._raw_reader.close()
    
    
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
        
        # open file if necessary
        should_close = self.open()
        
        # set current controller to MS
        self._raw_reader.SetCurrentController(0, 1)
        
        # get number of scans
        count_l = ctypes.c_long()
        self._raw_reader.GetNumSpectra(count_l)
        
        # read headers
        for i in range(1, count_l.value+1):
            
            # init scan data container
            scan_data = self._make_template()
            scan_data['scan_number'] = i
            
            # pre-check scan data
            if not self._check_header_data(scan_data, min_rt, max_rt, ms_level, polarity):
                continue
            
            # retrieve raw header data
            self._retrieve_header_data(scan_data, i)
            
            # create scan header
            yield self._make_header(scan_data)
        
        # close file
        if should_close:
            self.close()
    
    
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
        
        # open file if necessary
        should_close = self.open()
        
        # set current controller to MS
        self._raw_reader.SetCurrentController(0, 1)
        
        # check scan number
        if scan_number is None:
            scan_number = 1
        
        # init scan data container
        scan_data = self._make_template()
        scan_data['scan_number'] = scan_number
        
        # retrieve raw header data
        self._retrieve_header_data(scan_data, scan_number)
        
        # create header
        header = self._make_header(scan_data)
        
        # close file
        if should_close:
            self.close()
        
        return header
    
    
    def scans(self, min_rt=None, max_rt=None, ms_level=None, polarity=None, profile=True, **kwargs):
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
            
            profile: bool
                If set to True the profile data are retrieved (if available).
                Otherwise, only centroids are retrieved.
        
        Yields:
            msread.Scan
                MS scan.
        """
        
        # open file if necessary
        should_close = self.open()
        
        # set current controller to MS
        self._raw_reader.SetCurrentController(0, 1)
        
        # get number of scans
        count_l = ctypes.c_long()
        self._raw_reader.GetNumSpectra(count_l)
        
        # read headers
        for i in range(1, count_l.value+1):
            
            # init scan data container
            scan_data = self._make_template()
            scan_data['scan_number'] = i
            
            # pre-check scan data
            if not self._check_header_data(scan_data, min_rt, max_rt, ms_level, polarity):
                continue
            
            # retrieve raw header data
            self._retrieve_header_data(scan_data, i)
            
            # retrieve raw spectrum data
            self._retrieve_spectrum_data(scan_data, i, profile)
            
            # create scan
            yield self._make_scan(scan_data)
        
        # close file
        if should_close:
            self.close()
    
    
    def scan(self, scan_number, profile=True, **kwargs):
        """
        Retrieves specified scan from document.
        
        Args:
            scan_number: int or None
                Specifies the scan number of the scan to be retrieved. If not
                provided or set to None, first scan is returned. The None value
                is typically used for files containing just one scan without
                specific scan number assigned.
            
            profile: bool
                If set to True the profile data are retrieved (if available).
                Otherwise, only centroids are retrieved.
        
        Returns:
            msread.Scan
                MS scan.
        """
        
        # open file if necessary
        should_close = self.open()
        
        # set current controller to MS
        self._raw_reader.SetCurrentController(0, 1)
        
        # check scan number
        if scan_number is None:
            scan_number = 1
        
        # init scan data container
        scan_data = self._make_template()
        scan_data['scan_number'] = scan_number
        
        # retrieve raw header data
        self._retrieve_header_data(scan_data, scan_number)
        
        # retrieve raw spectrum data
        self._retrieve_spectrum_data(scan_data, scan_number, profile)
        
        # create scan
        scan = self._make_scan(scan_data)
        
        # close file
        if should_close:
            self.close()
        
        return scan
    
    
    def _make_template(self):
        """Creates scan template."""
        
        return {
            'scan_number': None,
            'parent_scan_number': None,
            'acquisition_date': None,
            'instrument_name': None,
            'instrument_model': None,
            'ms_level': None,
            'mass_analyzer': None,
            'ionization_source': 'ESI',
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
            'activation_energies': None,
            
            'scan_filter': None,
            'isolation_width': None,
            'isolation_offset': None,
            'profile': None,
            'centroids': None,
            
            'extra_values': {},
            'status_log': {},
            'instrument_methods': [],
        }
    
    
    def _make_header(self, scan_data):
        """Creates msread.ScanHeader object from raw data."""
        
        # copy header data
        header_data = scan_data.copy()
        
        # set precursor range
        if (header_data['precursor_low_mz'] is None or header_data['precursor_high_mz'] is None) \
            and header_data['precursor_mz'] is not None \
            and header_data['isolation_width'] is not None:
            
            header_data['precursor_low_mz'] = header_data['precursor_mz'] - 0.5*header_data['isolation_width']
            header_data['precursor_high_mz'] = header_data['precursor_mz'] + 0.5*header_data['isolation_width']
        
        # correct charge state polarity
        if header_data['precursor_charge'] is not None and header_data['polarity'] is not None:
            header_data['precursor_charge'] = abs(header_data['precursor_charge']) * header_data['polarity']
        
        # remove some items from raw data
        del header_data['scan_filter']
        del header_data['isolation_width']
        del header_data['isolation_offset']
        del header_data['profile']
        del header_data['centroids']
        del header_data['extra_values']
        del header_data['status_log']
        del header_data['instrument_methods']
        
        # make header
        header = ScanHeader(header_data)
        
        # add custom values
        header.custom_data = {}
        header.custom_data['scan_filter'] = scan_data['scan_filter']
        header.custom_data['extra_values'] = scan_data['extra_values']
        header.custom_data['status_log'] = scan_data['status_log']
        header.custom_data['instrument_methods'] = scan_data['instrument_methods']
        
        return header
    
    
    def _make_scan(self, scan_data):
        """Creates msread.Scan object from raw data."""
        
        # create header
        header = self._make_header(scan_data)
        
        # create scan
        scan = Scan(
            profile = scan_data['profile'],
            centroids = scan_data['centroids'],
            header = header)
        
        return scan
    
    
    def _check_header_data(self, scan_data, min_rt=None, max_rt=None, ms_level=None, polarity=None):
        """Checks whether scan  passes filter criteria."""
        
        # get scan number
        scan_number = scan_data['scan_number']
        
        # check MS level
        if ms_level is not None:
            ret_ms_level = self._retrieve_ms_level(scan_number)
            if ret_ms_level and ret_ms_level != ms_level:
                return False
        
        # check polarity
        if polarity is not None:
            ret_polarity = self._retrieve_polarity(scan_number)
            if ret_polarity and ret_polarity != polarity:
                return False
        
        # check retention time
        if min_rt is not None or max_rt is not None:
            self._retrieve_scan_header_info(scan_data)
            if min_rt is not None and scan_data['retention_time'] < min_rt:
                return False
            if max_rt is not None and scan_data['retention_time'] > max_rt:
                return False
        
        return True
    
    
    def _retrieve_header_data(self, scan_data, scan_number):
        """Retrieves scan header data."""
        
        # retrieve instrument methods
        if self._inst_methods is None:
            self._retrieve_instrument_methods()
            scan_data['instrument_methods'] = self._inst_methods
        
        # retrieve acquisition date
        acquisition_date = self._retrieve_acquisition_date()
        if acquisition_date is not None:
            scan_data['acquisition_date'] = acquisition_date
        
        # retrieve instrument name
        instrument_name = self._retrieve_instrument_name()
        if instrument_name is not None:
            scan_data['instrument_name'] = instrument_name
        
        # retrieve instrument model
        instrument_model = self._retrieve_instrument_model()
        if instrument_model is not None:
            scan_data['instrument_model'] = instrument_model
        
        # retrieve scan filter
        scan_filter = self._retrieve_scan_filter(scan_number)
        if scan_filter is not None:
            scan_data['scan_filter'] = scan_filter
        
        # retrieve ms level
        ms_level = self._retrieve_ms_level(scan_number)
        if ms_level is not None:
            scan_data['ms_level'] = ms_level
        
        # retrieve analyzer type
        mass_analyzer = self._retrieve_mass_analyzer(scan_number)
        if mass_analyzer is not None:
            scan_data['mass_analyzer'] = mass_analyzer
        
        # retrieve polarity
        polarity = self._retrieve_polarity(scan_number)
        if polarity is not None:
            scan_data['polarity'] = polarity
        
        # retrieve resolution
        resolution = self._retrieve_resolution(scan_number)
        if resolution is not None:
            scan_data['resolution'] = resolution
        
        # retrieve scan header info data
        self._retrieve_scan_header_info(scan_data)
        
        # retrieve precursor data
        self._retrieve_precursor_data(scan_data)
        
        # retrieve parent scan number
        self._retrieve_parent_scan_number(scan_data)
        
        # retrieve all trailer extra values
        self._retrieve_extra_values(scan_data)
        
        # retrieve all status log values
        self._retrieve_status_log(scan_data)
    
    
    def _retrieve_spectrum_data(self, scan_data, scan_number, profile):
        """Retrieves spectrum data."""
        
        # get spectrum type
        is_profile_l = ctypes.c_long()
        if self._raw_reader.IsProfileScanForScanNum(scan_number, is_profile_l):
            return
        
        # get polarity
        polarity = scan_data['polarity']
        
        # get profile
        if is_profile_l and profile:
            scan_data['profile'] = self._retrieve_profile(scan_number)
        
        # read centroids
        scan_data['centroids'] = self._retrieve_profile_centroids(scan_number, polarity)
        if not scan_data['centroids']:
            scan_data['centroids'] = self._retrieve_masslist_centroids(scan_number, polarity)
    
    
    def _retrieve_precursor_data(self, scan_data):
        """Retrieves precursor data."""
        
        # scan info
        scan_number = scan_data['scan_number']
        ms_level = scan_data['ms_level']
        
        # check ms level
        if not ms_level or ms_level < 2:
            return
        
        # get all precursor data
        self._retrieve_precursor_info(scan_data)
        
        # get precursor charge
        precursor_charge = self._retrieve_precursor_charge(scan_number)
        if precursor_charge is not None:
            scan_data['precursor_charge'] = precursor_charge
        
        # get precursor mass
        if scan_data['precursor_mz'] is None:
            precursor_mz = self._retrieve_precursor_mz(scan_number)
            if precursor_mz is not None:
                scan_data['precursor_mz'] = precursor_mz
        
        # get precursor range
        if scan_data['precursor_low_mz'] is None or scan_data['precursor_high_mz'] is None:
            precursor_range = self._retrieve_precursor_range(scan_number, ms_level)
            if precursor_range is not None:
                scan_data['precursor_low_mz'] = precursor_range[0]
                scan_data['precursor_high_mz'] = precursor_range[1]
        
        # get isolation width
        if scan_data['isolation_width'] is None:
            isolation_width = self._retrieve_isolation_width(scan_number, ms_level)
            if isolation_width is not None:
                scan_data['isolation_width'] = isolation_width
        
        # get activation energy
        if scan_data['activation_energy'] is None:
            activation_energy = self._retrieve_activation_energy(scan_number, scan_data['dissociation_method'])
            if activation_energy is not None:
                scan_data['activation_energy'] = activation_energy
        
        # get activation energy steps
        if scan_data['activation_energies'] is None:
            activation_energies = self._retrieve_activation_energies(scan_number, scan_data['dissociation_method'])
            if activation_energies is not None:
                scan_data['activation_energies'] = activation_energies
    
    
    def _retrieve_scan_header_info(self, scan_data):
        """Retrieves scan header data."""
        
        # get scan info
        scan_number = scan_data['scan_number']
        
        # init vars
        num_packets_l = ctypes.c_long()
        start_time_d = ctypes.c_double()
        low_mass_d = ctypes.c_double()
        high_mass_d = ctypes.c_double()
        tic_d = ctypes.c_double()
        base_peak_mass_d = ctypes.c_double()
        base_peak_intensity_d = ctypes.c_double()
        num_channels_l = ctypes.c_long()
        uniform_time_l = ctypes.c_long()
        frequency_d = ctypes.c_double()
        
        # get data
        ret = self._raw_reader.GetScanHeaderInfoForScanNum(
                scan_number,
                num_packets_l,
                start_time_d,
                low_mass_d,
                high_mass_d,
                tic_d,
                base_peak_mass_d,
                base_peak_intensity_d,
                num_channels_l,
                uniform_time_l,
                frequency_d)
        
        # set values
        if not ret:
            scan_data['retention_time'] = start_time_d.value * 60.
            scan_data['low_mz'] = low_mass_d.value
            scan_data['high_mz'] = high_mass_d.value
            scan_data['tic'] = tic_d.value
            scan_data['basepeak_mz'] = base_peak_mass_d.value
            scan_data['basepeak_intensity'] = base_peak_intensity_d.value
    
    
    def _retrieve_parent_scan_number(self, scan_data):
        """Retrieves parent scan number."""
        
        # get scan info
        ms_level = scan_data['ms_level']
        master_ms_level = ms_level - 1
        scan_number = scan_data['scan_number']
        precursor_mz = scan_data['precursor_mz']
        
        # check ms level
        if not ms_level or ms_level < 2:
            return
        
        # try trailer
        master_scan_number = self._retrieve_parent_scan_number_by_trailer(scan_number, master_ms_level)
        
        # try event index
        if master_scan_number is None:
            
            event_index = self._retrieve_scan_event_index(scan_number)
            master_event_index = self._retrieve_master_scan_event_index(scan_number)
            
            if event_index and master_event_index:
                master_scan_number = self._retrieve_parent_scan_number_by_event_index(scan_number, master_event_index, precursor_mz)
        
        # try nearest previous MSn-1
        if master_scan_number is None:
            master_scan_number = self._retrieve_parent_scan_number_by_ms_level(scan_number, master_ms_level, precursor_mz, -1)
        
        # try nearest next MSn-1
        if master_scan_number is None:
            master_scan_number = self._retrieve_parent_scan_number_by_ms_level(scan_number, master_ms_level, precursor_mz, 1)
        
        # set master scan number
        scan_data['parent_scan_number'] = master_scan_number
        self._master_scan_numbers[scan_number] = master_scan_number
    
    
    def _retrieve_parent_scan_number_by_trailer(self, scan_number, ms_level):
        """Retrieves parent scan number using trailer."""
        
        # try cache
        if scan_number in self._master_scan_numbers:
            return self._master_scan_numbers[scan_number]
        
        # try to get master scan number from trailer
        master_scan_number_v = comtypes.automation.VARIANT()
        if self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, 'Master Scan Number:', master_scan_number_v):
            return None
        
        # get value
        master_scan_number = int(master_scan_number_v.value)
        if master_scan_number <= 0:
            return None
        
        # check MS level
        master_ms_level = self._retrieve_ms_level(master_scan_number)
        if master_ms_level and master_ms_level == ms_level:
            return master_scan_number
        
        # check flags
        if not VALIDATE_MS_LEVEL:
            return master_scan_number
        
        if not FOLLOW_PRECURSOR:
            return None
        
        # follow precursor until MS level is correct
        return self._retrieve_parent_scan_number_by_trailer(master_scan_number, ms_level)
    
    
    def _retrieve_parent_scan_number_by_event_index(self, scan_number, event_index, precursor_mz):
        """Retrieves parent scan number by master scan event index."""
        
        # try cache
        if scan_number in self._master_scan_numbers:
            return self._master_scan_numbers[scan_number]
        
        # use nearest higher MSn having corresponding event index (for MSn>2)
        lowest_reached = False
        current_scan = scan_number - 1
        
        while current_scan:
            
            # get current scan event index
            current_event_index = self._retrieve_scan_event_index(current_scan)
            
            # check for lowest event index
            if lowest_reached and current_event_index > 1:
                return None
            
            # requested event found
            if current_event_index == event_index:
                
                # get mass range
                low_mz, high_mz = self._retrieve_mass_range(current_scan)
                
                # check mass range
                if not precursor_mz or (low_mz <= precursor_mz <= high_mz):
                    return current_scan
            
            lowest_reached = current_event_index <= 1
            current_scan -= 1
        
        return None
    
    
    def _retrieve_parent_scan_number_by_ms_level(self, scan_number, ms_level, precursor_mz, direction):
        """Retrieves parent scan number by nearest master MS level."""
        
        # try cache
        if scan_number in self._master_scan_numbers:
            return self._master_scan_numbers[scan_number]
        
        # get more info
        cycle = self._retrieve_scan_cycle(scan_number)
        is_dia = self._inst_methods and "DIAScan" in self._inst_methods
        
        # set candidate
        candidate_scan = scan_number + direction
        
        # use nearest MS(n-1)
        while candidate_scan:
            
            # check scan cycle
            if self._retrieve_scan_cycle(candidate_scan) != cycle:
                break
            
            # check ms level
            if self._retrieve_ms_level(candidate_scan) != ms_level:
                candidate_scan += direction
                continue
            
            # get mass range
            low_mz, high_mz = self._retrieve_mass_range(candidate_scan)
            
            # check mass range
            if not precursor_mz or (low_mz <= precursor_mz <= high_mz) or is_dia:
                return candidate_scan
            
            candidate_scan += direction
        
        return None
    
    
    def _retrieve_profile(self, scan_number):
        """Retrieves profile data."""
        
        # read masslist
        scan_number_l = ctypes.c_long(scan_number)
        mass_list_v = comtypes.automation.VARIANT()
        flags_v = comtypes.automation.VARIANT()
        size_l = ctypes.c_long()
        
        error = self._raw_reader.GetMassListFromScanNum(
            scan_number_l,
            comtypes.BSTR(''),  # filter
            ctypes.c_long(0),  # intensity cut-off mode
            ctypes.c_long(0),  # intensity cut-off value
            ctypes.c_long(0),  # max num of peaks
            ctypes.c_long(0),  # centroid result
            ctypes.c_double(0),  # centroid peak width
            mass_list_v,
            flags_v,
            size_l)
        
        if error:
            return None
        
        # get arrays
        mz_array = numpy.array(mass_list_v.value[0])
        ai_array = numpy.array(mass_list_v.value[1])
        
        # make profile
        profile = numpy.dstack((mz_array, ai_array))[0].copy()
        
        return profile
    
    
    def _retrieve_profile_centroids(self, scan_number, polarity):
        """Retrieves centroids from profile data."""
        
        # read labels
        labels_v = comtypes.automation.VARIANT()
        flags_v = comtypes.automation.VARIANT()
        scan_number_l = ctypes.c_long(scan_number)
        if self._raw_reader.GetLabelData(labels_v, flags_v, scan_number_l):
            return None
        
        # get arrays
        mz_array = numpy.array(labels_v.value[0])
        ai_array = numpy.array(labels_v.value[1])
        res_array = numpy.array(labels_v.value[2])
        base_array = numpy.array(labels_v.value[3])
        noise_array = numpy.array(labels_v.value[4])
        charge_array = numpy.array(labels_v.value[5])
        
        # create centroids
        centroids = []
        for i in range(len(mz_array)):
            
            ai = ai_array[i] if OLD_BASE else ai_array[i] + base_array[i]
            noise = noise_array[i] - base_array[i] if OLD_BASE else noise_array[i]
            charge = (charge_array[i] * polarity) if charge_array[i] else None
            fwhm = (mz_array[i] / res_array[i]) if res_array[i] else None
            
            centroid = Centroid(
                mz = mz_array[i],
                ai = ai,
                base = base_array[i],
                noise = noise,
                charge = charge,
                fwhm = fwhm)
            
            if centroid.intensity > 0.:
                centroids.append(centroid)
        
        return centroids
    
    
    def _retrieve_masslist_centroids(self, scan_number, polarity):
        """Retrieves centroids from centroided data."""
        
        # read masslist
        scan_number_l = ctypes.c_long(scan_number)
        mass_list_v = comtypes.automation.VARIANT()
        flags_v = comtypes.automation.VARIANT()
        size_l = ctypes.c_long()
        
        error = self._raw_reader.GetMassListFromScanNum(
            scan_number_l,
            comtypes.BSTR(''),  # filter
            ctypes.c_long(0),  # intensity cut-off mode
            ctypes.c_long(0),  # intensity cut-off value
            ctypes.c_long(0),  # max num of peaks
            ctypes.c_long(0),  # centroided result
            ctypes.c_double(0),  # centroid peak width
            mass_list_v,
            flags_v,
            size_l)
        
        if error:
            return None
        
        # get arrays
        mz_array = numpy.array(mass_list_v.value[0])
        ai_array = numpy.array(mass_list_v.value[1])
        
        # create centroids
        centroids = []
        for i in range(len(mz_array)):
            if ai_array[i] > 0:
                centroids.append(Centroid(mz_array[i], ai_array[i]))
        
        return centroids
    
    
    def _retrieve_acquisition_date(self):
        """Retrieves acquisition date value."""
        
        # get acquisition date
        acquisition_date_d = comtypes.c_double()
        if not self._raw_reader.GetCreationDate(acquisition_date_d):
            return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=acquisition_date_d.value)
        
        return None
    
    
    def _retrieve_instrument_name(self):
        """Retrieves instrument name value."""
        
        # get instrument name
        instrument_name_s = comtypes.BSTR()
        if not self._raw_reader.GetInstName(instrument_name_s):
            return instrument_name_s.value
        
        return None
    
    
    def _retrieve_instrument_model(self):
        """Retrieves instrument model value."""
        
        # get instrument model
        instrument_model_s = comtypes.BSTR()
        if not self._raw_reader.GetInstModel(instrument_model_s):
            return instrument_model_s.value
        
        return None
    
    
    def _retrieve_scan_filter(self, scan_number):
        """Retrieves scan filter string."""
        
        # get filter string
        filter_string_s = comtypes.BSTR()
        if self._raw_reader.GetFilterForScanNum(scan_number, filter_string_s):
            return None
        
        return filter_string_s.value
    
    
    def _retrieve_ms_level(self, scan_number):
        """Retrieves MS level value."""
        
        # get value directly
        ms_level_l = ctypes.c_long()
        if not self._raw_reader.GetMSOrderForScanNum(scan_number, ms_level_l):
            if ms_level_l.value > 0:
                return ms_level_l.value
        
        return None
    
    
    def _retrieve_mass_range(self, scan_number, index=0):
        """Retrieves mass range."""
        
        # init vars
        low_value_d = ctypes.c_double()
        high_value_d = ctypes.c_double()
        
        # get data
        error = self._raw_reader.GetMassRangeFromScanNum(
                scan_number,
                index,
                low_value_d,
                high_value_d)
        
        return low_value_d.value, high_value_d.value
    
    
    def _retrieve_mass_analyzer(self, scan_number):
        """Retrieves analyzer type value."""
        
        # get value directly
        mass_analyzer_l = ctypes.c_long()
        if not self._raw_reader.GetMassAnalyzerTypeForScanNum(scan_number, mass_analyzer_l):
            if mass_analyzer_l.value < len(ANALYZERS):
                return ANALYZERS[mass_analyzer_l.value]
            else:
                return 'Unknown'
        
        return None
    
    
    def _retrieve_polarity(self, scan_number):
        """Retrieves polarity value."""
        
        # get scan filter
        scan_filter = self._retrieve_scan_filter(scan_number)
        if scan_filter is None:
            return None
        
        # parse scan filter
        match = SCAN_FILTER_POLARITY_PATTERN.match(scan_filter)
        if not match:
            return None
        
        # get polarity value
        if match.group('polarity') == '+':
            return POSITIVE
        elif match.group('polarity') == '-':
            return NEGATIVE
        
        return None
    
    
    def _retrieve_resolution(self, scan_number):
        """Retrieves resolution value."""
        
        # get value from trailer
        for label in ('FT Resolution:', 'Orbitrap Resolution:', 'FT Resolution'):
            
            resolution_v = comtypes.automation.VARIANT()
            if not self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, label, resolution_v):
                if resolution_v.value:
                    return int(resolution_v.value)
        
        return None
    
    
    def _retrieve_precursor_info(self, scan_data):
        """Retrieves all precursor info."""
        
        # retrieve values
        scan_number = scan_data['scan_number']
        values_v = comtypes.automation.VARIANT()
        flags_v = comtypes.automation.VARIANT()
        size_l = ctypes.c_long()
        
        if self._raw_reader.GetAllMSOrderData(scan_number, values_v, flags_v, size_l):
            return
        
        # get values from last event
        values = values_v.value
        flags = flags_v.value
        last = size_l.value - 1
        
        scan_data["precursor_mz"] = values[0][last]
        scan_data["isolation_width"] = values[1][last]
        scan_data["activation_energy"] = values[2][last]
        scan_data["dissociation_method"] = DISSOCIATION_METHODS[flags[0][last]]
        
        # width is not valid
        if scan_data["isolation_width"] == 1.0:
            scan_data["isolation_width"] = None
        
        # range is valid
        if flags[1][last]:
            scan_data["precursor_low_mz"] = values[3][last]
            scan_data["precursor_high_mz"] = values[4][last]
            scan_data["isolation_offset"] = values[5][last]
    
    
    def _retrieve_precursor_mz(self, scan_number):
        """"Retrieves precursor m/z value."""
        
        # get value from trailer
        precursor_mass_v = comtypes.automation.VARIANT()
        if not self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, 'Monoisotopic M/Z:', precursor_mass_v):
            if precursor_mass_v.value:
                return float(precursor_mass_v.value)
        
        # get scan filter
        scan_filter = self._retrieve_scan_filter(scan_number)
        if scan_filter is None:
            return None
        
        # parse filter string
        matches = SCAN_FILTER_DISSOCIATION_PATTERN.findall(scan_filter)
        if matches:
            return float(matches[-1][1])
        
        return None
    
    
    def _retrieve_precursor_charge(self, scan_number):
        """Retrieves precursor charge value."""
        
        # get value from trailer
        precursor_charge_v = comtypes.automation.VARIANT()
        if not self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, 'Charge State:', precursor_charge_v):
            if precursor_charge_v.value and precursor_charge_v.value < 255:
                return int(precursor_charge_v.value)
        
        return None
    
    
    def _retrieve_precursor_range(self, scan_number, ms_level):
        """Retrieves precursor isolation range values."""
        
        # get value directly
        first_precursor_mass_d = ctypes.c_double()
        last_precursor_mass_d = ctypes.c_double()
        valid_l = ctypes.c_long()
        
        if not self._raw_reader.GetPrecursorRangeForScanNum(scan_number, ms_level, first_precursor_mass_d, last_precursor_mass_d, valid_l):
            if valid_l.value:
                return float(first_precursor_mass_d.value), float(last_precursor_mass_d.value)
        
        return None
    
    
    def _retrieve_isolation_width(self, scan_number, ms_level):
        """Retrieves precursor isolation width value."""
        
        # get value from trailer
        label = "MS%d Isolation Width:" % ms_level
        isolation_width_v = comtypes.automation.VARIANT()
        if not self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, label, isolation_width_v):
            if isolation_width_v.value:
                return float(isolation_width_v.value)
        
        return None
    
    
    def _retrieve_activation_energy(self, scan_number, method):
        """"Retrieves activation energy value."""
        
        # get value from trailer
        label = "%s Energy eV:" % method
        activation_energy_v = comtypes.automation.VARIANT()
        if not self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, label, activation_energy_v):
            if activation_energy_v.value:
                return float(activation_energy_v.value)
        
        # get filter string
        filter_string_s = comtypes.BSTR()
        if self._raw_reader.GetFilterForScanNum(scan_number, filter_string_s):
            return None
        
        # parse filter string
        matches = SCAN_FILTER_DISSOCIATION_PATTERN.findall(filter_string_s.value)
        if matches:
            return float(matches[-1][3])
        
        return None
    
    
    def _retrieve_activation_energies(self, scan_number, method):
        """"Retrieves activation energies values."""
        
        # get all step energies from trailer
        label = "%s Energy:" % method
        activation_energies_v = comtypes.automation.VARIANT()
        if self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, label, activation_energies_v):
            return None
        
        # check values
        raw_value = activation_energies_v.value
        if not raw_value:
            return None
        
        # check if instrument method needed
        if '...' in raw_value and self._inst_methods:
            for match in STEPPED_ENERGIES.findall("; ".join(self._inst_methods)):
                if match[0] == method:
                    raw_value = match[1]
                    break
        
        # split and parse values
        values = raw_value.split(",")
        try:
            return tuple(float(x) for x in values)
        except ValueError:
            return None
    
    
    def _retrieve_scan_event_index(self, scan_number):
        """Retrieves scan event index."""
        
        # get value from trailer
        index_v = comtypes.automation.VARIANT()
        if not self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, 'Scan Event:', index_v):
            return int(index_v.value)
        
        return None
    
    
    def _retrieve_scan_cycle(self, scan_number):
        """Retrieves scan cycle."""
        
        # get value
        cycle_l = ctypes.c_long()
        if not self._raw_reader.GetCycleNumberFromScanNumber(scan_number, cycle_l):
            return int(cycle_l.value)
        
        return None
    
    
    def _retrieve_master_scan_event_index(self, scan_number):
        """Retrieves master scan event index."""
        
        # get value from trailer
        index_v = comtypes.automation.VARIANT()
        if not self._raw_reader.GetTrailerExtraValueForScanNum(scan_number, 'Master Index:', index_v):
            return int(index_v.value)
        
        return None
    
    
    def _retrieve_instrument_methods(self):
        """Retrieves instrument method values."""
        
        self._inst_methods = []
        
        # get methods count
        channels_l = ctypes.c_long()
        if self._raw_reader.GetNumInstMethods(channels_l):
            return
        
        # retrieve methods
        for channel in range(channels_l.value):
            
            # get data
            method_s = comtypes.BSTR()
            if self._raw_reader.GetInstMethod(channel, method_s):
                continue
            
            # store
            self._inst_methods.append(method_s.value)
    
    
    def _retrieve_extra_values(self, scan_data):
        """Retrieves all available trailer extra values for scan."""
        
        # get scan info
        scan_number = scan_data['scan_number']
        
        # retrieve values
        labels_v = comtypes.automation.VARIANT()
        values_v = comtypes.automation.VARIANT()
        size_l = ctypes.c_long()
        if self._raw_reader.GetTrailerExtraForScanNum(scan_number, labels_v, values_v, size_l):
            return
        
        # set values
        labels = labels_v.value
        values = values_v.value
        for i in range(size_l.value):
            scan_data['extra_values'][labels[i]] = values[i]
    
    
    def _retrieve_status_log(self, scan_data):
        """Retrieves all available status log values for scan."""
        
        # get scan info
        scan_number = scan_data['scan_number']
        
        # retrieve values
        rt_d = ctypes.c_double()
        labels_v = comtypes.automation.VARIANT()
        values_v = comtypes.automation.VARIANT()
        size_l = ctypes.c_long()
        if self._raw_reader.GetStatusLogForScanNum(scan_number, rt_d, labels_v, values_v, size_l):
            return
        
        # set values
        labels = labels_v.value
        values = values_v.value
        for i in range(size_l.value):
            scan_data['status_log'][labels[i]] = values[i]
