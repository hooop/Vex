#include <stdlib.h>
#include <string.h>

void cleanup(char **arr, int count)
{
	int	i;

	i = 0;
	while (i < count)
	{
		if (i != 300)
			free(arr[i]);
		i++;
	}
	free(arr);
}

int main(void)
{
	char	**arr;
	int		i;

	arr = malloc(500 * sizeof(char *));
	i = 0;
	while (i < 500)
	{
		arr[i] = malloc(10);
		strcpy(arr[i], "hello");
		i++;
	}
	cleanup(arr, 500);
	return (0);
}
