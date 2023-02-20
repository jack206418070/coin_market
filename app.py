from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import timedelta, timezone, datetime
import os
import pyotp
import qrcode
from bson.objectid import ObjectId
from form_verify import Fverify
from db_catch import DB
import hashlib

# from flask_wtf import FlaskForm
# from flask_wtf.csrf import CSRFProtect

### 產生 totp qrcode
# key = 'iLufaMySuperSecretKey'
# uri = pyotp.totp.TOTP(key).provisioning_uri(name="BTPay", issuer_name="iLufa App")
# print(uri)

# qrcode.make(uri).save('totp.png')
basedir = os.path.abspath(os.path.dirname(__file__))  # 獲取當前檔案所在目錄
UPLOAD_FOLDER = basedir+'/public/images'  # 計算圖片檔案存放目錄
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}   # 設定可上傳圖片字尾 


app = Flask(
  __name__,
  static_folder='public',
  static_url_path='/'
)  # 建立 application 物件

# csrf = CSRFProtect(app)


app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=60)
app.config['SECRET_KEY'] = os.urandom(24)

# 資料庫參數設定
connection_string = "mongodb+srv://ginjack:a12081616@cluster0.js6ij.mongodb.net/hotel?retryWrites=true&w=majority"
# connection_string = "mongodb+srv://samsonm825:g4zo1j6y94@cluster0.ow4o5g4.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)
dbs = client.market
db = DB(client, 'market')

# totp key 
key = 'iLufaMySuperSecretKey'

# 驗證動態驗證碼
def verify_potp(potp):
  totp = pyotp.TOTP(key)
  result = totp.verify(potp) #驗證傳進來的 otp 是不是正確的 正確 True 錯誤 False
  return result

# 驗證上傳檔案格式
def allowed_file(filename):
  return '.' in filename and \
      filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 

# 建立根目錄的路由
@app.route('/', methods=['GET', 'POST'])
def index():
  return render_template('index.html')

# 管理員登入判斷
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
  if request.method == "POST":
    account = request.form['account']
    password = request.form['password']
    potp = request.form['potp']
    potp_result = verify_potp(potp)
    db_data = {'collect': 'admin', 'condition': [{ "account": account }] }
    user_data = db.find_one(db_data)
    if user_data == None:
      return redirect('admin_login')
    

    password_str = password + user_data['salt']
    user_password = hashlib.sha1(password_str.encode('utf-8'))


    if user_password.hexdigest() == user_data['password']:  # and potp_result:
      session['id'] = str(user_data['_id'])
      session['display_name'] = user_data['display_name']
      return redirect('admin_dashboard')
    else:
      return redirect('admin_login')
  else:
    if 'display_name' in session:
      return redirect('admin_dashboard')
    return render_template('admin_login.html')

# 管理員登出
@app.route('/admin_logout')
def admin_logout():
  session.clear()
  return redirect('admin_login')

# 管理者首頁面板
@app.route('/admin_dashboard')
def admin_dashboard():
  if 'display_name' in session:
    return render_template('admin_dashboard.html')
  else:
    return redirect('admin_login')

# 管理員-驗證業務帳號頁面
@app.route('/admin_verify', methods=['POST', 'GET'])
def admin_verify():
  if 'display_name' in session and session['display_name'] == '最高管理者':
    # 處理網址有參數
    if request.args.get('id'):
      if request.args.get('is_verify') == '1':
        dbs.member.update_one(
          {
            "_id": ObjectId( request.args.get('id') )
          },
          {
            "$set": {
              "is_verify": 1
            }
          }
        )
      else:
        dbs.member.update_one(
          {
            "_id": ObjectId( request.args.get('id') )
          },
          {
            "$set": {
              "is_verify": 2
            }
          }
        )
      return redirect('admin_verify')

      # if request.args.get('is_verify') == '1':
        # dbs.member.update_one(
        #   {
            
        #   }
        # )
        # db_data = { 'collect': 'member', 'condition': [{ '_id': ObjectId(request.args.get('id')) }, { "$set": { "is_verify": 1 } }] }
        # db.update_one(db_data)
      # else:
        # db_data = { 'collect': 'member', 'condition': [{ '_id': ObjectId(request.args.get('id')) }, { "$set": { "is_verify": 2 } } ] }
        # db.update_one(db_data)
      # return redirect('admin_verify')
    
    # 處理 單純 GET 頁面
    if request.method == 'GET':
      db_data = { 'collect': 'member', 'condition': [{ "is_verify": 0 }, { "password": 0 }] }
      member_data = db.find_all(db_data)
      return render_template('admin_verify.html', member_data=member_data)
  else:
    return redirect('admin_login')

