# [T-2632] B-4 の対応証拠 — base driver に harness 書きの provenance side channel を足し、prerun caller の lock 読取りを既存 codec 経由にした

- authority: none
- default_effect: no-state-change

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。
本書は wave `dev-wave-t2632-b4-evidence-carrier` (branch `worktree-dev-wave-t2632-b4-evidence-carrier`、起点 local main `5f48a298a`、
Codex の利用上限による中断後に `36fb14a3d` へ ff-only) の一次資料を凍結したものである。実測は 2026-09-21 JST、機体 Pegasus
(login node と計算ノードの dispatch)。

## 0. 一行で・主張すること・しないこと

**一行で:** D2194 項 3 の 4 項のうち、(1) base driver (`orchestrator/campaign/p3_s4_loop.py`) の provenance side channel と、
(4) `p3_b4_prerun_caller.py` の v2 lock 読取りを実装し、(2) 参照点の定義を side channel の docstring と本書・decisions fragment に書き、
(3) の順序 (新規 base campaign の起動前) を本 wave の land で満たす。

**主張すること:**

- 新しく走る base campaign は、iteration ごとに `reports/p3_s4_loop_provenance.json` の entry
  (`iteration` / `variant` / `build_attempt_id` / `initial_proposal_sha256` / `wal_refs` / `outcome`) を、評価と whiteboard 射影の後・
  checkpoint 保存の前に harness が書く。whiteboard の 5 field と planner / coder / critic の入力は変えていない (出力 bytes の同一性を test で固定)。
- `initial_proposal_sha256` は、`load_proposal_file` が読んで検証した document の `canonical_b4_proposal_sha256` (receipt key を除いた canonical JSON)。
- `wal_refs` は、当該 variant かつ当該 `build_attempt_id` に属する WAL record 全体の `wal:` + `agent_outputs.canonical_sha256` を WAL 順に並べたもの。
- `p3_b4_prerun_caller` は campaign.lock を `campaign_lock.decode_campaign_lock_bytes` で読み、`trial` を decode 後の identity から取る。
  現行の v2 lock の campaign が「赤候補あり → 不足報告・issuer 未呼出し / 候補なし → 空 batch で issuer 到達」の 2 経路に乗る。

**主張しないこと:**

- 適格行を作れるようになった、とは言わない。caller は side channel を読まないので、赤候補 1 件につき不足 12 件の報告は本 wave 後も変わらない
  (D2100 の 12 field のうち出所が生まれたのは attempt・proposal・参照点候補の辿り方まで。`block_id` / `workload` / `calibrated_workload_member` /
  `bootstrap_member` / `arm_digest_received` は不足のまま、`reference_is_unique` は `reps` と `ycsb_max_ope` の不足を残す)。
- 既存 campaign に遡って entry を埋めない (D2194 項 3 (3)、規律 7)。
- 中断からの回復や対応の完全保持は保証しない (§2.4)。
- admission が base の provenance を検査する、とは言わない (scope 外、§7)。
- B-4 本走・床値 w2 は投入していない。計算ノードへ投げたのはテスト job (焦点走・変異・受入) だけである。

## 1. 依頼と裁定

依頼の逐語は `verbatim/request.md`。裁定は D2194 項 3 (`verbatim/d2194-item3.md`)、D2120 項 5 (`verbatim/d2120-item5.md`)、控え
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full27-verdicts.md` 項 3 (`verbatim/rulings-inbox-full27.md`)。
一次資料は `output/insights/2026-09-20/t2632-b4-evidence-provenance/README.md` §7 (本書 `verbatim/insight-t2632-s7.md` ほか)。

**着手条件の待ち:** 依頼の着手条件 ([T-2795] と [T-2830] の land) を 08:20〜17:34 JST 待った。[T-2795] は 13:35 に main `d99c556df`、
[T-2830] は 17:33 に main `5f48a298a` へ land (いずれも local main の ref で検算)。17:34 に `5f48a298a` から fresh worktree を作った。

**依頼文と裁定の食い違い (brief P7):** 依頼は先例を `p3_s4_loop_trigger_gating._write_source_preimage_artifact` と名指すが、同関数の出力は
`source-bindings/<proposal raw sha256>.preimage` で、裁定が指す `reports/<driver>_provenance.json` の先例は `_provenance_path` /
`_append_provenance_entry` 系である。F31 (裁定優先) に従い、file の意味は後者、書き込みの堅さ (排他 tmp・fsync・atomic 公開) は前者に合わせた。
base に source preimage artifact は足していない。段 3 の過剰・削除レンズがこの読みを妥当と判定した。

**中断 (Codex の利用上限):** 段 2 の plan 子 (17:46:49 起動) が 9 秒で rc=1 になり、events 末尾は
`You've hit your usage limit ... try again at Sep 26th, 2026 7:35 PM.` だった。14:33 JST 以降の全 wave の codex 実行 9 件が同じ上限だった。
D582 に従いユーザーへ通知して停止し、ユーザーの「codex今なら使えると思う」(20:1x) で再開した。再開時に worktree を local main `36fb14a3d` へ
ff-only した (取り込み 8 commit は docs のみ、変更面・参照先・dev-wave 手順書は不変)。

