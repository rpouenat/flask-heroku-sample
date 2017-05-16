import os
import requests
from bs4 import BeautifulSoup
import re
from functools import wraps
import json

from flask import jsonify, Flask, abort, render_template, request, redirect, url_for
from flask_cors import CORS, cross_origin

app = Flask(__name__)

CORS(app)

def connected(fn):
    """Decorator that checks that requests
    contain an id-token in the request header.
    user will be None if the
    authentication failed, and have the User otherwise.

    Usage:
    @app.route("/")
    @authorized
    def secured_root(user=None):
        pass
    """
    @wraps(fn)
    def wrapped(*args, **kwargs):
        datas = request.get_json()
        user = datas.get('user','')
        if user is '':
            # Unauthorized
            abort(400)
            return None

        return fn(user=user, *args, **kwargs)
    return wrapped


def authorized(fn):
    """Decorator that checks that requests
    contain an id-token in the request header.
    user will be None if the
    authentication failed, and have the User otherwise.

    Usage:
    @app.route("/")
    @authorized
    def secured_root(user=None):
        pass
    """
    @wraps(fn)
    def wrapped(*args, **kwargs):
        datas = request.get_json()
        spip_session = datas.get('spip_session','')
        if spip_session is '':
            # Unauthorized
            abort(400)
            return None

        return fn(spip_session=spip_session, *args, **kwargs)
    return wrapped



@app.route('/', methods=['GET'])
def index():
  return render_template('index.html')


# Récupération du cookie de l'utilisateur
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

  # Post de la requête 
  post_data = {'var_ajax':'form', 'page':'login','lang':'fr','ajax':1,'formulaire_action':'login','formulaire_action_args':formulaire_action_args,'var_login':var_login,'password':password}
  post_response = requests.post(url=url, data=post_data)
  spip_session = post_response.cookies.get('spip_session')



  # On récupère la valeur de user
  url = "https://www.root-me.org/?page=news&lang=fr"
  s.cookies.update({
    "spip_session": spip_session
  })
  r = s.get(url)
  soup = BeautifulSoup(r.text, 'html.parser')
  user = (soup.find('a', {'class': 'hide-for-small-only'}).get('href')).split("?")[0]


  # On retourne la valeur de spip_session et user
  return jsonify(spip_session=spip_session,user=user),200




# Récupération des inforamtions lié au profile de l'utilisateur
@app.route('/profile', methods=['POST'])
@authorized
@connected
def profile(spip_session,user):

  s = requests.Session()

  s.cookies.update({
    "spip_session": spip_session
  })

  # On récupère la valeur de user
  url = "https://www.root-me.org/"+str(user)
  r = s.get(url)
  soup = BeautifulSoup(r.text, 'html.parser')
  name = soup.find('span', {'class': ' forum'}).text

  tab = soup.find_all('ul',{'class':'spip'})


  # statut, score, nbrPost, chatBox
  statut = tab[0].find_all('li')[1].text.split(":\xa0")[1]
  score = tab[0].find_all('li')[2].text.split(":\xa0")[1]
  nbrPost = tab[0].find_all('li')[3].text.split(":\xa0")[1]
  chatBox = tab[0].find_all('li')[4].text.split(":\xa0")[1]


  # Nombre de challenge validé, nombre de challenge total, classement, classement TOTAL
  url = "https://www.root-me.org/"+str(user)+"?inc=score"
  r = s.get(url)

  soup = BeautifulSoup(r.text, 'html.parser')
  tabNbrChall = soup.find('span', {'class': 'gris tm'}).text.strip().split("/")
  nbrChallValidate = tabNbrChall[0]
  nbrChallTotal = tabNbrChall[1]

  place = soup.find_all('span', {'class': 'color1 tl'})
  classement = place[1].text.strip().split("/")[0]
  nbrOfPeople = place[1].text.strip().split("/")[1]



  # Récupération des différents challenge
  tabChallenge = soup.find_all('div',{'class':'panel animated_box'})
  dicoChall = {}
  for challenge in tabChallenge:
    nameChallenge = challenge.find('h4').text.strip()
    pointChallenge = challenge.find('span',{'class':'gris'}).text.strip()
    pourcentageChall = challenge.find('div',{'class':'gris'}).text.strip()
    dicoChall[nameChallenge] = [{'Points':pointChallenge},{'Pourcentage':pourcentageChall}]


  return jsonify(name=name,score=score,statut=statut,nbrPost=nbrPost,chatBox=chatBox,nbrChallValidate=nbrChallValidate,nbrChallTotal=nbrChallTotal,classement=classement,nbrOfPeople=nbrOfPeople,challenge=json.dumps(dicoChall, ensure_ascii=False)),200









if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port, debug=True)
