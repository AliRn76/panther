1. git clone https://github.com/AliRn76/panther.git
2. cd panther
3. python3.11 -m venv .venv
4. source .venv/bin/activate
5. pip install .
6. pip install pymongo python-jose (if needed)
7. cd example
8. panther run --reload
9. pip install ../ && panther run --reload

Repeat number 9 on every change you are going to make on panther 

or make a change on `.venv/lib/python3.11/site-packages/panther` so you don't need to pip install the package again, 
but make sure you moved the changes you made from `.venv/lib/python3.11/site-packages/panther` to the actual code
