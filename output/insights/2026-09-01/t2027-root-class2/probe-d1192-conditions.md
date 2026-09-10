== cache entry ==
completion: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/mainprobe/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/87aa2e6a61d85ef61b1ba88616bb19c39b5dfe49030f6f78fdc68175102d5c94/completion.json
contract dir: e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
entry dir: 87aa2e6a61d85ef61b1ba88616bb19c39b5dfe49030f6f78fdc68175102d5c94
manifest schema: s8b-compiler-input/v1
manifest sha256 (recorded): 4f072a8975823229cb61912fbde19493af40fd2fa5ffbbc5afc6dc0f337284cf
recomputed: 4f072a8975823229cb61912fbde19493af40fd2fa5ffbbc5afc6dc0f337284cf
target: ycsb_silo.exe
input_policy: snapshot-and-external-hashes/v1
depfile_count: 3
inputs: 588

== descriptor / completion 側の同一性材料 ==
admission: <dict len=11>
binary: <dict len=2>
compiler_input_manifest_sha256: 4f072a8975823229cb61912fbde19493af40fd2fa5ffbbc5afc6dc0f337284cf
complete_toolchain_manifest: <dict len=3>
complete_toolchain_manifest_sha256: 6a73081a1bead42ac9f8ad18fcaeaf196aed0955482ce5459d9e2656c34625c0
completion_marker: complete
contract_sha256: e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
full_build_digest: 87aa2e6a61d85ef61b1ba88616bb19c39b5dfe49030f6f78fdc68175102d5c94
preimage: <dict len=12>
schema_version: buildcache/v2
toolchain: <dict len=3>

== 入力の置き場ごとの内訳と実在 ==
/usr/include: 415 件 (現存しない 0 件)
     /usr/include/alloca.h
     /usr/include/arpa/inet.h
     /usr/include/asm-generic/bitsperlong.h
/usr/lib: 96 件 (現存しない 0 件)
     /usr/lib/gcc/x86_64-linux-gnu/11/include/adxintrin.h
     /usr/lib/gcc/x86_64-linux-gnu/11/include/ammintrin.h
     /usr/lib/gcc/x86_64-linux-gnu/11/include/amxbf16intrin.h
build-cache staging (root class 1): 31 件 (現存しない 31 件)
     /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/mainprobe/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2092533-79aabeed6c1584d75a7e167d1a539d09/_deps/masstree-src/btree_leaflink.hh
     /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/mainprobe/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2092533-79aabeed6c1584d75a7e167d1a539d09/_deps/masstree-src/circular_int.hh
     /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/mainprobe/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2092533-79aabeed6c1584d75a7e167d1a539d09/_deps/masstree-src/compiler.hh
job workspace (root class 2): 7 件 (現存しない 7 件)
     /scr/0_952631.nqsv/gflags-install/include/gflags/gflags.h
     /scr/0_952631.nqsv/gflags-install/include/gflags/gflags_declare.h
     /scr/0_952631.nqsv/gflags-install/include/gflags/gflags_gflags.h
snapshot-relative: 39 件 (現存しない 0 件)
     cc/silo/include/atomic_tool.hh
     cc/silo/include/common.hh
     cc/silo/include/log.hh

== 現行コードへ通したときの拒否述語 (全件) ==
CompilerInputError: external compiler input is unavailable

== クラスごとに単独で通したときの拒否述語 ==
build-cache staging (root class 1): CompilerInputError: external compiler input is unavailable
job workspace (root class 2): CompilerInputError: external compiler input is unavailable

== v2 形へ写したときの拒否述語 (クラス 2 は filesystem 根で記録される) ==
build-cache staging (root class 1): CompilerInputError: compiler input is unavailable or cannot be hashed
job workspace (root class 2): CompilerInputError: compiler input is unavailable or cannot be hashed
