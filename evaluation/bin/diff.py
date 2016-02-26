from collections import defaultdict
from recordclass import recordclass
from fuzzy_dict import fuzzy_dict
from queue import PriorityQueue

import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s : %(levelname)s : %(module)s : %(message)s',
)
logger = logging.getLogger(__name__)

DiffResult      = recordclass('DiffResult', 'commons replaces')
DiffReplaceItem = recordclass('DiffReplaceItem', 'deletes inserts')
DiffCommonItem  = recordclass('DiffCommonItem', 'pos1 pos2 element')
DiffDeleteItem  = recordclass('DiffDeleteItem', 'pos1 pos2 element matched')
DiffInsertItem  = recordclass('DiffInsertItem', 'pos1 pos2 element matched')

MappingItem     = recordclass('MappingItem','deletions insertion')
RunItem         = recordclass('RunItem', 'deletion insertion')

def diff(old, new, rearrange=False, junk=[], max_dist=0, min_sim=1, 
        visual_path=None):
    '''
    Finds the differences between the two given lists of strings. If the 
    rearrange flag is set to true, tries to rearrange the elements in 'new' as 
    much as possible to reproduce the same order of the elements in 'old'. 
    If max_dist or min_sim is given, the algorithms considers two elements as 
    equal if the distance between them is at most max_dist (if the similarity) 
    of both elements is at least min_sim).
    Returns a list of common elements and a list of replaced elements. A 
    replaced element consists of a list of deleted elements (elements that occur
    in 'old' but not in 'new') and a list of inserted elements (elements that 
    occur in 'new' but not in 'old') and deleted elements. Each common, 
    insertion and deletion is given by a tuple (pos1, pos2, element) where 
    'pos1' denotes the position in 'old', 'pos2' denotes the position in 'new' 
    and 'element' denotes the new element.
       
    * Inspired by the simplediff lib by Paul Butler 
    (see https://github.com/paulgb/simplediff/) *  
    '''
        
    if rearrange:
        # Try to rearrange the elements in 'new'
        new = rearrange_elements(old, new, max_dist=max_dist, min_sim=min_sim)

    # Do the diff.
    commons, replaces = [], []
    _diff(old, new, 0, 0, commons, replaces, junk=junk, max_dist=max_dist, 
        min_sim=min_sim)
     
    result = DiffResult(commons, replaces)
    
    if visual_path:
        visualize_diff_result(result, visual_path)
        
    return result
   
def _diff(old, new, pos1, pos2, commons, replaces, junk=[], max_dist=0, min_sim=1):
    '''
    Finds the differences between the two given lists of strings recursively. 
    pos1 and pos2 are the current positions in 'old' and 'new'. 
    If max_dist or min_sim is given, the algorithms considers two elements 
    as equal if the distance between them is at most max_dist (if the similarity
    of both elements is at least min_sim).
    Fills the common elements and replaced elements into the given lists 
    'commons' and 'replaces'.
    '''

    # Create an index from values in 'old', where each value is mapped to its 
    # position in 'old':
    # { element1: [1, 5, 7], element2: [4, 6, ], ... } 
    old_index = fuzzy_dict()  
    for i, element in enumerate(old):
        if element in old_index:
            old_index[element].append(i)
        else:
            old_index[element] = [i]

    # Find the largest substring common to 'old' and 'new'.
    # 
    # We iterate over each value in 'new'. At each iteration, overlap[i] is the
    # length of the largest suffix of old[:i] equal to a suffix of 
    # new[:index2] (or unset when old[i] != new[index2]).
    #
    # At each stage of iteration, the new overlap (called _overlap until 
    # the original overlap is no longer needed) is built from 'old'.
    #
    # If the length of overlap exceeds the largest substring
    # seen so far (length), we update the largest substring
    # to the overlapping strings.
    overlap = defaultdict(lambda: 0)
    
    # start_old is the index of the beginning of the largest overlapping
    # substring in old. start_new is the index of the beginning of the 
    # same substring in new. length is the length that overlaps in both.
    # These track the largest overlapping substring seen so far, so naturally
    # we start with a 0-length substring.
    start_old = 0
    start_new = 0
    length = 0

    for index2, element in enumerate(new):    
        _overlap = defaultdict(lambda: 0)
        # Get the 'closest' match to the string.
        for index1 in old_index.get(element, max_dist, min_sim, []):
            # now we are considering all values of index1 such that
            # old[index1] == new[index2].
            _overlap[index1] = (index1 and overlap[index1 - 1]) + 1
            # Check if this is the largest substring seen so far.
            if _overlap[index1] > length:
                length = _overlap[index1]
                start_old = index1 - length + 1
                start_new = index2 - length + 1
        overlap = _overlap
        
    ignore = False
    if length == 0:
        # No common substring was found. Return an insert and delete...
        deletes, inserts = [], []
        ignore = False
        for element in old:
            ignore = ignore or any(re.search(regex, element) for regex in junk)
        
        if not ignore:
            for element in old:
                deletes.append(DiffDeleteItem(pos1, pos2, element, False))
                pos1 += 1
            for element in new:
                inserts.append(DiffInsertItem(pos1, pos2, element, False))
                pos2 += 1
            if old or new:
                replaces.append(DiffReplaceItem(deletes, inserts))
        
    else:
        # A common substring was found. Call diff recursively for the substrings
        # to the left and to the right
        left1 = old[ : start_old]
        left2 = new[ : start_new]
        pos1, pos2 = _diff(left1, left2, pos1, pos2, commons, replaces, 
            junk=junk, max_dist=max_dist, min_sim=min_sim)
        
        for item in new[start_new : start_new + length]:
            commons.append(DiffCommonItem(pos1, pos2, item))
            pos1 += 1
            pos2 += 1
        
        right1 = old[start_old + length : ]
        right2 = new[start_new + length : ]
        pos1, pos2 = _diff(right1, right2, pos1, pos2, commons, replaces, 
            junk=junk, max_dist=max_dist, min_sim=min_sim)
        
    return (pos1, pos2)

