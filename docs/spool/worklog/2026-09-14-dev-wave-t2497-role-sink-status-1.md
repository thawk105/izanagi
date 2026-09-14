---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2497-role-sink-status
seq: 1
title: [T-2497] role sink 非干渉 node へ report status 検査と partial 負例を足し、変異で受理集合の縮小を実測した (コード + docs、branch worktree-dev-wave-t2497-role-sink-status、変異 matrix = 走 4 本・baseline すべて PASSED・差分確定走で M9 KILLED / M9' SURVIVED の期待一致 rc=0・M5 系は内側 gate に masked のため erratum で取り下げ)
---

## 本文

- **依頼は「`test_role_sink_bytes_vary_only_at_declared_declassifications` が partial report を
  完全走として読む穴を塞ぐ」。** status 検査を足し、partial report で確実に赤になる負例を
  同じ commit へ足す。恒真な保証の型なので検査を足す側であって受理集合は広げない。
- **成果物は test file 1 件への追加のみ (71 insertions / 2 deletions、commit 6babfe8e0)。**
  module-local helper が各 wire の実 report について `status == "complete"` を wire 入り
  メッセージで assert し、`report["cells"][0]` を返す。既存の 2 つの `report["cells"][0]`
  利用箇所をこの戻り値経由にしたので、呼出し行の単独削除は `NameError` になる。
  負例 node は実 `run_trial` から partial を 2 形 (critic 欠落 → `supervisor-error` で
  `fatal_error` あり / `_InvalidPlanner` → `role-invalid` で `fatal_error` なし) 得て、
  helper がそれぞれを拒否することを確かめる。production file は変更していない (D1847)。
- **DW-O13 の実測を段 1 で行った。** `--basetemp` を repo 外へ向けて既存 node を 1 回走らせ、
  `run_trial` が書いた 32 本の `report.json` を直接読んだ。すべて `status="complete"` /
  `fatal_error` なし / `stop_reason="fixed-generation-budget"` だったので、
  `assert report["status"] == "complete"` は到達可能で baseline を赤にしない。
- **親 brief の説明が間違っていたので段 4 で訂正した。** 「32 wire の一部しか回っていない report でも
  緑になる」は構造と一致しない。32 件の収集は `executor.map` 後の件数 assert が守っており、
  31 wire しか集まらなければ status 検査が無くても赤になる。**真の穴は、収集などを満たした
  個々の trial の完了性を見ていないこと**である。段 3 の 2 レンズが独立に指摘した。
- **段 3 と段 6 の 4 レンズが独立に「負例だけでは受理集合の真の縮小を示せない」と指摘した。**
  critic 欠落構成を旧 node に持ち込むと payload 件数検査で落ちるので、
  その負例は「旧 node が受理していた走」の再現になっていない。親はこれを採用し、
  **証明を負例でなく `DW-M08` の新旧両走 (変異) へ移した。**
- **変異で最初に登録した M5 は masked だった。** producer の `status` リテラルだけを
  `"complete"` → `"partial"` に反転する変異は KILLED になったが、**赤は追加した検査ではなく
  既存の production gate だった** — `orchestrator/campaign/autonomous_trial_completeness.py:2886`
  の `_check_status_projection` が producer と同じ述語を独立に再計算して `status` と突き合わせ、
  `[terminal-projection] report status must be 'complete'` で落とす。この gate は
  `p3_autonomous_workload_trial.py:3902` から `run_trial` の末尾で無条件に呼ばれる。
  F820 の「同じ入力を拒否する層が内側にある」状態なので M5 / M5' を取り下げ、erratum に残した。
- **再照準を 2 回した。** (1) report へ `fatal_error` を直接注入する形は同 file 2405 の
  「journal event を伴わない fatal_error」で masked。(2) wall budget 経路
  (`cell.pop("_deferred_wall_generation", 1)`) は同 file の `[workload-coverage]
  wall-budget terminal event has no missing workload` で masked。
  **この 3 度の mask 自体が、report の完了性については production 側に既に厚い層があるという実測である。**
- **3 度目の再照準 M9 で差分が出た。** `_run_pending_critics` の末尾へ `raise` を注入すると、
  cell が完成し 4 role の payload も WAL も揃った後に `supervisor-error` が立ち、
  内側 gate をすべて通過した**本物の partial report** が `run_trial` から返る。
  本 node の赤は `AssertionError: wire=00000: expected complete, got status=partial` で、
  **追加した検査そのもの**だった。同じ producer 変異に「呼出し接続を外す置換」を重ねた M9' では
  本 node が緑になる。**この 2 走の差が、受理集合が真に縮まった実測である。**
- **段 6 のレンズ A が、塞がずに測ると裁定した生存変異を 2 件見つけた。**
  (M6) helper の述語を `stop_reason not in {"supervisor-error","role-invalid"}` へ書き換えると、
  負例の 2 形とも同じメッセージで拒否されるので**status を全く見ない helper が両 node を緑にできる。**
  (M7) 呼出し行を `cell = report["cells"][0]` へ 1 行置換しても両 node は緑のまま。
  いずれも事前登録どおり SURVIVED を実測した。注入 diff の sha256 は変異ごとに相異なり
  anchor は各 1 件だったので no-op ではない (DW-M04)。
  **防壁を足して塞ぎにいかず、D387 の射程として docstring と本エントリに明記する** ({{D:role-sink-status-gate-boundary}})。
- **レンズ B は独立に既存被覆の保存を確認した。** 変更前後で AST 上の assert 列が一致し、
  test 関数名集合は 230 → 231 で削除・改名 0 件。親も同じ照合を別経路 (`grep -oE "^def "` の
  集合 diff、277 → 279) で行い一致した。`cell` が参照するオブジェクトも変更前と同一である。
- **レンズ B の nit を 3 件採用した。** 新規 docstring が英語だったので日本語化した (fix 子)。
  「1 node に収める = 直列 work を増やさない」という親の説明は誤りで、node 数を抑えても
  `run_trial` 2 走分の費用は残る (既存同型 node の台帳値 0.099 / 0.11 秒から見積り約 0.2 秒)。
  「`.get()` にすると欠落を受理する」という親の不採用理由も誤りで、`report.get("status") == "complete"`
  でも欠落は拒否する。
- **受入全走は attempt 1 で通った。** verdict `child-green`、`child_rc=0`、
  `red_nodeids` と `flake_nodeids` はいずれも空、**23315 passed / 68 skipped / 0 failed**。
  tested_main `c347c049b` / tested_tip `d8556c3ed`。投入時の login node load average は
  `43.00 / 58.39 / 54.62` で、1483 で決めた「1分 < 5分 < 15分 の下降局面で 1 回だけ投げる」運用に従った。
  **輻輳期に 5 回投げて赤を量産した前回と違い、窓を待った 1 投入で非帰属赤が 0 件だった。**
- 焦点走は 423 passed / 0 failed。変更 test file 全 node に加え、node 集合を pin する
  meta-test 3 群 (`test_real_repo_serialization.py` の canonical node 照合、
  `test_acceptance_schedule_order.py`、`test_pytest_collection_config.py`) を 1 投入で直列に流した。
- 段 2 に codex plan 1 本、段 3 に consult 2 本 (sol / luna)、段 5 に author 1 本、
  段 6 に review 2 本 + fix 1 本を使った。実装子は sandbox から dispatch できず (rc=16)
  **実走 0 件**を正直に申告し、実測はすべて親が行った。
- **段 8 の自己改善は候補 2 件で、1 件を採用・1 件を refuted にした。**
  採用したのは M5 の mask (F820 の 3 回目の再発として追記)。**reference への追記は
  byte 予算で 2 回続けて弾かれた** — `DW-M01` へ入れると `docs/dev-wave/**` の L1 unique
  footprint が 10795 > 10625、発火点である `DW-M07` へ移すと単節 1216 > 1000 だった。
  DW-M01 が既に F820 を指しているので、知見は F820 側だけに置いて reference は無改変にした
  (同じ物語を入口・reference へ再掲しない契約に従う)。上限は引き上げていない。
  refuted にしたのは「受入 lease dir の正本が dev-wave docs に無い」で、
  `docs/pegasus-runbook.md` §7.3 に dir も定型 argv も既に書かれていた。親の読み落としである。
- 段 5 の初回投入は `--reasoning` を author 段へ渡して rc=2 で即死した。DW-C01 に
  「`--reasoning` は plan/consult で必須、他段指定は rc=2」と明記されている既知契約への違反で、
  新しい失敗型ではない。argv を直して再投入した。

## 次の一手差分

### 完了

- [T-2497] status 検査と partial 負例を足し、変異で受理集合の縮小を実測した。
  remaining: none
  base: adae8ee5658470dbe281c4ad6d8e3b64e39e93e815ff6f86f1dbd9dd96737f39
