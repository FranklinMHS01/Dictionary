import os 
from os.path import join ,dirname
from dotenv import load_dotenv

from flask import Flask, render_template, jsonify, request, redirect, url_for
import requests
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

dotenv_path = join(dirname(__file__),'.env_dictionary')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get('MONGODB_URI')
DB_NAME = os.environ.get('DB_NAME')

url_db = MongoClient(MONGODB_URI)
client = MongoClient(url_db)
db = client[DB_NAME]

app = Flask(__name__)

@app.route('/')
def main() :
    words_result = db.words.find({}, {"_id":False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word' : word['word'],
            'definition' : definition,
        })
    msg = request.args.get('msg')
    return render_template('index.html', words = words, msg=msg)

@app.route('/error')
def error():  
    words_result = db.words.find({}, {"_id":False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word' : word['word'],
            'definition' : definition,
        })
    msg = request.args.get('msg')
    msg_2 = request.args.get('msg_2')
    suggestion = request.args.get('suggestion')
    return render_template('error.html', words = words, msg=msg,msg_2 = msg_2, suggestion=suggestion)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = '325d00a1-e2c0-4544-9bdd-1701085964ab'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'

    response =requests.get(url)
    definitions = response.json()

    if not definitions:
        return redirect(url_for(
            'error',
            msg = f'Could Not Find The Word, "{keyword}"'
        ))

    if type(definitions[0]) is str:
        suggestion = ",".join(definitions)
                
        return redirect (url_for(
            'error',
            msg = f'Could Not find The Word, "{keyword}"',
            msg_2 = f"did you mean one of these word",
            suggestion = suggestion
        ))

    status = request.args.get('status_give', 'new')

    return render_template('detail.html', word = keyword, definitions = definitions, status = status)


@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data =request.get_json()
    word = json_data.get('word_give')
    definitions =json_data.get('definitions_give')
    doc = {
        'word' : word,
        'definitions' : definitions,
        'date': datetime.now().strftime('%Y-%m-%d')
    }

    db.words.insert_one(doc)

    return jsonify ({
        'result' : "success",
        'msg' : f'the word, {word},  was saved',
    })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word' : word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} deleted'
    })

@app.route("/api/save_ex", methods=["POST"])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')

    doc = {
        'word' : word,
        'example' : example,
    }

    db.examples.insert_one(doc)
    return jsonify ({
        "result" : "success",
        "msg" : f"your sentense, {example}, for the word, {word}, was saved"
    })

@app.route('/api/get_exs',methods=['GET'])
def get_exs():
    word = request.args.get('word_give'),
    example_data = list(db.examples.find({},{'_id':False}))
    return jsonify({
        'result' : 'success',
        'examples' : example_data
    })


@app.route('/api/delete_exs', methods=['POST'])
def delete_exs():
    sentence = request.form.get('sentence_give')
    word = request.form.get('word')
    db.examples.delete_one({'example': sentence})
    
    return jsonify ({
        "result" : 'success',
        'msg' : f'Your sentence, {sentence},was deleted!',
    })
if __name__ == '__main__':
    app.run ('0.0.0.0', port=5000, debug=True)