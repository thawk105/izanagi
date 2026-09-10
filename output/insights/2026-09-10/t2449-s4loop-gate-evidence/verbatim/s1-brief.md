# 段 1 brief — [T-2449] 段 4 loop の condition gate supply arm を再現し証拠を採る

- wave `dev-wave-t2449-s4loop-gate-evidence` / branch `worktree-dev-wave-t2449-s4loop-gate-evidence`
- base local main `7f17e1c63b5db01b424c87cf5778635dd653dab2` (2026-09-09 22:36 JST 時点、乖離 0)
- worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence`
- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence`

## 研究前進

段 4 loop の driver は計算ノードで 1 iteration も完走しておらず、CC 合成の試行台帳に compute 実走の
行が 1 件も無い。job `983020.nqsv` は `condition_meaning_gate` の supply arm で止まり、止まった理由の
本文 (preprocess の argv と stderr) は job 終了時に失われた。**完了判定 = 現行 main の driver を計算
ノードで 1 本走らせ、supply arm が (a) 通るか (b) 落ちるかを判定し、落ちるなら失敗本文を job 終了後も
残る evidence root に持つこと。** これが取れるまで「供給経路の次に何が要るか」を誰も測れない。

## brief 前の実測で判明した、依頼の前提を覆す新事実 (段 4 で再裁定する)

1. **gate へ offline configure 引数を渡す seam は、job `983020.nqsv` の後に main へ入った。**
   job の commit `a173f0ab5` では `_require_condition_gate(sub, genome)` が無条件で、offline 引数
   (`-DCMAKE_PREFIX_PATH` / `-DFETCHCONTENT_BASE_DIR` / `-DFETCHCONTENT_SOURCE_DIR_*`) は後段の
   `campaign_options` にしか渡っていなかった (`logs/p3_s4_loop_a173f0ab5.py:1679`)。現行 main は
   receipt がある分岐で `_condition_gate_offline_configure_args(...)` を渡す
   (`orchestrator/campaign/p3_s4_loop.py:1826-1837`)。導入 commit は `9a32ef5ca` (2026-09-09 02:36 JST)
   で、`git merge-base --is-ancestor 9a32ef5ca a173f0ab5` は rc=1 (job の木に無い)。
   → **983020 の失敗は現行 producer では既に消えている可能性がある。** 旧 commit の再走は別命題を測る
   ことになるので、再現は現行 main 系の tip で行う。
2. **失敗本文は既に record の中にある — 捨てているのは driver である。**
   `condition_meaning_gate._run_process` は失敗時に `rc=` と stderr 末尾 500 byte を
   `ConditionMeaningGateError.detail` へ入れ (`:1580-1586`)、
   `evaluate_define_supply_effectuation` はそれを red の arm record の `evidence.detail` に載せる
   (`:2562-2570`)。しかし `p3_s4_loop._require_condition_gate` は `reason_code` 2 個だけで
   `RuntimeError` を上げ、record を捨てる (`:409-412`)。983020 の `job.stderr` にも reason code 行しか
   無い。→ **必要な配線は「record を evidence root へ落とす」であり、gate の判定を変える必要は無い。**
3. **system gflags/glog はログインノードにも無い** (`/usr/include/gflags` 不在、`pkg-config --exists
   gflags` rc=1)。「計算ノードに system gflags が無い」は計算ノード固有ではない。job body の prologue が
   `$TMPDIR` へ install して `CMAKE_PREFIX_PATH` で供給する形は D1773/D1801 のまま有効。
4. preprocess argv は record に**入っていない**。`_preprocess_argv` の戻り値は `_run_process` へ渡るだけで
   失敗 detail に載らない (`:2064-2073`、`:2226-2236`)。依頼の「preprocess argv」を満たすには
   `condition_meaning_gate` 側に 1 箇所の追記が要る。

## scope (成果物影響 = DW-G05)

