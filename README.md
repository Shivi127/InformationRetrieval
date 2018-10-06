# InformationRetrieval
CS:590R

This code is used to Build an Inverted Index on the Shakspeare Corpus. 
To load the file and make a simple inverted index call the functions in the following order

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
print("Checking Vocabulary:", compareVocab())
