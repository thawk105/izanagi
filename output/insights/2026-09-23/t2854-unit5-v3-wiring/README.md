# [T-2854] 残り (1) 単位 5 — v3 の構造化出力を CLI・pipeline 診断・受領証 digest へ配線し、pipeline の trace allowlist を TPC-C 段 1 (57:43) の v3 へ広げた。実 TPC-C trace (silo、36,156 取引) が pipeline の executor で certified に届き、違反注入・末尾欠落の写しは reject される (2026-09-23)

wave: dev-wave-t2854-unit5-v3-wiring / branch `worktree-t2854-unit5-v3-wiring` / 起点 local main `65fd1422f` (開始 gate fresh rc=0、`verbatim/startup-gate.log`)。
依頼の逐語 `verbatim/request.md`、段 1 brief `verbatim/s1-brief.md`、段 4 裁定 `verbatim/s4-ruling.md`、段 6 裁定 `verbatim/s6-ruling.md`、Codex 子の出力 `verbatim/s*.md`。
設計 = `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §3.5・§6.1・§7.1。前提の存在履歴 = `output/insights/2026-09-23/t2854-v3-existence/README.md` (D2232)。

## 0. この wave が主張すること・しないこと

- **主張する:** (1) CLI の `--json`、pipeline の reject 診断、verification capability の digest 射影が `core.result_to_dict_v3` を通り、v3 の run では anomaly の表・取引種別と
  存在違反の件数・詳細を出す / 束縛する。v2 (YCSB) では dict・JSON bytes・digest が変わらない (試験で固定)。(2) pipeline の `_run_trace` は `ycsb_` に加えて、
  `tpcc_` で 4 flag が文字列で payment=43・order_status=0・delivery=0・stock_level=0 のときだけ trace を走らせる。TPC-C は verifier の結果が v3 であることを要求し、
  v2 は既存 `trace-witness-unsupported-workload` で reject する。(3) 単位 1・2 の実 trace と実 stdout を pipeline の executor に通すと certified になり、
  R 行 1 本を初期不存在の key の genesis 読みに変えた写しは存在違反 (read-unborn-genesis、表 8) で、末尾 frame を 1 つ落とした写しは witness 不一致で reject される (§4)。
- **主張しない:** production の `evaluate` が TPC-C の binary を build・選択して認定すること (buildcache は `ycsb_<protocol>.exe` だけを作る: `orchestrator/campaign/buildcache.py` の
  target 定義。設計 §7.1 の単位 5 に含まれない)。現 pin の tpcc binary が v3 emitter・計数修正を持つこと (持たない。v3 要求で reject される)。flag が実際の取引の選択を
  証明すること (§6 の限界)。既発行の v3 capability の digest を新しい射影で再現できること (v3 の digest は意図的に変わる)。mocc の認定 (単位 11 以後)。段 2。
- **規律 1・2:** trace は compile 時に除去する既存の構成のまま (本 wave は CCBench を触らない)。TPC-C の run が認定されるのは、57:43 の flag・v3・witness 一致・存在違反 0・
  X/P 充足がそろうときだけ。どれかが欠ければ reject。

## 1. 変更 (統合 commit `599da1b85`、fix1 `9a78e4174`、fix2 `2a35f260d`)

| 面 | 内容 |
|---|---|
| `orchestrator/verifier/core.py` | capability の digest 射影を `result_to_dict_v3` に (trace_dir・framing / permutation 詳細の pop は維持、存在詳細は残す)。domain `izanagi-verifier-result-v1` は据え置き |
| `orchestrator/verifier/cli.py` | `--json` の結果を `result_to_dict_v3` に (text 出力・`render_text` は不変) |
| `orchestrator/campaign/pipeline.py` | `_run_trace` の受理条件 (ycsb_ または tpcc_ + 4 flag の文字列一致)、根拠コメント 3 行、verifier 直後の TPC-C の v3 要求 (`existence_violation_details is not None`)、reject 診断を `result_to_dict_v3` に |
| `orchestrator/tests/test_verifier.py` | 新規 3 本: CLI の v3 出力と v2 の旧 JSON との bytes 一致、capability digest の束縛 (表・種別・存在詳細) と v2 の旧射影 digest との一致、§6.1 の District lost update (表 1、ww・rw の cycle) と直列対照の certified |
| `orchestrator/tests/test_campaign.py` | 新規 2 本: 実 `_run_trace` + fake executable の受理・拒否 (57:43 受理、payment=44・delivery 欠落・`"043"`・他 binary の拒否、ycsb の従来受理)、実 verifier の executor で v3 正例 certified・v2 reject (verifier 単独では certified の trace)・存在違反の診断・witness 欠落 3 形態 |

production は追加削除 32 行 + コメント 3 行、試験は新規 5 本 (段 4 の上限 production 60 行・試験 320 行・8 本の内側)。report.py・`orchestrator/verifier/__init__.py`
(fixture の campaign.lock が現行 sha256 を持つ)・既存試験の期待値は変えていない。新しい abort reason・test file・module は足していない。

## 2. 段の経過

| 段 | 内容 | 成果 |
|---|---|---|
| 1 | brief (親)。現状の実測: `_run_trace` は `ycsb_` 以外を trace 前に拒否、CLI・診断・digest は旧射影、buildcache は ycsb だけ。B0 の argv・計数・tx_type を記録から確認 | `verbatim/s1-brief.md` |
| 2 | plan (Codex read-only、4 分) | 配線 3 箇所、`.exe` + 4 flag の受理、verifier 後の v3 要求、§6.1 の対応表 |
| 3 | 相談 A (正しさ境界。初回は親 prompt の誤 path で停止、再投入)・B (整合・過剰) | A1「flag は実取引を証明しない」、B1「production evaluate に届かない」、B3「trace_runner は allowlist を迂回」ほか |
| 4 | 裁定 (親) | A1 は編集面外の workload code で閉じるので検査を足さない (§6)、B1〜B9 の多くを採用、author 1 本、M0〜M11 事前登録 (M11 は後で登録外) |
| 5 | author (Codex、約 8 分) | 子は pytest 未実走 (dispatch の事前確認失敗と login の hook 拒否) と正直に報告 |
| 6 | 親の自走 → 焦点走 1 → review A / B → fix1 → 焦点走 2 → fix2 → 単独走 → 焦点再レビュー → 変異 | 新試験の key が 16 進でなかった (`district`)、存在違反 case が契約上違反でなかった、の 2 件を fix で閉じた (§3) |

## 3. 検査の結果

| 検査 | 対象 commit | 結果 |
|---|---|---|
| test_verifier.py 自走 (login) | `599da1b85` / fix1 子 | 140 passed / 1 failed (lost update 試験) → 141 passed |
| 焦点走 1 (変更 test file + core / cli / pipeline の consumer 55 file + inventory 群 + 受入所要台帳の meta 試験、計算ノード 21117.nqsv、Elapse 460 秒) | `599da1b85` | 7,924 passed / 15 skipped / 2 failed (新試験 2 本、key `district` が malformed) |
| 焦点走 2 (同じ集合、21152.nqsv、Elapse 464 秒) | `9a78e4174` | 7,925 passed / 15 skipped / 1 failed (executor の existence case が certified: 最初の write が U の key は存在の契約で genesis から存在する) |
| 新試験 2 本の単独走 (21195.nqsv、Elapse 12 秒) | `2a35f260d` | 2 passed |
| 変異 runner と同じ argv の単走 (21198.nqsv、Elapse 13 秒) | `2a35f260d` | 147 passed (変異 job の単価の実測を兼ねる) |
| 変異本走 (独立 clone、dispatch) | `2a35f260d` | 11 / 11 が事前登録どおり (§5) |
| AI provenance (各 commit 前の message 検査と範囲監査) | 各 commit | 違反なし |

review 所見の閉じ方は `verbatim/s6-ruling.md` と焦点再レビュー `verbatim/s6-focus.md` (全所見 closed、新規所見なし、静的)。
焦点走は受入形でない走行で、受入全走の代わりにはしない。

## 4. 実 trace の pipeline 結合 probe (親、repo 外)

単位 1・2 の B0 (silo、thread 2・extime 1 s・倉庫 1・57:43、trace 2 file、raw の sha256 は記録と一致) と、その実 stdout (`commit_counts_: 36156`・`batch_commit_counts_: 0`) を、
`_execute_verification_repetition` に trace_runner seam で渡した (`_run_trace` は login で site 検査が拒否するため。受理条件そのものは repo の試験が実 `_run_trace` で確かめる)。
計数は pipeline の実 parser (`_parse_commit_witness`)、verifier は実物、build binding は試験 helper (`commit_receipt_support._proof_build_binding`、pin e9e477ca の silo source)。

| case | 結果 (`measurements/real-trace-pipeline-probe-2.json`) |
|---|---|
| そのまま | **certified**、capability certified、36,156 取引、辺 268,209、存在違反 0、X/P evidence-present、witness 36,156 一致 (7.6 秒) |
| R 行 1 本を「表 8 に実行中 I された key の genesis 読み」へ書き換え | indeterminate で reject。診断 (`result_to_dict_v3`) に `read-unborn-genesis`・表 8・key `00010800000bba00`・版 (1,0) が載る |
| 最後の C..E frame を 1 つ落とす | indeterminate で reject。notes = witness 不一致 (expected 36,156 / observed 36,155) と txid gap |

`real-trace-pipeline-probe-1.json` は注入先を「I を受けた key の R 行」から探したため見つからず (段 1 では挿入先の表を誰も読まない)、注入なしで certified になった初回で、
erratum として残す (2 回目で前 wave と同じ注入法に直した)。

## 5. 変異 matrix

段 4 で事前登録 (`verbatim/s4-ruling.md`)。M11 (reason の表を落とす) は実装後の確認で既存 v3 試験も赤になり単一理由性が無いので登録から外した (author・fix1 の報告、焦点再レビュー)。
anchor は `9a78e4174` の行 (fix2 は試験だけなので `2a35f260d` でも同じ)。期待 node は `2a35f260d` の独立 clone で dispatch probe (初回、全 SURVIVED 期待) で集めた
(`mutation/mutation-probe2-results.json`、baseline PASSED)。

**本走** (spec `mutation/mutation-spec-final.json` sha256 `224b5b81…`、`tools/mutation_worktree.py` の独立 clone @`2a35f260d` で dispatch、runner は
test_verifier.py 全体 + test_campaign.py の関係 6 node): baseline PASSED、**11 / 11 が事前登録どおり** (赤 node の集合が probe の観測と完全一致、`mutation/mutation-final-results.json`)。

| 変異 | 内容 | 結果 | 赤の試験 | 数え方 |
|---|---|---|---|---|
| M0 | `os.path.basename(str(binary))` (等価、harness の正例) | SURVIVED (期待どおり) | — | 正例 |
| M1 | CLI を旧 `result_to_dict` へ | KILLED | test_v3_cli_json_wiring_and_v2_bytes | 診断感度 |
| M2 | pipeline の reject 診断を旧へ | KILLED | test_tpcc_executor_v3_v2_existence_and_witness (existence case の詳細欠落) | 診断感度 |
| M3 | capability 射影を旧へ | KILLED | test_v3_capability_digest_binds_anomaly_and_existence | 診断感度 (digest) |
| M4 | capability 射影で存在詳細を pop | KILLED | 同上 | 診断感度 (digest) |
| M5 | payment の比較を外す | KILLED | test_tpcc_stage1_run_trace_allowlist | 受理集合 |
| M6 | delivery の欠落を許す | KILLED | 同上 | 受理集合 |
| M7 | payment を整数比較 (`"043"` を受理) | KILLED | 同上 | 受理集合 |
| M8 | TPC-C の v3 要求を外す | KILLED | test_tpcc_executor_v3_v2_existence_and_witness (v2 case が認定経路へ進む) | 受理集合 |
| M9 | `ycsb_` の受理を消す | KILLED | test_run_trace_parses_commit_witness_from_stdout、test_tpcc_stage1_run_trace_allowlist | 受理集合 |
| M10 | TPC-C の受理を消す | KILLED | test_tpcc_stage1_run_trace_allowlist (executor 試験は seam なので赤にならない = 裁定 B3 の帰属どおり) | 受理集合 |

初回の probe-1 (`9a78e4174` の独立 clone) は executor 試験が赤のまま (fix2 前) で、harness が「baseline が緑でない」と正しく abort した (収集・基準の 2 job だけ)。

M1〜M4 は受理集合を変えず構造化出力 (CLI JSON・診断・digest) だけを変えるので、DW-M08 に従い kill でなく診断感度の pin として別枠に数える。
M5〜M10 は受理集合 (trace を走らせるか、v2 の TPC-C を認定経路へ通すか) を変えるので kill に数える。M8 の赤は v2 の TPC-C run の `abort` が None になる形 (認定経路へ進む)、
M2 の赤は診断の `existence_violations` の欠落で、同じ試験関数でも赤の assertion が別。

## 6. 限界

- **flag は実際の取引を証明しない (段 3 A1):** 受理条件は binary 名と 4 flag の文字列で、trace の取引種別や op=D を見ない。flag を無視する手製 binary なら段 1 外の trace が通りうる。
  合成の編集面 (EVOLVE-BLOCK) は `cc/silo/transaction.cc` だけで、取引の選択は編集面外の `include/tpcc/tpcc_query.hh` の閾値なので、候補 binary では flag どおりに選ばれる
  (親が grep で確認)。trace 側の検査は依頼外の仮想リスク向け gate として足さなかった。
- **名前・flag は計数修正 (単位 1 の C1) の証拠でない (段 3 A2):** 現 pin の tpcc binary は v2 を出すので v3 要求で reject される。v3 emitter だけを持ち計数修正の無い binary では、
  短い走で数え落としが偶然 0 件なら witness が一致しうる。
- **v3 の capability digest は変わる:** 既発行の v3 capability (公開 API で発行できた) の digest を新しい射影で再計算しても一致しない。consumer は digest を 64 桁 hex として束縛し
  再計算しないので、domain 据え置きで v2 と v3 を取り違える経路は見つからなかった (段 3 A3)。
- **critic の説明文:** `orchestrator/critic/digest.py` の `trace-witness-unsupported-workload` の説明は「YCSB allowlist 外」のまま。TPC-C の v2 の reject にも同じ reason を使うので、
  production で TPC-C を build する経路ができたら説明が不正確になる (段 6 RB2、今回は触らない)。
- 実 trace は silo の 1 走 (thread 2・倉庫 1・1 秒) だけ。mocc は X/P 証拠面が pin に入る単位 11 の後。

## 7. 計算量

D2219 項 1 (1 タスクの job 合計が 2 node 時間以上なら事前確認) の線で数える。

| 項目 | 値 | 出所 |
|---|---|---|
| 焦点走 1・2 | Elapse 460 秒 + 464 秒 | 実測 |
| 単独走・単価実測 | Elapse 12 秒 + 13 秒 | 実測 |
| 変異 probe-1 (基準が赤で abort、収集と基準の 2 job) | 開始〜終了の合計 462 秒 (待ち行列込みの上限。収集 job は待ち行列で約 7 分) | 実測 (attempt 記録) |
| 変異 probe-2 (13 job) | 開始〜終了の合計 418 秒 (待ち行列込みの上限) | 実測 (attempt 記録) |
| 変異本走 (13 job) | 開始〜終了の合計 419 秒 (待ち行列込みの上限)、台帳の `duration_s` 合計 391 秒 | 実測 |
| 受入全走 1 回 | 約 0.25 node 時間 | 換算 (直近の受入の実測単価)。記録 commit の後、land 直前に行う (本 README の時点では未実施) |
| **合計** | **約 0.8 node 時間** (実測の上限 2,248 秒 ≈ 0.62 h に受入 0.25 h を足した上限側の見込み) | 2 node 時間の線の内側 |

変異 probe-1 は、同じ argv の 1 job で単価を実測せず、walltime (1 時間) × job 数の上限も取らずに投入した (F1041 の再発、failures fragment)。実使用は上の表のとおり線の内側。
probe-2 と本走は、同じ argv の 1 job (21198.nqsv、Elapse 13 秒) で単価を実測してから投じた。

## 8. 見送り台帳 [T-156] の発火条件の再評価

依頼は「pipeline が tpcc を受理した時点で [T-156] (selector-8b の workload descriptor への set-size 条件) の発火条件を再評価する」。同項の発火条件は
「8b descriptor の拡張を設計するとき」または「TPC-C 級 workload corpus を採るとき」で、着手前に workload 別の set-size 分布を測る順序が裁定済み (`docs/phase3.md` の見送り台帳)。

- **形式上は成立:** 本 wave で pipeline の `_run_trace` が TPC-C 段 1 の binary を受理するようになった (worklog の [T-2854] 項が発火の時点として名指した状態)。
- **corpus の実体はまだ無い:** production の build (buildcache) と workload 選択は ycsb だけで、TPC-C の候補を campaign が実際に評価した記録は無い。TPC-C の trace は単位 1・2 と
  単位 3 の構造検査の各 1 走 (thread 2・倉庫 1・1 秒) だけ。
- **結論:** [T-156] は着手しない (見送りのまま)。既裁定の順序 (着手前に workload 別の set-size 分布を測る) を維持し、実際の着手は TPC-C の候補を campaign が評価する wave
  (build と workload 選択の配線、単位 11 の pin 前進の後) で判断する。分布の材料は単位 1・2 の B0 trace (取引ごとの R / W 件数が取引種別つきで読める) にある。

## 9. 後続への引継ぎ

- **単位 11 (pin 前進):** 本 wave の範囲外。v3 emitter (C1' / C2 / C3) が pin に入るまで、現 pin の tpcc binary は v2 を出し本 wave の v3 要求で reject される。
- **TPC-C を production で評価する配線 (未起票):** buildcache の target (`ycsb_<protocol>.exe` 固定)、workload の登録・flag の受け渡し、critic の reason 説明 (§6)。
  設計 §7.1 の単位に無い。TPC-C の候補を campaign で評価するときに要る。
- **mocc:** 存在の契約は静的に成り立ち実 trace も存在違反 0 (D2232)。認定は X/P 証拠面が pin に入った後。

## 10. 記録の検査

- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`): rc=1 だが hit 3 件はすべて既存の較正記録
  (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file) で、本 wave の file は 0 件。
- 逐語の行末空白: Codex 出力 7 file の Markdown 改行用の空白を可逆に除いた (`NORMALIZATION.md` に原文 sha256・byte 数・除去位置)。
