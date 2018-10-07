import pandas as pd
import json
from nltk.corpus import stopwords
import random
import operator

# Loading Stopwords
stop_words = set(stopwords.words('english'))

vocab = [] 

# Dictionary that maps docID to a Scene Name
docdic = {}
playDic ={}
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
termstats = {}
def createstats():
    
    for k, value in term_position_dic.items():
        total_occurances = 0
        for v in value:
            total_occurances+= v[1]
        termstats[k] = {'#ofdocumnetsInCollection': len(value) ,'#ofoccurancesInCollection' : total_occurances}
    return termstats



def loadJSON():
    # Dictionary storing the
    # key: term
    # Value : [#document, position of word in text]
    termdic ={}
    
    #     For finding the average number of words in a scene
    totalnumberofscenes = 0
    currenttotal =0
    shortestscenelength = 99999999
    shortestscenename = ""
    curr_scene = ""
    
    with open("/Users/shivangisingh/Desktop/shakespeare-scenes.json",'r') as f:
        data = json.loads(f.read())
    
        doc_count= 1
    play = ""
    for obj in data['corpus']:
        for k,v in obj.items():    
    #   Parsing SceneID 
            if k== 'sceneId':
                curr_scene = v
                playindex = curr_scene.find(":")
                play = curr_scene[:playindex]
#                 print(play)
                if play not in playDic:
                    playDic[play] = 0
                
                totalnumberofscenes +=1
                if v not in docdic:
                    docdic[doc_count]= v.strip()
                    doc_count+=1
        #       Parsing the text field of each object
            if k == 'text':
        #           Tokenizing Text
                text = v.split(" ")
        #           Removing StopWords
                text = [word.strip() for word in text if word not in stop_words if len(word)!=None if word != " "]
                currenttotal += len(text)
                playDic[play] += len(text)
                if(shortestscenelength>len(text)):
                    shortestscenelength = len(text)
                    shortestscenename = curr_scene
#                     print("Updated", shortestscenename,shortestscenelength)
                
                
                term_pos = 1
                for term in text:
        #                 term_pos+=1
                    if term not in termdic:
                        termdic[term]=[[doc_count-1,term_pos]]
                    else :
                        termdic[term].append([doc_count-1,term_pos])
                    term_pos+=1
                    
    print("Average number of Wordsper scene",currenttotal/totalnumberofscenes)
    print("Smallest Scene", shortestscenename )
#     print("PlayDic",playDic)

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
    

# Function that deltaencodes and does vbyte compression for the lists

# from random import randint

K = 128

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


def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + int(b)
    return result

def compareVocab():
    return(set(CompressedLookup.keys()) == set(UncompressedLookup.keys()))


def longestPlay():
    print("Max word Play",max(playDic.items(), key=operator.itemgetter(1))[0])
def shortestPlay():
    print("Min Word Play",min(playDic.items(), key=operator.itemgetter(1))[0])
# Load the JSON
loadJSON()
# Loading Vocab
getvocab()
# DumpDocID
dumpDocumetID()
# Create Stats
term_stats = createstats()
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
longestPlay()
shortestPlay()
print("Checking Vocabulary:", compareVocab())


################################# Evaluation #############################################
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
def dicecoffeicient(t1,t2, flag, breader,UClookup):
    if flag == True:
#         Read Uncompressed
        
#         UClookup = readUCLookUpIntoMemory()
        
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
        
#         UClookup = readUCLookUpIntoMemory()
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


# Pass in the offset, size to read and filereader
def read_from_disk(byteoffset, bsize, breader):
#     3 of the numbers together make a number
    
    breader.seek(byteoffset)
    m = breader.read(bsize)
    array = []
    while len(m)>0:
        character = m[:3]
        array.append(bytes_to_int(character))
        m=m[3:]
        
    return(array)

breader = open("/Users/shivangisingh/Desktop/InformationRetrieval/CIndex.txt",'rb')
def readCompresssssssss(byteoffset, bsize, breader):
    breader.seek(byteoffset)
    m = breader.read(bsize)
#     print(m)
    array = DecodeByteArray(m)
    return array



# output a file of (term #ofdocumentswiththatterm termfrequency) on each line and a blank line between each run
# Stored the 7*100 list of words have to use this now Array of Arrays
seven_hundredtimes = []
def randomSelectandCheckTermDocFrequency():
    f = open("/Users/shivangisingh/Desktop/InformationRetrieval/randomSelectandCheckTermDocFrequency.txt", "a")
    t = open("/Users/shivangisingh/Desktop/InformationRetrieval/SevenHundredTerms.txt", "a")
    for i in range(100):
        seven = sevenrandomwords()
        seven_hundredtimes.append(seven)
        for s in seven:
            t.write(s +" ")
            line = ""
            docnum = term_stats[s]['#ofdocumnetsInCollection']
            termnum = term_stats[s]['#ofoccurancesInCollection']
            line = s+"  "+ str(docnum) +"  "+ str(termnum) 
            f.write(line)
            f.write('\n')
        t.write('\n')
        f.write('\n')
        f.write('\n')
    f.close()
randomSelectandCheckTermDocFrequency()


