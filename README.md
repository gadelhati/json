# _JSON_

![Python](https://img.shields.io/badge/Python-3.13.5-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.13-009688?logo=fastapi)

## install
```
# create virtual environment
python -m venv .venv

# activate virtual environment
.venv/Scripts/activate

# udpate pip
python.exe -m pip install --upgrade pip

# install dependencies
pip install --upgrade -r requirements.txt

# run application
uvicorn app.main:app --reload

# test coverage verification
python -m pytest --cov=app --cov-report=term-missing

# test report, in /htmlcov/index.html
python -m pytest --cov=app --cov-report=html

# test execution, with details
python -m pytest -v

pip install --proxy http://user:password@proxy.fqdn:6060 -r requirements.txt
git config --global http.proxy http://user:password@proxy.fqdn:6060
```
