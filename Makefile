all : robinhood_api r2q

robinhood_api:
	cd Robinhood && pip install .

r2q:
	python setup.py install
