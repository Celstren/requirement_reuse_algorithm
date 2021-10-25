from train_doc2vec import model_trainer
from extract_phrases import attribute_extractor
from clean_text import clean_requirements
from flask import Flask, request
from flask_cors import CORS, cross_origin
from requirement_generator import requirement_generation
import os

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/generator", methods=['POST'])
def generator():
    if request.args.get('marketTypeId') is None:
        return 'Bad Request', 400
    clusters = 5
    iterations = 1
    if request.args.get('clusters') is not None:
        clusters = int(request.args.get('clusters'))
    if request.args.get('iterations') is not None:
        iterations = int(request.args.get('iterations'))
    market_type_id = request.args.get('marketTypeId')
    translate_to = "es"
    if request.args.get('translateTo') is not None:
        translate_to = request.args.get('translateTo')
    requirements = requirement_generation(clusters, iterations, market_type_id, translate_to)
    return {
        "data": requirements
    }

@app.route("/cleaner", methods=['POST'])
def cleaner():
    success = clean_requirements()
    return {
        "success": success
    }

@app.route("/extractor", methods=['POST'])
def extractor():
    success = attribute_extractor()
    return {
        "success": success
    }

@app.route("/trainer", methods=['POST'])
def trainer():
    success = model_trainer()
    return {
        "success": success
    }

@app.route("/process-algorithm", methods=['POST'])
def processAlgorithm():
    min_requirements = 0
    min_words = 5
    if request.args.get('minRequirements') is not None:
        min_requirements = int(request.args.get('minRequirements'))
    if request.args.get('minWords') is not None:
        min_words = int(request.args.get('minWords'))
    clean_success = clean_requirements(min_requirements, min_words)
    attribute_success = attribute_extractor(min_requirements)
    trainer_success = model_trainer(min_requirements)
    return {
        "success": clean_success and attribute_success and trainer_success
    }

@app.route("/hello", methods=['POST'])
@cross_origin()
def greetings():
    return "Hello"


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', debug = True, port=port)