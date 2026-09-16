# [T-2288] B-4 床値 spec 凍結の前提 — 較正の再取得なしに閉じられる A-3 / A-4 / C 群を閉じ、[T-2465] の §11.3 を追記反映した

`authority: none`
`default_effect: no-state-change`

2026-09-17。wave `dev-wave-t2288-floor-spec-prereqs`、branch `worktree-dev-wave-t2288-floor-spec-prereqs`。
起点 local main `20a92f6a636c0aaf7d3e8f98ea99e3cb3b2fbae9`。
**実装面 (D95 決定 2) の差分は 0。** 本 wave の成果物は decisions fragment (D 3 件)、worklog fragment、
事前登録 §11.1 / §11.3 への追記 2 箇所、本スナップショットである。可変状態の正本は worklog 末尾と
現行 phase doc であり、本書ではない。設計判断の正本は decisions (fold 後の D 番号) であり、本書は経緯と証拠を持つ。

## 依頼と答え

依頼は「床値 spec 凍結を塞ぐ前提のうち、較正と独立な A-3 (perf_config の extime / reps / ycsb_max_ope の
採用根拠を calibrator 出力から D1641 決定 3 の委任の下で承認)・A-4 (§5 の contention セル集合の具体列を
3 workload × §5 の方針から起こす)・C 群 (rr50 の accepted 較正が複数ある件に、D2044 項 11 の逐語どおり
値に依存しない適格条件と採用順序を定める) を閉じ、同じ変更単位で [T-2465] (事前登録 §11.3 の 4 点を AI の
追記訂正で反映) を入れる。A-5 は記入せず、何が要るかを裁定パッケージで返す」だった。

**答え: 3 件とも閉じた。ただし依頼の前提のうち 2 点は現物と食い違い、そのまま記録した。**

1. **A-3 の 3 値のうち calibrator から導けるのは 2 値だけ。** `extime=3` と `ycsb_max_ope=10` は較正の取得構成
   (tracked な取得 argv と CLI / CCBench の既定) から復元できるが、`reps` は較正 JSON にも argv にも無い。
   **`reps=5` は AI の選択として承認し、そう明記した。** spec 凍結前なら D への追記で改められる。
2. **A-4 の「§5 に列挙する contention セル」は現物のどこにも無い。** 具体列は既裁定の転記ではなく、
   accepted 較正が実在し binder の exact 一致を通る条件から起こした**新しい具体化**である
   (3 workload × 1 セル = 3 cell)。集合の十分性は主張しない。
3. **C 群の規則で同条件 (rr50 / silo) の 2 件を分けたのは既裁定の identity だけだった。** 2 件は環境契約の世代
   g1 / g2 で、g1 は D1537 が自己不整合と裁定済み。挙動基準の条件で g1 を除き g2 を採る (非 silo の 4 件は protocol
   条件で外れる)。較正値は既知 (2026-07 以降公開) で本 wave も閲覧したこと、床値結果は 1 件も無いこと、
   「結果を見る前に」を床値結果と読むのは本 wave の解釈であることを D に隠さず書いた。

「較正と独立な」は正確には「較正の再取得なしに閉じられる」である — 導出は取得構成・較正の実在・取得 identity に
依存する。

## A-3 — `perf_config` の 3 項目 (D: `b4-floor-perf-config-approval`)

| 項目 | 値 | 出所 | 根拠 (現物) |
|---|---|---|---|
| `extime` | 3 | 較正の取得構成 | calibrator CLI 既定 `--extime 3` (`orchestrator/calibrator/cli.py`)。silo 4 job の `output/env/pegasus/calibration/job-staging/<job>/calibrate-argv.json` (`0:867876.nqsv` / `0:892707.nqsv` / `0:995805.nqsv` / `0:478.nqsv`) に `--extime` 無し (`verbatim/probe-calibrate-argv.txt`)。runner は `-extime=<値>` を bench へ渡す |
| `ycsb_max_ope` | 10 | 較正の取得構成 | 取得 argv の workload は 3 key で `ycsb_max_ope` を含まず、runner の固定 flags にも無い → CCBench 既定 `DEFINE_uint64(ycsb_max_ope, 10, …)` (`external/ccbench/include/ycsb.hh`)。floor driver は明示で渡すので 10 を書く。runner 一般が渡せないという意味ではない |
| `reps` | 5 | **AI の選択** | 較正 JSON (`calibration/v2`) に反復数の key は無く、calibrator は sweep 3 / noise floor 10 を別用途に使う。事前登録 §11.2 の名目 (1 測定 = 5 反復 × 3 秒)、`PerfConfig` 既定 5、D1640 の参照測定 (5 反復) と揃え、`median/v1` が実 rep を返す奇数 |

