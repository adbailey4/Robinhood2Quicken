all : robinhood_api r2q

robinhood_api:
#	cd Robinhood && pip install .
	cd submodules/Robinhood && python setup.py install

r2q:
	python setup.py install
