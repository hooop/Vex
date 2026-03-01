#include <stdlib.h>
#include <string.h>

/*
** Test: scope leak.
** Memory is allocated in a helper function but only
** used locally. The caller never receives the pointer.
*/

void	init_data(void)
{
	char	*tmp;

	tmp = malloc(128);
	strcpy(tmp, "temporary data");
}

int	main(void)
{
	init_data();
	return (0);
}
