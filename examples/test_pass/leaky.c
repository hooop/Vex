#include <stdlib.h>
#include <string.h>

/*
** Test: pointer passed as function argument.
** The pointer is allocated in create(), passed to process()
** which does NOT free it, and main() does not free it either.
** Expected: Type 2 — pointer lost at end of process().
*/

char	*create(void)
{
	char	*buf;

	buf = malloc(64);
	strcpy(buf, "hello");
	return (buf);
}

void	process(char *ptr)
{
	ptr[0] = 'H';
}

int	main(void)
{
	char	*data;

	data = create();
	process(data);
	return (0);
}
