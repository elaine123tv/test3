import json
import re
import os
import newspaper
from openai import OpenAI
from textblob import TextBlob
import BBCNewsScraper
import GuardianScraper
import MirrorScraper
import SkyNewsScraper
import TheSunScraper
import string
import nltk
import contractions
import pandas as pd

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import time


def clean(articleData, includeQuotes):

    punctuation_list = list(string.punctuation)

    for key, value in articleData.items():
        if key in ["title", "subTitle", "content"]:
            newValue = value

            newValue = re.sub(r'http[s]?://\S+|www\.\S+', '', newValue)
    
            # Remove email addresses (including .co.uk, .com, etc.)
            newValue = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:com|org|net|edu|gov|co\.uk|co|io|info|biz)\b', '', newValue)

            # standardise quotes
            newValue = newValue.replace("“", '"').replace("”", '"')

            # remove numbers, special chars except quotation marks
            newValue = re.sub(r'[^A-Za-z\s\'"]', '', newValue)

            # handling contractions#
            newValue = contractions.fix(newValue)
            newValue = newValue.replace("'s", " ")

            # if remove quotes
            if not includeQuotes:
                # Check if quotes are uneven
                quoteMarks = newValue.count("'")
                quoteMarks+= newValue.count('"')
                if quoteMarks and quoteMarks % 2 != 0:
                    print(f"⚠️ Warning: Uneven number of quotation marks ({quoteMarks}) in text.")

                # remove quotes
                newValue = re.sub(r'"(.*?)"', ' ', newValue)
                newValue = re.sub(r"'(.*?)'", ' ', newValue)

            # remove punctuation
            for punctuation in punctuation_list:
                newValue = newValue.replace(punctuation,  " ")

            # remove whitespace
            newValue = newValue.strip()
            
            if "US" in newValue:
                newValue = newValue.replace("US", "USA") # lemmatizer treating US as a plural noun, lematizing it to u
            tokens = word_tokenize(newValue.lower())

            # remove stopwords (e.g.  "the", "a")
            filteredTokens = [token for token in tokens if token not in stopwords.words('english') or token == "US"]
            
            # Reduce words to their base or root form to handle different variations of a word. e.g. "running -> run"
            lemmatizer = WordNetLemmatizer()
            lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filteredTokens]

            newValue = ' '.join(lemmatized_tokens)



            articleData[key] = newValue
        

    return articleData

def textBlobAnalysis(articleData):
    newContent = articleData["subTitle"] + " " + articleData["content"]
    for caption in articleData["captions"]:
        newContent+=" " + caption

    blob = TextBlob(articleData['title'])
    print("title: " + articleData['title'])
    blob2 = TextBlob(newContent)

    sentiment = blob.sentiment
    sentiment2 = blob2.sentiment
    analysis = {
        "titlePolarity": sentiment.polarity if articleData["title"] else "",
        "titleObjectivity": sentiment.subjectivity if articleData["title"] else "",
        "bodyPolarity": sentiment2.polarity if newContent else "",
        "bodyObjectivity": sentiment2.subjectivity if newContent else "",
    }
    return analysis

def nltkPolarityAnalysis(articleData):
    newContent = articleData["subTitle"] + " " + articleData["content"]
    for caption in articleData["captions"]:
        newContent+=" " + caption
    analyzer = SentimentIntensityAnalyzer()


    analysis = {
        "titlePolarity": analyzer.polarity_scores(articleData['title']) if articleData["title"] else "",
        "contentPolarity": analyzer.polarity_scores(newContent) if newContent else "",
    }

    return analysis

def gptAnalysis(articleData):

    apiKey = os.getenv("GPT_KEY")
    if "Captions" in articleData:
        captions = "Captions:" + articleData["Captions"]
    else:
        captions = ""
    if "Sub Titles" in articleData:
        subTitle = articleData["Sub Titles"]
    else:
        subTitle = ""
    
    with open(r'C:\Users\Boss (Dia)\OneDrive - Liverpool John Moores University\0final proj\llmBiasDetectorPrompt.txt', 'r') as file:
            promptTemplate = file.read()

    prompt = promptTemplate.format(insertTitle = articleData['title'],insertSubTitle=subTitle, insertContent=articleData['content'], insertCaptions=captions)
    print(prompt)
    client = OpenAI(api_key=apiKey)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a news bias and sentiment detector."},
            {"role": "user", "content": prompt},
        ]
    )
    content = response.choices[0].message.content
    results = json.loads(content)

    return results

