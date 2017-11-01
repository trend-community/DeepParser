import sys
sys.path.insert(0, '/nlpengine/parser/src')
from RestfulService import app as application

#/etc/apache2/sites-enabled/parser.conf
#<VirtualHost *:5001>
#    #ServerName example.com
#
#    WSGIDaemonProcess yourapplication user=team group=staff processes=12
#    WSGIScriptAlias / /nlpengine/parser/src/RestfulService.wsgi
#    AllowEncodedSlashes On
#    <Directory /nlpengine/parser/>
#        WSGIProcessGroup yourapplication
#        WSGIApplicationGroup %{GLOBAL}
#        Require all granted
#    </Directory>
#ErrorLog ${APACHE_LOG_DIR}/Parser_error.log
#CustomLog ${APACHE_LOG_DIR}/Parser_access.log combined
#</VirtualHost>

