#  Created by Martin Strohalm

# import module
import msread

# init path
path = r"sample.raw"

# init reader
with msread.open(path) as reader:
    
    scan = reader.scan(1000)
    print(scan)
    print(scan.centroids)
