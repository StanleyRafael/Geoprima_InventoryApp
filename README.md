Install Git if not already installed.

Install Python (make sure to check "Add Python to PATH" during installation).

Install XAMPP or another MySQL database server.

Clone the repository:
git clone https://github.com/StanleyRafael/Geoprima_InventoryApp.git

Update app.py with the new database credentials.

Run the batch file to set up the environment and install dependencies.

Run database migrations (in the app's root folder):
flask db upgrade 
