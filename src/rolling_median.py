#!/usr/bin/python

import sys
from datetime import datetime, time
import json


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
    afterDec = len(median[median.index('.')+1:])  # Digits after decimal
    if afterDec == 1:
        median += '0'
    elif afterDec > 2:
        median = median[:median.index('.')+3]

    return median
    

def getLast(sortedList, item):
    """
    Get index of last occurring item in a sorted list
    Example: getLast([5,5,2,2,2,1], 2) --> 4
    """
    i = len(sortedList) - 1  # Start from end
    while i > 0:
        if sortedList[i] == item:
            break
        i -= 1
    return i


def writeToOutput(output_file, text):
    """
    Append text (the median) to the given output file
    """
    with open(output_file, "a") as output:
        output.write(text + "\n")


def rollingMedian(inFile, outFile):

    edges = {}  # (node1, node2): timestamp
    times = {}  # timestamp: [(edge1), (edge2), ... ]
    degrees = {}  # node: # of degrees
    degreeList = []  # maintain list in reverse sorted order
    windowMin = 0
    windowMax = 0
    median = 0.00

    with open(inFile) as inF, open(outFile, "w") as outF:
        for line in inF:
            try:
                created, target, actor = json.loads(line).values()
                if not (created and target and actor):
                    raise ValueError("Missing Field")
            except ValueError as e:
                # Ignore line and continue if missing field
                # or unable to parse json line (Extra data)
                continue
            created = cleanTime(created)  # Convert to unix timestamp

            # Undirected graph: order doesn't matter so alphabetize edge
            edge = (actor, target) if actor < target else (target, actor)

            # If payment out-of-order and outside window,
            # ignore it, but print the previous median
            if created < windowMin:
                outF.write(median+"\n")
                #writeToOutput(outFile, median)  # Uncomment to append to file
                continue

            # Add edge if two nodes aren't already connected
            if edge not in edges:
                # setdefault: if key doesn't exist, create list then append
                times.setdefault(created, []).append(edge)
                edges[edge] = created
                for name in edge:
                    if name not in degrees:
                        degrees[name] = 1
                        degreeList.append(1)  # Reverse sorted, put 1 at end
                    else:
                        # If node/user exists, find # of degrees user has
                        # then find 1st occurrence of that # in reverse sorted
                        # degreeList and increment, keeping it sorted
                        i = degreeList.index(degrees[name])
                        degreeList[i] += 1
                        degrees[name] += 1
            else:
                # Nodes already connected, don't add a new edge
                # but update timestamp if later than previous
                oldTime = edges[edge]
                if created > oldTime:
                    times[oldTime].remove(edge)
                    times.setdefault(created, []).append(edge)
                    edges[edge] = created

            # If incoming payment is oldest, adjust time window
            # and prune/evict edges outside window
            if created > windowMax:
                windowMax = created
                windowMin = created - 60

                allTimestamps = times.keys()
                for t in allTimestamps:
                    if t < windowMin:
                        # Evict all edges with this timestamp
                        for e in times[t]:
                            for name in e:
                                # Get last occurrence of degree # and decrement
                                # keeping degreeList reverse sorted
                                i = getLast(degreeList, degrees[name])
                                degreeList[i] -= 1
                                degrees[name] -= 1
                                if degrees[name] == 0:
                                    del degreeList[i]
                                    del degrees[name]
                            del edges[e]
                        del times[t]
          
            median = getMedian(degreeList)
            outF.write(median+"\n")
            #writeToOutput(outFile, median)  # Uncomment to append to file


def usage():
    if sys.argv[0].startswith('./'):
        print "Usage: %s <path_to_input> <path_to_output>" % sys.argv[0]
    else:
        print "Usage: python %s <path_to_input> <path_to_output>" % sys.argv[0]
    sys.exit(1)


if __name__ == '__main__':
    
    try:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
    except IndexError as e:
        usage()

    try:
        rollingMedian(input_path, output_path)
    except IOError as e:
        print e
        usage()

