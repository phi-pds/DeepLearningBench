#include <stdio.h>

int main()
{
	int i, j, k;

	for (i = 0; i <1000000; i++) {
		for (j = 0; j <1000; j++) {
			k = 10 + 1 + i + j;
		}
	}
	k = 0;
	return 0;
}