`reps` は bench 1 回の flags を変えない量だが、実行量・時間的標本化・median の標本分布には効く
(段 3 が親 brief の「分散だけ」を訂正)。D1854 のとおり rratio・rmw・max_ope は resident peak に効くので、
extime と max_ope を較正時と変えると「校正済み動作点で測る」(floor driver の逐語) が成立しない。

## A-4 — セル集合の具体列 (D: `b4-floor-cell-set`)

| spec | cell `workload` (逐語、`"0"` を `"false"` へ置換しない) | `records` | 較正 (registered) |
|---|---|---|---|
| rr95 (read-heavy) | `{"ycsb_rmw": "0", "ycsb_rratio": "95", "ycsb_zipf_skew": "0.9"}` | 1,000,000 | `calibration-5c836a22eff9ab40.json` |
| rr50 (balanced) | `{"ycsb_rmw": "0", "ycsb_rratio": "50", "ycsb_zipf_skew": "0.9"}` | 1,000,000 | `calibration-94a4b79fa31bba3c.json` (C 群で選択) |
| rr5 (write-heavy) | `{"ycsb_rmw": "0", "ycsb_rratio": "5", "ycsb_zipf_skew": "0.9"}` | 2,000,000 | `calibration-2b7ba072b88023ae.json` |

全 cell で `threads 48`、`extime 3`、`reps 5`、`ycsb_max_ope 10`、`env_tag pegasus`、`clocks_per_us 2100`。
導出規則: 対象 driver (silo)・Pegasus・3 workload について、accepted 較正が実在し
`_bind_checkout_inputs` の exact 一致 (env_tag / threads / clocks_per_us / workload dict / records) を通る条件を
採る。skew を足すには新しい較正 (D15 の関門) が要り、認可されていない。段 3 レンズ B が 3 件の較正 JSON の
実 field 値で束縛可能性を独立に確認した (較正側のみ。binary・build receipt を含む binder 全体は未実測)。

## C 群 — 同条件の accepted 較正が複数あるときの選択規則 (D: `calibration-record-selection-rule`)

適格条件 = (1) registered 配下の tracked record (新規の人手規則)、(2) accepted かつ floor driver と同じ入口
(`load_verified_calibration`、mode=required) を通る、(3) protocol が対象 driver と一致 (`genome` 先頭要素。
genome 不在は歴史的 2 件の完全 sha256 に限って silo と見なす — job-staging の `calibrate-argv.json` の
`--binary` / `--binary-sha256` で裏付け、D1538 の限定を保つ)、(4) env_tag / clocks_per_us / threads / workload の
exact 一致、(5) 自分の attestation 述語を通らないと記録・裁定された記録 (現物は D1537 の g1 1 件、identity は
`layer3_report.SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS`) でない。
採用順序 = `acquisition_receipt.qsub.submit_epoch` 最小、同値は `qsub` の `(project, queue, request_id)` 辞書順。
内容 sha256 は順位に使わない (測定値を含む)。

| record | rr | protocol (根拠) | submit_epoch | (2) admission | (5) | 結果 |
|---|---|---|---|---|---|---|
| `753f535a…` (g1) | 50 | silo (genome 不在、argv `ycsb_silo.exe`) | 1784404710 | ADMITTED | D1537 の自己不整合 (method `proc-cpuinfo`) | 不適格 |
| `94a4b79f…` (g2) | 50 | silo (同上) | 1785983265 | ADMITTED | 通過 | **採用** |
| `5c836a22…` | 95 | silo (genome) | 1789310388 | ADMITTED | 通過 | **採用** (唯一) |
| `2b7ba072…` | 5 | silo (genome) | 1789523899 | ADMITTED | 通過 | **採用** (唯一) |
| `449d0ad2…` / `9b49335d…` | 50 | mocc / tictoc | — | ADMITTED | — | (3) で不適格 |
| `b3329d93…` / `cb985139…` | 95 | mocc / tictoc | — | ADMITTED | — | (3) で不適格 |

- **method 文字列の不一致を拒否理由にしない** (規律 7)。較正 verifier が現行 policy と照合するのは tolerance だけで
  (`calibration_verify.py`)、method 一致は既存 gate ではない。条件 (5) は「自分の述語で落ちた」という挙動基準。
