# -*- coding: utf-8 -*-
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from yawxt import OfficialAccount, check_signature
from yawxt.persistence import PersistentMessageProcessor

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = ''
db = SQLAlchemy(app)

wechat_account = OfficialAccount("appid", "appsecret")
token = "token"

session_maker = db.create_session({})

@app.route('/wechat', methods=["GET", "POST"])
def wechat():
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    if not check_signature(token, timestamp, nonce, signature):
        return "Messages not From Wechat"
    if request.method == "GET":
        return request.args.get('echostr')
        
    msg = PersistentMessageProcessor(request.data, wechat_account,
                            db_session_maker=session_maker,
                            debug_to_wechat=app.debug)
    return msg.reply()
    
if __name__ == "__main__":
    app.run()
