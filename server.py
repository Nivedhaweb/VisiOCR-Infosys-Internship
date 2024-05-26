from flask import Flask, render_template, request, jsonify
import qrcode
import datetime
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-pass', methods=['POST'])
def generate_pass():
    name = request.form['name']
    dob = request.form['dob']
    
    # Calculate age based on date of birth
    today = datetime.date.today()
    birth_date = datetime.datetime.strptime(dob, '%Y-%m-%d').date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    # Determine eligibility
    if age >= 18:
        eligibility = 'Eligible'
    else:
        eligibility = 'Not Eligible'

    # Generate QR code
    qr = qrcode.make(f"Name: {name}, Date of Birth: {dob}, Age: {age}, Eligibility: {eligibility}")
    qr_img = BytesIO()
    qr.save(qr_img, format='PNG')
    qr_img_b64 = qr_img.getvalue()

    return jsonify({
        'name': name,
        'dob': dob,
        'age': age,
        'eligibility': eligibility,
        'qr_code': qr_img_b64.decode('utf-8')
    })

if __name__ == '__main__':
    app.run(debug=True)
