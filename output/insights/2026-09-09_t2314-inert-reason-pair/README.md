# [T-2314] inert 比較の受理条件を「組」2 つのどちらか 1 つへ

`worktree-dev-wave-t2314-inert-reason-pair` (2026-09-09) の成果物。
上流はユーザー裁定 D1625 (2026-09-04 /rulings 全件 第 8 回、相談で受理条件を「組」へ正した)。

**一行で言うと**: sandbox backend probe の条件関門が inert 比較の緑を受理する条件を、
1 つの (理由コード, comparison) の組の exact 一致から、**condition meaning gate の表が定める
2 組のどちらか 1 つへの exact 一致**へ変えた。**これは受理集合を変える変更である。**

## 何が変わったか

実装 commit `bf09c81df`。編集面は 2 file。

- `tools/pegasus/probes/t316_sandbox_backend_probe.py`
  - `_INERT_CONDITION_GATE_PAIRS` (`frozenset[tuple[str, str]]`) を新設。要素は 2 組だけ。
  - `_condition_gate_family_valid` の 2 行の exact 比較を、この集合への tuple membership に置換。
  - `_condition_gate_receipt_summary` の supply entry へ `comparison` を純増 (発火した組の記録)。
    `evidence` mapping 自体は受領証へ出さない。
- `orchestrator/tests/test_t316_sandbox_probe.py` — 正例 2・負例 3 を追加 (下記)。

### 受理集合 (変更後の完全集合)

| 理由コード | comparison |
|---|---|
| `stock-inert-preprocess-identical` | `stock-inert-identity` |
| `stock-inert-preprocess-root-location-only` | `stock-inert-root-location-only` |

gate が admit する第 3 の組 (`requested-default-preprocess-different` /
`requested-default-difference`) は probe では受理しない。組を跨いだ交叉も受理しない。
gate の表は `orchestrator/campaign/condition_meaning_gate.py` の `status_contract`。

### 変えなかったもの

`require_condition_gate_family` の呼出し、`observed == expected`、`admitted is True`、
受領証 summary の一致、`driver_id`、`macro`、`terminal_status == "green"`、
meaning arm の `unestablished` / `meaning-witness-undeclared`。既存テストの期待値も不変。

## 段 3 敵対相談が変えた設計

- **A-01 (採用):** 段 2 プランは `supply.evidence["comparison"]` を添字参照していた。gate は
  production 発行の**赤** supply (例: `stock-tree-unavailable`) を正当な record として返し、
  そこに `comparison` key は無い。添字だと `verdict_s6` が `KeyError` で脱出し、
  fail-closed の判定が process 失敗に変わる。`.get("comparison")` へ直した。
- **B-02 (採用):** 第 3 の組の負例 fixture は `stock_comparison=False` でなければ
  `request-contract-invalid` で evaluator の前段から落ち、負例が恒真になる。
- **B-03 (採用):** 交叉の負例は、gate 層を局所 seam で中和するだけでは足りない。
  交叉 family から作り直した受領証を渡さないと、`receipt_summary` の一致検査の手前で
  恒真に拒否され、probe の述語に到達しない。
- **B-01 (採用。段 7 で一度不採用へ倒し、受入の赤で採用へ戻した):** 受入所要台帳への新規
  nodeid 追加。経緯を全部書く。
  1. 段 4: 親は採用したが、相談の理由づけ「`nodeid_count` が合わないと受入が赤」を実測で否定し、
     実際の関門は `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` の
     **90% 被覆**だと訂正した (gate 側の root-location-only test は当時台帳に無かった)。
  2. 段 7: 親が `D1152` (定期更新の担い手は land 側) を引き当て、**不採用へ倒した**。
     このとき「追加後の被覆は 20042/20047 = 99.98%」と書いたが、**これは誤った計算**である。
     被覆の分母は台帳の entry 数ではなく **collection の node 数**であり、正しくは
     19935/22152 だった。
  3. 受入全走: `test_g5_...` が **89.991874% (19935/22152)** で赤。5 件を除くと
     90.0122% (19935/22147) なので、**この赤は本 wave に帰属する**。段 7 の判断が誤りだった。
  4. 是正 (1 回目): 本 wave の受入 JUnit を正本 producer
     (`tools/update_acceptance_duration_ledger.py --add-only`) へ通して台帳を更新した
     (commit `d44bc8a01`)。`nodeid_count` 20042 → 22118 (追加 2076、削除 0)、既存 entry の値と
     bytes は不変 (親が独立照合)、追加値はすべて本走の実測で 0.0 の placeholder は 0 件。
  5. **取り下げ (最終形)。** その直後、別 wave が local main で同じ台帳へ 2081 node を
     add-only 登録して先に着地した (main 側 commit `2fd1679dd`、台帳は 22123 entry)。
     両者は同じ挿入位置へ書くため forward merge が必ず競合し、実際に受入 3 回目の merge が
     `terminal-merge` で落ちた。競合を解決した merge は land が拒否するので、
     **本 wave 側の台帳追加を取り下げ、local main と byte 単位で同一に戻した**
     (Codex `role=author` による revert)。sha256 は
     `10fcebe306121258106f40880ff37252417662693ae30b5d4a24ebb12f6de1f4` で main 側と一致。
     取り下げても被覆は main 側の 22123 entry で **21993/22152 = 99.282232%** となり閾値を割らない。
     本 wave の 5 node は台帳に無いままだが、次に誰かが `--add-only` を回せば入る。
  段 4 の裁定文 (`verbatim/s4-ruling.md`) は当時の判断としてそのまま残し、ここで追記訂正する。

  **本 wave の新規 nodeid (台帳には入っていない)** は次の 5 件である。

  - `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_accepts_each_exact_inert_condition_gate_pair[identity]`
  - `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]`
  - `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]`
  - `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_crossed_inert_condition_gate_pair[root_location_reason__identity_comparison]`
  - `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_requested_default_preprocess_difference`

