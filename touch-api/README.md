#  FastAPI
- [ FastAPI]()
  - [Development](#development)
  - [Production](#production)
  - [Author(s)](#authors)


## Development

1. Read [this](./markdown/pyodbc.md) for things to do before installing pyodbc with pip. That is the backup Markdown file I copied from [here](https://github.com/mkleehammer/pyodbc/wiki/Install)
   
2. Download MS ODBC Driver 18 for [Windows](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16#download-for-windows)  or [Linux](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver16&tabs=alpine18-install%2Calpine17-install%2Cdebian8-install%2Credhat7-13-install%2Crhel7-offline#18)
3. Fill out server details in the .env file
4. Create a virtual environment using the `requirements.txt` in this folder, using [VSCode](https://code.visualstudio.com/docs/python/environments#_creating-environments) or [PyCharm](https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html) or manually:
  
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

and for when you want to exit the venv:

```
deactivate
```

5. Run Dev Server by typing `fastapi dev src/main.py` 

6. **READ THE DOCUMENTATION!** *All classes and functions have docstrings and/or comments.* If you wish to know how this code works, start with `main.py` in the `src` folder

7. The `.gitkeep` file will be deleted when you upload into the folder, be sure to add it back before committing or else the `static` folder won't be committed to git.

## Production

1. Fill out server details in .env file
2. `sudo chmod +x run.sh`
3. `./run.sh` The script will install all prerequisites, install the server as systemd service and start it.
 
 
## Author(s)
Johnny (Lost) - jmlin0101@gmail.com