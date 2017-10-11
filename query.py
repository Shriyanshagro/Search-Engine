import xml.sax, os, sys, re, pdb, linecache, operator, time, subprocess
import Stemmer
from string import printable
from math import log10

stemmer = Stemmer.Stemmer('english')
indexFolder = "Merged/"
numberOfDocuments = 0
idToTitle = {}
noise = u".,|+-@~`:;?()*\"'=\\&/<>[]{}#!%^$ "
frequentWords = [u".", u",", u"|", u"-", u":", u";", u"?", u"(", u")", u"*", u"\"", u"\'", u"=", u'\\', u"&", u'/', u"<", u">", u"[", u"]", u"{", u"}", u"#", u"!", u"%", "access", "first", "title", "url", "date", "publisher", "last", "location", "cite", "web", "book", "article", "author", "year", "isbn", "ref", "editor", "volume", "issue"]
stopwords = {}
linesInIndex = {"title": 0, "infobox": 0, "body": 0, "category": 0, "links": 0, "references": 0}
weights = {"title": 100.000, "infobox": 0.500, "body": 0.750, "category": 0.750, "links": 0.100, "references": 0.750}
tfidfScores = {}

def init():
    global stopwords, numberOfDocuments, stopwords, linesInIndex
    fileName = indexFolder + "titles.txt"
    first = 0
    with open(fileName) as f:
        for line in f:
            if first == 0:
                numberOfDocuments = int(line)
                first = 1
            else:
                line = line.split("-")
                idToTitle[int(line[0])] = line[1:]

    with open('stopwords.txt') as f:
        for words in f:
            word = words.strip()
            if word:
                stopwords[word] = 1
    for stopword in frequentWords:
        stopwords[stopword] = 1

    fileName = indexFolder + "Category/offset.txt"
    linesInIndex["category"] = sum(1 for line in open(fileName))
    fileName = indexFolder + "Links/offset.txt"
    linesInIndex["links"] = sum(1 for line in open(fileName))
    fileName = indexFolder + "Infobox/offset.txt"
    linesInIndex["infobox"] = sum(1 for line in open(fileName))
    fileName = indexFolder + "Title/offset.txt"
    linesInIndex["title"] = sum(1 for line in open(fileName))
    fileName = indexFolder + "References/offset.txt"
    linesInIndex["references"] = sum(1 for line in open(fileName))
    fileName = indexFolder + "Body/offset.txt"
    linesInIndex["body"] = sum(1 for line in open(fileName))

def getPostingList(word, field):
    folderName = field
    if field == "title":
        folderName = "Title/offset.txt"
    elif field == "infobox":
        folderName = "Infobox/offset.txt"
    elif field == "body":
        folderName = "Body/offset.txt"
    elif field == "category":
        folderName = "Category/offset.txt"
    elif field == "links":
        folderName = "Links/offset.txt"
    elif field == "references":
        folderName = "References/offset.txt"
    fileName = indexFolder + folderName

    fileNumber = -1
    low = 0
    high = linesInIndex[field]-1
    while(low<=high):
        mid = (low+high)/2
        cur = linecache.getline(fileName, mid).strip()
        if cur == word:
            fileNumber = mid
            break
        elif cur > word:
            high = mid-1
        else:
            low = mid+1
    fileNumber = high

    if fileNumber > linesInIndex[field]-1:
        fileNumber = linesInIndex[field]-1
    fileName = indexFolder + folderName[:-10] + "/" + field + str(fileNumber) + ".txt"
    command = "wc -l " + fileName
    result = subprocess.check_output(command, shell=True)
    numberOfLines = int(result.split()[0])
    #numberOfLines = sum(1 for line in open(fileName))

    posting = []
    low = 1
    high = numberOfLines
    while (low<=high):
        mid = (low+high)/2
        cur = linecache.getline(fileName, mid).split(":")
        if cur[0] == word:
            posting = cur[1]
            break
        elif cur[0] > word:
            high = mid-1
        else:
            low = mid+1

    if posting == []:
        return []
    postingList = posting.split("|")
    return postingList[:500]

def computeTfIdf(field, postingList):
    global tfidfScores
    for posting in postingList:
        temp = posting.split(",")
        docID = temp[0]
        termFrequency = int(temp[1])
        tf = log10(1.0 + termFrequency)
        idf = log10((1.0 * numberOfDocuments)/len(postingList))
        if docID in tfidfScores:
            tfidfScores[docID] += weights[field] * tf * idf
        else:
            tfidfScores[docID] = weights[field] * tf * idf

