#!/usr/bin/make

include .env

build:
	docker build -t astonish_image .

run:
	docker run -d --name astonish_container -p 80:80 astonish_image
stop:
	docker container stop $(CONTAINER_NAME)

# Remove the Docker container
clean:
	docker container rm $(CONTAINER_NAME)

# Remove the Docker image
clean-image:
	docker image rm $(IMAGE_NAME)

# Remove the container and the image
clean-all: clean clean-image
