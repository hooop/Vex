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
SRC = leaky.c
TARGET = leaky_1

all: $(TARGET)

$(TARGET): $(SRC)
	@docker run $(PLATFORM) --rm -v $(PWD):/work -w /work vex $(CC) $(CFLAGS) $(SRC) -o $(TARGET)

clean:
	@rm -f $(TARGET)

re: clean all

.PHONY: all clean re