# ______________________________________________________________________________
# Rearrange

def rearrange_elements(old, new, max_dist=0, min_sim=1.0):
    ''' Tries to rearrange the elements in 'new' as much as possible to 
    reproduce the same order of the elements in 'old'. If the ignore_cases flag 
    is set to True, the diff is done case-insensitive. If the ignore_whitespace 
    flag is set to True, all whitespaces will be ignored.
    If there are translations given in the translates dict, they will be applied
    to 'old' and 'new' (e.g. you can specify a dict {".,!?": " "} to translate
    all occurrences of '.', ',', '!' and '?' to the whitespace ' '. If max_dist 
    or min_sim is given, the algorithms considers two elements as equal if the 
    distance between them is at most max_dist (if the similarity of both 
    elements is at least min_sim).
    Let's define a running example to clarify the function of the method:
    old = ["The", "fox", "and", "the", "cow"]
    new = ["The", "cow", "and", "the", "red", "fox"]  
    '''
                      
    # First, do a normal diff without rearranging:
    # commons = [
    #    (pos1=0, pos2=0, element='The'), 
    #    (pos1=2, pos2=2, element='and'), 
    #    (pos1=3, pos2=3, element='the')
    # ]
    # inserts = [
    #    (pos1=2, pos2=1, element='cow', matched=False), 
    #    (pos1=5, pos2=4, element='red', matched=False),
    #    (pos1=5, pos2=5, element='fox', matched=False)
    # ]
    # deletes = [
    #    (pos1=1, pos2=1, element='fox', matched=False), 
    #    (pos1=4, pos2=4, element='cow', matched=False)
    # ]
    diff_result = diff(old, new, rearrange=False, max_dist=max_dist, 
        min_sim=min_sim)
                          
    # Map each deleted element to its deleted items:
    # { 
    #   'cow': [(pos1=4, pos2=4, element='cow', matched=False)], 
    #   'fox': [(pos1=1, pos2=1, element='fox', matched=False)],
    # }
    deletes_index = fuzzy_dict()
    for replace in diff_result.replaces:
        for item in replace.deletes:
            if item.element in deletes_index:
                deletes_index[item.element].append(item)
            else:
                deletes_index[item.element] = [item]
                                            
    # Separate the insertions and associate each element of each insertion to 
    # its positions in the deletes_index:
    # [
    #   # Insertion 1
    #   [
    #     ([(pos1=4, pos2=4, element='cow', matched=False)], (pos1=2, pos2=1, element='cow', matched=False))
    #   ], 
    #   # Insertion 2
    #   [
    #     ([None], (pos1=5, pos2=4, element='fox', matched=False)),
    #     ([(pos1=1, pos2=1, element='fox', matched=False)], (pos1=5, pos2=5, element='fox', matched=False))
    #   ]
    # ]
     
    inserts_mappings = []
    for replace in diff_result.replaces:
        insert_mapping = []
        for insert in replace.inserts:
            deletions = deletes_index.get(insert.element, max_dist, min_sim, [None])
            insert_mapping.append(MappingItem(deletions, insert))    
        inserts_mappings.append(insert_mapping) 
     
                         
    # For each mapping, compute the longest "run", that is a sequence of words 
    # in an insertion that occurs in the same order as in the groundtruth. Try
    # to keep unmatched insertions at the original position.
    # [
    #   (None, (pos1=5, pos2=4, element='red', matched=False)), 
    #   ((pos1=1, pos2=1, element='fox', matched=False), (pos1=5, pos2=5, element='fox', matched=False))
    # ]
    run = find_longest_run_in_mappings(inserts_mappings)
                       
    while run:    
        # There may be insertions which could not be matched to a deleted 
        # position. Hence we do not know where to insert such insertions.
        # If there is such insertion within a run, concat it with a preceding
        # or succeeding matched insertion.
        
        # The last matched insertion.
        last_matched_insertion = None
        # If there is no matched insertion yet, add a unmatched insertion to
        # this queue.
        unmatched_insertions = []
        
        for matching in run:
            deletion, insertion = matching
            
            if deletion is not None:
                # The insertion has a matched deletion.
                last_matched_insertion = insertion
                
                # First, concat all unmatched insertions (if any) to this 
                # deletion.
                for i, unmatched in enumerate(unmatched_insertions):
                    unmatched.pos1 = deletion.pos1
                    unmatched.pos2 = deletion.pos2 + i
                    unmatched.matched = True

                # Then map the actual insertion to this deletion.
                insertion.pos1 = deletion.pos1
                insertion.pos2 = deletion.pos2 + len(unmatched_insertions)            
                
                unmatched_insertions = []
                deletion.matched = insertion.matched = True
            else:
                # The insertion has no matched deletion.
                if last_matched_insertion:
                    # If there was a matched insertion seen so far, add the 
                    # unmatched insertion to the this matched insertion.
                    insertion.pos1 = last_matched_insertion.pos1
                    insertion.pos2 = last_matched_insertion.pos2 + 1
                    last_matched_insertion = insertion
                else:
                    # Otherwise queue the unmatched insertion.
                    unmatched_insertions.append(insertion)
                insertion.matched = True  

        # Find another run.
        run = find_longest_run_in_mappings(inserts_mappings)

 
    # The rearranged list follows from the commons and the (updated) inserts.       
    rearranged = diff_result.commons
    
    for replace in diff_result.replaces:
        rearranged.extend(replace.inserts)

    rearranged.sort()
        
    # Remove all the meta stuff.
    rearranged = [item.element for item in rearranged]
              
    return rearranged

