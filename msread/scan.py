#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# import modules
import numpy
from .masslist import Masslist
from .header import ScanHeader


class Scan(object):
    """
    Scan represents a single mass spectrum either profile or centroided or
    containing both.
    
    Attributes:
        
        header: msread.ScanHeader
            All the spectrum metadata.
        
        profile: numpy.ndarray
            Profile signal as a 2D array of m/z and intensity points.
        
        centroids: msread.Masslist
            Collection of mass centroids.
    """
    
    
    def __init__(self, profile=None, centroids=None, header=None):
        """
        Initializes a new instance of msread.Scan.
        
        Args:
            
            profile: ((float, float),) or None
                Continuous profile points specified as (m/z, ai) pairs.
            
            centroids: (msread.Centroid,) or None
                Collection of mass centroids.
            
            header: msread.ScanHeader or None
                Spectrum metadata.
        """
        
        # check profile
        profile = profile if profile is not None else []
        if not isinstance(profile, numpy.ndarray):
            profile = numpy.array(profile, dtype='float64')
        
        # check centroids
        centroids = centroids if centroids is not None else []
        if not isinstance(centroids, Masslist):
            centroids = Masslist(centroids)
        
        # check header
        header = header if header is not None else {}
        if not isinstance(header, ScanHeader):
            header = ScanHeader(header)
        
        self._profile = profile
        self._centroids = centroids
        self._header = header
    
    
    def __str__(self):
        """Gets standard string representation."""
        
        return str(self.header)
    
    
    def __repr__(self):
        """Gets debug string representation."""
        
        return "%s(%s)" % (self.__class__.__name__, self.__str__())
    
    
    @property
    def header(self):
        """
        Gets spectrum header.
        
        Returns:
            msread.ScanHeader
                All the spectrum metadata.
        """
        
        return self._header
    
    
    @property
    def profile(self):
        """
        Gets profile points.
        
        Returns:
            numpy.ndarray
                Profile signal as a 2D array of m/z and intensity points.
        """
        
        return self._profile
    
    
    @profile.setter
    def profile(self, value):
        """
        Sets profile points.
        
        Args:
            ((float, float),) or None
                Continuous profile points specified as (m/z, ai) pairs.
        """
        
        # check value
        if value is None:
            value = []
        
        # check type
        if not isinstance(value, numpy.ndarray):
            value = numpy.array(value, dtype='float64')
        
        # set profile
        self._profile = value
    
    
    @property
    def centroids(self):
        """
        Gets mass centroids.
        
        Returns:
            msread.Masslist
                Collection of mass centroids.
        """
        
        return self._centroids
    
    
    @centroids.setter
    def centroids(self, value):
        """
        Sets mass centroids.
        
        Args:
            (msread.Centroid,) or None
                Collection of mass centroids.
        """
        
        # check value
        if value is None:
            value = []
        
        # check centroids
        if not isinstance(value, Masslist):
            value = Masslist(value)
        
        # set centroids
        self._centroids = value
    
    
    def has_profile(self):
        """Returns True if scan has any profile data."""
        
        return bool(len(self._profile))
    
    
    def has_centroids(self):
        """Returns True if scan has any centroid."""
        
        return bool(len(self._centroids))
