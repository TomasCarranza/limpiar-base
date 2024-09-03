from flask import Flask, request, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
import pandas as pd
import re
import io
import os
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def is_valid_email(email):
    if pd.isna(email):
        return False
    email = str(email)
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    invalid_emails = [
        'abuse@', 'admin@', 'avidandlb@', 'billing@', 'compliance@', 'devnull@',
        'dns@', 'ftp@', 'hostmaster@', 'inoc@', 'ispfeedback@', 'ispsupport@',
        'list@', 'list-request@', 'maildaemon@', 'noc@', 'noreplyno-reply@',
        'null@', 'phish@', 'phishing@', 'popmaster@', 'postmaster@', 'privacy@',
        'registrar@', 'root@', 'security@', 'soporte@', 'spam@', 'support@',
        'sysadmin@', 'tech@', 'undisclosed-recipients@', 'unsubscribe@',
        'usenet@', 'uucp@', 'webmaster@', 'webmasters@',
    	'@gmial', '@hotmial', '@hotmaill', '@noregistra', 
        '@hormail', '@gamail', '@gamil', '@gimail', '@outlooki', '@ooutlook', 
        '@yohoo', '@oitlook', '@gogglemail', '@gogolemail', '@outlooi', '@gmaio', '@gmil', '@gmal'
        '@yahhoo', '@yahool', '@yahoocom', '@gamil', '@hmail', '@gimail', '@ymail', '@yimail',
    ]

    invalid_domains = [
        '.de', '.fr', '.it', '.au', '.ca', '.uk', '.ru', '.combjnkkklooo', 
        '.comty', '.comcom', '.comhmn', '.con', '.comm', '.comn', '.xon', '.comj'
        '.comnb', '.comb', '.como', '.comx', '.coma', '.comf', '.cm', '.comk', '.comar'
        '.om', '.cmo', '.cim', '.conm', '.conb', '.comz', '.commm', '.comhjm', '.comco'
    ]
    if not re.match(email_regex, email):
        return False
    if any(invalid in email for invalid in invalid_emails):
        return False
    if any(email.endswith(domain) for domain in invalid_domains):
        return False
    return True

def is_valid_name(name):
    if pd.isna(name):
        return False
    name = str(name)
    return bool(re.match(r'^[A-Za-záéíóúüñ0-9\s]+$', name))