def find_longest_run_in_mappings(mappings):
    longest_run = []
    for mapping in mappings:
        run = find_longest_run_in_mapping(mapping)
        if run and len(run) > len(longest_run):
            longest_run = run
    return longest_run

def find_longest_run_in_mapping(mapping): # Find run in a single(!) element.        
    ''' Finds the longest possible run in the given mapping. The mapping is of 
    the form: [([deletions1], insert1), ([deletions2], insert2), ...] where each
    list of deletions is of form [(pos1, pos2, element), ...]. Note that 
    deletions could be [None] if there is no matched deletion for the insert.
    '''
            
    if not mapping:
        return []
        
    # The runs found so far.
    active_runs = []
    # The longest run found so far.
    longest_run = []
        
    # The runs by their end elements. For example, if the runs at indices
    # 1, 2, 3 end with '5' and the runs at indices 4 and 5 ends with '7' the 
    # map looks like: { 5: {1, 2, 3}, 7: {4, 5} }
    runs_by_end_elements = defaultdict(lambda: set())
    # The end elements by runs. For the example above, this map looks like:
    # { 1: 5, 2: 5, 3: 5, 4: 7, 5: 7 }
    end_elements_by_runs = defaultdict(lambda: set())
    # The queue of unmatched inserts (inserts with no associated deletion).
    unmatched_queue = []
                      
    for item in mapping:           
        deletions, insert = item            

        if insert.matched:
            # If the insert is already matched, the item shouldn't be a member 
            # of a run anymore.
            continue
        
        prev_active_runs = active_runs
        active_runs = []
        
        prev_runs_by_end_elements = runs_by_end_elements
        runs_by_end_elements = defaultdict(lambda: set())
        
        prev_end_elements_by_runs = end_elements_by_runs
        end_elements_by_runs = defaultdict(lambda: set())
         
        # Iterate through the deleted positions. 
        for deletion in deletions:          
            # If the deletion is already matched, the item shouldn't be a member
            # of a run anymore.
            if deletion is not None and deletion.matched:
                continue
            
            # Obtain the position of the deletion (could be None).
            pos = deletion.pos1 if deletion is not None else None
                                      
            if pos is not None: # There is a matched deletion.
                # Check, if there are runs with end element 'pos-1'
                if pos - 1 in prev_runs_by_end_elements:
                    # There are runs that end with 'pos-1'. 
                    run_indices = prev_runs_by_end_elements[pos - 1]
                                                                 
                    for run_index in run_indices:
                        # Append the element to the run.
                        run = prev_active_runs[run_index]
                        run.append(RunItem(deletion, insert)) 
                        
                        # Add the run to active runs.
                        active_runs.append(run)
                        new_run_index = len(active_runs) - 1
                        
                        # Check, if the current run is now the longest run. 
                        if len(run) > len(longest_run):
                            longest_run = run
                        
                        # Update the maps
                        runs_by_end_elements[pos].add(new_run_index)
                        end_elements_by_runs[new_run_index].add(pos)
                else:                   
                    # There is no run that end with 'pos-1'.
                    # Create new run.
                    new_run = unmatched_queue + [RunItem(deletion, insert)]
                                        
                    # Append the run to active runs.
                    active_runs.append(new_run)
                    new_run_index = len(active_runs) - 1
                                              
                    # Check, if the new run is the longest run.     
                    if len(new_run) > len(longest_run):
                        longest_run = new_run
                                
                    # Update the maps.
                    runs_by_end_elements[pos].add(new_run_index)
                    end_elements_by_runs[new_run_index].add(pos)
                # Clear the queue.
                unmatched_queue = []
            else: # There is no matched deletion.
                run_item = RunItem(deletion, insert)
                unmatched_queue.append(run_item)
                                
                for j, active_run in enumerate(prev_active_runs):
                    pos = max(prev_end_elements_by_runs[j]) + 1
                        
                    # Append the element to run.
                    active_run.append(run_item)
                    active_runs.append(active_run)
                    new_run_index = len(active_runs) - 1
                      
                    runs_by_end_elements[pos].add(new_run_index)
                    end_elements_by_runs[new_run_index].add(pos)
                                            
                    if len(active_run) > len(longest_run):
                        longest_run = active_run
            
            debug_queue = [item.insertion.element for item in unmatched_queue]
                 
    if longest_run:
        return longest_run
    else:
        return unmatched_queue  
                      