## 2. 実装

| commit | 内容 | 著者 |
|---|---|---|
| `ec6459863` | side channel (p3_s4_loop.py + test) と caller の codec 経由化 (p3_b4_prerun_caller.py + test) | Codex author 2 本、親が所有 path 限定 patch を統合 |
| `eee7e4ba3` | 段 6 の must-fix: canonical 化できない proposal を hash=null で続行、docstring 2 件の限定、新設 test の fixture 修正、launcher positive test の stub 出力の実物化 | Codex fix 1 本 |
| `f5049bf6d` / `3bfbecfca` / `92f501c28` | duplicate 系 test の helper の fixture 修正 (先行 attempt の位置、`anomalies`、受領証の `tags`) | Codex fix 3 本 (test のみ) |

統合差分 (`36fb14a3d`..`92f501c28`、`git diff --numstat`): 5 file、+834 / −21。`p3_s4_loop.py` +211 / −3、`p3_b4_prerun_caller.py` +14 / −10、
`test_p3_s4_loop.py` +507 / −2、`test_p3_b4_prerun_caller.py` +97 / −5、`test_p3_b4_closed_critic.py` +5 / −1。

### 2.1 side channel の形

`<campaign root>/reports/p3_s4_loop_provenance.json`。top-level は `schema_version` (`p3-s4-loop-provenance/v1`)・`axis`
(`silo-backoff-magnitude`)・`entries` (iteration の十進文字列 → entry)。trigger 固有の header (情報源・firewall・gate record) は写していない。
entry は 6 field ちょうどで、値域を読み書きの両方で検査する (`_validate_provenance`)。

| outcome / 経路 | variant | build_attempt_id | wal_refs |
|---|---|---|---|
| certified / duplicate | 採用された variant | 採用された commit の ID | その attempt の record 全体 |
| aborted | out の variant | abort の ID、無ければ start の ID | 同上。ID 未確定なら null / `[]` |
| rejected (検疫) | `diffq-*` | 今回の reject の abort の ID | 同上 |
| dry-pass / duplicate-skip / rejected-preprocess | null | null | `[]` |

certified / duplicate / rejected で attempt ID を特定できない、または start が一意でないときは記録不能として停止する (証拠不足を別 attempt で救済しない)。
stock 対照 (`--stock-control`) と入口停止 (`stopped-before`) は iteration を消費しないので entry を書かない。

### 2.2 書き込み位置と順序

`drive_iteration`: 入口停止判定 → iteration 加算 → 既存の評価・重複解決・whiteboard 射影 → **provenance 公開** → checkpoint 保存 → B-5 早期 return /
digest。加えて、layout が決まった直後 (B-4 認可の検査・消費と評価より前) に既存 report を読んで検証する (書かない)。破損なら評価も認可消費もしない。

### 2.3 proposal hash の配管

`load_proposal_file` の capture に検証済み document を足し、`main()` の `--run-iteration` 経路は `--agent-inputs` の有無にかかわらず capture を渡す。
`drive_iteration` へは keyword-only 引数 `initial_proposal_sha256` (既定 None = この呼出しでは canonical identity を提供しない) で渡す。
canonical 化できない proposal (例: 任意項目に NaN) は mode を問わず hash=null で走行を続ける (段 6 A2)。canonical hash を既に要求するのは
B-4 bootstrap の registry 束縛だけで、bootstrap はそこで先に拒否される。ここで停止させると B-4 continuation と非 B-4 の受理集合が縮むため。

