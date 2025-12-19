.PHONY: build run rebuild shell clean

# Détection automatique de l'architecture (je suis sur mac avec puce M3 donc archi arm64)
UNAME_M := $(shell uname -m)
ifeq ($(UNAME_M),arm64)
    PLATFORM := --platform linux/amd64
else
    PLATFORM :=
endif

# Build l'image Docker
build:
	docker build $(PLATFORM) -t vex .

# Compile leaky.c puis lance VEX
run:
	docker run $(PLATFORM) -it --rm \
		-v $(PWD):/app \
		-w /app/test_cases \
		vex /bin/bash -c "make re && ../srcs/vex.py ./leaky"

# Rebuild complet (clean + build)
rebuild: clean build

# Shell interactif dans le conteneur
shell:
	docker run $(PLATFORM) -it --rm -v $(PWD):/app vex /bin/bash

# Clean l'image
clean:
	docker rmi vex 2>/dev/null || true