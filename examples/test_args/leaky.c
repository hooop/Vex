#include <stdlib.h>
#include <string.h>
#include <stdio.h>

char	*duplicate_arg(const char *arg)
{
	char	*copy;

	copy = malloc(strlen(arg) + 1);
	strcpy(copy, arg);
	return (copy);
}

int	main(int argc, char **argv)
{
	char	*first;
	char	*second;

	if (argc < 3)
	{
		printf("Usage: ./leaky <arg1> <arg2>\n");
		return (1);
	}
	first = duplicate_arg(argv[1]);
	second = duplicate_arg(argv[2]);
	printf("Got: %s and %s\n", first, second);
	free(first);
	return (0);
}
