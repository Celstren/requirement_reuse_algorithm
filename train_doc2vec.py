'''
Clustering software requirements (as a sentence) using doc2vec
'''

import spacy
from spacy.tokenizer import Tokenizer
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.test.utils import get_tmpfile
import os
from constants import DB_HOST,DB_NAME, DB_USER, DB_PASSWORD
import mysql.connector
from mysql.connector import Error

nlp = spacy.load('en_core_web_sm')

def model_trainer(min_requirements = 0):

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
                
                features = []
                
                for cleaned_requirement in cleaned_requirements:
                    tokenizer = Tokenizer(nlp.vocab)
                    tokens = [token.text for token in tokenizer(cleaned_requirement.get("cleanActionDescription").replace('\n', ''))]
                    features.append(tokens)
                
                documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(features)]
                model = Doc2Vec(documents, vector_size=20, window=2, min_count=1, workers=4)
                
                model.delete_temporary_training_data(keep_doctags_vectors=True, keep_inference=True)

                fname = get_tmpfile(os.path.join(os.getcwd(), 'model', "model_" + str(market[0])))
                model.save(fname)
        return True
    except Error as e:
        print("Error while connecting to MySQL", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")