# 管理員-會員管理頁面 
@app.route('/admin_member', methods=['GET', 'POST'])
def admin_member():
  if 'display_name' in session:
    if request.method == 'POST':
      coin = request.form['coin']
      name = request.form['name']
      bankAccount = request.form['bankAccount']
      id = request.form['id']
      db_data = { "collect": "member", "condition": [{ "_id": ObjectId(id) }, { "$set": { "coin": int(coin), "name": name, "bankAccount": bankAccount } }]}
      db.update_one(db_data)
      return redirect('admin_member')
    else:
      if request.args.get('methods') == 'delete':
        db.delete_one({ "collect": "member", "condition": [{ "_id": ObjectId(request.args.get('id')) }] })
        return redirect('admin_member')
      member_data = db.find_all({ "collect": "member", "condition": [{ "is_verify": 1 }, { "password": 0 }] })
      return render_template('admin_member.html', member_data=member_data)
  else:
    return redirect('admin_login')

# 管理員-產品新增頁面
@app.route('/admin_product', methods=['POST', 'GET'])
def admin_product():
  if 'display_name' in session and session['display_name'] == '最高管理者':
    if request.method == 'POST':
      potp = request.form['potp']
      potp_result = verify_potp(potp)
      potp_result = True
      if potp_result:
        name = request.form['name']
        price = int(request.form['price'])
        desc = request.form['desc']
        factory_name = request.form['factory_name']
        factory_bank = request.form['factory_bank']
        # id 如果是空值 就是 新增
        if request.form['id'] == '':
          db_data = { "collect": "product", "condition": [{ "name": name, "price": price, "desc": desc, "factory_name": factory_name, "factory_bank": factory_bank, "is_buy": False }] }
          db.insert_one(db_data)
        
        # id 有值 就是更新
        else:
          db_data = { "collect": "product", "condition": [{ "_id": ObjectId(request.form['id']) }, { "$set": { "name": name, "price": price, "desc": desc, "factory_name": factory_name, "factory_bank": factory_bank } }] }
          db.update_one(db_data)
      else:
        return redirect('admin_product')
      return redirect('admin_product')
    else:
      # get 方法有 methods 參數 delete 就是刪除
      if request.args.get('methods') == 'delete':
        db.delete_one({ "collect": "product", "condition": [{ "_id": ObjectId(request.args.get('id')) }] })
      product_data = db.find_all({ "collect": "product", "condition": [{}] })
      print('product_data', product_data)
      return render_template('admin_product.html', product_data=product_data)
  else:
    return redirect('admin_login')

# 管理員-訂單管理頁面
@app.route('/admin_order', methods=['GET'])
def admin_order():
  if 'display_name' in session:
    if request.args.get('methods') == 'post':
      db.update_one({ "collect": "order", "condition": [{ "_id": ObjectId(request.args.get('oid')) }, { "$set": { "is_paid": True } }] })
    elif request.args.get('methods') == 'delete':
      db.delete_one({ "collect": "order", "condition": [{ "_id": ObjectId(request.args.get('oid')) }] })
    order_data = []
    order_find = dbs.order.aggregate([
      {
        "$lookup": {
          "from": "product",
          "localField": "product_id",
          "foreignField": "_id",
          "as": "product"
        }
      },
      {
        "$lookup": {
          "from": "member",
          "localField": "mid",
          "foreignField": "_id",
          "as": "member"
        }
      }
    ])
    for doc in order_find:
      order_data.append(doc)
    return render_template('admin_order.html', order_data=order_data)
  else:
    return redirect('admin_login')

# 管理員-管理員帳號管理
@app.route('/admin_user', methods=['GET', 'POST'])
def admin_user():
  if 'display_name' in session and session['display_name'] == '最高管理者':
    if request.method == 'POST':
      name = request.form['name']
      account = request.form['account']
      id = request.form['id']
      password = request.form['password']
      display_name = request.form['display_name']
      
      if id == '':
        user_data = dbs.admin.find_one({ "account": account })
        if user_data != None:
          return redirect('admin_user')
        salt = '&*(%^)&&&^'
        password_str = password + salt
        user_password = hashlib.sha1(password_str.encode('utf-8'))
        dbs.admin.insert_one({
          "name": name,
          "account": account,
          "password": user_password.hexdigest(),
          "salt": salt,
          "display_name": display_name
        })
        return redirect('admin_user')
      else:
        user_data = dbs.admin.find_one({ "_id": ObjectId(id) })
        if user_data['password'] != password:
          password_str = password + user_data['salt']
          user_password = hashlib.sha1(password_str.encode('utf-8'))
          password = user_password.hexdigest()
        dbs.admin.update_one(
          {
            "_id": ObjectId(id)
          },
          {
            "$set": {
              "name": name,
              "password": password,
              "display_name": display_name
            }
          }
        )
        return redirect('admin_user')
    else:
      if request.args.get('methods') == 'delete':
        dbs.admin.delete_one({ "_id": ObjectId(request.args.get('id')) })

      user_data = []
      user_find = dbs.admin.find()
      for doc in user_find:
        doc['_id'] = str(doc['_id'])
        user_data.append(doc)
      return render_template('admin_user.html', user_data=user_data)
  else:
    return redirect('admin_dashboard')



