#  Created by Martin Strohalm
#  Copyright (c) Martin Strohalm. All rights reserved.

# import modules
from .centroid import Centroid


class Masslist(object):
    """
    Masslist represents a container for mass centroids. It provides essential
    functionality to add new centroids and ensures that all the centroids are
    automatically sorted by m/z value.
    """
    
    
    def __init__(self, centroids=None):
        """
        Initializes a new instance of msread.Masslist.
        
        Args:
            centroids: (msread.Centroid,) or ((float, float),)
                Collection of mass centroids.
        """
        
        self._centroids = []
        
        # check centroids
        if centroids:
            self._centroids = [self._parse_centroid(x) for x in centroids]
            self._centroids.sort(key=lambda x: x.mz)
    
    
    def __str__(self):
        """Gets standard string representation."""
        
        centroids = ""
        for centroid in self._centroids:
            centroids += "\t%s\n" % centroid
            
        return "[\n%s]" % centroids
    
    
    def __repr__(self):
        """Gets debug string representation."""
        
        return "%s(%s)" % (self.__class__.__name__, self.__str__())
    
    
    def __eq__(self, other):
        """Equal operator."""
        
        if self is other:
            return True
        
        if not isinstance(other, Masslist):
            return False
        
        if len(self) != len(other):
            return False
        
        for i in range(len(self)):
            if self[i] != other[i]:
                return False
        
        return True
    
    
    def __ne__(self, other):
        """Not equal operator."""
        
        return not self.__eq__(other)
    
    
    def __len__(self):
        """Gets number of centroids."""
        
        return len(self._centroids)
    
    
    def __iter__(self):
        """Gets iterator."""
        
        return self._centroids.__iter__()
    
    
    def __getitem__(self, i):
        """Gets mass centroid at index."""
        
        return self._centroids[i]
    
    
    def __delitem__(self, i):
        """Deletes mass centroid at index."""
        
        del self._centroids[i]
    
    
    def add(self, centroid):
        """
        Adds given mass centroid into masslist.
        
        Args:
            msread.Centroid or (float, float)
                Centroid to be added into masslist.
        """
        
        # parse centroid
        centroid = self._parse_centroid(centroid)
        
        # append centroid
        self._centroids.append(centroid)
        
        # sort
        self.sort()
    
    
    def sort(self):
        """Sorts entire mass list by increasing m/z."""
        
        self._centroids.sort(key=lambda x: x.mz)
        
    
    def basepeak(self):
        """
        Gets the most intense centroid.
        
        Returns:
            msread.Centroid
                The basepeak centroid.
        """
        
        if not self._centroids:
            return None
        
        return max(self._centroids, key=lambda c: c.intensity)
    
    
    def tic(self):
        """
        Gets the summed intensity of all centroids.
        
        Returns:
            float
                Summed intensity.
        """
        
        return sum(x.intensity for x in self._centroids)
    
    
    def clone(self):
        """
        Makes a clone of current Masslist instance. For each centroid a new
        cloned instance is created as well.
        
        Returns:
            msread.Masslist
                Clone of current masslist.
        """
        
        centroids = [c.clone() for c in self._centroids]
        return Masslist(centroids)
    
    
    def _parse_centroid(self, item):
        """Checks item to be a valid Centroid."""
        
        if isinstance(item, Centroid):
            return item
        
        elif type(item) in (list, tuple) and len(item) == 2:
            return Centroid(mz=float(item[0]), ai=float(item[1]))
        
        else:
            message = "Each mass centroid must be of type msread.Centroid or list/tuple of two floats! -> '%s'" % type(item)
            raise TypeError(message)
