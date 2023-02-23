import time
from flask import Flask, render_template
from screener import Screener
from flask import jsonify

app = Flask(__name__)
screener = Screener()

@app.route('/')
def main_page():
    time_now = round(time.time() - screener.monet_usd_10[0], 2)

    return render_template('main.html', coins=screener.monet_usd_10[1:10], time_now=time_now)




@app.route("/update_table")
def your_function():
    coins = screener.monet_usd_10[1:10]
    return render_template("update_table.html", coins=coins)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)