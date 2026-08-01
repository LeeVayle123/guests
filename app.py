import os
from flask import Flask, request, render_template, jsonify, session
from flask_cors import CORS
import mysql.connector
from flask import redirect, url_for

# Configuration de Flask avec template a la racine
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder=base_dir, static_folder=base_dir)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')
CORS(app)

# Configuration sécurisée via variables d'environnement
def get_db_connection():
    host = os.environ.get('DB_HOST', 'localhost')
    user = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASSWORD', '')
    database = os.environ.get('DB_NAME', 'invitation')
    port = int(os.environ.get('DB_PORT', 3306))
    
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        connect_timeout=5
    )


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

    except Exception as err:
        print(f"Erreur DB / Serveur : {err}")
        return jsonify({"success": False, "message": "Connexion à la base de données temporairement indisponible."}), 500


@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html')


def login_required(fn):
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            return jsonify({"success": False, "message": "Authentication requise"}), 401
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('login.html')

    # POST
    data = request.form or request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password')
    admin_user = os.environ.get('ADMIN_USER', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

    if username == admin_user and password == admin_password:
        session['admin'] = username
        return redirect(url_for('admin_dashboard'))
    return render_template('login.html', error='Nom d\'utilisateur ou mot de passe incorrect')


@app.route('/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/api/admin/add-guest', methods=['POST'])
@login_required
def admin_add_guest():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Données introuvables"}), 400

    nom = data.get('nom', '').strip()
    postnom = data.get('postnom', '').strip()
    prenom = data.get('prenom', '').strip()
    telephone = data.get('telephone', '').strip()
    table_assignee = data.get('table_assignee')
    if table_assignee == "":
        table_assignee = None
    secret_code = (data.get('secret_code') or '').strip().upper() or None
    nombre_places = int(data.get('nombre_places', 1))
    a_confirme = bool(data.get('a_confirme', False))
    statut = data.get('statut', 'Invité')

    if not nom or not prenom:
        return jsonify({"success": False, "message": "Le nom et le prénom sont obligatoires."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = (
            "INSERT INTO guests (nom, postnom, prenom, telephone, table_assignee, nombre_places, a_confirme, statut, secret_code)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        cursor.execute(insert_query, (nom, postnom, prenom, telephone, table_assignee, nombre_places, a_confirme, statut, secret_code))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Invité ajouté avec succès."}), 201
    except Exception as err:
        print(f"Erreur ajout invité : {err}")
        return jsonify({"success": False, "message": f"Erreur serveur lors de l'ajout : {str(err)}"}), 500


@app.route('/api/admin/update-guest', methods=['POST'])
@login_required
def admin_update_guest():
    data = request.get_json() or {}
    guest_id = data.get('id')
    if not guest_id:
        return jsonify({"success": False, "message": "Identifiant invité requis."}), 400

    fields = []
    params = []
    for key in ['nom', 'postnom', 'prenom', 'telephone', 'table_assignee', 'nombre_places', 'a_confirme', 'statut', 'secret_code']:
        if key in data:
            if key == 'secret_code':
                fields.append(f"{key} = %s")
                params.append((data[key] or '').strip().upper())
            else:
                fields.append(f"{key} = %s")
                params.append(data[key])
    if not fields:
        return jsonify({"success": False, "message": "Aucune donnée à mettre à jour."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"UPDATE guests SET {', '.join(fields)} WHERE id = %s"
        params.append(guest_id)
        cursor.execute(query, tuple(params))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Invité mis à jour."}), 200
    except Exception as err:
        print(f"Erreur mise à jour invité : {err}")
        return jsonify({"success": False, "message": "Erreur serveur lors de la mise à jour."}), 500


@app.route('/api/admin/delete-guest', methods=['POST'])
@login_required
def admin_delete_guest():
    data = request.get_json() or {}
    guest_id = data.get('id')
    if not guest_id:
        return jsonify({"success": False, "message": "Identifiant invité requis."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM guests WHERE id = %s", (guest_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Invité supprimé."}), 200
    except Exception as err:
        print(f"Erreur suppression invité : {err}")
        return jsonify({"success": False, "message": "Erreur serveur lors de la suppression."}), 500


@app.route('/api/admin/assign-table', methods=['POST'])
@login_required
def admin_assign_table():

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Données introuvables"}), 400

    guest_id = data.get('id')
    table_assignee = data.get('table_assignee')
    table_id = data.get('table_id')
    nombre_places = data.get('nombre_places')

    if not guest_id:
        return jsonify({"success": False, "message": "Identifiant invité requis."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # If table_id provided, fetch table name
        if table_id:
            cursor.execute("SELECT name FROM tables WHERE id = %s", (table_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close(); conn.close()
                return jsonify({"success": False, "message": "Table introuvable."}), 404
            table_assignee = row[0]

        update_query = "UPDATE guests SET table_assignee = %s, nombre_places = %s WHERE id = %s"
        cursor.execute(update_query, (table_assignee, nombre_places, guest_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Table attribuée."}), 200
    except Exception as err:
        print(f"Erreur assignation table : {err}")
        return jsonify({"success": False, "message": "Erreur serveur lors de l'assignation."}), 500


@app.route('/api/admin/guests', methods=['GET'])
@login_required
def admin_get_guests():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # join with tables to get table names if needed (guests.table_assignee stores name)
        cursor.execute("SELECT * FROM guests ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "guests": rows}), 200
    except Exception as err:
        print(f"Erreur récupération invités : {err}")
        return jsonify({"success": False, "message": "Erreur serveur."}), 500


@app.route('/api/admin/tables', methods=['GET'])
@login_required
def admin_get_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tables ORDER BY id")
        rows = cursor.fetchall()
        
        # Auto-création des tables par défaut si aucune table n'existe
        if not rows:
            default_tables = [
                ('Table VIP', 8, 'Table pour les invités d\'honneur'),
                ('Table 1', 8, 'Table 1'),
                ('Table 2', 8, 'Table 2'),
                ('Table 3', 8, 'Table 3'),
                ('Table 4', 8, 'Table 4'),
                ('Table 5', 8, 'Table 5'),
                ('Table 6', 8, 'Table 6'),
                ('Table 7', 8, 'Table 7'),
                ('Table 8', 8, 'Table 8'),
                ('Table 9', 8, 'Table 9'),
                ('Table 10', 8, 'Table 10')
            ]
            c_ins = conn.cursor()
            for name, cap, desc in default_tables:
                try:
                    c_ins.execute("INSERT IGNORE INTO tables (name, capacity, description) VALUES (%s, %s, %s)", (name, cap, desc))
                except Exception as e:
                    print(f"Ignored table init error: {e}")
            conn.commit()
            c_ins.close()
            
            cursor.execute("SELECT * FROM tables ORDER BY id")
            rows = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify({"success": True, "tables": rows}), 200
    except Exception as err:
        print(f"Erreur récupération tables : {err}")
        return jsonify({"success": False, "message": "Erreur serveur."}), 500


@app.route('/api/admin/add-table', methods=['POST'])
@login_required
def admin_add_table():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    capacity = int(data.get('capacity', 8))
    description = data.get('description', '')
    if not name:
        return jsonify({"success": False, "message": "Nom de table requis."}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tables (name, capacity, description) VALUES (%s, %s, %s)", (name, capacity, description))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Table ajoutée.", "table": {"name": name, "capacity": capacity}}), 201
    except Exception as err:
        print(f"Erreur ajout table : {err}")
        return jsonify({"success": False, "message": "Erreur serveur lors de l'ajout."}), 500


@app.route('/api/admin/wishes', methods=['GET'])
@login_required
def admin_get_wishes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM wishes ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "wishes": rows}), 200
    except Exception as err:
        print(f"Erreur récupération souhaits : {err}")
        return jsonify({"success": False, "message": "Erreur serveur."}), 500


@app.route('/api/admin/add-wish', methods=['POST'])
@login_required
def admin_add_wish():
    data = request.get_json() or {}
    guest_name = data.get('guest_name')
    content = data.get('content')
    if not guest_name or not content:
        return jsonify({"success": False, "message": "Nom et souhait requis."}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO wishes (guest_name, content) VALUES (%s, %s)", (guest_name, content))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Souhait ajouté."}), 201
    except Exception as err:
        print(f"Erreur ajout souhait : {err}")
        return jsonify({"success": False, "message": "Erreur serveur lors de l'ajout."}), 500


@app.route('/api/admin/metrics', methods=['GET'])
@login_required
def admin_metrics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM guests")
        total = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM guests WHERE a_confirme = TRUE")
        confirmed = cursor.fetchone()[0] or 0
        pending = total - confirmed
        cursor.execute("SELECT COUNT(*) FROM tables")
        tables = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COALESCE(SUM(nombre_places), 0) FROM guests")
        total_places = cursor.fetchone()[0] or 0
        cursor.close()
        conn.close()

        return jsonify({
            "success": True, 
            "total": total, 
            "confirmed": confirmed, 
            "pending": pending,
            "tables": tables,
            "places": total_places
        }), 200
    except Exception as err:
        print(f"Erreur metrics : {err}")
        return jsonify({"success": False, "message": "Erreur serveur."}), 500


@app.route('/api/admin/confirmed', methods=['GET'])
@login_required
def admin_confirmed():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM guests WHERE a_confirme = TRUE")
        confirmed = cursor.fetchall()
        count = len(confirmed)
        cursor.close()
        conn.close()

        return jsonify({"success": True, "count": count, "confirmed": confirmed}), 200
    except Exception as err:
        print(f"Erreur récupération confirmations : {err}")
        return jsonify({"success": False, "message": "Erreur serveur."}), 500


@app.route('/api/verify-code', methods=['POST'])
def verify_secret_code():
    data = request.get_json() or {}
    code = (data.get('code') or '').strip().upper()
    if not code:
        return jsonify({"success": False, "message": "Veuillez saisir le code secret."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM guests WHERE UPPER(secret_code) = %s", (code,))
        guest = cursor.fetchone()

        if guest:
            if guest.get('secret_used'):
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "Ce code secret a déjà été utilisé."}), 401

            update_query = "UPDATE guests SET secret_used = TRUE WHERE id = %s"
            cursor.execute(update_query, (guest['id'],))
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({"success": True, "message": "Code secret valide ! Bienvenue.", "guest": {
                "nom": guest['nom'],
                "postnom": guest['postnom'],
                "prenom": guest['prenom'],
                "table": guest['table_assignee'],
                "place": guest['nombre_places'],
                "statut": guest['statut']
            }}), 200
            
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Erreur vérification code secret : {err}")

    valid_codes = ['2026', 'VIP2026', 'SARAH2026', 'MARIAGE2026', 'LOVE2026', 'INVITE2026', 'VIP', 'MARIAGE']
    env_code = os.environ.get('SECRET_INVITE_CODE', '').strip().upper()
    if env_code:
        valid_codes.append(env_code)

    if code in valid_codes:
        return jsonify({"success": True, "message": "Code secret valide ! Bienvenue."}), 200
    else:
        return jsonify({"success": False, "message": "Code secret incorrect. Demandez le code à l'administrateur."}), 401


@app.route('/api/wishes', methods=['GET', 'POST'])
def handle_public_wishes():
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM wishes ORDER BY created_at DESC LIMIT 50")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "wishes": rows}), 200
        except Exception as err:
            print(f"Erreur récupération souhaits : {err}")
            return jsonify({"success": False, "message": "Erreur serveur."}), 500
            
    # POST
    data = request.get_json() or {}
    guest_name = (data.get('guest_name') or '').strip()
    content = (data.get('content') or '').strip()
    if not guest_name or not content:
        return jsonify({"success": False, "message": "Le nom et le message sont obligatoires."}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO wishes (guest_name, content) VALUES (%s, %s)", (guest_name, content))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Votre message a été publié dans le Livre d'or !"}), 201
    except Exception as err:
        print(f"Erreur ajout vœu : {err}")
        return jsonify({"success": False, "message": "Erreur lors de la publication du vœu."}), 500


def ensure_db_schema():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE guests ADD COLUMN IF NOT EXISTS secret_code VARCHAR(255)")
        cursor.execute("ALTER TABLE guests ADD COLUMN IF NOT EXISTS secret_used BOOLEAN DEFAULT FALSE")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Erreur de migration de schéma : {err}")

if __name__ == '__main__':
    ensure_db_schema()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
