import os
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import mysql.connector

# Chemin absolu vers les dossiers template et static
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'template')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
CORS(app)

# Configuration de la base de données
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'invitation'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/verifi-guest', methods=['POST'])
def verifiy_guest():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Données introuvables"}), 400

    nom_saisi = data.get('nom', '').strip().upper()
    postnom_saisi = data.get('postnom', '').strip().upper()
    prenom_saisi = data.get('prenom', '').strip()
    telephone_saisi = data.get('telephone', '').strip()
    statut_saisi = data.get('statut', 'celibataire')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Recherche de l'invité
        query = """
            SELECT * FROM guests
            WHERE UPPER(nom) = %s AND UPPER(postnom) = %s AND LOWER(prenom) = LOWER(%s)
        """
        cursor.execute(query, (nom_saisi, postnom_saisi, prenom_saisi))
        guest = cursor.fetchone()  # Récupération du résultat

        if guest:
            # Mise à jour de la confirmation
            update_query = """
                UPDATE guests
                SET a_confirme = TRUE, telephone = %s, statut = %s
                WHERE id = %s
            """
            new_phone = telephone_saisi if telephone_saisi else guest['telephone']
            cursor.execute(update_query, (new_phone, statut_saisi, guest['id']))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Invitation trouvée et confirmée !",
                "guest": {
                    "nom": guest['nom'],
                    "postnom": guest['postnom'],
                    "prenom": guest['prenom'],
                    "table": guest['table_assignee'],
                    "place": guest['nombre_places'],
                    "confirme": True
                }
            }), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "message": "Aucun invité ne correspond aux infos saisies. Veuillez contacter l'administrateur."
            }), 404

    except mysql.connector.Error as err:
        print(f"Erreur MySQL : {err}")
        return jsonify({"success": False, "message": "Erreur de connexion à la base de données"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)