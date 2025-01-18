from flask import Flask, request, Response
from bs4 import BeautifulSoup
import requests
import json  # مكتبة JSON للتعامل مع النصوص العربية

app = Flask(__name__)

# تخزين عدد المحاولات لكل مستخدم
user_usage = {}

# الرابط الأساسي
BASE_URL = "https://3bili.com"

# إعدادات الرؤوس
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    'cache-control': "max-age=0",
    'sec-ch-ua': "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"",
    'sec-ch-ua-mobile': "?1",
    'sec-ch-ua-platform': "\"Android\"",
    'upgrade-insecure-requests': "1",
    'sec-fetch-site': "none",
    'sec-fetch-mode': "navigate",
    'sec-fetch-user': "?1",
    'sec-fetch-dest': "document",
    'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
}

# دالة لجلب csrf_token و token1
def fetch_tokens():
    response = requests.get(BASE_URL, headers=HEADERS)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'id': 'csrf_token'})['value']
    token1 = response.cookies.get('PHPSESSID')
    return csrf_token, token1

@app.route('/')
def home():
    return "مرحبًا بك! التطبيق يعمل بنجاح."

@app.route('/check', methods=['GET'])
def check_email():
    email = request.args.get("email")
    if not email:
        return Response(
            response=json.dumps({"error": "يرجى إدخال البريد الإلكتروني في الرابط."}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=400
        )
    
    user_id = request.remote_addr  # تحديد المستخدم بناءً على عنوان IP
    
    # الحصول على قيم csrf_token و token1
    csrf_token, token1 = fetch_tokens()
    
    try:
        while True:
            # إرسال طلب POST
            post_url = f"{BASE_URL}/answer.php"
            params = {'version': "0.7517866631793415"}
            payload = {
                'csrf_token': csrf_token,
                'operator_service': "syriatel",
                'typed': "0",
                'sender_num': "9647723708853",
                'sender_email': email,
                'receiver_num': "9673348686",
                'us_amount': "2.00",
                'sy_amount': "13039",
                'coupon': ""
            }
            headers = {
                **HEADERS,
                'x-requested-with': "XMLHttpRequest",
                'origin': BASE_URL,
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': BASE_URL,
                'Cookie': f"PHPSESSID={token1}"
            }
            
            post_response = requests.post(post_url, params=params, data=payload, headers=headers)
            post_response.raise_for_status()
            
            # تحديث عدد المحاولات
            user_usage[user_id] = user_usage.get(user_id, 0) + 1
            
            # إذا تجاوز المستخدم الحد، تحديث القيم وإعادة المحاولة
            if user_usage[user_id] > 100:
                csrf_token, token1 = fetch_tokens()
                user_usage[user_id] = 0
                continue
            
            # تحليل النتيجة
            if "الإيميل المدخل صحيح ولكنه غير موجود" in post_response.text:
                result = "الإيميل غير متاح"
            else:
                result = "الإيميل متاح"
            
            # إرجاع الاستجابة باللغة العربية
            response_data = {
                "email": email,
                "status": f"{result} [↯] @Q_B_H"  # النص المطلوب
            }
            
            # إرجاع الاستجابة بتنسيق JSON مع ترميز UTF-8
            return Response(
                response=json.dumps(response_data, ensure_ascii=False),  # فك الترميز
                content_type="application/json; charset=utf-8",
                status=200
            )

    except Exception as e:
        return Response(
            response=json.dumps({"error": str(e)}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=500
        )

@app.errorhandler(404)
def not_found(e):
    return "الصفحة غير موجودة. تأكد من المسار.", 404

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
