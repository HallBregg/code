build:
	docker build -t book .


test: build
	docker run --rm -it book pytest
