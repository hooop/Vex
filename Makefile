.PHONY: build run rebuild shell clean

# Build l'image Docker
build:
	docker build --platform linux/amd64 -t vex .

# Compile leaky.c puis lance VEX
run:
	docker run --platform linux/amd64 -it --rm -v $(PWD):/app vex /bin/bash -c "gcc -g -o leaky2 leaky2.c && ./vex.py ./leaky2"

# Rebuild complet (clean + build)
rebuild: clean build

# Shell interactif dans le conteneur
shell:
	docker run --platform linux/amd64 -it --rm -v $(PWD):/app vex /bin/bash

# Clean l'image
clean:
	docker rmi vex 2>/dev/null || true