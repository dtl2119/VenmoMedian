#!/usr/bin/python

import sys
from datetime import datetime, time
import json
import time #FIXME



def getMedian(lst):
    """
    Get Median of list of numbers.  Result should have 2 digits 
    after decimal place (truncate if more than 2)
    Examples:
    1 --> 1.00
    2.0 --> 2.00
    3.678 --> 3.67
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
    This fuction converts time format given
    in json input data to a Unix Timestamp
    
    Example: 2016-04-07T03:33:19Z --> 1459999999
    """
    dt = datetime.strptime(raw_str, "%Y-%m-%dT%H:%M:%SZ")
    # Get unix timestamp UTC in seconds since Epoch (1/1/1970)
    timestamp = (dt - datetime(1970, 1, 1)).total_seconds()
    return timestamp


def writeToOutput(output_file, text):
    """
    Use to write median to output file
    """
    with open(output_file, "a") as output:
        output.write(text)
        #print text #FIXME


def main():

    input_path = sys.argv[1] #FIXME
    output_path = sys.argv[2] #FIXME

#    input_path = "../venmo_input/venmo-trans.txt" #FIXME
#    output_path = "../venmo_output/output.txt" #FIXME

    venmoGraph = {} # Dict representing our graph (key=time value=list of tuples)
    time_list = [] # Keep track of timestamps in graph
    current_max = 0 # Graph should only include payments w/ timestamps < current_max - 60s
    current_min = current_max - 59 # Should be less than 59 of current_max (60s, exclusive)
    median = 0

    # Ovewrite output file
    open(output_path, "w").close()
        
    with open(input_path) as f:
    #with open("../venmo_input/venmo-trans.txt") as f:
    #with open("../data-gen/venmo-trans.txt") as f:#FIXME
    #with open("../data-gen/test-trans.txt") as f:
        for line in f:
            #print json.loads(line)
            try:
                created, target, actor = json.loads(line).values()
                if not (created and target and actor):
                    raise ValueError("Missing Field")
            except ValueError as e:
                #print "%s: %s" % (e, line) #FIXME
                # Completely ignore line and continue if missing
                # Field or unable to parse json line (Extra data)
                continue
            created = cleanTime(created)
            
            # If incoming payment not in 60s window, ignore
            # But still write previous rolling median
            if created < current_min:
                writeToOutput(output_path, median)
                continue
           
            #FIXME Make algo faster deque/enque
            # Add timestamp to time_list
            i = 0
            length = len(time_list)
            while i < length:
                if created > time_list[i]:
                    i += 1
                else:
                    break

            if length == 0:
                time_list.append(created)
            elif created not in time_list:
                time_list.insert(i,created)
           

            if created > current_max:
                current_max = created
                current_min = current_max - 59

            edge = (actor, target)
            # venmoGraph is a dict whose values are lists of edges as tuples --> (actor, target)
            if created not in venmoGraph:
                venmoGraph[created] = []
                
            venmoGraph[created].append(edge)


            # Remove all edges from less than min
            for timestamp in time_list:
                if timestamp < current_min:
                    time_list.remove(timestamp)
                    del venmoGraph[timestamp]

            
            # Get median degree
            degrees = {} # key:value == name:degrees
            for timestamp,edges in venmoGraph.iteritems():
                for edge in edges:
                    for name in edge:
                        if name not in degrees:
                            degrees[name] = 1
                        else:
                            degrees[name] += 1

            d = sorted(degrees.values())
            median = getMedian(d) + "\n"

            # Write median to output file
            writeToOutput(output_path, median)
            #print median


if __name__ == '__main__':
    main()
    #t = timeit.timeit("main()", setup="from __main__ import main", number=100)


#NOTES
# Think about this:
# key = (from, created); value = to # or maybe a tuple?
# Don't forget try/except for opening input
# Clearing output.txt line (as of now, clears if it exists, creates if it doesn't)
