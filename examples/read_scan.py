#  Created by Martin Strohalm

# import module
import msread

# init path
path = r"sample.raw"

# init reader
with msread.read(path) as reader:
    
    scan = reader.scan(1000)
    print(scan)
    print(scan.centroids)
