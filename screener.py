import time
import requests
import json
from threading import Thread
import operator
from pybit import account_asset
from settings import bybit_keys


class Screener:
    def __init__(self):
        self.txt_monets = self.get_txt_monets()
        self.txt_exchangers = self.get_txt_exchangers()
        self.bybit_client = account_asset.HTTP(endpoint=bybit_keys['endpoint'], api_key=bybit_keys['api_key'],
                                               api_secret=bybit_keys['api_secret'])

        self.bybit_network = self.bybit_client.query_coin_info()

        self.skip_val_les = 990
        self.max_val_to_buy = 1500

        self.start_threads()

    def start_threads(self):
        Thread(target=self.get_Bybit_price).start()
        Thread(target=self.get_BestChange_rates).start()
        time.sleep(10)
        Thread(target=self.get_monet_usd_10).start()

    def get_txt_monets(self):
        with open('Txt_files/whitetickers.txt', 'r') as file:
            text = file.readlines()
            data = []
            for line in text:
                line = line.split(';')
                monet = {'id': line[0].split('=')[1],
                         'name': line[2].split('=')[1],
                         'ticker': line[3].split('=')[1],
                         # 'wallet': line[4].split('=')[1],
                         'memo': line[5].split('=')[1],
                         'chain': line[6].split('=')[1].replace('\n', ''),
                         'network_fee': '0'}

                data.append(monet)

            return data

    def get_txt_exchangers(self):
        with open('Txt_files/exchangers.txt', 'r') as file:
            text2 = file.readlines()
            data2 = []
            for line2 in text2:
                line2 = line2.split(';')
                data2.append(
                    {'status': line2[0].split('=')[1],
                     'id': line2[1].split('=')[1],
                     'name': line2[2].split('=')[1][:-1]}
                )
            return data2

    def write_file(self, price):
        with open(f'Json_files/bybit_ask-bid.json', 'w') as file:
            json.dump(price, file)

    def read_file(self):
        with open(f'Json_files/bybit_ask-bid.json') as file:
            return json.load(file)

    def get_BestChange_rates(self):
        while True:
            try:
                url_server_1 = "http://62.217.180.252/clear_rates.json"

                url_server_2 = "http://62.113.112.229/get"

                bestchange_2 = requests.get(url_server_2).json()

                self.clear_rates = bestchange_2[1]

                print(f'Зд/сек: {round(time.time() - self.clear_rates[0]["time"], 2)}   Обновил пары с BestChange')
            except:
                print('Не удалось запросить обменники с серверов Bestchange')
            time.sleep(0.5)

    def get_Bybit_price(self):
        while True:
            try:
                url_bybit = "https://api.bybit.com/spot/quote/v1/ticker/book_ticker"
                bybit = requests.get(url_bybit).json()
                time_start = time.time()
                Bybit_price = []
                for ticker in self.txt_monets[:-3]:
                    for monet in bybit['result']:

                        if monet['symbol'] == ticker['ticker'] + 'USDT':
                            ticker['ask_price'] = float(monet['askPrice'])
                            ticker['bid_price'] = float(monet['bidPrice'])
                            for network2 in self.bybit_network['result']['rows']:
                                if ticker['ticker'] == network2['name']:
                                    for chain in network2['chains']:
                                        if ticker['chain'] == chain['chain']:
                                            ticker['network_fee'] = chain['withdraw_fee']
                            ticker['time'] = time.time()
                            Bybit_price.append(ticker)

                self.write_file(Bybit_price)
                print(f'Зд/сек: {round(time.time() - time_start, 2)}    Обновил цены с Bybit')
                time.sleep(0.5)
            except:
                print('Не удалось запросить цены с Bybit')
                time.sleep(3)

    def get_monet_usd_10(self):
        while True:
            self.monet_usd_10 = self.get_monet_usd_id(10)
            time.sleep(0.5)

    def get_monet_usd_id(self, get_id):
        start_time = time.time()
        try:
            Bybit_price = self.read_file()
        except:
            print('Не удалось получить данные из файла Json_files/bybit_ask-bid.json')
            return [time.time()]
        id_bybtit_ticker_1 = []
        clear_rates_1 = self.clear_rates.copy()
        for ticker in Bybit_price:
            id_bybtit_ticker_1.append(int(ticker['id']))
            ticker['pars'] = []
        for rate in clear_rates_1:
            if int(rate['get_id']) == get_id and int(rate['give_id']) in id_bybtit_ticker_1:
                index = id_bybtit_ticker_1.index(int(rate['give_id']))
                if round(rate['max_sum'] * rate['mon_usdt']) < self.skip_val_les:
                    continue
                Bybit_price[index]['pars'].append(rate)
        for monet in Bybit_price:
            monet['max_spred'] = -999
            monet['max_profit'] = -999
            monet['color'] = '#FFFFFF'
            if len(monet['pars']) < 1:
                monet['pars'].append({'get_id': '0000'})
                continue
            monet['price'] = float(monet['ask_price'])
            for par in monet['pars']:
                par['min'] = round(par['min_sum'] * par['mon_usdt'])
                par['max'] = round((par['max_sum'] * par['mon_usdt']) - 20)
                par['spred'] = round(((par['mon_usdt'] - monet['ask_price']) / par['mon_usdt']) * 100, 2)
                if par['max'] > self.max_val_to_buy:
                    tax = ((self.max_val_to_buy * 0.1) / 100) + (float(monet['network_fee']) * monet['ask_price'])
                    par['profit'] = round(
                        (self.max_val_to_buy / monet['ask_price'] * (par['mon_usdt'] - monet['ask_price']) - tax), 3)
                    par['sum_profit'] = self.max_val_to_buy
                else:
                    tax = ((par['max'] * 0.1) / 100) + (float(monet['network_fee']) * monet['ask_price'])
                    par['sum_profit'] = par['max']
                    par['profit'] = round(
                        (par['max'] / monet['ask_price'] * (par['mon_usdt'] - monet['ask_price']) - tax), 3)
                par['monets'] = par['sum_profit']/monet['ask_price']
            monet['pars'].sort(key=operator.itemgetter('profit'), reverse=True)
            monet['time'] = round((start_time - monet['time']) + (start_time - monet['pars'][0]['time']), 2)
            try:
                monet['max_spred'] = monet['pars'][0]['spred']
                monet['max_profit'] = monet['pars'][0]['profit']
                if monet['max_profit'] > 5:
                    monet['color'] = 'green'
                monet['url'] = f'https://www.bestchange.ru/click.php?id={monet["pars"][0]["exchange_id"]}&from={monet["pars"][0]["give_id"]}&to={monet["pars"][0]["get_id"]}&city=0'
            except:
                print('Ошибка создания максимального спреда/профита по монете', monet['name'])
        Bybit_price = sorted(Bybit_price, key=operator.itemgetter('max_profit'), reverse=True)
        Bybit_price.insert(0, time.time())
        return Bybit_price


if __name__ == '__main__':
    screener = Screener()
    screener.start_threads()
