#include <stdlib.h>
#include <string.h>

/*
** Test: pointer reuse leak.
** A pointer is used for two allocations in sequence.
** The first allocation is lost when the pointer is reused.
*/

int	main(void)
{
	char	*ptr;

	ptr = malloc(32);
	strcpy(ptr, "first");
	ptr = malloc(64);
	strcpy(ptr, "second");
	free(ptr);
	return (0);
}