### 2.4 書き込みの堅さと保証の限界 (P4)

排他 tmp → file fsync → `os.replace` → directory fsync。同 iteration は上書き merge (trigger 同型)。破損 (JSON・UTF-8・型・値域) は元 bytes を
`.corrupt.<epoch>` へ no-clobber で退避して停止し、原本が不在で退避ファイルがある限り再開を拒否する。

**保証は「provenance を公開できない iteration は checkpoint に確定しない」だけである。** 公開後・checkpoint 前の中断では、非 B-4 の certified は
再実行で duplicate になり得る。検疫 reject は再実行で新しい attempt を追加し、同 iteration の entry が上書きされて最初の attempt は WAL にだけ残る。
B-4 は WAL に履歴が残る bootstrap と continuation が履歴・receipt 検査で再実行を拒否し、公開済み entry が残る。2 file の transaction と並行 merge の
排他は保証しない。

### 2.5 caller

`collect_scheduled_batch` の lock 読取りを `decode_campaign_lock_bytes` に置き換え、`trial` を `decoded.identity.get("trial")` で取る
(v1 codec は trial を必須にしないので `.get` にし、欠落は既存の `unknown trial` で `campaign_input_unreadable` に写る)。codec の例外は `ValueError`
派生なので既存の catch に乗る。**受理集合の変化は 2 方向ある:** 有効な v2 lock が新たに読める / 旧 `json.loads` が受理していた不正な v1
(duplicate key・非有限値・reserved field) は拒否側へ移る。v1 / v2 の独自救済分岐は足していない。説明文は「この caller が読む checkpoint
(whiteboard 5 field) と lock だけでは構成できない静的な不足分類」へ限定した。

**実物での確認 (DW-O13):** B-5 試走の campaign の v2 lock 10 件 (例 `p3-s4-loop-s4-autonomous-6fc5d263`) は top-level key が
`authority` / `identity_preimage` / `schema_version` だけで、identity 内の `trial` = `"p3-s4-loop"` (jq 実測)。

## 3. 参照点の定義の確定 (D2194 項 3 (2))

事前登録 §5.1.1 の共通参照点 (凍結文、`verbatim/prereg-s5.1.1-reference.md`) の解釈として次を確定し、`_wal_attempt_provenance` の docstring と
decisions fragment に書いた。新 object・新 producer・resolver・`reference` 欄は作っていない。凍結された事前登録本文は編集していない。

- 祖先 = 同一 campaign 内の時間順。precursor の iteration より前の最後の whiteboard `success` に対応する certified attempt を、本 side channel の
  iteration → variant / `build_attempt_id` で引く。重複提案は既存評価を再利用するので、行順と評価の系譜は同一でない。
- `reference_snapshot_hash` = その attempt の WAL `commit` record 全体、`reference_receipt_hash` = 同 attempt の `bench_done` record 全体を
  `agent_outputs.canonical_bytes` (`allow_nan=False`) で canonical 化した sha256 (接頭辞なし 64 hex)。`wal_refs` は同じ digest に `wal:` を付けたもの。
- 祖先なし・同着・record 非一意・承認済み `PerfConfig` または `env_tag` の一致を確認できない場合は不適格。別の祖先や別基準へ切り替えず、
  実走前は `design_not_feasible`、実走後は protocol violation。
- `PerfConfig` は records / threads / workload の全 key / extime / reps を比較対象とする。`bench_done.payload.run_cmd` は threads・records・extime と
  workload の rratio・skew・rmw、record の `env_tag` は環境の証拠。`reps` と `ycsb_max_ope` は run_cmd で確認できない不足として残し、`len(tps)` や
  既定値で補わない。
- 定義と carrier は新規 base campaign の起動前に発効し、遡及補完はしない。

## 4. 相談・レビュー・裁定

