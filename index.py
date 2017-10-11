import xml.sax, os, sys, re, pdb
import Stemmer
from string import printable

numberOfDocuments = 0
numberOfFiles = 0
stopwords = {}
outputPath = ""
stemmer = Stemmer.Stemmer('english')
idToTitle = {}
titleDictionary = {}
infoboxDictionary = {}
bodyDictionary = {}
categoryDictionary = {}
linksDictionary = {}
referencesDictionary = {}

noise = u".,|+-@~`:;?()*\"'=\\&/<>[]{}#!%^$ "
punctuations = [u".", u",", u"|", u"-", u":", u";", u"?", u"(", u")", u"*", u"\"", u"\'", u"=", u'\\', u"&", u'/', u"<", u">", u"[", u"]", u"{", u"}", u"#", u"!", u"%"]
referencesRegex = re.compile(u"={2,3} ?references ?={2,3}.*?={2,3}", re.DOTALL)
linksRegex = re.compile(u"={2,3} ?external links?={2,3}.*?\n\n", re.DOTALL)
categoryRegex = re.compile(u"\[\[category:.*?\]\]", re.DOTALL)
infoboxRegex = re.compile(u"\{\{infobox.*?\}\}", re.DOTALL)
referenceSubjectRegex = "(={2,3} ?[rR]eferences ?={2,3})|(={2,3})|access|first|title|url|date|publisher|last|location|cite|web|book|article|author|year|isbn|ref|editor|volume|issue"

class xmlHandler(xml.sax.ContentHandler):
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        self.id = "NULL"
        self.tag = ""
        self.title = ""
        self.text = ""
        self.content = ""
        self.infobox = ""
        self.body = ""
        self.category = ""
        self.links = ""
        self.references = ""

    def startElement(self, tag, attributes):
        self.tag = tag
        if tag == "page":
            global numberOfDocuments
            numberOfDocuments += 1
            self.id = "NULL"

    def endElement(self, tag):
        if tag == "page":
            global idToTitle
            idToTitle[self.id] = self.title
            self.title = self.title.lower()
            self.text = self.text.lower()
            self.text = self.text.encode("ascii", "ignore")
            self.process()
            self.title = ""
            self.id = "NULL"
            self.text = ""
            self.infobox = ""
            self.body = ""
            self.category = ""
            self.links = ""
            self.references = ""
            global numberOfDocuments, numberOfFiles
            if numberOfDocuments % 1000 == 0:
                writeToFile()
                numberOfFiles += 1

    def characters(self, content):
        if self.tag == "id":
            if self.id == "NULL":
                self.id = content
        elif self.tag == "title":
            if self.title == "" and self.title != content:
                self.title = content
        elif self.tag == "text":
            self.text += content

    def process(self):
        '''
            infobox starts with "{{Infobox" and ends with "}}" note: infoboxes are multi-line
            category starts with "[[Category" and ends with "]]"
            external links have "==External links=="
            references have "==References=="
        '''
        text = self.text

        titleTokens = self.title.split()
        self.tokenize(titleTokens, "title")

        text = re.sub(r"\{\{[c|C]ite.*?\}\}", u"", text)
        try:
            self.references = referencesRegex.search(self.text).group()
        except AttributeError:
            pass

        if self.references != "":
            self.references = re.sub(referenceSubjectRegex, u"", self.references)
            text = re.sub(referencesRegex, u"==", text)
            referencesTokens = self.references.split()
            self.tokenize(referencesTokens, "references")

        self.category = re.findall(categoryRegex, self.text)
        text = re.sub(categoryRegex, u"", text)
        categoryTokens = []
        if self.category != []:
            for category in self.category:
                categoryTokens.extend(category[11:-2].split())
            self.tokenize(categoryTokens, "category")

        self.links = ""
        try:
            self.links = linksRegex.search(self.text).group()
            text = re.sub(linksRegex, u"", text).encode("ascii", "ignore")
        except AttributeError:
            pass

        if self.links:
            self.links = self.links.split("\n")
            for link in self.links:
                if link == "":
                    break
                linkTokens = link.split()
                self.tokenize(linkTokens, "links")

        try:
            infoboxTokens = infoboxRegex.search(text).group()
            infoboxTokens = infoboxTokens.split()
            if infoboxTokens != []:
                self.tokenize(infoboxTokens, "infobox")
                text = re.sub(infoboxRegex, "", text)
        except AttributeError:
            pass

        bodyTokens = text.split()
        self.tokenize(bodyTokens, "body")

    def tokenize(self, data, field):
        global titleDictionary, bodyDictionary, categoryDictionary, referencesDictionary, linksDictionary, infoboxDictionary, outputPath, numberOfFiles

        for line in data:
            words = re.split(u"(\|)|\-|\:|\;|\?|\(|\)|\*|\=|\\|\&|\/|\<|\>|\[|\]|\{|\}|\#|\+|\&|\%20|\_|\&nbsp|(\')|(\")", line)
            for word in words:
                if word is not None and len(word) > 1:
                    temp = word.strip(noise)
                    if temp not in stopwords:
                        temp = stemmer.stemWord(temp)
                        temp = temp.strip(noise)
                        temp = filter(lambda x: x in printable, temp)
                        if len(temp) == 0:
                            continue
                        if field == "title":
                            if temp not in titleDictionary:
                                titleDictionary[temp] = {}
                            if self.id not in titleDictionary[temp]:
                                titleDictionary[temp][self.id] = 1
                            else:
                                titleDictionary[temp][self.id] += 1
                        elif field == "body":
                            if temp not in bodyDictionary:
                                bodyDictionary[temp] = {}
                            if self.id not in bodyDictionary[temp]:
                                bodyDictionary[temp][self.id] = 1
                            else:
                                bodyDictionary[temp][self.id] += 1
                        elif field == "category":
                            if temp not in categoryDictionary:
                                categoryDictionary[temp] = {}
                            if self.id not in categoryDictionary[temp]:
                                categoryDictionary[temp][self.id] = 1
                            else:
                                categoryDictionary[temp][self.id] += 1
                        elif field == "references":
                            if temp not in referencesDictionary:
                                referencesDictionary[temp] = {}
                            if self.id not in referencesDictionary[temp]:
                                referencesDictionary[temp][self.id] = 1
                            else:
                                referencesDictionary[temp][self.id] += 1
                        elif field == "links":
                            if temp not in linksDictionary:
                                linksDictionary[temp] = {}
                            if self.id not in linksDictionary[temp]:
                                linksDictionary[temp][self.id] = 1
                            else:
                                linksDictionary[temp][self.id] += 1
                        else:
                            if temp not in infoboxDictionary:
                                infoboxDictionary[temp] = {}
                            if self.id not in infoboxDictionary[temp]:
                                infoboxDictionary[temp][self.id] = 1
                            else:
                                infoboxDictionary[temp][self.id] += 1

