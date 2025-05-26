#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.


class ScanHeader(object):
    """
    ScanHeader encapsulates all the mass spectrum metadata.
    
    Attributes:
        
        scan_number: int or None
            Unique spectrum number.
        
        parent_scan_number: int or None
            Scan number of the parent spectrum.
        
        acquisition_date: datetime or None
            Acquisition date.
        
        instrument_name: str or None
            Instrument name.
        
        instrument_model: str or None
            Instrument model.
        
        title: str or None
            Custom spectrum title.
        
        ms_level: int or None
            MS level (order).
        
        polarity: int or None
            Spectrum polarity as msread.POSITIVE or msread.NEGATIVE.
        
        spectrum_type: str or None
            Type of spectrum data points.
                msread.CENTROIDS - centroided spectrum
                msread.PROFILE - profile spectrum
        
        mass_analyzer: str or None
            Type of mass analyzer used.
        
        ionization_source: str or None
            Type of ionization source used.
        
        resolution: int or None
            Instrument resolution.
        
        retention_time: float or None
            Retention time in seconds.
        
        low_mz: float or None
            Lower mass limit of data acquisition.
        
        high_mz: float or None
            Higher mass limit of data acquisition.
        
        points_count: int or None
            Number of data points.
        
        tic: float or None
            Total ion current.
        
        basepeak_mz: float or None
            Mass-to-charge ratio of the most intense peak.
        
        basepeak_intensity: float or None
            Intensity of the most intense peak.
        
        precursor_mz: float or None
            Precursor m/z.
        
        precursor_intensity: float or None
            Precursor intensity.
        
        precursor_charge: int or None
            Precursor charge state.
        
        precursor_low_mz: float or None
            Lower limit of precursor window.
        
        precursor_high_mz: float or None
            Higher limit of precursor window.
        
        dissociation_method: str or None
            Dissociation method used for fragmentation.
        
        activation_energy: float or None
            Energy used for fragmentation.
        
        activation_energies: (float,) or None
            Step energies used for fragmentation.
        
        custom_data: ?
            Arbitrary custom data.
    """
    
    
    def __init__(self, attributes={}, **attrs):
        """Initializes a new instance of msread.ScanHeader."""
        
        self.scan_number = None
        self.parent_scan_number = None
        
        self.acquisition_date = None
        self.instrument_name = None
        self.instrument_model = None
        
        self.title = ''
        self.ms_level = None
        self.polarity = None
        self.spectrum_type = None
        self.mass_analyzer = None
        self.ionization_source = None
        self.resolution = None
        
        self.retention_time = None
        self.low_mz = None
        self.high_mz = None
        self.points_count = None
        self.tic = None
        self.basepeak_mz = None
        self.basepeak_intensity = None
        
        self.precursor_mz = None
        self.precursor_intensity = None
        self.precursor_charge = None
        self.precursor_low_mz = None
        self.precursor_high_mz = None
        self.dissociation_method = None
        self.activation_energy = None
        self.activation_energies = None
        
        self.custom_data = None
        
        # combine attributes
        attributes = dict(attributes, **attrs)
        
        # assign known attributes
        for name, value in attributes.items():
            if hasattr(self, name):
                setattr(self, name, value)
            else:
                message = "ScanHeader attribute not found! -> '%s'" % name
                raise AttributeError(message)
    
    
    def __str__(self):
        """Gets standard string representation."""
        
        label = "#%s" % self.scan_number
        
        label += " MS%s" % (self.ms_level if self.ms_level is not None else '?')
        if self.parent_scan_number is not None:
            label += "-#%s" % self.parent_scan_number
            
        if self.mass_analyzer is not None:
            label += " %s" % self.mass_analyzer
        
        if self.polarity == 1:
            label += " (+)"
        elif self.polarity == -1:
            label += " (-)"
        
        if self.retention_time is not None:
            label += " RT:%.3f min" % (self.retention_time / 60)
        
        if self.resolution is not None:
            label += " R:%d" % self.resolution
        
        if self.dissociation_method is not None:
            label += " %s" % self.dissociation_method
            
            if self.activation_energy is not None:
                label += ":%.2f" % self.activation_energy
            
        if self.precursor_mz is not None:
            label += " P:%.6f" % self.precursor_mz
            
            if self.precursor_charge is not None:
                label += " (%+d)" % self.precursor_charge
            
            if self.precursor_low_mz is not None and self.precursor_high_mz is not None:
                label += " [%.6f-%.6f]" % (self.precursor_low_mz, self.precursor_high_mz)
            
        return label
    
    
    def __ne__(self, other):
        """Not equal operator."""
        
        return not self.__eq__(other)
    
    
    def __repr__(self):
        """Gets debug string representation."""
        
        return "%s(%s)" % (self.__class__.__name__, self.__str__())
    
    
    def __eq__(self, other):
        """Equal operator."""
        
        if self is other:
            return True
        
        if not isinstance(other, ScanHeader):
            return False
        
        return (self.scan_number == other.scan_number
                and self.parent_scan_number == other.parent_scan_number
                and self.acquisition_date == other.acquisition_date
                and self.instrument_name == other.instrument_name
                and self.instrument_model == other.instrument_model
                and self.title == other.title
                and self.ms_level == other.ms_level
                and self.polarity == other.polarity
                and self.spectrum_type == other.spectrum_type
                and self.mass_analyzer == other.mass_analyzer
                and self.ionization_source == other.ionization_source
                and self.resolution == other.resolution
                and self.retention_time == other.retention_time
                and self.low_mz == other.low_mz
                and self.high_mz == other.high_mz
                and self.points_count == other.points_count
                and self.tic == other.tic
                and self.basepeak_mz == other.basepeak_mz
                and self.basepeak_intensity == other.basepeak_intensity
                and self.precursor_mz == other.precursor_mz
                and self.precursor_intensity == other.precursor_intensity
                and self.precursor_charge == other.precursor_charge
                and self.precursor_low_mz == other.precursor_low_mz
                and self.precursor_high_mz == other.precursor_high_mz
                and self.dissociation_method == other.dissociation_method
                and self.activation_energy == other.activation_energy
                and self.activation_energies == other.activation_energies)
