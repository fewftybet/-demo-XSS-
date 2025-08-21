@echo off
chcp 65001
cd /d %~dp0
start cmd /k "cd legit_site && python app.py"
start cmd /k "cd phishing_site && python app.py"
echo 两个服务器已启动！
echo 正常网站运行在 http://example.com:5000
echo 钓鱼网站运行在 http://examp1e.com:5001
pause