- **in:** (i) gate が red のとき supply / meaning の arm record を `IZANAGI_S4_EVIDENCE_ROOT` 配下へ
  canonical JSON で落とし、`RuntimeError` の本文にも `detail` を載せる。(ii) 失敗した process の argv を
  失敗 detail に載せる。(iii) (i)(ii) の契約テスト。(iv) 現行 tip の専用 checkout から計算ノードへ
  1 本投入し、evidence root を一次資料に写す。
- **out:** gate の受理集合を変える修正、preprocess の成否そのものを直す修正、供給経路の再設計。
  これらは実測結果を添えて**裁定パッケージ**で返す (依頼の明示指示)。
- 放置時の成果物影響: 段 4 loop の compute 実走が 0 件のまま = certified 選択の材料が計算ノードで
  1 行も生産できない。

## 不変条件 (規律 2 を緩めない)

- gate の受理集合・reason code 語彙・admission 判定を変えない。red は red のまま、rc も変えない。
- 追記は **red 経路の報告のみ**。green 経路の record bytes を変えない (proof chain の hash が動く)。
- `tools/pegasus/policy.json` は不変 (`orchestrator/tests/pegasus_policy_expected_goldens.py:6` に
  whole-file sha256 golden `a8806c4a…`)。`admission_registry.json` の分類も不変。
- `tools/pegasus/` へ新規実行体を作らない (F660)。`p3_s4_loop_pegasus.sh` は main の登録簿に既登録
  (path key、hash 束縛なし) なので、同 wave で投入してよい。
- `p3_s4_loop.py` は B-4 projection closure hash に参加する
  (`orchestrator/campaign/p3_b4_closed_critic.py:635`)。編集で live hash が動くのは既定の帰結で、
  凍結事前登録 `docs/phase3-b4-reflux-ablation-preregistration.md` が固定するのは**書式**であって値ではない
  (`:245-251`)。errata は不要。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- (P1a) evidence の落とし先は driver 側 (`p3_s4_loop`) とし、`condition_meaning_gate` には
  「失敗 process の argv を detail に載せる」1 点だけ触る。gate module を厚くしない。
- (P1b) argv を detail に足すのは red 記録の bytes を変えるが、red の arm record を hash 束縛する
  consumer は無いと見ている。**段 2 はこれを file:line で検証すること。** 反証が出れば (P1a) を
  「driver 側だけ・argv 断念」へ後退させる。
- (P1c) 計算ノード投入は 1 本。fixture 経路 (`--value`)、`IZANAGI_S4_FIXTURE_VALUE` は 20 以外にする
  (README §7 の WAL skip 注記)。gate は `run_campaign` より前なので skip の影響は受けないが、
  gate が通った場合に build まで進めるため。

## 分割方針

- 段 2 = 1 本 (read-only、file:line プラン)。段 3 = 2 本 (レンズ A: 規律 2 / 受理集合の不変、
  レンズ B: 証拠の到達性と job 終了後の残存)。段 5 = 実装子 1 本 (編集面が 1 モジュール + driver + test)。
  段 6 = 敵対レビュー 2 本 + 変異 matrix。
- 正しさ防壁に触るので **軽量版にしない** (DW-C00)。

## 変更面 (実アンカー)

| file | anchor | 変更の性質 |
|---|---|---|
| `orchestrator/campaign/p3_s4_loop.py` | `_require_condition_gate` `:378-416` | red 時に record を evidence root へ書き、message に detail を載せる |
| `orchestrator/campaign/condition_meaning_gate.py` | `_run_process` `:1559-1587` | 失敗 detail に argv を追記 (red 経路のみ) |
| `orchestrator/tests/test_p3_s4_loop.py` | 新規 test | evidence 書き出しの正例・負例 |
| `orchestrator/tests/test_condition_meaning_gate.py` | 新規 test | argv が detail に載る正例 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 新規 test 行 | 受入台帳 (正本 producer で生成) |
