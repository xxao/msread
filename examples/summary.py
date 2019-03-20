#  Created by Martin Strohalm

# import module
import msread

# init path
path = r"sample.raw"

import msread

# open file
with msread.open(path) as reader:
    
    # show summary
    reader.summary(show=True)
    
    # read headers only
    for header in reader.headers(min_rt=5*60, max_rt=10*60, ms_level=1):
        print(header)
    
    # read scans
    for scan in reader.scans(min_rt=5*60, max_rt=10*60, ms_level=1):
        print(scan.header)
        print(scan.centroids)