- **適格集合は各 workload で 1 件になったので、採用順序は今回勝者を決めていない。**
- **時系列:** 床値結果は 1 件も無い (spec も測定も存在しない)。較正値は既知で本 wave も閲覧した。実際に候補を
  落とした条件は (3) (protocol = `genome` という既存事実) と (5) (D1537 の既裁定 identity) で、同条件 (rr50 / silo)
  の 2 件を分けたのは (5) だけである。本 wave が新しく置いた条件 (registered 限定・最早順・同値処理) は候補を
  1 件も落としていない。D2044 項 11 の「結果を見る前に」は床値結果に対して満たす — 「結果」を床値結果と読むのは
  本 wave の解釈である。admission 成功も本規則の適用も、選択規則の事前性を機械的に保証しない。

## T-2465 — 事前登録 §11.3 の追記反映

- §11.3 第 2 bullet の「追記 (2026-09-07)」段落末へ追記 1 段落: 担当者の指名 (D1641 決定 1)、対象集合と統計関数
  (D1641 決定 3、D1936 項 7、n = 62 は D1695)、採用証拠の受理 (D1641 決定 2 — 手順の確定であって個別成果物の
  受理ではない)、driver の変更単位 (D1453 / D1694)。D1887 が未確認としていた 2 点は D1936 末尾が閉じた。
- §11.1 の D1812 (c) 追記段落末 (「ユーザー裁定へ返してある。」直後) へ決着の追記 1 箇所。
- 既存文は書き換えていない。§5 の値セル (行 154〜167) は bytes 不変 (変更前後の sha256 が一致)。
- 事前登録 doc は `tools/check_docs.py` で living 扱いで、全文 sha256 の pin は歴史記録 1 件のみ (DW-O09 閉包)。

## 閉包 (親の実測、段 3 レンズ B が独立に再現)

| 対象 | 方法 | 結果 |
|---|---|---|
| registered 較正 | 8 件を JSON で読み sha256 照合 | rr5 silo×1 / rr50 silo×2 + mocc×1 + tictoc×1 / rr95 silo×1 + mocc×1 + tictoc×1 |
| admission | 8 件を `load_verified_calibration(pegasus, 2100, required)` へ通す | 8/8 ADMITTED (g1 を含む = method 一致は gate でない) |
| registered 外の accepted | tracked JSON 全域 + 圧縮 1,771 件展開 (レンズ B) | mocc 2 件 (insight 配下) と registered の複製のみ。silo の追加取得なし |
| genome 不在 2 件の protocol | `pbs_jobid` → job-staging `calibrate-argv.json` | `--binary …/cc/silo/ycsb_silo.exe`、`--binary-sha256` は receipt と一致 |
| extime / max_ope | 4 job の argv + `cli.py` 既定 + `runner.py` base_flags + `ycsb.hh` | `--extime` 無し (=3)、`ycsb_max_ope` 無し (=10) |
| 事前登録の pin | path と変更前 sha256 で repo と output/ を逆引き | living、pin なし。§5 を parse する consumer 4 本は §11 を読まない |

## 裁定パッケージ (ユーザーへ返す。いずれも本 wave の成果物を無効にしない)

1. **A-5 — spec 凍結に要る値 (本 wave は値を書かない)。** 1 spec あたり: 2 窓の `not_before` / `not_after`
   (UTC、重複なし、24 時間以上の分離は人手確認 — D1974)、各窓の `campaign_id`、`seed_hex` (64 桁 lowercase hex、
   結果を見る前に固定)、`artifact_relpath` ×2 (窓ごとの create-only 出力先)、`summary_relpath` (create-only)。
   3 spec 分と集約出力の対応も要る。実行設定 = site / env_tag / clocks_per_us (D1641 決定 3 で確定済み)、
   配置済み binary (`output/env/pegasus/binaries/<sha256>`、T-2697 の `place` を凍結 checkout で実行)、
   予定標本 (n = 62 × 2 窓) と pair の対応。§11.1 の割り当て表は「標本数・campaign 数・時間窓の分離」
   「成果物の書式と命名」の決定主体をユーザーとし、「AI が起草した候補値を無裁定の既定値として凍結へ入れない」。
   本 wave の依頼が値を書かないよう指示したので候補も付けていない。
