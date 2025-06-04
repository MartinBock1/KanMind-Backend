# Django project - set up KanMind backend

**1. clone repository** 
Copy the existing project to your computer: 
```sh
git clone <REPOSITORY-LINK>
cd <Projektordner>
```

**2. set up a virtual environment**
Create a virtual environment and activate it:  
```sh
python -m venv env
env/Scripts/activate  # Windows
source env/bin/activate  # macOS/Linux
```
*Note:* On macOS/Linux you may need to use `python3` instead of `python`.

**3. check & install dependencies**
First check if packages are installed and then install the dependencies from the file:  
```sh
pip freeze  # check currently installed packages
pip install -r requirements.txt  # install packages
pip freeze  # check whether everything has been installed correctly
```

**4. run migrations**
Apply the existing migrations (there is **no need** to do `makemigrations` as they are already included):
```sh
python manage.py migrate
```

**5. start local server** 
Start the Django server: 
```sh
python manage.py runserver
```

**Tipp:** If errors occur, check the `settings.py` for paths, database settings or forgotten `.env` files.