def writeToFile():
    global titleDictionary, bodyDictionary, categoryDictionary, referencesDictionary, linksDictionary, infoboxDictionary, outputPath, numberOfFiles

    # dump title dictionary
    fileName = str(outputPath) + "/Title/title" + str(numberOfFiles) + ".txt"
    f = open(fileName, "w")

    for key in sorted(titleDictionary.items()):
        entry = key[0] + ":"
        for docID in key[1]:
            entry += str(docID) + "," + str(titleDictionary[key[0]][docID]) + "|"
        entry = entry[:-1]
        entry += "\n"
        f.write(entry.encode("utf-8"))
    f.close()

    # dump body dictionary
    fileName = str(outputPath) + "/Body/body" + str(numberOfFiles) + ".txt"
    f = open(fileName, "w")

    for key in sorted(bodyDictionary.items()):
        entry = key[0] + ":"
        for docID in key[1]:
            entry += str(docID) + "," + str(bodyDictionary[key[0]][docID]) + "|"
        entry = entry[:-1]
        entry += "\n"
        f.write(entry.encode("utf-8"))
    f.close()

    # dump category dictionary
    fileName = str(outputPath) + "/Category/category" + str(numberOfFiles) + ".txt"
    f = open(fileName, "w")

    for key in sorted(categoryDictionary.items()):
        entry = key[0] + ":"
        for docID in key[1]:
            entry += str(docID) + "," + str(categoryDictionary[key[0]][docID]) + "|"
        entry = entry[:-1]
        entry += "\n"
        f.write(entry.encode("utf-8"))
    f.close()

    # dump references
    fileName = str(outputPath) + "/References/references" + str(numberOfFiles) + ".txt"
    f = open(fileName, "w")

    for key in sorted(referencesDictionary.items()):
        entry = key[0] + ":"
        for docID in key[1]:
            entry += str(docID) + "," + str(referencesDictionary[key[0]][docID]) + "|"
        entry = entry[:-1]
        entry += "\n"
        f.write(entry.encode("utf-8"))
    f.close()

    # dump infobox
    fileName = str(outputPath) + "/Infobox/infobox" + str(numberOfFiles) + ".txt"
    f = open(fileName, "w")

    for key in sorted(infoboxDictionary.items()):
        entry = key[0] + ":"
        for docID in key[1]:
            entry += str(docID) + "," + str(infoboxDictionary[key[0]][docID]) + "|"
        entry = entry[:-1]
        entry += "\n"
        f.write(entry.encode("utf-8"))
    f.close()

    # dump links
    fileName = str(outputPath) + "/Links/links" + str(numberOfFiles) + ".txt"
    f = open(fileName, "w")

    for key in sorted(linksDictionary.items()):
        entry = key[0] + ":"
        for docID in key[1]:
            entry += str(docID) + "," + str(linksDictionary[key[0]][docID]) + "|"
        entry = entry[:-1]
        entry += "\n"
        f.write(entry.encode("utf-8"))
    f.close()

    titleDictionary.clear()
    infoboxDictionary.clear()
    categoryDictionary.clear()
    referencesDictionary.clear()
    linksDictionary.clear()
    bodyDictionary.clear()

if __name__ == "__main__":
    corpus = sys.argv[1]
    outputPath = sys.argv[2]
    with open('stopwords.txt') as f:
        for words in f:
            word = words.strip()
            if word:
                stopwords[word] = 1
    for stopword in noise:
        stopwords[stopword] = 1
    for stopword in punctuations:
        stopwords[stopword] = 1

    xml.sax.parse(open(corpus, "r"), xmlHandler())
    if numberOfDocuments % 1000 != 0:
        writeToFile()
        numberOfFiles += 1

    fileName = str(outputPath) + "/titles.txt"
    f = open(fileName, "w")
    entry = str(numberOfFiles) + "\n"
    f.write(entry)
    entry = str(numberOfDocuments) + "\n"
    f.write(entry)
    keys = idToTitle.keys()
    keys.sort()
    for key in keys:
        entry = key + "-" + idToTitle[key] + "\n"
        f.write(entry.encode("utf-8"))
    f.close()
