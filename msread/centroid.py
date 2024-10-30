#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.


class Centroid(object):
    """
    Centroid represents a label of a mass spectrum peak.
    
    Attributes:
        
        mz: float
            Mass-to-charge value.
        
        ai: float
            Acquired intensity without baseline correction.
        
        base: float
            Intensity of a baseline.
        
        intensity: float (read-only)
            Acquired intensity with baseline correction applied.
        
        noise: float or None
            Noise band width.
        
        sn: float or None (read-only)
            Signal-to-noise value. Set to None if noise value is not available.
        
        area: float
            Peak area.
        
        fwhm: float or None
            Full-width-at-half-maximum. Peak width in its half-height after
            baseline correction.
        
        resolution: float or None (read-only)
            Peak resolution. Set to None if fwhm value is not set.
        
        charge: int or None
            Assigned charge state (including polarity sign).
        
        custom_data: ?
            Arbitrary custom data.
    """
    
    
    def __init__(self, mz, ai, base=.0, noise=None, area=None, fwhm=None, charge=None, custom_data=None):
        """
        Initializes a new instance of msread.Centroid.
        
        Args:
        
            mz: float
                Mass-to-charge value.
            
            ai: float
                Acquired intensity without baseline correction.
            
            base: float
                Intensity of a baseline.
            
            noise: float or None
                Noise band width.
            
            area: float
                Peak area.
            
            fwhm: float or None
                Full-width-at-half-maximum. Peak width in its half-height after
                baseline correction.
        
            charge: int or None
                Assigned charge state (including polarity sign).
            
            custom_data: ?
                Arbitrary custom data.
        """
        
        self.mz = float(mz)
        self.ai = float(ai)
        self.base = float(base)
        self.noise = float(noise) if noise is not None else None
        self.area = float(area) if area is not None else None
        self.fwhm = float(fwhm) if fwhm is not None else None
        self.charge = int(charge) if charge is not None else None
        
        self.custom_data = custom_data
    
    
    def __str__(self):
        """Gets standard string representation."""
        
        data =  "mz:%f ai:%f" % (self.mz, self.ai)
        
        if self.base:
            data += " int:%f" % self.intensity
            data += " base:%f" % self.base
        
        if self.sn is not None:
            data += " s/n:%f" % self.sn
        
        if self.charge is not None:
            data += " z:%+d" % self.charge
        
        if self.fwhm is not None:
            data += " fwhm:%f" % self.fwhm
            data += " res:%d" % self.resolution
        
        return data
    
    
    def __repr__(self):
        """Gets debug string representation."""
        
        return "%s(%s)" % (self.__class__.__name__, self.__str__())
    
    
    def __eq__(self, other):
        """Equal operator."""
        
        if self is other:
            return True
        
        if not isinstance(other, Centroid):
            return False
        
        return (self.mz == other.mz
            and self.ai == other.ai
            and self.base == other.base
            and self.noise == other.noise
            and self.area == other.area
            and self.fwhm == other.fwhm
            and self.charge == other.charge)
    
    
    def __ne__(self, other):
        """Not equal operator."""
        
        return not self.__eq__(other)
    
    
    @property
    def intensity(self):
        """
        Gets baseline-corrected intensity.
        
        Returns:
            float
                Acquired intensity corrected by baseline.
        """
        
        return self.ai - self.base
    
    
    @property
    def sn(self):
        """
        Gets signal-to-noise ratio.
        
        Returns:
            float or None
                Signal-to-noise value calculated from the baseline-corrected
                intensity and noise value. Returns None if the noise value is
                not set.
        """
        
        if not self.noise:
            return None
        
        return (self.ai - self.base) / self.noise
    
    
    @property
    def resolution(self):
        """
        Gets peak resolution.
        
        Returns:
            float or None
                Peak resolution calculated from fwhm value. Returns None if the
                fwhm value is not set.
        """
        
        if not self.fwhm:
            return None
        
        return self.mz / self.fwhm
    
    
    def clone(self):
        """
        Makes a clone of current Centroid instance.
        
        Returns:
            msread.Centroid
                Clone of current centroid.
        """
        
        return Centroid(
            mz = self.mz,
            ai = self.ai,
            base = self.base,
            noise = self.noise,
            area = self.area,
            fwhm = self.fwhm,
            charge = self.charge,
            custom_data = self.custom_data)
