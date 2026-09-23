# [T-2854] 単位 5 — 段 4 裁定 (親、2026-09-23 20:3x JST)

入力: s1-brief.md、codex/s2-plan.md (rc=0、4 分)、codex/s3-consult-A2.md (正しさ境界、rc=0。初回 A は親 prompt の誤 path で停止 rc=1)、codex/s3-consult-B.md (整合・過剰、rc=0)。
裁定 inbox 再走査: 最新は 2026-09-23 19:53 の第 33 回 (wave 開始前)。項 1 は単位 11 の branch 名の話で本単位に影響なし。

## 所見の裁定

| ID | 裁定 | 採否・理由 |
|---|---|---|
| A1 (flag は実取引を証明しない、種別 3〜5 と D を受理しうる) | real だが must-fix でない (refuted as must-fix) | 反例は flag を無視する手製 binary でだけ成立する。合成の編集面 (EVOLVE-BLOCK) は `cc/silo/transaction.cc` だけで、取引の選択は編集面外の `include/tpcc/tpcc_query.hh` の閾値 (親が grep で実測)。候補 binary は pin の workload code で flag どおりに取引を選ぶ。trace の種別・op 検査は依頼外の仮想リスク向け gate (DW-G05) なので足さない。限界として insight に書く |
| A2 (名前・flag は emitter・計数修正の証拠でない) | real、記録のみ | 現 pin の v2 出力は v3 要求で拒否される。「flag を持つ v3 run を受理」と「計数修正済み producer の認定」は別と insight に明記。検査は足さない |
| A3 / B7 (既発行 v3 capability の digest が変わる) | real、記録 + 試験 | v2 は dict 同一・digest 不変を試験で固定。v3 は意図的に変わる (新旧互換を主張しない)。domain は v1 のまま (consumer は 64 桁 hex を束縛するだけで再計算しない: commit_receipt.py:465 付近、A3 の確認) |
| A4 (不正 AnomalyV3 の ValueError) | real、変更なし | 正規 parser 入力から到達しない。回復処理も試験も足さない (B6) |
| B1 (完了判定 (a) は production evaluate に届かない) | real、採用 | 完了判定を `_run_trace` の受理 + executor と実 verifier の結合 + 親の実 trace probe に限る。buildcache・workload 選択は後続 |
| B2 (digest の表・取引種別は certified 正例では検査不能) | real、採用 | digest 試験は v3 の異常結果 (cycle と存在違反) で表・種別・存在詳細の束縛を確かめる |
| B3 (trace_runner 注入は allowlist を迂回) | real、採用 | 受理・拒否は実 `_run_trace` (fake executable) で、認定の結合は executor の seam で、試験を分ける |
| B4 (witness 変異の帰属) | real、採用 | 変異 control は「完全な末尾 C..E frame を落とし残りは正常」の 1 例。(b)〜(d) は欠落形態の確認で赤理由を witness だけと断定しない |
| B5 (実 CC は外す) | real、採用 | lost update は合成 v3 fixture + 直列対照。実 CC 走は完了条件に数えない (計算投入なし) |
| B6 (過剰) | 一部採用 | `.exe` 接尾辞は要求しない (ycsb と対称)。新 abort reason は作らず、v2 の TPC-C は既存 `trace-witness-unsupported-workload` (critic digest.py の説明「commit 後 counter 加算契約を証明済みでない」) で拒否し detail に schema を載せる。値の文字列比較は == の帰結で、変異 M7 のために `"043"` 1 例だけ置く |
| B8 (呼び手の区分・行番号) | 採用 | 配線は CLI JSON (cli.py:90)・pipeline 拒否診断 (pipeline.py:656)・capability 射影 (core.py:284) の 3 箇所 + pipeline の受理 (`_run_trace`) と verifier 後の v3 要求。silo_ladder_rung1・reflux は YCSB 専用で対象外 |
| B9 (1 本に寄せる) | 採用 | author 1 本 |
| plan 異議「.exe まで条件に」 | 不採用 | B6 のとおり |

## plan v2 (author 1 本、Codex role=author)

