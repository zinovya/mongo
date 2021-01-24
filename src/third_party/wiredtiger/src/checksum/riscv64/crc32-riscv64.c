/*
 * 
 */

#include <wiredtiger_config.h>
#include <inttypes.h>
#include <stddef.h>


extern uint32_t __wt_checksum_sw(const void *chunk, size_t len);
#if defined(__GNUC__)
extern uint32_t (*wiredtiger_crc32c_func(void))(const void *, size_t)
  __attribute__((visibility("default")));
#else
extern uint32_t (*wiredtiger_crc32c_func(void))(const void *, size_t);
#endif

/*
 * wiredtiger_crc32c_func --
 *     WiredTiger: just software checksum function for now.
 */
uint32_t (*wiredtiger_crc32c_func(void))(const void *, size_t)
{
    return (__wt_checksum_sw);
}
