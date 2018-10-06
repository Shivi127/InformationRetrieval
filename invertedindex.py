# Importing the Json and making(DID, pos) list
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
#   Parsing SceneID 
        if k== 'sceneId':
    #       Then add it to the dic and this is a new posting?
            if v not in docdic:
                docdic[doc_count]=v
                doc_count+=1
    #       Parsing the text field of each object
        if k == 'text':
    #           Tokenizing Text
            text = v.split(" ")
    #           Removing StopWords
            text = [word for word in text if word not in stop_words if len(word)!=None]
            term_pos = 1
            for term in text:
    #                 term_pos+=1
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
    

delta_position_dic ={}
term_position_dic = {}
for key, value in termdic.items():
#     value = List of lists where 1st entry is a documentID and the second is a position
    i=0
    temp = []
    
    for v in value:
        current_doc = v[0]
        if i==0:
            prev_doc = v[0]
            i+=1
        if (prev_doc == current_doc):
                temp.append(v[1])
        if (prev_doc != current_doc):
            if key not in term_position_dic:
                term_position_dic[key] = [[prev_doc,len(temp),temp]]
            else:
                term_position_dic[key].append([prev_doc,len(temp),temp])
            prev_doc= current_doc
            temp = [v[1]]

# Stats 
termstats = {}
def createstats():
    for k, value in term_position_dic.items():
        total_occurances = 0
        for v in value:
            total_occurances+= v[1]
        termstats[k] = {'#ofdocumnetsInCollection': len(value) ,'#ofoccurancesInCollection' : total_occurances}
createstats()

# Creating a dictionary for the Uncompressed
uncompressed_dic = {}
for k, value in term_position_dic.items():
    temparray = []
    for v in value:
        t= [v[0],v[1]]
        t.extend(v[2])
        temparray.extend(t)
    uncompressed_dic[k] = temparray



# Writing the Uncompressed Stuff to file
# Now that I have the uncompressed inverted index I have to make a lookup table and write to a byte file
# Two things Maybe JSON 
#     Term
#     Number of Occurances
#     Offset
#     Number of documents associated with the term

# UncompressedLookUp
import sys
import pickle
offset = 0
UncompressedLookup = {}
def writeUncompressed():
    f = open('/Users/shivangisingh/Desktop/InformationRetrieval/UCIndex.txt', 'wb')
    for k, v in uncompressed_dic.items():
        UncompressedLookup[k] = {'offset': offset, 
                                 'size': sys.getsizeof(v), 
                                 '#ofdocumnetsInCollection': termstats[k]['#ofdocumnetsInCollection'] ,
                                 '#ofoccurancesInCollection' : termstats[k]['#ofoccurancesInCollection'] }
        f.seek(offset,0)
        for b in v:
            f.write(b.to_bytes(3, byteorder='big'))
        offset= f.tell()

    f.close()
    
writeUncompressed()  

# Delta Encodings
# This will update term_position_dic and then if you write the uncompressed thing it will break, so run this after 
# you have run that 
def deltaencodetheInvertedIndex():
    i=0
    for k, value in term_position_dic.items():
        prev_document = 0
        lst = []
        for i,v in enumerate(value):
            curr_document = v[0]
    #       Update docID according to delta encoding
            v[0] = curr_document - prev_document
    #       Update prev
            prev_document = curr_document
    #     Delta encode the posting lists
            poslist = encode(v[2]) 
            v[2] = poslist
            temp = [v[0],v[1]]
            temp.extend(v[2])
            #v = temp
            term_position_dic[k][i] = temp
            lst.extend(temp)
        term_position_dic[k]= lst
        
        
deltaencodetheInvertedIndex()


def writeCompressedIndex():
    offset = 0
    CompressedLookup = {}
    f = open('/Users/shivangisingh/Desktop/InformationRetrieval/CIndex.txt', 'wb')
    for k, v in uncompressed_dic.items():
        CompressedLookup[k] = {'offset': offset, 
                               'size': sys.getsizeof(v), 
                               '#ofdocumnetsInCollection': termstats[k]['#ofdocumnetsInCollection'] ,
                               '#ofoccurancesInCollection' : termstats[k]['#ofoccurancesInCollection'] }
        f.seek(offset,0)
        for b in v:
            f.write(b.to_bytes(3, byteorder='big'))
        offset= f.tell()

    f.close()
    
writeCompressedIndex()

# Getting the vocab
vocab = []
for k in term_position_dic.keys():
    vocab.append(k)

def dumpDocumetID():
    docdump = json.dumps(docdic)
    f = open("/Users/shivangisingh/Desktop/InformationRetrieval/DocIDmap","w")
    f.write(docdump)
    f.close()
    
dumpDocumetID()