---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2639-branch-rescue-path-first
seq: 3
---

## 新規

### {{F:flaky-hold-registry-pinned-to-one}}. 不安定 test の登録手順と、登録簿を 1 件へ固定する契約テストが正面から衝突する [恒真ゲート] [手順漏れ]

- 事象: 受入全走が同一 tip・同一差分で 10 回続けて赤になり、赤はすべて非帰属だった
  (本 wave が変更した 2 file を 1 度も参照せず、単独走では全件緑)。`DW-O18` は
  「再赤・決定的赤は main 既存 F を証拠に Codex `role=author` が
  `orchestrator/tests/flaky_test_holds.py` へ登録する」と定めるので、F300 を証拠に 4 node を
  登録した。登録簿自身の validator は通ったが、
  `orchestrator/tests/test_flaky_test_holds_contract.py::test_live_registry_exports_exact_registered_hold_and_digest`
  が **`assert len(REG._FLAKY_TEST_HOLD_ROWS) == 1`**、登録 node、`evidence_id == "F57"`、
  `reintroduction_task_id == "t-1079"`、登録簿の sha256 まで逐語で固定しており赤になった。
  同 file の `test_live_flaky_summary_derives_exact_count_and_digest_from_registry` も同時に赤。
- 根本原因: `DW-O18` は「証拠付きなら登録してよい」と書き、契約テストは
  「登録簿はちょうど 1 件・その内容」と書く。**手順に従うと契約テストが赤くなり、契約テストを
  守ると手順を使えない。** どちらも main に在り、どちらも自分の側では正しい。
- **この衝突は防壁として働いた。** 契約テストは、wave が自分を緑にするために除外集合を広げることを
  「wave 開始前から在るテストの期待値を書き換えないと不可能」にする。本 wave は登録を撤回した
  (`git checkout --` で clean に戻し、作業ツリーの状態行 0 を実測)。**pin を書き換える側が
  誤りである**と裁定した。
- 恒久対応: **未定。裁定パッケージへ送る。** `DW-O18` の登録手順を残すなら契約テストを
  「登録は追加のみ・各行に証拠必須」の形へ変える必要があり、契約テストを残すなら `DW-O18` から
  登録手順を落として「非帰属赤は投げ直しのみ」と書き直す必要がある。**正本どうしの選択であり
  AI が単独で決めない。**
- 再発検知: `flaky_test_holds.py` を編集する wave は、同じ commit で
  `test_flaky_test_holds_contract.py` が赤になる。登録簿の行数・digest を固定する assert が
  そのまま signature である。

## 再発

### F300

- **再発: 2026-09-16 (2 例目)** — [T-2639] wave が同日・同機序で独立 2 例目を出した。
  同一 tip・同一差分で受入全走を **10 回**走らせ、**10 回とも赤**だった
  (赤 2 → 3 → 1 → 8 → 2 → 1 → 2 → 2 → 2 → 3、通過は毎回 23832〜23949)。
  赤になった test は走行ごとに変わり、**本 wave が変更した `tools/check_branch_landed.py` /
  `tools/check_branch_rescue.py` を参照する test は 1 件も無く** (`grep -c` で 0 を実測)、
  単独再走はすべて緑 (3 件 → 3 passed、3 件 → 3 passed、2 件 → 2 passed、いずれも rc=0)。
  親の worktree は全走の前後とも `git status --porcelain=v1 --untracked-files=all` が **0 行**で、
  残骸も無い。落ちる検査はこの status を処理の前後で撮って一致を要求するので、変化の出所は
  **走行の内側**である。
  **本エントリが 2026-09-14 の再発項で「恒久対応は未定」とした循環 (証拠 F が main へ着地するまで
  hold 登録できない) は、本追記の親エントリが main に在ることで既に解けている。** しかし
  hold 登録は別の防壁 ({{F:flaky-hold-registry-pinned-to-one}}) に阻まれるため、**恒久対応は
  依然として未定である。** 本 wave はこれを理由に land を見送り、正式停止した。
  観測された node は `test_disposable_tree_mutation_does_not_change_main_worktree` (7/10)、
  `test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch` (4/10)、
  `test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink` (3/10)、
  `test_provenance_headroom_short_queue_unavailable_cap_oom_stops` (2/10)、ほか 5 件が各 1 回。
