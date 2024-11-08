from flask import Flask, render_template, request, jsonify
import requests
import threading

app = Flask(__name__)

FREE_FIRE_API_KEY = 'infoplayertrial_61029305'
FREE_FIRE_API_URL = 'https://drxzsecurityapi.info/api/player/info/{region}/{uid}?key={api_key}'

# تعريف كلمة السر
USERNAME = 'admin'  # يمكنك تغيير اسم المستخدم
PASSWORD = 'password123'  # تغيير كلمة السر هنا

cookies = {
    '_ga': 'GA1.1.2123120599.1674510784',
    '_fbp': 'fb.1.1674510785537.363500115',
    '_ga_7JZFJ14B0B': 'GS1.1.1674510784.1.1.1674510789.0.0.0',
    'source': 'mb',
    'region': 'MA',
    'language': 'ar',
    'datadome': '6h5F5cx_GpbuNtAkftMpDjsbLcL3op_5W5Z-npxeT_qcEe_7pvil2EuJ6l~JlYDxEALeyvKTz3~LyC1opQgdP~7~UDJ0jYcP5p20IQlT3aBEIKDYLH~cqdfXnnR6FAL0',
    'session_key': 'efwfzwesi9ui8drux4pmqix4cosane0y',
}

headers = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://shop2game.com',
    'Referer': 'https://shop2game.com/app/100067/idlogin',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
    'accept': 'application/json',
    'content-type': 'application/json',
}

def get_player_info(player_id):
    json_data = {
        'app_id': 100067,
        'login_id': f'{player_id}',
        'app_server_id': 0,
    }

    res = requests.post('https://shop2game.com/api/auth/player_id_login', cookies=cookies, headers=headers, json=json_data)

    if res.status_code == 200:
        response = res.json()
        name = response.get('nickname', 'Unknown')
        region = response.get('region', 'Unknown')
        return {'name': name, 'region': region}
    else:
        return {'error': f"فشل في جلب المعلومات. كود الحالة: {res.status_code}"}

def fetch_player_info(region, uid):
    url = FREE_FIRE_API_URL.format(region=region, uid=uid, api_key=FREE_FIRE_API_KEY)
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def send_request(region, uid, successful_results, failed_results, count, lock):
    result = fetch_player_info(region, uid)
    with lock:
        if result:
            successful_results.append(count)
        else:
            failed_results.append(count)

def send_multiple_requests(region, uid, view_count, progress_callback):
    threads = []
    successful_results = []
    failed_results = []
    lock = threading.Lock()

    for count in range(1, view_count + 1):
        thread = threading.Thread(target=send_request, args=(region, uid, successful_results, failed_results, count, lock))
        threads.append(thread)
        thread.start()
        progress_callback(count, view_count)

    for thread in threads:
        thread.join()

    return successful_results, failed_results

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    if username == USERNAME and password == PASSWORD:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'})

@app.route('/send', methods=['POST'])
def send():
    player_id = request.form['player_id']
    view_count = int(request.form['view_count'])
    
    if view_count > 100:
        return jsonify({'error': 'الحد الأقصى لعدد الزيارات هو 100. يرجى كتابة عدد أقل.'})
    
    player_info = get_player_info(player_id)

    if 'error' in player_info:
        return jsonify({'error': player_info['error']})
    
    region = player_info['region'].lower()
    uid = player_id

    successful_results, failed_results = [], []
    
    def progress_callback(count, total):
        percentage = (count / total) * 100
        print(f"تم إرسال زيارة رقم {count} من {total} ({percentage:.2f}%)")

    successful_results, failed_results = send_multiple_requests(region, uid, view_count, progress_callback)

    total_success = len(successful_results)
    total_failed = len(failed_results)
    final_message = f"🌟 تحية طيبة! تم إرسال جميع الزيارات: {view_count} زيارة إلى اللاعب {player_info['name']}."

    return jsonify({
        'player_name': player_info['name'],
        'total_success': total_success,
        'total_failed': total_failed,
        'final_message': final_message
    })

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")