| 段 | 子 | 時刻 (JST) | 結論 | 逐語 |
|---|---|---|---|---|
| 段 2 | plan (read-only、medium) | 20:20:47〜20:27:19 | P1〜P7 採用、file:line 粒度 | `verbatim/codex/s2-plan-r2.md` |
| 段 3 | 相談 A 正しさ境界 (sol) | 20:27:47〜20:31:34 | must-fix 2 (P4 の回復説明の誤り・評価前検証の欠如 / 変異 S10 が NameError)、should-fix 3 | `verbatim/codex/s3-consult-A.md` |
| 段 3 | 相談 B 過剰・削除 (luna) | 20:27:48〜20:30:57 | must-fix 0、should-fix 1 (説明の限定)、nit 1 (test 重複) | `verbatim/codex/s3-consult-B.md` |
| 段 4 | 親の裁定 | 20:3x | 所見 13 件、scope 外 4 件、プラン v2、変異事前登録 | `verbatim/stage4-ruling.md` |
| 段 5 | author A (side channel) / B (caller) | 20:37〜20:52 / 20:37〜20:43 | 実装済み・未実走、所有外 0 | `verbatim/codex/s5-author-*.md` |
| 段 6 | review A 正しさ / B 過剰・削除 | 21:05〜21:09 | 両方 NO-GO (A2・fixture 11 件・consumer 1 件) | `verbatim/codex/s6-review-*.md` |
| 段 6 | 親の裁定 + fix 4 巡 | 21:1x〜21:39 | §4 の誤診断を §4.1 で撤回、§4.2 で親の probe が拒否理由を特定 | `verbatim/stage6-ruling.md`、`verbatim/codex/s6-fix-A*.md` |
| 段 6 | 焦点再レビュー (全体 1 本) | 21:41:28〜21:45:54 | real 所見 5 件すべて closed、変異割り振りに must-fix 1 (F1) | `verbatim/codex/s6-focus.md` |

**段 6 の誤診断と訂正 (記録として残す):** 焦点走 f2 の赤 1 件 (`test_base_provenance_duplicate_reuses_selected_attempt`) を、親は §4 で
「採用 commit の後の abort が原因」と診断し、fixture の順序を直させた (fix A2)。f3 でも同じ赤が残り、診断は誤りだった。`_resolve_duplicate` は
拒否理由を握りつぶして `aborted` にまとめるので、親が読み取り probe (`probe/probe_duplicate_reject.py.txt`) で同じ fixture を組んで直接呼び、
`persisted COMMIT verify anomalies must be exact int zero` (fix A3 で修正) と、その後の `persisted COMMIT receipt evidence does not match WAL verifies`
(helper が受領証を既定 `tags=("legacy",)` で作っていた。fix A4) を特定した。fix A4 の前に修正案を当てた probe (`probe/probe_duplicate_fixed.py.txt`)
で `duplicate`・採用 attempt・refs 4 件を確かめた。production は fix 1 巡目以降変えていない。

## 5. 検査

| 走行 | request | 対象 | 結果 |
|---|---|---|---|
| 焦点走 f1 | `15633.nqsv` | 33 file (変更 test 2 + consumer 30 + inventory 群、`focus-set.txt`)、`ec6459863` | 12 failed / 4689 passed / 15 skipped / 167.68 s |
| 焦点走 f2 | `15636.nqsv` | 同 33 file、`eee7e4ba3` (production の最終形) | 1 failed / 4701 passed / 15 skipped / 166.08 s |
| 焦点走 f3 | `15639.nqsv` | test_p3_s4_loop.py、`f5049bf6d` | 1 failed / 654 passed / 13.75 s |
| 焦点走 f4 | `15658.nqsv` | 同、`3bfbecfca` | 1 failed / 654 passed / 13.67 s |
| 焦点走 f5 | `15673.nqsv` | 同、`92f501c28` | 655 passed / 13.69 s |

- f1 の赤 12 件 = 新設 test の fixture 不具合 11 件 + 既存 `test_p3_b4_closed_critic.py::test_launcher_positive_uses_real_factory_and_real_base_main_for_commit`
  (評価 stub が attempt ID の無い certified を返していた。本番の attempt 検査は緩めず、stub の出力を実物の形にした)。
- f2 の skip 15 件は `-rfs` で理由を確認し、既存の growth hold 7・template patch 未適用 3・実機 build 環境の未設定 3・Python 3.11 要件 2 で、本 wave と無関係。
- `eee7e4ba3` 以後の変更は test_p3_s4_loop.py だけなので、f2 の他 32 file の結果を最終形の回帰証拠として持ち越した
  (最終 commit で 33 file を一括で走らせた結果ではない。焦点再レビューが統合差分から同じ判断をした)。
