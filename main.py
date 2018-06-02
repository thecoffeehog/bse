import cherrypy

import requests, zipfile, io


class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return "Hello world!"

    @cherrypy.expose
    def download(self):

        # Download Zip TODO: Make Link using date
        url = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ010618_CSV.ZIP'
        r = requests.get(url)

        # Extract Zip
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall()

        # Save CSV into the Redis DB

        return "";


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '127.0.0.1','server.socket_port': 8080})
    cherrypy.quickstart(StringGenerator(), '/', 'app.conf')