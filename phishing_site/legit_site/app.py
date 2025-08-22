from flask import Flask, render_template, request, redirect, url_for, make_response
import datetime
import secrets
import json
import os
app = Flask(__name__)

# 允许抓包和代理访问
app.config['DEBUG'] = True
# 设置 SERVER_NAME 为 None，使用 IP 地址
app.config['SERVER_NAME'] = None

# 用于存储有效令牌的全局变量（在实际应用中应使用数据库）
valid_tokens = set()
# 用于存储用户信息的全局变量（在实际应用中应使用数据库）
users = {
    'admin': {'password': 'admin', 'role': 'admin'},
    'user': {'password': 'user', 'role': 'user'}
}
# 留言数据文件路径
messages_file = 'messages.json'

# 加载留言数据
def load_messages():
    if os.path.exists(messages_file):
        with open(messages_file, 'r') as f:
            return json.load(f)
    return []

# 保存留言数据
def save_messages(messages):
    with open(messages_file, 'w') as f:
        json.dump(messages, f, indent=2)

# 初始化留言数据
messages = load_messages()

@app.route('/')
def home():
    token = request.cookies.get('auth_token')
    if token and token in valid_tokens:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/index')
def index():
    token = request.cookies.get('auth_token')
    if not token or token not in valid_tokens:
        return redirect(url_for('login'))
    username = request.cookies.get('username')
    role = users.get(username, {}).get('role', 'user')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('index.html', current_time=current_time, username=username, role=role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    token = request.cookies.get('auth_token')
    if token and token in valid_tokens:
        return redirect(url_for('index'))
    else:
        # 清除无效的 cookie
        response = make_response(render_template('login.html'))
        response.set_cookie('auth_token', '', expires=0)
        response.set_cookie('username', '', expires=0)
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if username in users and users[username]['password'] == password:
                # 生成一个安全的随机令牌
                new_token = secrets.token_hex(16)
                valid_tokens.add(new_token)
                response = make_response(redirect(url_for('index')))
                response.set_cookie('auth_token', new_token, max_age=3600)  # Cookie 有效期为1小时
                response.set_cookie('username', username, max_age=3600)
                return response
            else:
                return render_template('login.html', error='用户名或密码错误')
        return response

@app.route('/logout')
def logout():
    token = request.cookies.get('auth_token')
    if token in valid_tokens:
        valid_tokens.remove(token)
    response = make_response(redirect(url_for('login')))
    response.set_cookie('auth_token', '', expires=0)  # 清除 cookie
    response.set_cookie('username', '', expires=0)
    return response

@app.route('/message_board', methods=['GET', 'POST'])
def message_board():
    token = request.cookies.get('auth_token')
    if not token or token not in valid_tokens:
        return redirect(url_for('login'))
    username = request.cookies.get('username')
    role = users.get(username, {}).get('role', 'user')
    global messages
    if request.method == 'POST':
        if role == 'user':
            action = request.form.get('action')
            if action == 'add':
                message = request.form.get('message')
                if message:
                    messages.append({'id': len(messages), 'username': username, 'message': message, 'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                    save_messages(messages)
            elif action == 'edit':
                message_id = int(request.form.get('message_id'))
                new_message = request.form.get('message')
                for msg in messages:
                    if msg['id'] == message_id and msg['username'] == username:
                        msg['message'] = new_message
                        msg['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        save_messages(messages)
                        break
            elif action == 'delete':
                message_id = int(request.form.get('message_id'))
                messages[:] = [msg for msg in messages if not (msg['id'] == message_id and msg['username'] == username)]
                save_messages(messages)
            return redirect(url_for('message_board'))
        elif role == 'admin':
            action = request.form.get('action')
            if action == 'delete':
                message_id = int(request.form.get('message_id'))
                messages[:] = [msg for msg in messages if msg['id'] != message_id]
                save_messages(messages)
            elif action == 'edit':
                message_id = int(request.form.get('message_id'))
                new_message = request.form.get('message')
                for msg in messages:
                    if msg['id'] == message_id:
                        msg['message'] = new_message
                        msg['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        save_messages(messages)
                        break
            return redirect(url_for('message_board'))
        else:
            return redirect(url_for('index'))
    return render_template('message_board.html', messages=messages, role=role, username=username)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0', ssl_context=None)