1. core.py:284 の capability 射影を `result_to_dict_v3(result)` にする (trace_dir・framing 詳細・permutation 詳細の pop は維持、存在件数・詳細は残す)。
2. cli.py の `--json` の結果を `result_to_dict_v3` にする (import は `.core` から。`render_text` は不変)。
3. pipeline.py:656 の reject 診断を `result_to_dict_v3` にする。
4. `_run_trace` の受理: `basename.startswith("ycsb_")` または (`basename.startswith("tpcc_")` かつ flags の `tpcc_perc_payment == "43"`・`tpcc_perc_order_status == "0"`・
   `tpcc_perc_delivery == "0"`・`tpcc_perc_stock_level == "0"`)。それ以外は従来どおり `_TraceWitnessUnsupportedWorkload`。
5. v3 要求: `_execute_verification_repetition` で verifier が返した直後 (verify_payload・certified 判定より前)、binary (payload 名でなく trace を走らせた binary) の basename が
   `tpcc_` なら `verify_result.integrity.existence_violation_details is not None` を要求し、違えば `trace-witness-unsupported-workload` で abort
   (detail に `{"trace_schema": "v2"}` 程度、文言は日本語で既存に揃える)。ycsb は不変。
6. 試験 (既存 file だけ、新規 test 関数 ≤ 8):
   - test_verifier.py: (i) CLI `--json` が v3 の cycle で表・取引種別、存在違反で件数・詳細を出し、v2 fixture では旧 `result_to_dict` の json と bytes 一致。
     (ii) capability の `_result_sha256` が v3 異常結果で `result_to_dict_v3` の射影 (同じ pop) の digest と一致し、存在詳細だけ違う 2 結果で digest が異なる。
     v2 では旧射影の digest と一致。(iii) §6.1 lost update の v3 合成 fixture (District = 表 1、2 取引が同じ版を読み順に U) が non-serializable で
     ww・rw の辺と表 1 を報告し、同じ操作の直列版が certified。既存の表識別 (3475)・手書き G2 (3517)・genesis の誤用 (3903 の read-unborn-genesis) は対応づけるだけで足さない
     (表識別の試験に「表を落としたら増える辺」の assertion を 1 行足すのは可)。
   - test_campaign.py: (iv) 実 `_run_trace` + fake executable `tpcc_*` で 57:43 の 4 flag は trace 実行まで進み、payment=44・delivery 欠落・`"043"` は
     unsupported-workload、`ycsb_` は従来どおり。(v) executor (trace_runner seam + 実 verifier と既存の build binding helper) で tpcc の v3 直列 trace が certified、
     v2 trace が unsupported-workload で reject、存在違反が indeterminate で reject し診断に `existence_violation_details` が載る、
     完全な末尾 frame を落とした trace が witness 不一致で indeterminate (witness の変異 control)。(b)〜(d) の欠落形態は同じ試験の parametrize でよい。
7. 規模上限: production 追加削除 ≤ 60 行、試験 ≤ 320 行、新規 test 関数 ≤ 8。既存試験の期待値は変えない。report.py・verifier/__init__.py・新 module・新 test file 禁止。

## 変異の事前登録 (DW-M01、実装後に単一理由性を確認)

| # | 変異 | 殺す試験 (予定) |
|---|---|---|
| M1 | cli.py を旧 `result_to_dict` に戻す | (i) |
| M2 | pipeline 診断を旧に戻す | (v) 存在違反 |
| M3 | capability 射影を旧に戻す | (ii) |
| M4 | capability 射影で存在詳細を pop | (ii) |
| M5 | payment の比較を外す | (iv) payment=44 |
| M6 | delivery の条件を外す (欠落を許す) | (iv) delivery 欠落 |
| M7 | 値を int 比較にする | (iv) "043" |
| M8 | tpcc の v3 要求を外す | (v) v2 trace |
| M9 | `ycsb_` の受理を消す | 既存 test_run_trace_parses_commit_witness_from_stdout |
| M10 | tpcc の受理を消す (従来に戻す) | (iv) 57:43 の受理、(v) は seam なので赤にならないこと (B3 の帰属確認) |
| M11 | lost update の表を表 0 と 1 で分ける fixture 側でなく verifier の reason の表を落とす | (iii) の表 1 の assertion (既存 v3 試験も赤になりうる。単一理由性は実装後に確認し、成り立たなければ登録から外す) |

## 研究前進と成果物影響 (DW-G05)
放置時: pipeline は TPC-C の run を trace 前に拒否し続け、CLI・診断・受領証は v3 の表・種別・存在詳細を落とす (TPC-C 候補の認定と構造化診断が得られない)。
