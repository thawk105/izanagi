## must-fix

- [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/campaign/condition_meaning_gate.py:1754): `BACKOFF_NOINLINE=0/default=0` を `_configured_define_compile_commands` で共有すると、supply 用 control は `(stock_root, None)` ですが、meaning は `(source_root, "1")` を要求するため [compile-command-drift](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/campaign/condition_meaning_gate.py:3050) になります。成果物影響: 同じ正当入力が `configured_commands` の共有有無だけで admission green から red へ変わります。inert 時は meaning を独立 configure するか、値 1 の第三 command を用意し、0/0 の共有経路 test を追加してください。

## nit

なし。

## 合成の確認 (交差点ごとに 1 行)

- T-2226 は stock inert の preprocess 比較後の分類と supply validator に局在し、route 限定 `shared_branch_build` や非 inert の `stock_identity` 経路を変更していません。
- A-2、s1、t1683 は supply と meaning を別々に評価するため、現行配線では要求 0 の supply `(patched root, 0)` 対 `(stock root, None)` と meaning `(patched root, 0)` 対 `(patched root, 1)` は両立します。
- `stock_comparison=False` でも requested と default が同値なら inert になる既存契約は維持され、stock root が渡される A-2 と s1 の経路に矛盾はありません。
- `_validate_supply_green_evidence` と `_validate_meaning_green_evidence` は arm 分岐で独立しており、`common` 集合や `_validate_record_*` helper に両側からの競合変更はありません。
- 両側の追加 test、fixture、helper に同名衝突はなく、`_COMPILE_TIME_BRANCH_MACROS` と `_compile_time_source_root` の拡張も T-2226 test へ波及しません。
- T-2226 test は `supplied/include/backoff.hh` の固定 hash やファイル行数を pin しておらず、追加 3 行による破損経路はありません。
- AST と `^def |^class ` 一覧で、両対象ファイルに関数、class、module 定数の二重定義はありません。
- 意図された green 拡張は stock inert の root-location-only と NOINLINE の 0/1 meaning に限定されていますが、上記共有経路に意図しない red が 1 件あります。

## 総括

意味的合成は大部分で直交していますが、NOINLINE 要求 0 の共有 configured-command 経路に偽 red があるため、must-fix 1 件です。指定どおり静的検査のみ行い、pytest は実行していません。