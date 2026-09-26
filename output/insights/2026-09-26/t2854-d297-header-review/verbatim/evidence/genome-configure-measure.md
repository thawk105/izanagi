# genome 別 configure の compile database 実測 (親、login、2026-09-26 22:21〜22:22 JST、file mtime)

C2' 40a7f4ac の一時 worktree (job tmp `ccb-c2p`) を 3 通りに configure (いずれも rc=0、build はしない):

- base: `-DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_PREFIX_PATH=/work/1/SFC/tanab/izanagi-a2-deps` (option 既定値) → `compile_commands-C2p.json`
- g1 (silo genome の 1 点): base + `-DENABLE_SANITIZER=OFF -DCCBENCH_BACK_OFF=1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=1 -DCCBENCH_TRACE=0` → `compile_commands-C2p-g1.json`
- g2 (他 protocol の option を全部 1 + TRACE=1): base + `-DENABLE_SANITIZER=OFF -DCCBENCH_BACK_OFF=1 -DCCBENCH_INLINE_VERSION_OPT_CICADA=1 -DCCBENCH_INLINE_VERSION_PROMOTION=1 -DCCBENCH_REUSE_VERSION=1 -DCCBENCH_WRITE_LATEST_ONLY=1 -DCCBENCH_KEY_SORT=1 -DCCBENCH_TEMPERATURE_RESET_OPT=1 -DCCBENCH_PREEMPTIVE_ABORTS=1 -DCCBENCH_TIMESTAMP_HISTORY=1 -DCCBENCH_TRACE=1` → `compile_commands-C2p-g2.json`

結果 (source root 配下の entry、third_party の mimalloc 等を除く):

- entry 数は 3 通りとも 117、(file, target) の集合は 3 通りで一致 (option で target の有無は変わらない — この 3 点では)。
- g1 − base: silo の 12 entry で `-DWAL=0` → `-DWAL=1` だけ (base の既定が BACK_OFF=1・NWLIV=1・NWOT=0)。
- g2 − base: TRACE 0→1 は 33 entry (common・mvto・silo・test・tictoc)、cicada 12 entry は INLINE_VERSION_OPT・WRITE_LATEST_ONLY も、
  **d2pl・ermia・mocc・si・ss2pl の 60 entry は KEY_SORT も**、oze 12 entry は WRITE_LATEST_ONLY も変わる。
  → 1 つの CMake option が複数 protocol の define を同時に変える (`CCBENCH_KEY_SORT` は mocc の genome 軸だが si・ermia・ss2pl・d2pl にも効く)。
- 注: base の 135 entry は third_party (mimalloc 等) を含む総数、117 は source root 配下。consumer 21 entry はすべて source root 配下。
