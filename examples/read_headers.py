#  Created by Martin Strohalm

# import module
import msread

# init path
path = r"sample.raw"

# init reader
with msread.open(path) as reader:
    
    # read headers in RT range
    for header in reader.headers(min_rt=2*60, max_rt=3*60, polarity=1):
        print(header)
