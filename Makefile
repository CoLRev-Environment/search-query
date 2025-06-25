UID := $(shell id -u)
GID := $(shell id -g)
LANG := "en_CA.UTF-8"

pdf: 
	docker run --rm --volume "$(PWD)":/data --user $(id -u):$(id -g) --env JOURNAL=joss openjournals/inara
