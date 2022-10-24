local-docker: compile-contracts
	make copy-contracts
	docker-compose up -d --build
deploy-contracts:
	cd ../.. && yarn && yarn deploy
compile-contracts:
	cd ../.. && yarn && yarn compile
copy-contracts:
	cp -r ../../build/contracts ./launcher/src
	cp -r ../../build/contracts ./exchange/src
	cp -r ../../build/contracts ./recording-oracle
	cp -r ../../build/contracts ./reputation-oracle
test:
	docker-compose -f docker-compose.test.yml up -d --build
	cd ../.. && yarn && yarn deploy 
	cp -r ../../build/contracts ./tests/e2e-backend
	cd tests && yarn && yarn test:e2e-backend