- 全史 provenance 監査: `ec6459863` 後 12,443 件・`92f501c28` 後 12,447 件、いずれも新規違反なし・rc=0。各 commit は `--message-file` の事前検査 rc=0。

## 6. 変異 (事前登録 → probe → final)

事前登録は段 4 裁定 §4 (S1〜S14・C1〜C5・E1)、段 6 裁定 §3 (S15)、再照準は §4 (S4)、実行方法は §5 / §5.1 (いずれも走行前)。
対象 commit は `92f501c28` (最終の実装・test)。

**drift の実測:** `p3_s4_loop.py` は contract loader closure と B-4 projection closure に入る。独立 clone (`mutation-source`) で等価変異 E1 を注入すると、
`test_p3_s4_loop.py` + `test_p3_b4_closed_critic.py` で **150 node** が変異の内容と無関係に落ちた (103 / 47、新設 test 22 node を含む、一覧 `mutation/drift-nodes-e1.txt`)。
そこで変異を 3 群に分けた。

| 群 | 方法 | 対象 test | 変異 | final |
|---|---|---|---|---|
| commit 群 | `run-commit-group.sh` (変異を独立 clone の commit に焼いて dispatch、drift が出ない。段 6 裁定 §5 で走行前に登録した自作 harness) | `test_p3_s4_loop.py -k provenance` | S1・S2・S10・S11・S12・S13・S14・S15 | **KILLED 8 / 8** (baseline 緑、期待 node と完全一致) |
| 注入群 L | `mutation_worktree.py` (dispatch)、drift を受けない新設 test だけを `-k` で選ぶ | `test_p3_s4_loop.py -k` (merge・publish_failure・keeps_all・duplicate・invalid_entry・rejects_missing・preserves_whiteboard) | S3〜S9・E1 | **KILLED 7 / SURVIVED 1 (E1、期待どおり)** |
| 注入群 C | `mutation_worktree.py` (dispatch) | `test_p3_b4_prerun_caller.py` 全体 | C1〜C5 | **KILLED 5 / 5** |

| ID | 変異 | 期待 node (final で完全一致) |
|---|---|---|
| S1 | 公開呼出しを no-op に | 19 (outcome 6・checkpoint 系 5・B-5 早期 return 2・hash 系 4・別 attempt・直接呼出し null) |
| S2 | checkpoint を公開より前に | 5 (failure_keeps_checkpoint 4・precedes_checkpoint) |
| S3 | refs から attempt ID 条件を外す | 1 (duplicate_reuses_selected_attempt) |
| S4 | commit 由来 ID を同 variant の最初の start の ID に | 1 (同上) |
| S5 | ref の hash を payload だけに | 2 (keeps_all_attempt_records・duplicate) |
| S6 | refs を stage 単位に圧縮 | 2 (同上) |
| S7 | merge で他 iteration を捨てる | 4 (publish_failure 3・merge_is_idempotent) |
| S8 | 破損で `{}` を返す | 7 (invalid_entry_is_quarantined の parametrize 7) |
| S9 | file fsync を削除 | 1 (publish_failure[fsync]) |
| S10 | hash を raw bytes の sha256 に | 4 (hash 系) |
| S11 | capture を `--agent-inputs` 指定時だけに戻す | 4 (hash 系) |
| S12 | B-5 では公開しない | 2 (records_b5_early_returns) |
| S13 | 評価前の検証を削除 | 8 (corrupt_report_stops の parametrize 8) |
| S14 | critic digest に report を連結 | 1 (inputs_do_not_read_report) |
| S15 | hash 失敗を再送出 (過剰拒否、正の向き) | 1 (noncanonical_proposal_hash_is_null) |
| C1 | trial を raw lock の top-level から読む | 6 (v2 fixture の正常系) |
| C2 | codec を迂回して inner を手読み | 4 (unreadable の non_certifying・非 canonical inner / outer・authority) |
| C3 | v1 を拒否 (過剰拒否、正の向き) | 2 (v1 回帰・v1 trial 欠落) |
| C4 | catch から `ValueError` を外す | 11 (unreadable の parametrize 10・v1 trial 欠落) |
| C5 | `.get("trial")` を添字に | 1 (v1 trial 欠落) |
| E1 | canonical_sha256 を同値の式に (等価対照) | 0 (SURVIVED を期待) |

