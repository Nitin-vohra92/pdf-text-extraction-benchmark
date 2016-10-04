import unicodedata
import re
import string

def update_file_extension(path, new_file_extension):
    ''' Returns the given path where the actual file extension is replaced by 
    the given new file extension.''' 
    
    # Find the last dot in the path.
    index_last_dot = path.rfind('.')
    
    if index_last_dot < 0:
        basename = path
    else:
        basename = path[ : index_last_dot]
    
    return basename + new_file_extension    

def to_str(arg, default):
    ''' Parses the given arg as string. If parsing fails, returns the given 
    default value. '''
    try: 
        return str(arg)
    except:
        return default

def to_float(arg, default):
    ''' Parses the given arg as int. If parsing fails, returns the given 
    default value. '''
    try: 
        return float(arg)
    except:
        return default

def to_int(arg, default):
    ''' Parses the given arg as int. If parsing fails, returns the given 
    default value. '''
    try: 
        return int(arg)
    except:
        return default

def to_bool(arg, default):
    ''' Parses the given arg as bool. If parsing fails, returns the given 
    default value. '''
    arg_int = to_int(arg, None)
    if arg_int is not None:
        return arg_int != 0
    else:
        arg_str = to_str(arg, None)
        if arg_str is not None:
            return arg_str.lower() != "false" 
        else:
            return default
        
def to_list(arg, default, separator=" "):
    ''' Splits the given arg using the given separator as delimiter and wraps 
    all elements in a list. '''
    arg_str = to_str(arg, None)
    if arg_str:
        return arg_str.split(sep=separator)
    else:
        return default

def split_into_paragraphs(text):
    return re.split("\n\s*\n", text)

def to_formatted_paragraphs(text, to_lowercases=True, to_protect=[]):
    words_by_paragraph = []
    paragraphs = split_into_paragraphs(text)
    for paragraph in paragraphs:
        words = to_formatted_words(paragraph, to_lowercases, to_protect)
        words_by_paragraph.append(words)
    return words_by_paragraph

def to_formatted_words(text, to_lowercases=True, to_protect=[]):
    ''' 
    Transforms the given string to list of (formatted) words. Removes all 
    punctuation marks. Transforms all letters to lowercases if the 
    to_lowercases flag is set to True. 
    Single phrases can be protected by defining regular expressions in the 
    'to_protect' list. All phrases which match at least one of the regular 
    expressions won't be formatted.
    '''
   
    # Make sure, that the given element is indeed a string.
    text = str(text)
    # Define the characters to ignore: all non-alphanumeric characters and all
    # greek characters because the may decoded in different ways. 
    # For example, ∆ (code 8710) != Δ (code 916)
    CHARS_TO_IGNORE_PATTERN = re.compile("[\W]")
                       
    # Unicode can hold "decomposed" characters, i.e. characters with accents 
    # where the accents are characters on its own (for example, the character 
    # "ä" could be actually two characters: "a" and the two dots.
    # Try to compose these characters to a single one using unicodedata.  
    codepoints = [ord(i) for i in text]
             
    # Unicodedata has issues to compose 
    # "LATIN SMALL LETTER DOTLESS I" (that is an 'i' without the dot) / 
    # "LATIN SMALL LETTER DOTLESS J" (that is an 'j' without the dot)
    # with accents. So replace all occurrences of these chars by "i" resp. "j".
    # Map "LATIN SMALL LETTER DOTLESS I" to "LATIN SMALL LETTER I"
    # Map "LATIN SMALL LETTER DOTLESS J" to "LATIN SMALL LETTER J"        
    mappings = { 0x0131: 0x0069, 0x0237: 0x0061 } 
    for i, codepoint in enumerate(codepoints):
        if codepoint in mappings:
            codepoints[i] = mappings[codepoint]
            
    # Normalize (compose the characters). NFC = Normal form C(omposition)
    text = unicodedata.normalize("NFC", "".join([chr(i) for i in codepoints])) 

    # Split the string on whitespaces.                                
    words = text.split()
    
    # Compose a single regular expression from the given expression.
    to_protect_regex = "|".join(to_protect)
    
    result = []
    for i in range(0, len(words)):
        word = words[i]
        
        # Check, if we have to protect the word from formatting.
        match = re.search(to_protect_regex, word)
        
        if to_protect_regex and match:
            # Protect the word (don't format it)
            start = match.start()
            end   = match.end()
            if start > 0:
                # There is some preceding string. Format it.
                prefix = word[:start]
                result.extend(to_formatted_words(prefix, to_lowercases, to_protect))
            # Append the word to protect as it is.
            result.append(word[start : end])
            if end < len(word) - 1:
                # There is some succeeding string. Format it.
                suffix = word[end:]
                result.extend(to_formatted_words(suffix, to_lowercases, to_protect))
        else:
            # We don't have to protect the word from formatting. Let's go.
            
            # Keep track of the original and normalized (sub-) words.
            sub_words = []
            norm_sub_words = []    
            
            prev_punct_index = 0           
            word_chars = list(word)
            # Iterate through the characters to detect non-characters and to 
            # split the word at these positions.
            for index in range(0, len(word_chars)):
                char = word_chars[index]
                if CHARS_TO_IGNORE_PATTERN.match(char):
                    # Don't split the word if the special char lies between
                    # two digits (i.e. keep things like '1.23')
                    if char == "." and index > 0 and index < len(word_chars) - 1:
                        prev_char = word_chars[index - 1]
                        next_char = word_chars[index + 1]
                        if prev_char.isdigit() and next_char.isdigit():
                            continue

                    sub_word = word[prev_punct_index : index + 1]
                    norm_sub_word = "".join([x for x in list(sub_word) if not CHARS_TO_IGNORE_PATTERN.match(x)])
                    if norm_sub_word:
                        sub_words.append(sub_word)                        
                        norm_sub_words.append(norm_sub_word)    
                        prev_punct_index = index + 1
           
            # Don't forget the rest of string.
            sub_word = word[prev_punct_index : len(word_chars)]
            norm_sub_word = "".join([x for x in list(sub_word) if not CHARS_TO_IGNORE_PATTERN.match(x)])
            
            if norm_sub_word:
                sub_words.append(sub_word)                        
                norm_sub_words.append(norm_sub_word)    
                            
            if to_lowercases:
                # Transform all words to lowercases.                
                norm_sub_words = [x.lower() for x in norm_sub_words]

            # Append a whitespace to last word.
            if sub_words:
                sub_words[-1] = sub_words[-1] + " "

            result.extend(list(zip(norm_sub_words, sub_words)))              
    return result                    