if __name__ == "__main__":
    print "Loading."
    init()
    print "Loading completed."
    while True:
        fieldDictionary = {"title": None, "infobox": None, "body": None, "category": None, "links": None, "references": None}

        query = raw_input()
        query = query.strip()
        query = query.lower()
        if query == "exit":
            exit()
        startTime = time.time()
        #fields = {"title": 0, "infobox": 0, "body": 0, "category": 0, "links": 0, "references": 0}
        '''if query.find("t:") != -1:
            fields["title"] = 1
        if query.find("i:") != -1:
            fields["infobox"] = 1
        if query.find("b:") != -1:
            fields["body"] = 1
        if query.find("c:") != -1:
            fields["category"] = 1
        if query.find("l:") != -1:
            fields["links"] = 1
        if query.find("r:") != -1:
            fields["references"] = 1
        fielded = False
        for (key, value) in fields.iteritems():
            if value != 0:
                fielded = True
                break'''
        fielded = False
        categories = ["b:", "r:", "t:", "i:", "e:", "c:"]
        for category in categories:
            if category in query:
                fielded = True
                break
        if fielded:
            temp = re.split("(b\:)|(r\:)|(t\:)|(i\:)|(l\:)|(c\:)", query)
            temp = filter(lambda x: x != None and x != "", temp)
            for i in xrange(len(temp)):
                term = temp[i]
                if term == "t:" or term == "i:" or term == "b:" or term == "c:" or term == "l:" or term == "r:":
                    tempList = []
                    words = temp[i+1].split()
                    for word in words:
                        wordList = re.split(u"(\|)|\-|\:|\;|\?|\(|\)|\*|\=|\\|\&|\/|\<|\>|\[|\]|\{|\}|\#|\+|\&|\%20|\_|\&nbsp|(\')|(\")", word)
                        for token in wordList:
                            if token is not None and len(token) > 1:
                                temp2 = token.strip(noise)
                                if temp2 not in stopwords:
                                    temp2 = stemmer.stemWord(temp2)
                                    temp2 = temp2.strip(noise)
                                    temp2 = filter(lambda x: x in printable, temp2)
                                    if len(temp2) == 0:
                                        continue
                                    tempList.append(temp2)
                    if term == "t:":
                        fieldDictionary["title"] = tempList
                    elif term == "i:":
                        fieldDictionary["infobox"] = tempList
                    elif term == "b:":
                        fieldDictionary["body"] = tempList
                    elif term == "c:":
                        fieldDictionary["category"] = tempList
                    elif term == "l:":
                        fieldDictionary["links"] = tempList
                    elif term == "r:":
                        fieldDictionary["references"] = tempList
        else:
            tempList = []
            words = query.split()
            for word in words:
                wordList = re.split(u"(\|)|\-|\:|\;|\?|\(|\)|\*|\=|\\|\&|\/|\<|\>|\[|\]|\{|\}|\#|\+|\&|\%20|\_|\&nbsp|(\')|(\")", word)
                for token in wordList:
                    if token is not None and len(token) > 1:
                        temp = token.strip(noise)
                        if temp not in stopwords:
                            temp = stemmer.stemWord(temp)
                            temp = temp.strip(noise)
                            temp = filter(lambda x: x in printable, temp)
                            if len(temp) == 0:
                                continue
                            tempList.append(temp)
            for field in fieldDictionary:
                fieldDictionary[field] = tempList
        for field in fieldDictionary:
            if fieldDictionary[field]:
                for word in fieldDictionary[field]:
                    postingList = getPostingList(word, field)
                    computeTfIdf(field, postingList)
                    '''for (docID, score) in wordScores.iteritems():
                        if docID in tfidfScores:
                            tfidfScores[docID] += score
                        else:
                            tfidfScores[docID] = score'''
        sortedTfIdfScores = sorted(tfidfScores.items(), key=operator.itemgetter(1), reverse=True)
        count = 0
        for doc in sortedTfIdfScores:
            print "Document ID: ", int(doc[0]),  "Document Title: ", idToTitle[int(doc[0])][0].strip()
            count += 1
            if count == 10:
                break
        if count == 0:
            print "No results found"
        print "Time taken: ", time.time()-startTime, "seconds"
        tfidfScores = {}
