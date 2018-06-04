import cherrypy
import requests
import zipfile
import io
import csv
import redis
import os
import datetime

red = redis.StrictRedis(host='localhost', port=6379,
                        db=0, decode_responses=True)


class BSE(object):

    showing_data_for = ''

    @cherrypy.expose
    def index(self):

        csv_data, date_of_csv = self.get_csv()

        self.store_csv_in_redis(csv_data, date_of_csv)

        return self.get_html(self.get_top_ten_stocks())

    def get_html(self,top_ten):
        html_mid = ''

        for stock in top_ten:
            stock_info = red.hgetall(stock)
            code_html = '<td>' + stock_info['code'] + '</td>'
            name_html = '<td class="mdl-data-table__cell--non-numeric">' + \
                        stock_info['name'] + '</td>'
            open_html = '<td>' + stock_info['open'] + '</td>'
            high_html = '<td>' + stock_info['high'] + '</td>'
            low_html = '<td>' + stock_info['low'] + '</td>'
            close_html = '<td>' + stock_info['close'] + '</td>'
            begin_r = '<tr>'
            end_r = '</tr>'

            html_mid = html_mid + begin_r + code_html + name_html + \
                       open_html + high_html + low_html + close_html + end_r

        html_front = """
                    <html>
                    <head>
                        <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
                        <link rel="stylesheet" href="https://code.getmdl.io/1.3.0/material.indigo-pink.min.css">
                        <link rel="stylesheet" href="/static/css/main.css">
                        <script defer src="https://code.getmdl.io/1.3.0/material.min.js"></script>
                    </head>
                    <body>
                    <div id=header align=center>
                    <img width="100" height="34.5" src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Bombay_Stock_Exchange_logo.svg/2000px-Bombay_Stock_Exchange_logo.svg.png">
                    Top 10 stocks on """ + str(self.showing_data_for.date().strftime('%A %d %B %Y')) + """
                    </div>
                    <table align="center" class="mdl-data-table mdl-js-data-table mdl-shadow--2dp">
                        <thead>
                        <tr>
                            <th class="mdl-data-table__cell--non-numeric">Code</th>
                            <th class="mdl-data-table__cell--non-numeric">Name</th>
                            <th>Open</th>
                            <th>High</th>
                            <th>Low</th>
                            <th>Close</th>
                        </tr>"""
        html_rear = """
                        </thead>
                        <tbody>
                        </tbody>
                    </table>
                    <div id="info" align="center">
                    Use the below button to search details of any other BSE stock by its name like HDFC or DR.REDDY'S  
                    <form action="search">
                        <div class="mdl-textfield mdl-js-textfield mdl-textfield--expandable">
                             <label class="mdl-button mdl-js-button mdl-button--icon" for="search">
                             <i class="material-icons">search</i>
                             </label>
                            <div class="mdl-textfield__expandable-holder">
                                <input class="mdl-textfield__input" type="text" name="name_of_stock" id="search">
                                <label class="mdl-textfield__label" for="sample-expandable">Expandable Input</label>
                            </div>
                        </div>
                    </form>
                    </div>

                    </body>
                    </html>
                    """
        return html_front + html_mid + html_rear



    @cherrypy.expose
    def search(self, name_of_stock):

        name_of_stock = (name_of_stock.strip()).upper()

        stock_code = red.zscore('name', name_of_stock)

        if not stock_code:
            return 'Please enter a valid stock name and try again.'

        stock_hash_key = 'code:' + str(int(stock_code))

        stock_info = red.hgetall(stock_hash_key)

        code_html = '<td>' + stock_info['code'] + '</td>'
        name_html = '<td class="mdl-data-table__cell--non-numeric">' + \
                    stock_info['name'] + '</td>'
        open_html = '<td>' + stock_info['open'] + '</td>'
        high_html = '<td>' + stock_info['high'] + '</td>'
        low_html = '<td>' + stock_info['low'] + '</td>'
        close_html = '<td>' + stock_info['close'] + '</td>'
        begin_r = '<tr>'
        end_r = '</tr>'

        html_front = """
            <html>
            <head>
                <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
                <link rel="stylesheet" href="https://code.getmdl.io/1.3.0/material.indigo-pink.min.css">
                <link rel="stylesheet" href="/static/css/main.css">
                <script defer src="https://code.getmdl.io/1.3.0/material.min.js"></script>
            </head>
            <body>
            <div id=header align=center>
            <img width="100" height="34.5" src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Bombay_Stock_Exchange_logo.svg/2000px-Bombay_Stock_Exchange_logo.svg.png">
            </div>
            <table align="center" class="mdl-data-table mdl-js-data-table mdl-shadow--2dp">
                <thead>
                <tr>
                    <th class="mdl-data-table__cell--non-numeric">Code</th>
                    <th class="mdl-data-table__cell--non-numeric">Name</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                </tr>"""

        html_mid = begin_r + code_html + name_html + open_html + high_html + low_html + close_html + end_r

        html_rear = """
                </thead>
                <tbody>
                </tbody>
            </table>
            </body>
            </html>
            """

        return html_front + html_mid + html_rear

    def store_csv_in_redis(self, csv_path, date_of_csv):
        # Save CSV into the Redis DB

        with open(csv_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            self.showing_data_for = date_of_csv

            # Store the data we need from the CSV to the Redis DB

            for row in csv_reader:
                red.hset('code:' + row['SC_CODE'], 'code', row['SC_CODE'])
                # Because CSV returns name w/ spaces
                red.hset('code:' + row['SC_CODE'],
                         'name', row['SC_NAME'].strip())
                red.hset('code:' + row['SC_CODE'], 'open', row['OPEN'])
                red.hset('code:' + row['SC_CODE'], 'high', row['HIGH'])
                red.hset('code:' + row['SC_CODE'], 'low', row['LOW'])
                red.hset('code:' + row['SC_CODE'], 'close', row['CLOSE'])

                red.zadd('open', row['OPEN'], 'code:' + row['SC_CODE'])  # To find top 10 stocks quickly
                red.zadd('name', row['SC_CODE'], row['SC_NAME'].strip())  # To find by name

    def get_csv(self):

        red.flushall()

        # Try to find the zip for the current day, if not found
        # go and try to find one from previous day and keep trying for previous ten days
        i = 0
        while i < 10:

            date_of_csv = datetime.datetime.today() - datetime.timedelta(days=i)
            print(date_of_csv)
            date_str = str('%02d' % date_of_csv.day) + str('%02d' % date_of_csv.month) + str(date_of_csv.year - 2000)
            csv_path = 'EQ' + date_str + '.CSV'

            if os.path.exists('./'+csv_path):
                print('path exists')
                return csv_path, date_of_csv

            url = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ' + date_str + '_CSV.ZIP'
            request = requests.get(url)

            if request.status_code == 200:

                #Delete old CSV files, if any

                cwd = os.listdir(os.getcwd())

                for item in cwd:
                    if item.endswith(".CSV"):
                        os.remove(os.path.join(os.getcwd(), item))

                # Extract Zip
                z = zipfile.ZipFile(io.BytesIO(request.content))
                z.extractall()
                return csv_path, date_of_csv

            else:
                i += 1

    def get_top_ten_stocks(self):
        return red.zrevrange('open', 0, 9)


if __name__ == '__main__':
    cherrypy.config.update(
        {'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    cherrypy.quickstart(BSE(), '/', conf)