# @app.route('/admin_user', methods=['GET', 'POST'])
# def admin_user():
#   if 'display_name' in session:
#     if request.method == 'POST':
#       name = request.form['name']
#       display_name = request.form['display_name']
#       password = request.form['password']
#       id = request.form['id']
#       if request.form['id'] == '':
#         salt = '&)*&$%O*&*'
#         password_str = password + salt
#         user_password = hashlib.sha1(password_str.encode('utf-8'))
#         password = user_password.hexdigest()
#         account = request.form['account']
#         data = {
#           "name": name,
#           "password": password,
#           "display_name": display_name,
#           "account": account,
#           "salt": salt
#         }
#         db.insert_one({ "collect": "admin", "condition": [data] })
#         return redirect('admin_user')
#       else:
#         user_data = db.find_one({ "collect": "admin", "condition": [{ "_id": ObjectId(id) }] })
#         if password != user_data['password']:
#           password_str = password + user_data["salt"]
#           user_password = hashlib.sha1(password_str.encode('utf-8'))
#           password = user_password.hexdigest()
#         data = {
#           "name": name,
#           "password": password,
#           "display_name": display_name
#         }
#         db.update_one({ "collect": "admin", "condition": [{ "_id": ObjectId(id) }, { "$set": data }] })
#       return redirect('admin_user')
#     else:
#       if request.args.get('methods') == 'delete':
#         db.delete_one({ "collect": "admin", "condition": [{ "_id": ObjectId(request.args.get('id')) }] })
#       user_data = db.find_all({ "collect": "admin", "condition": [{}] })
#       return render_template('admin_user.html', user_data=user_data)
#   else:
#     return redirect('admin_login')
# 業務登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    member_data = []
    account = request.form['account']
    password = request.form['password']
    member_data = db.find_one({ "collect": "member", "condition": [{ "account": account }] })
      
    if member_data == None:
      return redirect('login')
    


    password_str = password + member_data["salt"]
    user_password = hashlib.sha1(password_str.encode('utf-8'))


    if member_data['password'] == user_password.hexdigest() and member_data['is_verify'] == 1:
      session.permanent = True
      session["name"] = member_data['name']
      session["id"] = member_data["_id"]
      return redirect('profile')
    else:
      return redirect('login')
  else:
    if 'id' in session:
      return redirect('profile')
    return render_template('login.html')

# 業務登出
@app.route('/logout')
def logout():
  session.clear()
  return redirect("login")

# 業務註冊頁面
@app.route('/register', methods=['GET', 'POST'])
def register():
  basedir = os.path.abspath(os.path.dirname(__file__))
  if request.method == 'POST':
    # 取得 使用者註冊資料(文本資料)
    account = request.form['account']
    password = request.form['password']
    name = request.form['name']
    resetPassword = request.form['resetPassword']
    IDcard = request.form['IDcard']
    bankName = request.form['bankName']
    bankAccount = request.form['bankAccount']

    # account_repeat = db.find_one({ "collect": "member", "condition": [ { "account": account } ] })

    # if account_repeat != None:
    #   return redirect('register')

    account_repeat = dbs.member.find_one({ "account": account })
    if account_repeat != None:
      return redirect('register')


    # 取得使用者 圖片資料
    f_arr = []
    imgArr = []
    f_arr.append(request.files['IDcardImage'])
    f_arr.append(request.files['bankImage'])
    f_arr.append(request.files['creditImage'])
    imgUrl = ''

    for f in f_arr:
      if f and allowed_file(f.filename):
        file_path = basedir + '/public/images/' + account
        if not os.path.isdir(file_path):
          os.mkdir(file_path)
        f.save(os.path.join(file_path, f.filename))
        imgUrl = f'/images/{account}/{f.filename}'
        imgArr.append(imgUrl)


    # 建立使用者完整的資料
    salt = '&*#)(&%@*&*%*(*(@'
    password_str = password + salt
    user_password = hashlib.sha1(password_str.encode('utf-8'))

    data = {
      'name': name,
      'account': account,
      'password': user_password.hexdigest(),
      'IDcard': IDcard,
      'bankName': bankName,
      'bankAccount': bankAccount,
      'img_data': imgArr,
      'coin': 0,
      'is_verify': 0,
      'salt': salt
    }


    # 存入資料庫
    dbs.member.insert_one(data)

    return redirect('register')
  else:
    return render_template('register.html')