2. **`reps=5` は AI の選択。** D1641 決定 3 の逐語「calibrator の出力を採り」の外にある値を、依頼文の名指しと
   事前登録 §11.2 の名目に基づいて承認した。異議があれば D への追記で改める (凍結前)。
3. **3 cell は対象集合の具体化 (AI の選択)。** contention 域の網羅性は主張していない。skew を足すなら新しい較正の
   認可が要る。
4. **C 群規則の事前性の記録形。** 較正値の既知性を開示した上で、床値結果に対する事前規則として記録した。
5. **D1538 の consumer 側限定 (genome 不在 record の内容 hash 許可リスト) は層 3 で未実装** (段 3 レンズ B)。
   本 wave は gate を足さない scope なので実装していない。

## 生証拠

| path | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親)。(P1)〜(P5) と、段 3 が訂正した根拠を含む原文 |
| `verbatim/probe-calibrations-summary.txt` / `probe-calibrations-diff.txt` | registered 8 件の要約・識別情報 (親の read-only probe) |
| `verbatim/probe-admission.txt` | 8 件の admission 結果と effective-clock method |
| `verbatim/probe-calibrate-argv.txt` | silo 4 job の取得 argv と実走ログの reps / noise floor 行 |
| `verbatim/s2-plan-prompt.md` / `s2-plan.md` | 段 2 plan の投げ文と成果物 (codex, read-only) |
| `verbatim/s3-a-prompt.md` / `s3-a.md` | 段 3 レンズ A — 授権範囲・正しさ境界・事前登録 |
| `verbatim/s3-b-prompt.md` / `s3-b.md` | 段 3 レンズ B — 実物照合・閉包・実効性 |
| `verbatim/s4-ruling.md` | 段 4 裁定 (親)。所見 21 件の real / refuted と plan v2 |
| `verbatim/s6-a-prompt.md` / `s6-a.md`、`s6-b-prompt.md` / `s6-b.md` | 段 6 敵対レビュー 2 本 (diff の検査) |

## 受入・検査

| 検査 | 結果 |
|---|---|
| `python3 tools/check_docs.py` | rc=0 (違反なし) |
| `python3 tools/spool_fold.py --dry-run --show-diff` | rc=0 (仮採番 D2088 / D2089 / D2090。実採番は land の fold が行う) |
| §5 を parse する consumer の test 5 file (`test_p3_b4_admission_record` / `test_p3_b4_floor_artifact_issuer` / `test_p3_b4_analysis_prereg_consumer` / `test_p3_b4_prerun_issuer` / `test_p3_b4_closed_critic`、実文書を読む test を含む) | 編集前 255 passed (login node、39.5 秒) / 編集後 255 passed (計算ノード request `2285.nqsv`、bnode014、7.6 秒) |
| §5 表 (行 154〜167) の bytes | 変更前後で sha256 `1762b7cc…` が一致 (段 6 レンズ B が独立に再計算) |
| 事前登録 diff | 追加 20 行・削除 0 行 (§11.1 / §11.3 の 2 箇所) |
| 段 6 敵対レビュー | レンズ A = real 5 / nit 1、レンズ B = real 1 / nit 2。real は本文の転記漏れ・単位・範囲・件数で、いずれも fix 済み。SHA・数値・識別子・条件 3 / 5・実装行は全件一致 |
| 変異 matrix | 実装面差分 0 につき免除 (DW-S04) |
| 受入全走 | 本記録 commit を含む最終 tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。受領証は job dir (`acceptance-receipt-1.json`) |

## 本 wave が保証しないこと

- **loader (`load_frozen_spec`)・driver・issuer・build・測定を実行していない。** spec は存在せず、較正側の照合が
  通ることまでしか確かめていない。binary・build receipt を含む binder 全体の成功は未実測。
- **3 cell が contention 域を網羅することは主張しない。**
- **`reps=5` は較正から導いた値ではない。**
- **C 群の規則は spec を書く人手の選択規則であり、機械検査ではない。** admission 成功は protocol・測定設定・
  対象集合の意味的一致や選択規則の事前性を保証しない (D1696 が人手責任として残した 9 項目のまま)。
- **較正値を見る前に規則を定めたとは主張しない。** 主張するのは、床値結果より前に定め、測定値を読まない規則で
  あること、候補を落とした条件が既裁定に基づくことだけである。
- 実装面差分が 0 なので DW-S04 により変異 matrix を免除した。受入全走は免除していない (結果は「受入・検査」節)。
