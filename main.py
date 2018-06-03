import cherrypy
import requests, zipfile, io
import csv
import redis

red = redis.StrictRedis(host='localhost', port=6379, db=0,decode_responses=True)

class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return "Hello world!"

    @cherrypy.expose
    def download(self):

        # Download Zip TODO: Make Link using date
        url = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ010618_CSV.ZIP'
        request = requests.get(url)

        # Extract Zip
        z = zipfile.ZipFile(io.BytesIO(request.content))
        z.extractall()

        # Save CSV into the Redis DB
        with open('EQ010618.csv', 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            red.flushall()
            top_ten = ''
            for row in csv_reader:
                red.hset('code:' + row['SC_CODE'], 'code', row['SC_CODE'])
                red.hset('code:' + row['SC_CODE'], 'name', row['SC_NAME'].strip())
                red.hset('code:' + row['SC_CODE'], 'open', row['OPEN'])
                red.hset('code:' + row['SC_CODE'], 'high', row['HIGH'])
                red.hset('code:' + row['SC_CODE'], 'low', row['LOW'])
                red.hset('code:' + row['SC_CODE'], 'close', row['CLOSE'])
                # red.zadd('open', 'code:' + row['SC_CODE'], row['OPEN'])
                red.zadd('open',  row['OPEN'], 'code:' + row['SC_CODE'])

                top_ten = red.zrevrange('open', 0, 9)

        print(top_ten)

        print('Top 10 Stocks!')
        for stock in top_ten:
            print(red.hgetall(stock))

if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '127.0.0.1','server.socket_port': 8080})
    cherrypy.quickstart(StringGenerator(), '/', 'app.conf')