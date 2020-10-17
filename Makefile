build:
	docker-compose build


pull:
	docker-compose pull


test: build app-test down


app-test:
	docker-compose run --rm app pytest


up:
	docker-compose up -d


down:
	docker-compose down


logs:
	docker-compose logs -f


all: down build up test
