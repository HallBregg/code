build:
	docker-compose build


app-test:
	docker-compose run --rm -e API_HOST=app app pytest


pull:
	docker-compose pull

up:
	docker-compose up -d


down:
	docker-compose down


logs:
	docker-compose logs -f


test: build up app-test down


all: down build up test