# 業務登入後資料畫面
@app.route('/profile', methods=['GET', 'POST'])
def profile():
  if 'id' in session:
    member_data = db.find_one({ "collect": "member", "condition": [{ "_id": ObjectId(session["id"]) }, { "password": 0 }] })
    return render_template('profile.html', member_data=member_data)
  return redirect('login')

@app.route('/resetPassword', methods=['POST', 'GET'])
def resetPassword():
  if 'id' in session:
    if request.method == 'POST':
      old_password = request.form['oldPassword']
      password = request.form['password']
      repeat_password = request.form['repeatPassword']
      
      member_data = db.find_one({ "collect": "member", "condition": [{ "_id": ObjectId(session['id']) }]})
      if member_data['password'] == old_password and password == repeat_password:
        password_str = password + member_data['salt']
        user_password = hashlib.sha1(password_str.encode('utf-8'))
        db.update_one({ "collect": "member", "condition": [{ "_id": ObjectId(member_data['_id']) }, { "$set": { "password": user_password.hexdigest() } }] })
        return redirect('login')
      else:
        return redirect('resetPassword')
    else:
      return render_template('resetPassword.html')
  else:
    return redirect('login')


# 業務購物車頁面    
@app.route('/cart/<product>')
def cart(product):
  if 'id' in session:
    member_data = db.find_one({ "collect": "member", "condition": [{ "_id": ObjectId(session['id']) }]})
    if product == 'all':
      product_data = db.find_all({ "collect": "product", "condition": [{ "price": { "$lte": member_data['coin'] }, "is_buy": False }] })
      return render_template('cart.html', product_data=product_data)
    else:
      prodcut_data = dbs.product.find_one(
        { 
          "_id": ObjectId(product)
        }
      )
      if request.args.get('methods') == 'buy':
        # 修改 使用者的 coin 數量
        if request.args.get('mid') != session['id']:
          session.clear()
          return redirect(url_for('login'))

        dbs.member.update_one(
          {
            "_id": ObjectId(request.args.get('mid'))
          },
          {
            "$set": {
              "coin": member_data['coin'] - prodcut_data['price']
            }
          }
        )

        # 修改 產品的 is_buy ==> True
        dbs.product.update_one(
          {
            "_id": ObjectId(product)
          },
          {
            "$set": {
              "is_buy": True
            }
          }
        )

        # 新增一比訂單 在資料庫裡面
        dbs.order.insert_one(
          {
            "product_id": ObjectId(product),
            "mid": ObjectId(request.args.get('mid')),
            "is_paid": False
          }
        )

        return redirect(url_for('cart', product = 'all'))

      else:
        return render_template('cart_order.html', product_data=prodcut_data, member_data=member_data)
    





      # product_data = db.find_one({ "collect": "product", "condition": [{ "_id": ObjectId(product) }] })
      # if request.args.get('methods') == 'buy':
      #   if request.args.get('mid') == session['id']:
      #     db.update_one({ "collect": "product", "condition": [{ "_id": ObjectId(product) }, { "$set": { "is_buy": True } }] })
      #     db.update_one({ "collect": "member", "condition": [{ "_id": ObjectId(request.args.get('mid')) }, { "$set": { "coin": member_data['coin'] - product_data['price'] } }] })
      #     db.insert_one({ "collect": "order", "condition": [{ "product_id": ObjectId(product), "mid": ObjectId(member_data['_id']), 'is_paid': False }] })
      #     return redirect(url_for('cart', product='all'))
      #   else:
      #     return redirect(url_for('cart', product='all'))
      # else:
      #   return render_template('cart_order.html', product_data=product_data, member_data=member_data)
  else:
    return redirect(url_for('login'))

# 業務訂單頁面
@app.route('/order')
def order():
  if 'id' in session:
    order_data = db.aggregate({ "collect": "order", "condition": [[ { "$match": { "mid": ObjectId(session["id"]) } } ,{ "$lookup": { "from": "product", "localField": "product_id", "foreignField": "_id", "as": "product" } } ]] })
    return render_template('order.html', order_data=order_data)
  else:
    return redirect('login')

if __name__ == "__main__":
 app.run()