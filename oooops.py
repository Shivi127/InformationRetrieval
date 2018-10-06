import pandas as pd
import json
from nltk.corpus import stopwords
import random

# Loading Stopwords
stop_words = set(stopwords.words('english'))

vocab = []  
# Dictionary storing the
# key: term
# Value : [#document, position of word in text]
termdic ={}
termstats = {}
# Dictionary that maps docID to a Scene Name
docdic = {}
term_position_dic = {}
uncompressed_dic = {}
UncompressedLookup = {}
CompressedLookup = {}

def encode(term_array):
    prev = 0
    for i in range (0,len(term_array)):
        curr = term_array[i]
        term_array[i]= curr - prev
        prev = curr
    return term_array
    
# Writing the docdic which maps docID to a scene to a file
def dumpDocumetID():
    docdump = json.dumps(docdic)
    f = open("/Users/shivangisingh/Desktop/InformationRetrieval/DocIDmap","w")
    f.write(docdump)
    f.close()


def createUncompressed():
    for k, value in term_position_dic.items():
        temparray = []
        for v in value:
            t= [v[0],v[1]]
            t.extend(v[2])
            temparray.extend(t)
        uncompressed_dic[k] = temparray

def createstats():
    for k, value in term_position_dic.items():
        total_occurances = 0
        for v in value:
            total_occurances+= v[1]
        termstats[k] = {'#ofdocumnetsInCollection': len(value) ,'#ofoccurancesInCollection' : total_occurances}
        
def loadJSON():
    
    with open("/Users/shivangisingh/Desktop/shakespeare-scenes.json",'r') as f:
        data = json.loads(f.read())

        doc_count= 1
    for obj in data['corpus']:
        for k,v in obj.items():    
    #   Parsing SceneID 
            if k== 'sceneId':
        #       Then add it to the dic and this is a new posting?
                if v not in docdic:
                    docdic[doc_count]= v.strip()
                    doc_count+=1
        #       Parsing the text field of each object
            if k == 'text':
        #           Tokenizing Text
                text = v.split(" ")
        #           Removing StopWords
                text = [word.strip() for word in text if word not in stop_words if len(word)!=None]
                term_pos = 1
                for term in text:
        #                 term_pos+=1
                    if term not in termdic:
                        termdic[term]=[[doc_count-1,term_pos]]
                    else :
                        termdic[term].append([doc_count-1,term_pos])
                    term_pos+=1

    for key, value in termdic.items():
    #     value = List of lists where 1st entry is a documentID and the second is a position
        i=0
        temp = []

        for v in value:
    #         print(v)
            current_doc = v[0]
            if i==0:
                prev_doc = v[0]
                i+=1
            if (prev_doc == current_doc):
                    temp.append(v[1])
            if (prev_doc != current_doc):
                if key not in term_position_dic:
    #                 initialize
                    term_position_dic[key] = [[prev_doc,len(temp),temp]]

                else:
                    term_position_dic[key].append([prev_doc,len(temp),temp])
    #           We are in the reset phase
                prev_doc= current_doc
                temp = [v[1]]

def writeUncompressed():
    offset = 0
    
    f = open('/Users/shivangisingh/Desktop/InformationRetrieval/UCIndex.txt', 'wb')
    for k, v in uncompressed_dic.items():
        
        f.seek(offset,0)
        for b in v:
            f.write(b.to_bytes(3, byteorder='big'))
        
        UncompressedLookup[k] = {'offset': offset, 
                                 'size': f.tell()-offset, 
                                 '#ofdocumnetsInCollection': termstats[k]['#ofdocumnetsInCollection'] ,
                                 '#ofoccurancesInCollection' : termstats[k]['#ofoccurancesInCollection'] }
        offset= f.tell()
    f.close()

def dumpUnCompressedLookup():
    docdump = json.dumps(UncompressedLookup)
    f = open("/Users/shivangisingh/Desktop/InformationRetrieval/UCLookup.json","w")
    f.write(docdump)
    f.close()
    
# Functions Used in Delta Encoding
K=128
        
def EncodeNum(n):
    nn =n
    b = bytearray()
    while True:
        b.append(n%K)
        if n < K: break
        n //= K
    b.reverse()
    b.append(K)
    #print("EncodeNum", " nn=",nn, " b=",b, " val=",b[0]," ",b[1])
    return b

def EncodeList(nums):
    b= bytearray()
    for n in nums:
        b.extend(EncodeNum(n))
    return b

def DecodeByteArray(bytearr):
    nums = []
    n = 0
    for i in range(len(bytearr)):
        if bytearr[i] < K:
            n = n * K + bytearr[i]
        else:
            nums.append(n)
            n = 0
    return nums

# Function that deltaencodes and does vbyte compression for the lists

def deltaencodePositionsandDocuments():
    i=0
    for k, value in term_position_dic.items():
        prev_document = 0
        lst = []
        for i,v in enumerate(value):
#             print(value)
            curr_document = v[0]
            v[0] = curr_document - prev_document
        #       Update prev
            prev_document = curr_document
            poslist = encode(v[2]) 
            v[2] = poslist
            temp = [v[0],v[1]]
            temp.extend(v[2])
            term_position_dic[k][i] = temp
            lst.extend(temp)
        term_position_dic[k]= EncodeList(lst)
#     term_position_dic[k] = EncodeList(value)


