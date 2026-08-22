段2 plan は、実行系の変更面については妥当です。ただし「grep 全域で literal は2箇所 בלבד」という記述は過大です。

### Consumer 網羅性

- 実行コード上の producer は [hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/tools/hold_inventory.py:107) のみ。
- import、JSON parse、human render、entry 件数・field 集合を機械検査する consumer は [test_hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/orchestrator/tests/test_hold_inventory.py:582) のみ。
- `growth_test_hold_inventory()` と `test_growth_test_holds_contract.py` は provider 側であり、`bypass_surface` metadata の consumer ではない。
- `from tools import hold_inventory`、動的 import、別 CLI consumer、production/CI の field 参照は発見できなかった。

一方、literal 自体は `docs/archive/` と `output/insights/` にも残る。これは履歴・レビュー成果物で実行 consumer ではないが、brief の「全域で2箇所」は正確ではない。「現行の実行系では2ファイル בלבד」と限定すべきです。

### 維持か削除か

維持は妥当です。D347 は保留状態をユーザーの判断入力・監査 snapshot と位置づけており、経路 ID、`T-930`、閉鎖結果を残せば、監査証跡と将来の guard 回帰検知を保てます。

ただし `bypass_surface` は本来「現在迂回し得る経路」と読めるため、解決済み経路を残すなら、`known-resolved-bypass` を「旧 bypass 経路だが現在は guard により拒否」と明示する必要があります。`tracking: T-930` も未完了 task ではなく解決元への履歴ポインタです。

### 履歴

brief の核心は正しいものの、経緯は不完全です。

- 2026-08-16 の T-1222 wave は stale metadata を `[T-1267]` として scope 外の real 所見に記録しています（[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/docs/archive/worklog-phase3-0816-606.md:592)）。
- 2026-08-17 の T-1049 でも `pytest-confcutdir-below-suite` の既存登録を再確認し、T-930 完了後の所有者は inventory entry 自身だと記録しています（[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/docs/archive/worklog-phase3-0817-624.md:29)）。
- 2026-08-21 の T-1222 wave で `[T-1456]` として再確認され、未着手のままです（[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/docs/archive/worklog-phase3-0821-778.md:559)）。

したがって「2 wave が未着手」は成立しますが、T-1267 と T-1049 の先行言及を追記した方が正確です。

### Entry 5/6 との整合

整合します。

- entry 5 は explicit release token の transport。
- entry 6 は `PYTEST_ADDOPTS` に suppression option を運ぶ transportであり、迂回成功を意味しません。
- 1–4 は「経路の現在状態」、5–6 は「transport の役割」を分類しているため、分類語彙は混在しますが、`effect` と entry ID により意味は区別できます。plan にこの分類方針を一文追加すると誤読を防げます。

pytest は実行していません。

## 総括

- P1: **real** — stale な `known-unresolved-bypass` metadata と golden copy は実在する。`known-resolved-bypass` 案は妥当だが、監査用の履歴意味を明記すべき。
- P2: **refuted** — D347 は literal 値を pin せず、今回の再分類は「未解決経路を未解決と明示する」趣旨に反しない。