# def to_formatted_paragraphs(string, to_lowercases=True, remove_whitespaces=True,
#         to_protect=[]):
#     ''' Formats the given string to paragraphs for paragraph evaluation. ''' 
    
#     paras = re.split("\n\s*\n", string)
#     words = [to_formatted_words(p, to_lowercases, to_protect) for p in paras]
    
#     if remove_whitespaces:
#         return ["".join(x) for x in words]
#     else:
#         return [" ".join(x) for x in words]

def compute_precision_recall(diff_result, junk=[]):
    ''' Computes precision and recall from the given diff result. '''
    
    fp, fn, tp = 0, 0, 0
    
    for replace in diff_result.replaces:
        if ignore(replace, junk):
            continue
        
        fp += len(replace.insert.items)
        fn += len(replace.delete.items)
    
    for common in diff_result.commons:
        tp += len(common.items)
                
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall    = tp / (tp + fn) if tp + fn > 0 else 0.0
    
    print("tp", tp, "fn", fn, "fp", fp)
    
    return (round(precision, 4), round(recall, 4))

def compute_distance_similarity(diff_result, junk=[]): 
    ''' Computes distance and similarity from the given diff result. '''
       
    distance = 0
    num_deletes = 0
    num_inserts = 0
    num_commons = len(diff_result.commons)
    for replace in diff_result.replaces:
        num_deletes += len(replace.deletes)
        num_inserts += len(replace.inserts)
        distance    += max(len(replace.inserts), len(replace.deletes))
        
    length_gt = num_commons + num_deletes
    length_actual = num_commons + num_inserts
    
    similarity = 1 - (distance / max(length_gt, length_actual))
    
    return (distance, round(similarity, 4))
    
def ignore(item, junk=[]):
    if item:
        for phrase in item.phrases:
            if ignore_phrase(phrase, junk):
                return True

    return False

def ignore_phrase(phrase, junk=[]):
    if phrase:
        for target_item in phrase.items_target:           
            if ignore_item(target_item, junk):
                return True

    return False

def ignore_item(item, junk=[]):
    if item:
        if any(re.search(regex, item.string) for regex in junk):
            return True

    return False
