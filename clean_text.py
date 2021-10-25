import nltk
from nltk.stem import WordNetLemmatizer
from constants import DB_HOST,DB_NAME, DB_USER, DB_PASSWORD

from googletrans import Translator

import mysql.connector
from mysql.connector import Error

wordnet_lemmatizer = WordNetLemmatizer()
translator = Translator()

def clean_requirements(min_words = 5):
    try:
        connection = mysql.connector.connect(host=DB_HOST,
                                            database=DB_NAME,
                                            user=DB_USER,
                                            password=DB_PASSWORD)
        if connection.is_connected():
            cursor = connection.cursor()
            requirements_query = '''SELECT requirement_id, action_description, LOWER(SUBSTR(pu.location_code, 1, 2)) AS code FROM requirement as r 
                                    LEFT JOIN product_backlog pb ON r.product_backlog_id = pb.product_backlog_id
                                    LEFT JOIN project p ON p.project_id = pb.project_id
                                    LEFT JOIN profile_user pu ON pu.profile_user_id = p.profile_user_id
                                    WHERE r.clean_action_description IS NULL OR r.clean_action_description = ""'''
            cursor.execute(requirements_query)
            requirement_records = cursor.fetchall()

            raw_requirements = []
            updated_requirements = []
            
            for row in requirement_records:
                if len(row[1].split(sep=" ")) >= min_words:
                    raw_requirements.append({
                        'id': row[0],
                        'actionDescription': translator.translate(row[1], src=row[2], dest="en").text,
                    })
            
            for raw_requirement in raw_requirements:
                cleaned_action_description = ' '.join(wordnet_lemmatizer.lemmatize(w.lower()) for w in nltk.wordpunct_tokenize(raw_requirement.get("actionDescription")) if w.isalpha())  # w.lower() in words and
                updated_requirements.append((cleaned_action_description, raw_requirement.get("id")))

            sql_update_query = """UPDATE requirement set clean_action_description = %s where requirement_id = %s"""

            cursor.executemany(sql_update_query, updated_requirements)
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