def dicewords():
    # Generating
    breader = open("/Users/shivangisingh/Desktop/InformationRetrieval/CIndex.txt",'rb')
    fresult =[]
    UClookup = readCLookUpIntoMemory()
    d = open("/Users/shivangisingh/Desktop/InformationRetrieval/Dicewords.txt", "a")
#     i=1
    for iteration in seven_hundredtimes:
        for term in iteration:

            result =[]
    #         CHECK FROM HERE
    #         Find Dices Coefficient Max one and write to a file?
            maxcoeff = -1
            maxterm = ""
    #         find dice coefficient between the term and the vocab
            for v in vocab:
                if v != term:
                    dvalue = dicecoffeicient(term,v, False,breader, UClookup)
                    if(dvalue > maxcoeff):
                        maxcoeff = dvalue
                        maxterm = v
            d.write(term + " " + maxterm+" ")
        d.write('\n')
        
dicewords()

import time
def undelta(arr):
#     Undothe delta
# Have to overwrite too
    temp = arr
    result = []
    
    prev_doc  = 0
    while(len(temp)>0):
        
        numberofterms = temp[1]
        positions = decode(temp[2:numberofterms+2])
        result.append(prev_doc+temp[0])
        result.append(numberofterms)
        result.extend(positions)
        prev_doc += temp[0]
        temp = temp[numberofterms+2:]

    return result
        
        
def decode(decodeme):
    prev = 0
    for i, v in enumerate(decodeme):
        current = v
        decodeme[i] += prev
        prev = current
    return decodeme

# returns an array of the top 5 docIDs
def getTopFive( doc_term_count):
    arr = []
    for i in range(5):
        docID = max(doc_term_count.iteritems(), key=operator.itemgetter(1))[0]
        arr.append(docID)
        try:
            del myDict[docID]
        except KeyError:
            pass
    return arr

def TermatatimeLookup(arr, doc_term_count):
    temp = arr
    while(len(temp)>0):
        docID = temp[0]
        numberofterms = temp[1]
        if docID not in doc_term_count:
            doc_term_count[docID] = numberofterms
        else:
            doc_term_count[docID] += numberofterms
    return doc_term_count


breader = open("/Users/shivangisingh/Desktop/InformationRetrieval/CIndex.txt",'rb')
def QueryTermsCompressed():
    doc_term_count ={}
    start_time = time.time()
    ULookup = readCLookUpIntoMemory()
#     Read the terms 
    with open("/Users/shivangisingh/Desktop/InformationRetrieval/SevenHundredTerms.txt",'r') as f:
        line = f.readlines()
        line = [x.strip() for x in line] 
#         print(lines) - array of lines
        for linex in line :
            QueryTerms = linex.split()
#             Perform Document at a time Evaluation
            for q in QueryTerms:
#                 Retrieve Index?
                byteoffset = ULookup[q]['offset']
                bsize = ULookup[q]['size']
                arr = undelta(readCompresssssssss(byteoffset, bsize, breader))
                doc_term_count = TermatatimeLookup(arr, doc_term_count)
#     By this time Doc Count has been updated accordingly
#     return top 5?
    top_five = getTopFive(doc_term_count)
    
    end_time = time.time()
    return(end_time - start_time )


print(QueryTermsCompressed())


def QueryTermsCompressedBig():
    doc_term_count ={}
    start_time = time.time()
    ULookup = readCLookUpIntoMemory()
#     Read the terms 
    with open("/Users/shivangisingh/Desktop/InformationRetrieval/Dicewords.txt",'r') as f:
        line = f.readlines()
        line = [x.strip() for x in line] 
#         print(lines) - array of lines
        for linex in line :
            QueryTerms = linex.split()
#             Perform Document at a time Evaluation
            for q in QueryTerms:
#                 Retrieve Index?
                byteoffset = ULookup[q]['offset']
                bsize = ULookup[q]['size']
                arr = undelta(readCompresssssssss(byteoffset, bsize, breader))
                doc_term_count = TermatatimeLookup(arr, doc_term_count)
    top_five = getTopFive(doc_term_count)
    print(top_five)
    end_time = time.time()
    
    return(end_time - start_time )

        

print(QueryTermsCompressedBig())

def QueryTermsUnCompressedBIG():
    breader = open("/Users/shivangisingh/Desktop/InformationRetrieval/UCIndex.txt",'rb')
    start_time = time.time()
    ULookup = readUCLookUpIntoMemory()
#     Read the terms 
    with open("/Users/shivangisingh/Desktop/InformationRetrieval/Dicewords",'r') as f:
        line = f.readlines()
        line = [x.strip() for x in line] 
#         print(lines) - array of lines
        for linex in line :
            QueryTerms = linex.split()
#             Perform Document at a time Evaluation
            for q in QueryTerms:
#                 Retrieve Index?
                byteoffset = ULookup[q]['offset']
                bsize = ULookup[q]['size']
                arr = undelta(readCompresssssssss(byteoffset, bsize, breader))
                doc_term_count = TermatatimeLookup(arr, doc_term_count)
    top_five = getTopFive(doc_term_count)
    print(top_five)
    end_time = time.time()  

    return (end_time - start_time )

print(QueryTermsUnCompressedBIG())