# Mojo Posts 💚

Welcome to Mojo Posts built with Coinset.org API's, chia-dev-tools and running Django.  There are only a few changes needed to make this your own (listed below). 

You can view this in action here:  https://memodemo-os.onrender.com/

This project will display memos sent to an XCH address of your choice by using API's from Coinset.org and python/html to decode and display the memos, block heights and amount on the home page.

#How to set up

To run this on a server use the start command is:

'gunicorn hello_world.wsgi:application'

Note that changing the 'SECRET_KEY' in .env is required for security.
When going into production 'DEBUG' needs to be set to False.

## .env
```python
SECRET_KEY=Your_Secret_Key   (Django recommends at least 50 characters)
DEBUG=False
```

There are other security settings that can be set.  Please check the Django documentation for a full list of settings:  https://docs.djangoproject.com/en/5.1/topics/security/

Change the XCH address to send mojos to on post.html here:

## hello_world/templates/post.html
```python
<div class="p-3 bg-gray-800 rounded-lg border border-gray-600 text-lg">
                <p>🈷️<strong>Send 1 Mojo to:</strong></p>
                <p class="mt-2 text-green-400 font-mono break-all">
                    xch_your_address_here
                </p>
            </div>
```

To have memos sent to your XCH address load on the home page put the hash of your XCH address in this line in settings.py:

## settings.py

```python
# Puzzle Hash for the application
PUZZLE_HASH = "Your_XCH_Address_Puzzle_Hash_Here"
```

To get the hash of your xch address you can use the tool here:

https://mojoposts.com/convert/




Other tips for using Django:

## Installing dependancies

```python
pip install -r requirements.txt
```

## To collect static files:

```python
python manage.py collectstatic
```

## To run this application:

```python
python manage.py runserver
```
## To check deployment readiness:

```python
Run manage.py check --deploy
```
Note there will be some settings like HSTS and CSRF Cookies to set for production, this setting is omitted in settings.py to allow editing the project and running it from the local server.  This is recommended to be set when put into production.  See the Django deploy check for more details.

Also, X_FRAME_OPTIONS can be added to settings.py to prevent your site from being loaded in an iframe.  It is omitted in settings.py for using the simple browser to load the site when editing it, but is recommended for in production.

## settings.py - Optional but recommended when going into production

```python
X_FRAME_OPTIONS = 'DENY'
```

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for more information.

## Disclaimer

This software is provided "as is," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

By using this software, you acknowledge that it is your responsibility to ensure its suitability for your purposes and to comply with any relevant laws and regulations.
