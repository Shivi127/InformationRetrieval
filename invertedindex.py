def invertedIndex():
    # Read file and create a term vector? Do we create a boolean one or frequency one
    import pandas as pd
    import json
    from nltk.corpus import stopwords


    # Loading Stopwords
    stop_words = set(stopwords.words('english'))

    with open("/Users/shivangisingh/Desktop/shakespeare-scenes.json",'r') as f:
        data = json.loads(f.read())
    
    # Dictionary storing the
    # key: term
    # Value : [#document, position of word in text]
    termdic ={}


    # Dictionary that maps docID to a Scene Name
    docdic = {}
    doc_count= 1

    for obj in data['corpus']:
        for k,v in obj.items():    
#       Parsing SceneID 
            if k== 'sceneId':
#           Then add it to the dic and this is a new posting?
                if v not in docdic:
                    docdic[doc_count]=v
                    doc_count+=1
#           Parsing the text field of each object
            if k== 'text':
#               Tokenizing Text
                text = v.split(" ")
#               Removing StopWords
                text = [word for word in text if word not in stop_words]
                term_pos = 1
                for term in text:
                    if term not in termdic:
                        termdic[term]=[[doc_count-1,term_pos]]
                    else :
                        termdic[term].append([doc_count-1,term_pos])
                    term_pos+=1
       

def encode(term_array):
    prev = 0
    for i in range (0,len(term_array)):
        curr = term_array[i]
        term_array[i]= curr - prev
        prev = curr
    return term_array

def deltaencoding(termdic):
#     Dictionary containing the delta encoding
    deltaterm_dic = {} # term : docID, termCount, deltapositions
    
    
    for term, value in termdic.items():
        prev_doc = value[0][0]
        temp = []
        for i in range (len(value)):
            current_doc = value[i][0]

            if (prev_doc == current_doc):
#                 part of the same doc
                temp.append(value[i][1])
    
            if (prev_doc != current_doc):
                total_positions_count = len(temp)
#                 Returns the delta encoded for that file
                delta_encoded_positions = encode(temp)
                if term not in deltaterm_dic:
                    deltaterm_dic[term] = [prev_doc, total_positions_count , delta_encoded_positions]
                else:
                    deltaterm_dic[term].append([prev_doc, total_positions_count , delta_encoded_positions])
#                 Resest temp and documents
                temp=[value[i][1]]
                prev_doc = current_doc
                
                
#         total_positions_count 
#             Look up same docid: within that make the encoding
#                 [0= docid , 1 = position]
        return deltaterm_dic

