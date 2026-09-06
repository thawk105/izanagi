---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2294-mocc-lock-instrumentation
seq: 2
---

## {{D:mocc-lock-coverage-instrumentation}}. mocc の lock 被覆・permutation 計装は RWLOCK counter と CLL を真実源にし、保持検査を 3 点にする

**決定:** mocc (`cc/mocc/transaction.cc`、preimage = submodule e9e477ca) の `#if TRACE` 計装は、Silo の Tidword ベース計装を転用せず、
`ReaderWriterLock` の counter (`W_LOCKED`) と `CLL_` の `LockElement` (`key_` / `mode_` / `lock_` の一致) を真実源にする。
X の検査点は (1) writePhase 入口 (`not-locked-at-entry`)、(2) payload 操作直前 (`lock-lost-before-write`)、(3) tidword publish 直前
(`lock-lost-before-publish`) の 3 点とし、P は `sort(write_set_)` 前後の size と `rcdptr_` multiset の保存だけを主張する。
歯の立証は負例 3 本 (`broken-mocc-{lockskip-validation,permutation-erase,early-unlock}.patch`) と compute 実走の 14 check で行い、
early-unlock は unlock と relock を対にした balanced 形にする。

**理由:**
- mocc は payload 書き込み・tidword publish・`unlockCLL()` が別の場所にあり、Silo の 2 点 (入口・store 直前) では publish 前の
  lock 喪失を見逃す。3 点目を足すことで保持検査が publish の直前まで届く。
- counter は owner ID を持たないため入口検査だけでは「CLL が stale で他 worker が再取得した」状態を区別できない。CLL の `lock_`
  pointer 一致を predicate に含めて、少なくとも CLL が指す lock と record の lock の不一致は捕まえる。残る限界は README に明記する。
- `w_unlock()` は `counter_++` なので、単純な早期 unlock は counter を `0 → 1` に壊して次の writer が永久 spin する。balanced に
  しないと負例が完走せず、保持検査だけの歯を独立に立証できない。
- 負例の裸 directive は owner file に 1 回だけ置く (condition gate の exactly-one 契約)。early-unlock は file scope の
  `static constexpr bool` 1 箇所と `if constexpr` 2 site で表現する。

**却下した選択肢:**
- 負例 2 本 (lockskip / perm-erase) で済ませる — 保持検査の歯を独立に立証しない gate は恒真ゲートの疑いが残る。
- `#ifndef RWLOCK / #error` を置く — 裸 define 登録簿が `RWLOCK` を新設 interface と数えて赤になる。RWLOCK 無しでは `CLL_` が
  宣言されず compile error になるので fail-closed は暗黙で成立する。
- CLL の順序や施錠順まで P で主張する — P は write_set_ sort の permutation 保存しか見ていない。

## {{D:trace0-preprocess-logical-row-witness}}. D14 契約に `#line` の例外を認め、TRACE=0 同一性の正本 witness を「論理行列の一致」にする

**決定:** `#if TRACE` 計装 patch は、各 `#endif` の直後に preimage の論理行番号を復元する `#line N` だけを literal `#if TRACE` の外に
置いてよい。規律 1 (観測者効果ゼロ) の正本 witness は、無 patch と patch 適用後の source を `g++ -E -DTRACE=0` (line marker を残す) し、
marker を論理行番号へ畳んだ「(行番号, 非空本文) 列」の一致とする。補助 witness として、無 patch と patch 適用の TRACE=0 binary の
`objdump -d` (行頭アドレスだけ除去) と `.text` の一致を compute JSON に記録する。

**理由:**
- `#line` が無いと、計装の行数分だけ後続の `ERR` / `NNN` の `__LINE__` immediate と rip 相対 lea が動き、TRACE=0 binary が preimage と
  一致しなくなる (login probe で 14 箇所)。`#line` は preprocessor 指令で code を生まず、これを許すことで「性能 build は bytes まで
  同一」という最強の形で規律 1 を置ける。
- `#line` 自体が `-E` 出力に `# N "file"` marker を増やすので、生 byte の一致は構造的に成立しない。一方 `-P` で marker を消すと
  `__LINE__` の drift に盲目になる。marker を論理行へ畳んだ列は、`#line` の値が ±1 ずれても差になる。
- build する dir 名の長さが違うだけで `__FILE__` 文字列長の差により `.rodata` が動き lea が 158 行ずれる (login 実測)。
  binary 比較は source と build の path 長を揃えて行い、揃えられない環境では前処理の論理行列を正本とする。

**却下した選択肢:**
- `#line` を使わず計装を末尾へ寄せる — 検査点は writePhase / validation の途中にあり、位置を変えれば検査の意味が変わる。
- `-ffile-prefix-map` で path 差を吸収する — 依存物 (gflags / masstree) の `__FILE__` は直らない。
- 段 4 で書いた「line marker 込みの byte 一致」を維持する — 上記のとおり構造的に不可能で、fix 子の初回実装が必ず赤になった。
