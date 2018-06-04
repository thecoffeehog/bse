import cherrypy
import requests
import zipfile
import io
import csv
import redis
import os

red = redis.StrictRedis(host='localhost', port=6379,
                        db=0, decode_responses=True)


class BSE(object):
    @cherrypy.expose
    def index(self):

        top_ten = self.get_top_ten_stocks()

        html_mid = ''
        for stock in top_ten:
            code_html = '<td>' + red.hgetall(stock)['code'] + '</td>'
            name_html = '<td class="mdl-data-table__cell--non-numeric">' + \
                red.hgetall(stock)['name'] + '</td>'
            open_html = '<td>' + red.hgetall(stock)['open'] + '</td>'
            high_html = '<td>' + red.hgetall(stock)['high'] + '</td>'
            low_html = '<td>' + red.hgetall(stock)['low'] + '</td>'
            close_html = '<td>' + red.hgetall(stock)['close'] + '</td>'
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
            Top 10 stocks of the day
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
            Search other BSE stocks by Name using the below button
            <form action="#">
                <div class="mdl-textfield mdl-js-textfield mdl-textfield--expandable">
                     <label class="mdl-button mdl-js-button mdl-button--icon" for="search">
                     <i class="material-icons">search</i>
                     </label>
                    <div class="mdl-textfield__expandable-holder">
                        <input class="mdl-textfield__input" type="text" id="search">
                        <label class="mdl-textfield__label" for="sample-expandable">Expandable Input</label>
                    </div>
                </div>
            </form>
            </div>

            </body>
            </html>
            """
        return html_front + html_mid + html_rear

    def get_top_ten_stocks(self):

        # Download Zip TODO: Make Link using date
        url = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ010618_CSV.ZIP'
        request = requests.get(url)

        # Extract Zip
        z = zipfile.ZipFile(io.BytesIO(request.content))
        z.extractall()

        # Save CSV into the Redis DB
        csv_path='EQ010618.CSV'
        with open(csv_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            red.flushall()
            top_ten = ''

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

                red.zadd('open', row['OPEN'], 'code:' + row['SC_CODE'])
                #red.zadd('name', row['SC_CODE'], row['SC_NAME'].strip())

                top_ten = red.zrevrange('open', 0, 9)

        return top_ten


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
t
