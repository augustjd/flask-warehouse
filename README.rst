*******************
Flask-Warehouse
*******************

Simple cloud file storage for Flask applications on platforms like S3, Alicloud, or Heroku.


.. code-block:: python

   import os

   from flask import Flask
   from flask_warehouse import Warehouse

   # 1. Configuring Warehouse
   app = Flask(__name__)
   app.config['WAREHOUSE_DEFAULT_SERVICE'] = 's3'          # or 'file' for filesystem
   app.config['WAREHOUSE_DEFAULT_LOCATION'] = 'us-west-1'  # required for 's3'
   app.config['WAREHOUSE_DEFAULT_BUCKET'] = None


   app.config['AWS_ACCESS_KEY_ID'] = '...'                 # required for 's3'
   app.config['AWS_SECRET_ACCESS_KEY'] = '...'             # required for 's3'

   warehouse = Warehouse(app)

   # Object-oriented approach:
   bucket = warehouse.bucket('mybucket')
   oo_cubby = bucket.cubby('keys')

   # Or compact approach:
   compact_cubby = warehouse('s3:///mybucket/keys')

   assert oo_cubby == compact_cubby

   cubby = oo_cubby

   # 2. Writing to/from bytes
   contents = b'12345'
   cubby.store(bytes=contents)

   assert cubby.filesize() == 5

   cubby_contents = cubby.retrieve()
   assert cubby_contents == contents

   # 3. Writing to/from files
   filepath = "local.txt"
   with open(filepath, 'wb') as f:
       f.write(b"Here are the contents of a file.")

   cubby.store(filepath=filepath)
   assert os.path.getsize(filepath) == cubby.filesize()

   assert cubby.retrieve() == open(filepath, 'rb').read()
   ```