# ______________________________________________________________________________
# Util methods.

def visualize_run(run):
    ''' Visualizes the given run. '''
    
    snippets = []
    run_insertion_start = "\033[30;42m"
    run_insertion_end = "\033[0m"
    run_deletion_start = "\033[30;41m"
    run_deletion_end = "\033[0m"
    
    for item in run:
        if item.insertion:
            snippets.append(run_insertion_start)
            snippets.append(item.insertion.element)
            snippets.append(run_insertion_end)
            snippets.append(" ")
    
    snippets.append("<=> ")
            
    for item in run:
        if item.deletion:
            snippets.append(run_deletion_start)
            snippets.append(item.deletion.element)
            snippets.append(run_deletion_end)
            snippets.append(" ")
        
    
    return "".join(snippets)
   
def visualize_diff_result(diff_result, path=None):
    ''' Visualizes the given diff result. '''
        
    full = []
    full += diff_result.commons
    
    for replace in diff_result.replaces:
        full += replace.inserts
        full += replace.deletes
    full.sort()
                   
    visualization_delete_start = "\033[30;41m"
    visualization_delete_end = "\033[0m"
    visualization_insert_start = "\033[30;42m"
    visualization_insert_end = "\033[0m"
     
    snippets = []
        
    x = 0
    y = 0
    z = 0
        
    for i, item in enumerate(full):
        if isinstance(item, DiffInsertItem):
            x += 1
            snippets.append(visualization_insert_start)
        elif isinstance(item, DiffDeleteItem):
            y += 1
            snippets.append(visualization_delete_start)
        else:
            z += 1
        snippets.append("%s" % item.element)
        if isinstance(item, DiffInsertItem):
            snippets.append(visualization_insert_end)
        elif isinstance(item, DiffDeleteItem):
            snippets.append(visualization_delete_end)
        snippets.append(" ")   
    visualization_string = "".join(snippets)
    if path:
        visualization = open(path, "w")
        visualization.write(visualization_string)
        visualization.close()
    
    return visualization_string

if __name__ == '__main__':
    print(diff(["Hello", "World"], ["World", "Hello"], rearrange=True))
