#ifndef LLDPREMMANADDRTABLE_OIDS_H
#define LLDPREMMANADDRTABLE_OIDS_H
#include <sys/types.h>

#define LLDPREMMANADDRTABLE_OID 1, 0, 8802, 1, 1, 2, 1, 4, 2
#define COLUMN_LLDPREMMANADDRSUBTYPE 1
#define COLUMN_LLDPREMMANADDR 2
#define COLUMN_LLDPREMMANADDRIFSUBTYPE 3
#define COLUMN_LLDPREMMANADDRIFID 4
#define COLUMN_LLDPREMMANADDROID 5

#define LLDPREMMANADDRTABLE_MIN_COL COLUMN_LLDPREMMANADDRSUBTYPE
#define LLDPREMMANADDRTABLE_MAX_COL COLUMN_LLDPREMMANADDROID
#endif