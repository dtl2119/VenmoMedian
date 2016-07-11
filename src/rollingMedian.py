#!/usr/bin/python

import sys
from datetime import datetime, time
from bisect import bisect
import json


def getMedian(lst):
    """
    Get median of sorted list of numbers.  Result should have exactly
    2 digits after the decimal place (truncate if more than 2)
    Examples: 1 --> 1.00, 2.0 --> 2.00, 3.678 --> 3.67
    """
    length = len(lst)
    mid = length / 2
    if length % 2 == 0:
        median = (lst[mid] + lst[mid - 1]) / 2.0
    else:
        median = lst[mid]
    
   # Result should always have two digits after decimal place 
    median = str(median)
    if '.' not in median:
        median += '.00'
    afterDec = len(median[median.index('.')+1:]) # Digits after decimal
    if afterDec == 1:
        median += '0'
    elif afterDec > 2:
        median = median[:median.index('.')+3]

    return median
    

def cleanTime(raw_str):
    """
    Convert raw time format of the 'created_time' field
    from the input JSON message to a Unix Timestamp
    
    Example: 2016-04-07T03:33:19Z --> 1459999999
    """
    dt = datetime.strptime(raw_str, "%Y-%m-%dT%H:%M:%SZ")
    # Get unix timestamp UTC in seconds since Epoch (1/1/1970)
    timestamp = (dt - datetime(1970, 1, 1)).total_seconds()
    return int(timestamp)


def writeToOutput(output_file, text):
    """
    Append text (the median) to the given output file
    """
    with open(output_file, "a") as output:
        output.write(text + "\n")
        #print text #FIXME


def rollingMedian(inFile, outFile):

    # Ovewrite output file
    open(outFile, "w").close()

    degrees = {}
    degreeList = []
    times = {} # timestamp: [(edge1), (edge2), ... ]
    edges = {} # (edge): timestamp
    windowMin = 0
    windowMax = 0
    median = 0.00

    with open(inFile) as f:
        for line in f:
            edgeAdded = True # Track because if False, median remains same #FIXME
            try:
                created, target, actor = json.loads(line).values()
                if not (created and target and actor):
                    raise ValueError("Missing Field")
            except ValueError as e:
                # Completely ignore line and continue if missing
                # Field or unable to parse json line (Extra data)
                continue
            created = cleanTime(created) # Convert to unix timestamp

            # Undirected graph: order doesn't matter so alphabetize edge
            edge = (actor, target) if actor < target else (target, actor)

            # If payment out-of-order and outside window,
            # ignore it, put print the previous median
            if created < windowMin:
                writeToOutput(outFile, median)
                continue

            # Only add edge if two nodes aren't already connected
            if edge not in edges:
                # setdefault: append value if key exists, else create list and add
                times.setdefault(created,[]).append(edge)
                edges[edge] = created
                for name in edge:
                    # If name/node doesn't exist, set to 0 before incrementing
                    degrees.setdefault(name,0)
                    degrees[name] += 1
#                    if name not in degrees: #FIXME remove this if/else
#                        degrees[name] = 1
#                    else:
#                        degrees[name] += 1
            else:
                edgeAdded = False
                # Update timestamp of existing edge
                oldTime = edges[edge]
                times[oldTime].remove(edge)
                times.setdefault(created,[]).append(edge)
                edges[edge] = created


            # If incoming payment is oldest, adjust time window
            # and prune/evict edges outside window
            if created > windowMax:
                windowMax = created
                windowMin = created - 60

                allTimestamps = times.keys()
                for time in allTimestamps:
                    if time < windowMin:
                        # Evict all edges with this timestamp
                        for e in times[time]:
                            for name in e:
                                degrees[name] -= 1
                                if degrees[name] == 0:
                                    del degrees[name]
                            del edges[e]
                        del times[time]
          
            
            # If no edge added, median same as last time
            # FIXME? What about evicted too..
#            if edgeAdded:
#                d0 = degrees[edge[0]]
#                d1 = degrees[edge[1]]
#                if (d0 > median and d1 > median) or (d0 < median and d1 < median):
#                    median = getMedian(sorted(degrees.values()))
                   
            median = getMedian(sorted(degrees.values()))
            writeToOutput(outFile, median)



if __name__ == '__main__':
    start = datetime.now() #FIXME
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    rollingMedian(input_path, output_path)
    print datetime.now() - start


#NOTES
# Don't forget try/except for opening input
# Make sure min/max windows and conditionals are exclusive (59 vs 60s)
# Clearing output.txt line (as of now, clears if it exists, creates if it doesn't)
# datetime times for 1832/1792 (data-gen) input lines: 
# 0.205093, 0.200994, 0.207007, 0.207117, 0.206432, 0.210309, 0.211183s
# Consider adding degreeList
