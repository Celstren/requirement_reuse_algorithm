'''
Generate new requirements
'''

from utils import make_requirements
from cluster import cluster_requirements
from constants import DB_HOST,DB_NAME, DB_USER, DB_PASSWORD

import mysql.connector
from mysql.connector import Error

from googletrans import Translator

import spacy
import numpy as np
import os

nlp = spacy.load('en_core_web_sm')
translator = Translator()

def requirement_generation(NUM_CLUSTERS, iterations, market_type_id, dest = "es"):
    model_path = os.path.join(os.getcwd(), 'model', 'model_' + market_type_id)

    try:
        connection = mysql.connector.connect(host=DB_HOST,
                                            database=DB_NAME,
                                            user=DB_USER,
                                            password=DB_PASSWORD)
        if connection.is_connected():
            cursor = connection.cursor()
            locations_query = '''SELECT LOWER(SUBSTR(pu.location_code, 1, 2)) AS code FROM requirement as r 
                                    LEFT JOIN product_backlog pb ON r.product_backlog_id = pb.product_backlog_id
                                    LEFT JOIN project p ON p.project_id = pb.project_id
                                    LEFT JOIN profile_user pu ON pu.profile_user_id = p.profile_user_id 
                                    WHERE p.market_type_id = %a AND r.clean_action_description != ""
                                    GROUP BY code ''' %(market_type_id)
            cursor.execute(locations_query)
            location_records = cursor.fetchall()
            for location_source in location_records:
                location_code = location_source[0]
                requirements_query = '''SELECT requirement_id, clean_action_description, popularity, pu.location_code FROM requirement as r 
                                            LEFT JOIN product_backlog pb ON r.product_backlog_id = pb.product_backlog_id
                                            LEFT JOIN project p ON p.project_id = pb.project_id
                                            LEFT JOIN profile_user pu ON pu.profile_user_id = p.profile_user_id 
                                            WHERE p.market_type_id = %a AND r.clean_action_description != "" AND UPPER(pu.location_code) LIKE UPPER("%s")''' %(market_type_id, "%" + location_code + "%")
                cursor.execute(requirements_query)
                requirement_records = cursor.fetchall()

                cleaned_requirements = []
                
                for row in requirement_records:
                    cleaned_requirements.append({
                        'id': row[0],
                        'cleanActionDescription': row[1],
                        'popularity': row[2],
                        'locationCode': row[3],
                    })

                cluster_arr = cluster_requirements(model_path, cleaned_requirements, NUM_CLUSTERS)

                indices = [np.where(cluster_arr == i) for i in range(NUM_CLUSTERS)]

                probabilities = []

                for ind in indices:
                    prob = [ cleaned_requirements[i].get("popularity") for i in ind[0] ]
                    total_probability = sum(prob)
                    prob = [ probability / total_probability for probability in prob ]
                    probabilities.append(prob)
                
                boilerplates_query = '''SELECT verb, phrase_object, detail, requirement_id FROM boilerplate
                                        WHERE market_type_id = %a''' %(market_type_id)

                cursor.execute(boilerplates_query)
                boilerplate_records = cursor.fetchall()

                boilerplates = []

                for row in boilerplate_records:
                    boilerplates.append({
                        'verb': row[0],
                        'object': row[1],
                        'detail': row[2],
                        'requirementId': row[3],
                    })
                
                requirements = set([])

                for i in range(iterations):
                    for ind, probs in zip(indices, probabilities):
                        triple = np.random.choice(ind[0], 3, p=probs)
                        bl_1 = next(filter(lambda bp: bp.get("requirementId") == int(cleaned_requirements[triple[0]].get("id")), boilerplates), None)
                        bl_2 = next(filter(lambda bp: bp.get("requirementId") == int(cleaned_requirements[triple[1]].get("id")), boilerplates), None)
                        bl_3 = next(filter(lambda bp: bp.get("requirementId") == int(cleaned_requirements[triple[2]].get("id")), boilerplates), None)

                        requirements.update(make_requirements([bl_1, bl_2, bl_3]))
                
                requirements = list(requirements)
                
                for idx, requirement in enumerate(requirements):
                    requirements[idx] = translator.translate(requirement, src="en", dest=dest).text

                return requirements
        else:
            return []

    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")