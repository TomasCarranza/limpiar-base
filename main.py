from flask import Flask, request, send_from_directory, render_template
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
    '@yohoo', '@oitlook', '@gogglemail', '@gogolemail', '@outlooi', '@gmaio', 
    '@gmil', '@gmal', '@yahhoo', '@yahool', '@yahoocom', '@ymail', '@yimail',
    '@noposee', '@notiene', '@notiene2', '@gmsil', '@yayoo', '@gemail', 
    '@gamail', '@test.com', '@iclod.com', '@gmaail', '@gnail', '@email', 
    '@gmali', '@igmail', '@gmaim', '@gmailc', 'noposee', 'notiene', 'notiene2',
    ]

    invalid_domains = [
    '.de', '.fr', '.it', '.au', '.ca', '.uk', '.ru', '.combjnkkklooo', 
    '.comty', '.comcom', '.comhmn', '.con', '.comm', '.comn', '.xon', '.comj',
    '.comnb', '.comb', '.como', '.comx', '.coma', '.comf', '.cm', '.comk', '.comar',
    '.om', '.cmo', '.cim', '.conm', '.conb', '.comz', '.commm', '.comhjm', '.comco',
    '.vom', '.comment', '.come', '.comy', '.comic', '.comTy', '.comg', '.comd', '.coma', 
    '.vn', '.comu'
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
    return render_template('index.html')

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
            error_message = 'Formato de archivo invalido. Ingresa un archivo XLSX'

    if error_message:
        return render_template('error.html', error_message=error_message)

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

    return render_template('result.html', cleaned_file=cleaned_filename, report_file=report_filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False)