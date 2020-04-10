MSRead
======

The MSRead module enables a simple reading of popular Mass Spectrometry data
formats including: mzData, mzXML, mzML, MGF, ASCII XY and Thermo Raw files.

.. code:: python
    
    import msread
    
    # open file
    with msread.read("myfile.mzML") as reader:
        
        # show summary
        reader.summary(show=True)
        
        # read headers only
        for header in reader.headers(min_rt=5*60, max_rt=10*60, ms_level=1):
            print(header)
        
        # read scans
        for scan in reader.scans(min_rt=5*60, max_rt=10*60, ms_level=1):
            print(scan.header)
            print(scan.centroids)


Requirements:
-------------

- Python 3.7
- Numpy
- [comtypes] (To read Thermo Raw files. Windows only.)
- [MSFileReader] (To read Thermo Raw files. Windows only.)


Install from source:
--------------------

$ python setup.py install

or

$ pip install .


Reading Thermo Raw files:
-------------------------

To enable Thermo Raw files reading you need to download and install the
MSFileReader by creating an account at:

https://thermo.flexnetoperations.com/control/thmo/login

then logging in and choosing "Utility Software". Current version is developed
using MSFileReader v3.1 SP2.


Disclaimer:
-----------

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.

For Research Use Only. Not for use in diagnostic procedures.