## 親 brief の訂正 (相談が正しかった点)

1. 成果物影響は「先行条件 (attempted / walltime / toolchain / source identity) を通過した
   root-location-only 観測では `S6_CONDITION_GATE_UNPROVEN` に固定」が正しい。
2. 到達可能性の根拠は **t316 自身の実測ではない**。`docs/archive/worklog-phase3-0907-1291-1292.md`
   の記録は A-5 の `backoff_sweep` 経路が**同じ evaluator** で root-location-only の緑になった
   ものである。値が production で到達可能であることは示すが、t316 driver がその環境に置かれる
   ことまでは示さない。**限界として明記する。**
3. 編集面は 2 file だが、受入所要台帳を含めれば 3 file である。
4. literal SHA の pin は 0 件だが、`HEAD:<path>` を key にした実行時 pin
   (`t316_sandbox_backend_probe.pbs` の `BOUND_PATHS`、probe の `_BOUND_RELATIVE_PATHS`) は
   存在する。commit 後に新しい blob へ自動束縛されるので co-edit は要らない。
   「pin は無い」とは書けない。

## 変異 matrix

`tools/mutation_harness.py` (`--runner-mode dispatch`、runner = `tools/run_tests.py --force-dispatch
orchestrator/tests/test_t316_sandbox_probe.py -q -rf`)、統合 commit `bf09c81df` の wave worktree で実走。
spec は実装前に段 4 で登録した (`mutation/mutation-spec.json`、sha256
`bc4bcd322cb9155c1f580ea30fc3529b5e88af4c7a1b08703c00eab137060334`)。
台帳は `mutation/mutation-ledger.json` (sha256
`d606791f11835d7693b561e1adbc3c63b2b3b5eceb52b36bde1bd5e1d452399a`)。

| 結果 | 値 |
|---|---|
| baseline | PASSED (`127 passed in 4.44s`) |
| 本走 | 4 変異、**KILLED 4 / SURVIVED 0**、MISMATCH 0、matching 4/4 (期待 node 完全一致)、rc=0 |

| 変異 | 内容 | KILLED した node |
|---|---|---|
| m01 | 受理集合から root-location-only の組を削る | `test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]` |
| m02 | 組の membership を直積判定へ緩める | `test_s6_rejects_crossed_inert_condition_gate_pair` 2 件 |
| m03 | 第 3 の組を受理集合へ足す | `test_s6_rejects_requested_default_preprocess_difference` |
| m04 | 受領証の `comparison` を定数へ固定する | `test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]` |

m02 は gate が交叉を先に弾くため、**gate 層を中和した test だけが殺せる** (DW-M02 の両層裏取りに相当)。
初回登録のまま probe 化・再登録は不要で、erratum はない。

**本走後に tip が進んだので、anchor の成立を内容同一性で再検証した。** 本走の commit `bf09c81df` と
land 対象 tip の間で、変異が触れる 4 path はすべて blob が同一である。

| path | blob |
|---|---|
| `tools/pegasus/probes/t316_sandbox_backend_probe.py` | 同一 |
| `orchestrator/tests/test_t316_sandbox_probe.py` | 同一 |
| `orchestrator/campaign/condition_meaning_gate.py` | 同一 |
| `orchestrator/tests/fixtures/condition_meaning_gate/supplied` | 同一 |

間に入ったのは `merge main` (無関係な module)、受入所要台帳、docs だけである。変異の anchor 逐語も
期待 node の所属 file も動いていないので、本走をやり直していない。

## 実測

| 走行 | 結果 |
|---|---|
| 変更前 baseline (`test_t316_sandbox_probe.py` 単独) | 122 passed / 4.50s |
| 変更後 baseline (同上、変異 harness の baseline) | 127 passed / 4.44s |
| 焦点走 (t316 probe / hooks / official_perf_closure / acceptance_schedule_order) | 687 passed, 1 skipped / 15.66s、rc=0 |