def writeCompressedIndex():
    offset = 0
 
    f = open('/Users/shivangisingh/Desktop/InformationRetrieval/CIndex.txt', 'wb')
    for k, v in term_position_dic.items():
        f.seek(offset,0)
        f.write(bytes(v))
        CompressedLookup[k] = {'offset': offset, 
                               'size': f.tell()-offset, 
                               '#ofdocumnetsInCollection': termstats[k]['#ofdocumnetsInCollection'] ,
                               '#ofoccurancesInCollection' : termstats[k]['#ofoccurancesInCollection'] }
        offset= f.tell()
    f.close()
    
def dumpCompressedLookup():
    docdump = json.dumps(CompressedLookup)
    f = open("/Users/shivangisingh/Desktop/InformationRetrieval/CLookup.json","w")
    f.write(docdump)
    f.close()
    


def getvocab():
    for k in term_position_dic.keys():
        vocab.append(k)
getvocab()


def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + int(b)
    return result

def compareVocab():
    return(set(CompressedLookup.keys()) == set(UncompressedLookup.keys()))




# Load the JSON
loadJSON()
# Loading Vocab
vocab()
# DumpDocID
dumpDocumetID()
# Create Stats
createstats()
# CreateUncompressed
createUncompressed()
# Write Compressed
writeUncompressed()
# Write Compressed Lookup
dumpUnCompressedLookup()
# Compressed Dic - delta + vbyte encoding
deltaencodePositionsandDocuments()
# Write Compressed Lookup
writeCompressedIndex()
# Dump Lookup
dumpCompressedLookup()
print("Checking Vocabulary:", compareVocab())





############### EVALUATION #####################
def sevenrandomwords():
    random_index= set()
    for i in range(7):
        randomnum = random.randint(0,len(vocab)-1)
        if randomnum not in random_index:
            random_index.add(randomnum)
    result = []
    for r in random_index:
        result.append(vocab[r])
    return result

# Given an encoded array returns a set of the document ID's
def getdocumentslist(arr):
# Given an array
    docIDs = set()
    temp = arr
    while(len(temp)>0):
        docIDs.add(temp[0])
        number = temp[1]
        temp = temp [number+2:]
    return docIDs

def readUCLookUpIntoMemory():
#     read the look up dic and return offset array and 
    f = open("/Users/shivangisingh/Desktop/InformationRetrieval/UCLookup.json",'r') 
    LookUpTable = json.loads(f.read())
    f.close()
    return LookUpTable

def readCLookUpIntoMemory():
#     read the look up dic and return offset array and 
    f = open("/Users/shivangisingh/Desktop/InformationRetrieval/CLookup.json",'r') 
    LookUpTable = json.loads(f.read())
    f.close()
    return LookUpTable


# flag = True = using the Uncompressed file
# False = Using the Compressed File
def dicecoffeicient(t1,t2, flag, breader):
    
#     TO OPTIMIZE WE CAN PASS BREADER instead of a flag
#         Get term list for t1 and t2
    if flag == True:
#         Read Uncompressed
# Make a breader for the Uncompressed 
        
        UClookup = readUCLookUpIntoMemory()
        
        t1offset = UClookup[t1]['offset']
        t1size = UClookup[t1]['size']
        t1array = read_from_disk(t1offset, t1size, breader)
        
        t2offset = UClookup[t2]['offset']
        t2size = UClookup[t2]['size']
        t2array = read_from_disk(t2offset, t2size, breader)
        
        ta = getdocumentslist(t1array)
        tb = getdocumentslist(t2array)
        tab = ta.intersection(tb)
        return (float(len(tab)/(len(ta)+len(tb))))
    
    else:
        
        UClookup = readUCLookUpIntoMemory()
        breader = open("/Users/shivangisingh/Desktop/InformationRetrieval/CIndex.txt",'rb')
#         But we have to have decoding logic in here which I havent though of right now
        
        t1offset = UClookup[t1]['offset']
        t1size = UClookup[t1]['size']
        t1array = read_from_disk(t1offset, t1size, breader)
        
        t2offset = UClookup[t2]['offset']
        t2size = UClookup[t2]['size']
        t2array = read_from_disk(t2offset, t2size, breader)
        
        ta = getdocumentslist(t1array)
        tb = getdocumentslist(t2array)
        tab = ta.intersection(tb)
        return (float(len(tab)/(len(ta)+len(tb))))


# ######################### DICE's Coefficient 
dicecompressed_fresult = []
randomwordsused =[]

# Generating
breader = open("/Users/shivangisingh/Desktop/InformationRetrieval/CIndex.txt",'rb')
fresult =[]
for i in range(100):
    randomterms = sevenrandomwords()
    randomwordsused.append(randomterms)
#     randomterms=['wand','venice']
    result =[]
    print(randomterms,i)
    for randomterm in randomterms:
        print("RandomTerm is", randomterm)
        maxcoeff = -1
        maxterm = ""
#         find dice coefficient between the term and the vocab
        for v in vocab:

            if v != randomterm:
                dvalue = dicecoffeicient(randomterm,v, False,breader)
                if(dvalue > maxcoeff):
                    maxcoeff = dvalue
                    maxterm = v
        print("Maxterm",maxterm)
        result.extend([randomterm,maxterm])
    fresult.append([result])

print ("Length",len(fresult))