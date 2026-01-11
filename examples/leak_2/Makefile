# Auto-detect architecture
UNAME_M := $(shell uname -m)
ifeq ($(UNAME_M),arm64)
    PLATFORM := --platform linux/amd64
else
    PLATFORM :=
endif

CC = gcc
CFLAGS = -g

# Variables
SRC = leaky_2.c
TARGET = leaky_2

# Detect if running inside Docker
IN_DOCKER := $(shell test -f /.dockerenv && echo 1 || echo 0)

all: $(TARGET)

ifeq ($(IN_DOCKER),1)
# Inside Docker - compile directly
$(TARGET): $(SRC)
	@$(CC) $(CFLAGS) $(SRC) -o $(TARGET)
else
# Outside Docker - use container
$(TARGET): $(SRC)
	@docker run $(PLATFORM) --rm -v $(PWD):/work -w /work vex $(CC) $(CFLAGS) $(SRC) -o $(TARGET)
endif

clean:
	@rm -f $(TARGET)

re: clean all

.PHONY: all clean re