段 6 レンズ D は「root-location-only family を 3 回生成するので 1〜3 秒の重複」を nit として挙げたが、
**実測では追加所要は観測されなかった** (4.50s → 4.44s)。fix は当てていない。

## 受入全走の経緯と非帰属赤

| 走 | 結果 | 判定 |
|---|---|---|
| 1 | `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` 89.991874% (19935/22152) | **本 wave 帰属**。5 node を除くと 90.0122%。台帳で是正 → 後に別 wave との競合で取り下げ |
| 2 | `git` 子プロセスの 30 秒 timeout 50 件ほか | 非帰属 |
| 3 | `terminal-merge` (受入所要台帳が main の `2fd1679dd` と競合) | 台帳を main と byte 同一へ戻して解消 |
| 4〜7 | `test_t1259_qsub_env_delivery_probe.py` の setup で `git ls-files --others --exclude-standard -z` が 30 秒 timeout (9〜24 件、毎回別の node 集合) | 非帰属 |

**非帰属の根拠 (実測 4 点)。**

1. 失敗本文はすべて `subprocess.TimeoutExpired`。assert の不一致ではない。
2. 同じ 3 file を単独走させると **287 passed / rc=0** で再現しない。
3. 同じ file は**他 wave の受入 session でも赤**になっている
   (`44ef8d2fe…` が 26 件、`8ce05242b…` が 1 件。いずれも本 wave の session ではない)。
4. 時間のかかる `git ls-files --others` は本 wave の worktree で 2.04 秒、隣の wave の worktree で
   1.52 秒と**同等**であり、木の大きさ (25180 file 対 24999 file) も同等である。
   つまり本 wave の worktree に固有の遅さは無い。

原因は login node の IO 競合である。受入は xdist 48 worker で走り、`t1259` の fixture は
test ごとに 25k file の untracked 走査を起動するため、他 wave の受入と重なると 30 秒上限を超える。
赤が出た走では 1 分平均負荷が 12〜22 だった。`--force-dispatch` で計算ノードへ回す案は採れない —
`tools/run_tests.py` に引数を足すと `_is_acceptance_run()` が False になり受入形でなくなる。

## 裁定パッケージ (scope 外・ユーザー裁定へ返す)

1. **`_BOUND_RELATIVE_PATHS` の index ずれ (既存の実在欠陥)。**
   `t316_sandbox_backend_probe.py` の `_execution_binding` は runtime PBS spool の bytes を
   `repo_root / _BOUND_RELATIVE_PATHS[1]` と比較するが、index 1 は `.py` であって `.pbs` ではない
   (`.pbs` は index 2)。`repo_pbs = ... _BOUND_RELATIVE_PATHS[1]` は commit `5e12db6ce` で
   index 1 が `.pbs` だった時点に書かれ、commit `0218acc61` が
   `orchestrator/campaign/condition_meaning_gate.py` を先頭へ足したときに 1 つずれた。
   次に計算ノードで probe を走らせると `runtime PBS bytes differ` で落ちる見込み。
   **本 wave の主題 (T-2314 が塞いでいた関門) を開けても、この 1 点で probe は前進しない可能性がある。**
   段 6 レンズ C が指摘し、親が git 履歴で裏取りした。
2. **受領証の scalar 型が非厳密。** 受領証 summary の equality は Python の `==` なので、
   JSON の `"admitted": 1` は生成値 `True` と等価になる。今回の文字列境界は破らない既存問題。
3. **receipt schema の版管理。** `condition_gates` に field を足したが `SCHEMA_VERSION` は
   v1 のまま。既発行の v1 receipt 2 本には `condition_gates` 自体が無く、閉じた key schema も
   reader も現行コードに無いため版上げは不要と判定した。「v1 は exact closed shape」とするなら
   別問題として扱う必要がある。
4. **t316 実経路での root-location-only 到達実測。** 上の「親 brief の訂正 2」を閉じるには、
   本 commit を束縛した計算ノード probe の実走が要る。本 wave は述語の変更のみ。
5. **受入の login node 競合で `test_t1259_qsub_env_delivery_probe.py` が繰り返し赤になる。**
   上の実測 4 点のとおり本 wave に帰属しないが、並行 wave が 2 本以上あると再現し、
   受入を通せない。`docs/failures.md` に同型の F が無いため
   `orchestrator/tests/flaky_test_holds.py` への登録要件 (既存 F を証拠とする) を満たせず、
   `DW-O18` に従い登録せず裁定へ返す。取りうる形は (a) 同 fixture の untracked 走査を
   session 単位へ寄せる、(b) 30 秒の timeout を負荷に見合う値へ上げる、(c) 同 file 用の F を
   起こして hold 登録を可能にする、のいずれか。**本 wave の scope 外。**

## 構成

- `verbatim/` — 段 1 brief、段 2 プラン、段 3 敵対相談 2 本、段 4 裁定、段 5 実装、
  段 6 敵対レビュー 2 本の prompt と出力。
- `mutation/` — 事前登録 spec と本走台帳。
