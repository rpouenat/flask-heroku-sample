import os
import requests
from bs4 import BeautifulSoup

from flask import jsonify, Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
  return render_template('index.html')

@app.route('/authUser', methods=['POST'])
def authUser():
  datas = request.get_json()
  var_login = datas.get('var_login','')
  password = datas.get('password','')

  # Récupération du paramètre formulaire_action_args
  url = "https://www.root-me.org/?page=login&lang=fr&ajax=1"
  s = requests.Session()
  r = s.get(url)
  soup = BeautifulSoup(r.text, 'html.parser')
  formulaire_action_args = soup.find('input', {'name': 'formulaire_action_args'}).get('value')
  print(formulaire_action_args)

  # Post de la requête 
  post_data = {'var_ajax':'form', 'page':'login','lang':'fr','ajax':1,'formulaire_action':'login','formulaire_action_args':formulaire_action_args,'var_login':var_login,'password':password}
  post_response = requests.post(url=url, data=post_data)
  print(post_response.text)
  print(post_response.cookies.get('spip_session'))


  return jsonify(spip_session=post_response.cookies.get('spip_session')),200


@app.route('/user', methods=['POST'])
def user():
  u = User(request.form['name'], request.form['email'])
  db.session.add(u)
  db.session.commit()
  return redirect(url_for('index'))


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port, debug=True)
