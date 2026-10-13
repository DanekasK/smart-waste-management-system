# Apache Reverse Proxy Configuration for R Shiny

To serve the R Shiny dashboard alongside static web pages on a production Linux/Apache server, configure a reverse proxy.

### 1. Enable Required Apache Modules
```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_wstunnel
sudo systemctl restart apache2
```

### 2. VirtualHost Proxy Configuration
Add the following proxy directives to `/etc/apache2/sites-available/waste-management.conf`:

```apache
<VirtualHost *:80>
    ServerName waste-management.local
    DocumentRoot /var/www/html

    # Proxy WebSocket and HTTP traffic to the Shiny app running on port 3838
    ProxyPreserveHost On
    ProxyPass /dashboard/ http://127.0.0.1:3838/
    ProxyPassReverse /dashboard/ http://127.0.0.1:3838/

    RewriteEngine on
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/dashboard/?(.*) "ws://127.0.0.1:3838/$1" [P,L]
</VirtualHost>
```

### 3. Launching Shiny in Background
```bash
nohup Rscript -e "shiny::runApp('/path/to/dashboard/data.R', port=3838, host='127.0.0.1')" > /var/log/shiny-dashboard.log 2>&1 &
```
