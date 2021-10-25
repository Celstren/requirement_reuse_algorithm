# from textblob import TextBlob
import spacy
from spacy.symbols import VERB
from constants import DB_HOST,DB_NAME, DB_USER, DB_PASSWORD
import mysql.connector
from mysql.connector import Error

nlp = spacy.load('en_core_web_sm')
stopwords = list(spacy.lang.en.stop_words.STOP_WORDS)

def extract_verbs_nps_pair(sentence):

    doc = nlp(sentence)

    verbs = []
    objects = []
    additional_details = []

    noun_phrases = []

    for np in list(doc.noun_chunks):
        t = str(np)
        if t not in noun_phrases and t not in stopwords:
            noun_phrases.append(t)

    start = 0
    ix = 0
    while ix < len(noun_phrases):
        l = len(noun_phrases[ix])

        pos = sentence.find(noun_phrases[ix])
        doc2 = nlp(sentence[start:pos])
        for token in reversed(doc2):

            if token.pos == VERB and token.text != 'should':
                v = token.lemma_
                obj = noun_phrases[ix].replace(token.text, '')
                if ix < len(noun_phrases) - 1:
                    detail = noun_phrases[ix+1]
                else:
                    detail = 'NA'

                verbs.append(v)
                objects.append(obj)
                additional_details.append(detail)

                ix += 1
                break
            start = pos + l
        ix += 1

    return verbs, objects, additional_details

def attribute_extractor(min_requirements = 0):
    try:
        connection = mysql.connector.connect(host=DB_HOST,
                                            database=DB_NAME,
                                            user=DB_USER,
                                            password=DB_PASSWORD)
        if connection.is_connected():
            cursor = connection.cursor()

            markets_query = '''SELECT p.market_type_id FROM requirement as r 
                                    LEFT JOIN product_backlog pb ON r.product_backlog_id = pb.product_backlog_id
                                    LEFT JOIN project p ON p.project_id = pb.project_id
                                    GROUP BY p.market_type_id
                                    HAVING COUNT(*) >= %a''' %(min_requirements)
            cursor.execute(markets_query)
            market_records = cursor.fetchall()

            for market in market_records:
                requirements_query = '''SELECT requirement_id, clean_action_description, popularity FROM requirement as r 
                                    LEFT JOIN product_backlog pb ON r.product_backlog_id = pb.product_backlog_id
                                    LEFT JOIN project p ON p.project_id = pb.project_id 
                                    WHERE p.market_type_id = %a AND r.clean_action_description IS NOT NULL AND r.clean_action_description != ""''' %(market[0])
                cursor.execute(requirements_query)
                requirement_records = cursor.fetchall()

                cleaned_requirements = []
                
                for row in requirement_records:
                    cleaned_requirements.append({
                        'id': row[0],
                        'cleanActionDescription': row[1],
                        'popularity': row[2],
                    })

                boilerplates = []
            
                for cleaned_requirement in cleaned_requirements:
                    vs, nps, dets = extract_verbs_nps_pair(cleaned_requirement.get("cleanActionDescription"))
                    if vs != None and nps != None and dets != None:
                        for (v, np, det) in zip(vs, nps, dets):
                            boilerplates.append((v, np, det, cleaned_requirement.get("id"), market[0]))

                clean_boilerplate = '''DELETE FROM boilerplate
                                        WHERE market_type_id = %s''' %(market[0])
                cursor.execute(clean_boilerplate)
                
                sql_insert_query = """INSERT INTO boilerplate
                                    (verb, phrase_object, detail, requirement_id, market_type_id)
                                    VALUES(%s, %s, %s, %s, %s)"""
            
                cursor.executemany(sql_insert_query, boilerplates)
                connection.commit()

        return True
    except Error as e:
        print("Error while connecting to MySQL", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")