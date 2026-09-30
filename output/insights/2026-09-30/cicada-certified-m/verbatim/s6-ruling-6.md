# 段 6 裁定 6 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: 親の本走 (chain-1: MAIN-2〜5 rc 0、IDENT rc 1。`runs/ident-2/result-IDENT.json`)。対象 = b432b81ed。実機で見つかった欠陥 (親の実機 blocker)。

**実測:** IDENT の 10 組 (default・best × ycsb・tpcc・bomb・sbomb の stock、default・best の ycsb E-max の M 無し対 M 有り) がすべて `equal=false`。default ycsb stock で比べると ycsb_cicada.cc・util.cc の命令列 sha256 は一致し、transaction.cc だけが違う。親が両側の `transaction.cc.o` を `objdump -d --no-show-raw-insn` (address 除去) で比べた差は 1 命令だけ: `TxExecutor::gc_records()` の中の `mov $0x355,%r9d` (pin) 対 `mov $0x356,%r9d` (M 適用後)。0x355 = 853 は pin の `transaction.cc:853` (`gc_records` の `ERR`) の行番号で、M 適用後はそれが 854 として展開されている。

| ID | 裁定 | 処置 |
|---|---|---|
| D8 M patch の `#line` が 1 行ずれ、TRACE=0 の命令列が pin と違う | real (must-fix、絶対規律 1) | U1: M patch の全 `#else` / `#line N` / `#endif` について、TRACE=0 で直後の行の実効行番号が pin の同じ行の行番号と一致するように直す。全 `#line` を機械的に確かめる方法 (scratch 内の検査 script でよい、repo には入れない) を用い、各 `#line` の番号と対応する pin の行を表で報告する。E-max stack でも同じ `#line` が正しいこと (forwarding 3 patch が行番号を動かす箇所で M の `#line` が pin でなく「M 無しの E-max source」の行番号に一致すること) を確かめる |

**計測の扱い:** `#line` は `#if TRACE` の `#else` 側だけにあり TRACE=1 の build には入らないが、patch の bytes が変わるので、直した bytes で SMOKE・MAIN-1〜5・IDENT・MUT を取り直す (合計の計算は約 20 分)。b432b81ed の bytes での SMOKE・MAIN の結果は記録として残し、一次資料では取り直しの値を使う。
