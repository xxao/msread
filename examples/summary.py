#  Created by Martin Strohalm

# import module
import msread

# init path
path = r"sample.raw"

# open file
with msread.read(path) as reader:
    
    # show summary
    reader.summary(show=True)
    
    # read headers only
    for header in reader.headers(min_rt=5.0*60, max_rt=5.1*60, ms_level=1):
        print(header)
    
    # read scans
    for scan in reader.scans(min_rt=5.0*60, max_rt=5.1*60, ms_level=1):
        print(scan.header)
        print(max(scan.centroids, key=lambda d: d.mz))
