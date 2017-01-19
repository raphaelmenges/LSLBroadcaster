# Import modules
from pylsl.pylsl import StreamInfo, StreamOutlet, local_clock
import xdf.xdf as xdf
import collections
import time
import sys

# Python sender example
'''
# first create a new stream info (here we set the name to BioSemi,
# the content-type to EEG, 8 channels, 100 Hz, and float-valued data) The
# last value would be the serial number of the device or some other more or
# less locally unique identifier for the stream as far as available (you
# could also omit it but interrupted connections wouldn't auto-recover).
info = StreamInfo('BioSemi', 'EEG', 8, 100, 'float32', 'myuid2424')

# append some meta-data
info.desc().append_child_value("manufacturer", "BioSemi")
channels = info.desc().append_child("channels")
for c in ["C3", "C4", "Cz", "FPz", "POz", "CPz", "O1", "O2"]:
    channels.append_child("channel") \
        .append_child_value("label", c) \
        .append_child_value("unit", "microvolts") \
        .append_child_value("type", "EEG")

# next make an outlet; we set the transmission chunk size to 32 samples and
# the outgoing buffer size to 360 seconds (max.)
outlet = StreamOutlet(info, 32, 360)

print("now sending data...")
while True:
    # make a new random 8-channel sample; this is converted into a
    # pylsl.vectorf (the data type that is expected by push_sample)
    mysample = [rand(), rand(), rand(), rand(), rand(), rand(), rand(), rand()]
    # get a time stamp in seconds (we pretend that our samples are actually
    # 125ms old, e.g., as if coming from some external hardware)
    stamp = local_clock()-0.125
    # now send it and wait for a bit
    outlet.push_sample(mysample, stamp)
    time.sleep(0.01)
'''

# Load file
streams = xdf.load_xdf(r"SampleData.xdf", None, False)[0]

###############################################################################
### CREATE STREAMS WITH INFO HEADERS
###############################################################################

# List for stream outlets
outlets = []

# Go over streams
for i in range(len(streams)):
    
    # Fetch stream info
    streamInfo = streams[i]['info']
    print("--- STREAM FOUND ---")
    
    # Extract info
    name        = streamInfo['name'][0]
    dataType    = streamInfo['type'][0]
    cannelCount = streamInfo['channel_count'][0]
    dataRate    = streamInfo['nominal_srate'][0]
    dataFormat  = streamInfo['channel_format'][0]
    identifier  = streamInfo['source_id'][0]
    
    # Print resuls
    print("Name: "          + name)
    print("Data Type: "     + dataType)
    print("Channel Count: " + cannelCount)
    print("Data Rate: "     + dataRate)
    print("Data Format: "   + dataFormat)
    print("Identifier: "    + identifier)
    
    # Create new info header
    info = StreamInfo(name, dataType, int(cannelCount), int(dataRate), dataFormat, identifier)
    
    # Announce extraction of child values
    print("Child Values:")
    
     # Extract child values
    children = streamInfo['desc'][0]
    
    # Go over values
    for childKey in children:
        
        # Fetch value by key
        childValue = children[childKey][0]
        
        # Is value a sequence ("append_child_value")
        if(isinstance(childValue, collections.Sequence)):
            print("   " + childKey + ": " + childValue)
            info.desc().append_child_value(childKey, childValue)
            
        # Is value a mapping ("append_child")
        elif(isinstance(childValue, collections.Mapping)):
            print("   " + childKey)
            child = info.desc().append_child(childKey)
            
            # Go over entries within child
            for innerChildKey in childValue:
                print("   " + "   " + innerChildKey)
                child.append_child(innerChildKey)
                
                # Now go over even more inner child
                for innererChild in childValue[innerChildKey]:
                    
                    # Now go over innermost child
                    for innermostChild in innererChild:
                        print("   " + "   " + "   " + innermostChild + ": " + innererChild[innermostChild][0])
                        child.append_child_value(innermostChild, innererChild[innermostChild][0])
                        
    # Add outlet with information
    outlets.append(StreamOutlet(info, 32, 360)) # chunk size and buffer for given seconds
    
    print("--------------------")

###############################################################################
### PREPARE STREAMING BY MERGING TIMESTAMPS
###############################################################################

# List to collect timestamps with meta information
events = []

# Save timestamps with pointer to outlet and data
for i in range(len(streams)):
    
    # Fetch timestamps
    timeStamps = streams[i]['time_stamps']
    
    # Go through timestamps and store tripple to global list of timestamps
    for j in range(len(timeStamps)):
        events.append([timeStamps[j], i, j]) # timeStamp, outletIndex / streamIndex, index of time_series
        
# Sort global timestamps after timestamps
def comparator(x, y):
    if x[0] < y[0]:
        return -1 # x smaller than y
    elif x[0] > y[0]:
        return 1 # x greater than y
    else:
        return 0 # x equal to y
events.sort(comparator)

###############################################################################
### SEND DATA
###############################################################################

# Initial waiting time
print("--- ABOUT TO START STREAMING ---")
for i in range(10, 0, -1):
    
    # Wait one second
    print(str(i))
    sys.stdout.flush()
    time.sleep(1)

# Do it while there are events
print("--- START STREAMING ---")
eventCount = len(events)
eventStartTime = events[0][0]
startTime = time.time()
i = 0
while i < eventCount:
    
    # Store current time
    currentTime = time.time()
    
    # Check whether time until next event is over
    event = events[i]
    timestamp = event[0]
    if (currentTime - startTime) > (timestamp - eventStartTime):
        
        # Extract further data from current event
        outletIndex = event[1]
        timeSeriesIndex = event[2]
    
        # Get sample data to push
        sampleData = streams[outletIndex]['time_series'][timeSeriesIndex]
        
        # Push sample data to outlet
        outlets[outletIndex].push_sample(sampleData) # TODO: stamp from hardware
    
        # Print timestamp
        print("Sample at: " + str(timestamp))
            
        # Increment i
        i = i+1
        
print("-----------------------")