**割り振りの訂正 (段 6 裁定 §5.1):** 焦点再レビューが、S13・S8 を注入すると drive を通す破損 test の入口停止が外れて live binding 照合 (drift) へ到達すると
指摘した (E1 で drift が出ない node でも)。S13 を commit 群へ移し、S8 は L の選択から破損 test を外して loader を直接呼ぶ test だけで検出させた。
L の probe は訂正前の選択で走っていたので、final の期待 node は probe の観測を final の選択へ制限して登録した (S8 は 15 → 7)。final は完全一致した。

**node 抽出の注意:** commit 群の harness は当初 `IZANAGI_FAILURE ... nodeid="..."` 行を `nodeid="[^"]*"` で抜き、引用符を含む parametrize id
(`corrupt_report_stops[False-{"schema_version":...}]`) を途中で切った。final の前に `-rf` の要約行 (`| FAILED <nodeid>`) からの抽出へ切り替え、
probe の観測も同じ規則で抜き直した (`mutation/collect_cg_observed.py.txt`)。F71 と同型。

## 7. 本書が閉じないこと・scope 外

- **scope 外 (起票しない):** base provenance の admission 検査、中断後に B-4 の認可を再利用可能にする変更・回復 gate・台帳、side channel の
  `reference` 欄、caller に side channel を読ませること、sort / trigger driver への展開 (段 4 裁定 §2、両相談・両レビューとも scope 外と明示)。
- 適格行の生成・参照点の適格性の証明・非空発行の完成は本 wave で達成しない (D2120 項 5 (1) の限定を維持)。bootstrap 集合は定義していない (同 (2))。
- 新規 base campaign の起動、B-4 本走、床値 w2 (2026-09-29 以降) は投入していない。carrier の実物での動作 (実 campaign の report) は、次に base campaign が
  走った時点で初めて観測できる。本 wave の証拠は test と変異だけである。
- 受入全走は、本記録を含む tip に対して land の前に投入する (本書の commit 時点で未実施)。

## 8. 段 8 (skill 自己改善)

段 8 の結果は本 wave の後続 commit と worklog fragment に書く。

## 収録物

| path | 内容 |
|---|---|
| `verbatim/request.md` | 依頼の逐語 |
| `verbatim/stage1-brief.md` | 段 1 brief (P1〜P7、17:45 確定。段 4 で完了判定の表現を訂正、brief 自体は書き換えていない) |
| `verbatim/d2194-item3.md` / `d2120-item5.md` / `rulings-inbox-full27.md` | 裁定の逐語 (decisions.md から見出しで機械的に切り出し) と控え |
| `verbatim/insight-t2632-s*.md` / `prereg-s5.1.1-*.md` | 一次資料 §2.2〜§2.3・§4・§7 と凍結事前登録 §5.1.1 の逐語 |
| `verbatim/stage4-ruling.md` / `stage6-ruling.md` | 段 4・段 6 の親の裁定 (erratum §4・§4.1・§4.2・§5.1 を含む) |
| `verbatim/codex/*-prompt.md` と `*.md` | codex 子 12 本の入出力 (plan・consult 2・author 2・review 2・fix 4・focus) |
| `mutation/spec-*.json` / `mutation-*-results.json` / `cg-final-judgement.json` | 変異の spec (probe・final) と結果 |
| `mutation/cgroup-*/` | commit 群 harness の log と変異ごとの失敗 node |
| `mutation/drift-nodes-e1.txt` / `observed-*.json` | E1 の drift 一覧と、final に登録した観測 node |
| `mutation/*.py.txt` / `*.sh.txt` | 親の spec 生成・commit 群 harness・判定・clone 準備の script (repo に入れないので .txt) |
| `probe/*.py.txt` | 段 6 §4.2 の親の読み取り probe |
| `focus/focus-f1.log`〜`focus-f5.log` / `focus-set.txt` | 焦点走 5 本の生 log と対象 file 集合 |
| `NORMALIZATION.md` / `normalize_trailing_ws.py.txt` | 逐語 11 本と焦点走 log 5 本の可逆最小正規化 (行末空白と末尾空行だけを除去、原文 sha256・bytes・除去位置を記録) と、その script |