def limpiar_base_datos(file_path, columnas):
    df = pd.read_excel(file_path, engine='openpyxl')
    if 'email' in columnas:
        df['Email_Valid'] = df['Email'].apply(is_valid_email)
    else:
        df['Email_Valid'] = True
    if 'nombre' in columnas:
        df['Name_Valid'] = df['Nombre'].apply(is_valid_name)
    else:
        df['Name_Valid'] = True

    df_clean = df[df['Email_Valid'] & df['Name_Valid']].copy()
    df_clean.drop(columns=['Email_Valid', 'Name_Valid'], inplace=True)
    
    base_clean_file = io.BytesIO()
    df_clean.to_excel(base_clean_file, index=False, engine='openpyxl')
    base_clean_file.seek(0)

    merged_df = df.merge(df_clean, how='left', indicator=True)
    removed_df = merged_df[merged_df['_merge'] == 'left_only'].copy()
    def motivo(row):
        reasons = []
        if 'email' in columnas and not is_valid_email(row['Email']):
            reasons.append('Email inválido')
        if 'nombre' in columnas and not is_valid_name(row['Nombre']):
            reasons.append('Nombre inválido')
        return ', '.join(reasons)
    removed_df['Motivo'] = removed_df.apply(motivo, axis=1)
    removed_df.drop(columns=['_merge'], inplace=True)

    report_file = io.BytesIO()
    removed_df.to_excel(report_file, index=False, engine='openpyxl')
    report_file.seek(0)

    return base_clean_file, report_file

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Limpieza de Base de Datos</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-style: normal;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: #7D799D;
            background: radial-gradient(at center, #7D799D, #193BE1);
            margin: 0;
            letter-spacing: 0px;
            color: #ffff;
        }
        .container {
            text-align: center;
            background-image: linear-gradient(to bottom, #141414 40%, #0e0e0e 100%);
            padding: 20px;         
            border-radius: 20px;
        }
        h1 {
            color: #ffff;
            font-family: "Poppins", sans-serif;
            font-weight: 600;
            font-size: 2.2em;
            padding-bottom: 1em;
        }
        form {
            margin-top: 20px;
        }
        .casillas {
            display: flex;
            justify-content: left;
            align-items: left;   
        }
        .casillas .form-check {
            margin-left: 1em; 
            margin-right: 1em; 
        }
        input[type="file"], input[type="submit"], .form-check #selector {
            margin-bottom: 10px;
            padding: 10px;
            background-color: #2d2d2d; 
            border-radius: 5px;
            width: 100%;
        }             
        input[type="submit"] {
            background-color: #3A4FCA;
            color: #fff;
            border: solid  0px;
            border-color: #0828c9;
            cursor: pointer;
            width: 20%;
            border-radius: 18px;
            margin: 1em;
            font-weight: 600;
        }
        input[type="submit"]:hover {
            background-color: #566ACE;
            border: 0px solid #ffffff;
            color: #ffffff;
            font-weight: 600;
        }
        a {
            color: #007bff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        p {
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-style: normal;
            display: flex;
            justify-content: left;
            align-items: center;
            color: #d6d6d6;
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-size: 1,1em;  
        }
        .error-message {
            color: red;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Limpieza de bases</h1>
        <p>Cargar archivo .XLSX con columnas “Nombre” y “Email”</p>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" id="selector"/>
            <br>
            <br><p>Seleccionar columnas a filtrar</p>
            <div class="casillas">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="columnas" value="nombre" id="nombre">
                    <label class="form-check-label" for="nombre">Nombre</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="columnas" value="email" id="email">
                    <label class="form-check-label" for="email">Email</label>
                </div>
            </div>
  <input type="submit" value="Limpiar base" />
        </form>
        {% if error_message %}
        <p class="error-message">{{ error_message }}</p>
        {% endif %}
        {% if cleaned_file %}
        <p>Archivo limpio generado:  <a href="{{ url_for('download_file', filename=cleaned_file) }}">Descargar archivo limpio</a></p>
        <p>Informe de eliminación:  <a href="{{ url_for('download_file', filename=report_file) }}">Descargar informe</a></p>
        {% endif %}
    </div>
</body>
</html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    error_message = None
    if 'file' not in request.files:
        error_message = 'No file part'
    else:
        file = request.files['file']
        if file.filename == '':
            error_message = 'Error: ingresa un archivo para continuar'
        elif not file.filename.endswith('.xlsx'):
            error_message = 'Invalid file format, only .xlsx files are allowed'

    if error_message:
        return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Limpieza de Base de Datos</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-style: normal;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: #7D799D;
            background: radial-gradient(at center, #7D799D, #193BE1);
            margin: 0;
            letter-spacing: 0px;
            color: #ffff;
        }
        .container {
            text-align: center;
            background-image: linear-gradient(to bottom, #141414 40%, #0e0e0e 100%);
            padding: 20px;         
            border-radius: 20px;
        }
        h1 {
            color: #ffff;
            font-family: "Poppins", sans-serif;
            font-weight: 600;
            font-size: 2.2em;
            padding-bottom: 1em;
        }
        form {
            margin-top: 20px;
        }
        .casillas {
            display: flex;
            justify-content: left;
            align-items: left;   
        }
        .casillas .form-check {
            margin-left: 1em; 
            margin-right: 1em; 
        }
        input[type="file"], input[type="submit"], .form-check #selector {
            margin-bottom: 10px;
            padding: 10px;
            background-color: #2d2d2d; 
            border-radius: 5px;
            width: 100%;
        }             
        input[type="submit"] {
            background-color: #3A4FCA;
            color: #fff;
            border: solid  0px;
            border-color: #0828c9;
            cursor: pointer;
            width: 20%;
            border-radius: 18px;
            margin: 1em;
            font-weight: 600;
        }
        input[type="submit"]:hover {
            background-color: #566ACE;
            border: 0px solid #ffffff;
            color: #ffffff;
            font-weight: 600;
        }
        a {
            color: #007bff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        p {
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-style: normal;
            display: flex;
            justify-content: left;
            align-items: center;
            color: #d6d6d6;
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-size: 1,1em;  
        }
        .error-message {
            color: red;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Limpieza de bases</h1>
        <p>Cargar archivo .XLSX con columnas “Nombre” y “Email”</p>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" id="selector"/>
            <br>
            <br><p>Seleccionar columnas a filtrar</p>
            <div class="casillas">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="columnas" value="nombre" id="nombre">
                    <label class="form-check-label" for="nombre">Nombre</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="columnas" value="email" id="email">
                    <label class="form-check-label" for="email">Email</label>
                </div>
            </div>
            <input type="submit" value="Limpiar base" />
        </form>
        {% if error_message %}
        <p class="error-message">{{ error_message }}</p>
        {% endif %}
    </div>
</body>
</html>
        ''', error_message=error_message)

    columnas = request.form.getlist('columnas')

    cleaned_file, report_file = limpiar_base_datos(file, columnas)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    cleaned_filename = f'base_limpia_{timestamp}.xlsx'
    report_filename = f'informe_{timestamp}.xlsx'

    cleaned_filepath = os.path.join(app.config['UPLOAD_FOLDER'], cleaned_filename)
    report_filepath = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)

    with open(cleaned_filepath, 'wb') as f:
        f.write(cleaned_file.getbuffer())
    with open(report_filepath, 'wb') as f:
        f.write(report_file.getbuffer())

    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Limpieza de Base de Datos</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-style: normal;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: #7D799D;
            background: radial-gradient(at center, #7D799D, #193BE1);
            margin: 0;
            letter-spacing: 0px;
            color: #ffff;
        }
        .container {
            text-align: center;
            background-image: linear-gradient(to bottom, #141414 40%, #0e0e0e 100%);
            padding: 20px;         
            border-radius: 20px;
        }
        h1 {
            color: #ffff;
            font-family: "Poppins", sans-serif;
            font-weight: 600;
            font-size: 2.2em;
            padding-bottom: 1em;
        }
        form {
            margin-top: 20px;
        }
        .casillas {
            display: flex;
            justify-content: left;
            align-items: left;   
        }
        .casillas .form-check {
            margin-left: 1em; 
            margin-right: 1em; 
        }
        input[type="file"], input[type="submit"], .form-check #selector {
            margin-bottom: 10px;
            padding: 10px;
            background-color: #2d2d2d; 
            border-radius: 5px;
            width: 100%;
        }             
        input[type="submit"] {
            background-color: #3A4FCA;
            color: #fff;
            border: solid  0px;
            border-color: #0828c9;
            cursor: pointer;
            width: 20%;
            border-radius: 18px;
            margin: 1em;
            font-weight: 600;
        }
        input[type="submit"]:hover {
            background-color: #566ACE;
            border: 0px solid #ffffff;
            color: #ffffff;
            font-weight: 600;
        }
        a {
            color: #007bff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .btn-primary {
            background-color: #314DD9;
            border-color: #0828c9;
            color: #fff;
            font-weight: 600;
            margin: 10px;
            border-radius: 18px;
        }
        .btn-primary:hover {
            background-color: #566ACE;
            border-color: #ffffff;
            color: #ffffff;
        }
        .btn-secondary {
            margin: 10px;
        }
                                  
        p {
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-style: normal;
            display: flex;
            justify-content: left;
            align-items: center;
            color: #d6d6d6;
            font-family: "Poppins", sans-serif;
            font-weight: 400;
            font-size: 1,1em;  
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Limpieza realizada</h1>
        <p>Archivo limpio generado: <a href="{{ url_for('download_file', filename=cleaned_file) }}" class="btn btn-secondary">Descargar archivo limpio</a></p>
        <p>Informe de eliminación:  <a href="{{ url_for('download_file', filename=report_file) }}" class="btn btn-secondary">Descargar informe</a></p>
        <br>
        <br>
        <a href="{{ url_for('index') }}" class="btn btn-primary">Nueva limpieza</a>
        
    </div>
</body>
</html>
    ''', cleaned_file=cleaned_filename, report_file=report_filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)