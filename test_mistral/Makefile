# Nom de l'exécutable
NAME = leaky

# Compilateur
CC = gcc

# Flags de compilation
CFLAGS = -g

# Fichiers sources
SRC = src/leaky.c

# Fichiers objets
OBJ = $(SRC:.c=.o)

# Règle par défaut
all: $(NAME)

# Compilation de l'exécutable
$(NAME): $(OBJ)
	$(CC) $(CFLAGS) $(OBJ) -o $(NAME)

# Nettoyage des .o
clean:
	rm -f $(OBJ)

# Nettoyage complet
fclean: clean
	rm -f $(NAME)

# Recompile tout
re: fclean all

# Exécution avec Valgrind (le --leak-check=full est ici)
valgrind: $(NAME)
	valgrind --leak-check=full --track-origins=yes ./$(NAME)

.PHONY: all clean fclean re valgrind
