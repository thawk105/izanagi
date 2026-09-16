---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2288-floor-spec-prereqs
seq: 2
title: [T-2288] B-4 床値 spec 凍結の前提のうち較正の再取得なしに閉じられる A-3 (PerfConfig の 3 項目)・A-4 (セル集合の具体列)・C 群 (同条件較正の選択規則) を D 3 件で閉じ、同じ変更単位で [T-2465] (事前登録 §11.3 の 4 点) を追記反映した (docs のみ、branch worktree-dev-wave-t2288-floor-spec-prereqs、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- **A-3 は 3 値のうち 2 値しか calibrator から導けなかった。** `extime=3` と `ycsb_max_ope=10` は較正の取得構成
  (tracked な `calibrate-argv.json` に `--extime` 無し、workload 3 key に `ycsb_max_ope` 無し → CLI 既定と
  CCBench 既定) から復元できるが、`reps` は較正 JSON にも argv にも無い。**`reps=5` は AI の選択として承認し、
  そう明記した** ({{D:b4-floor-perf-config-approval}})。依頼文の前提「calibrator 出力から」は `reps` には成り立たない。
- **A-4 の「§5 に列挙する contention セル」は現物のどこにも無く、具体列は既裁定の転記ではなく新しい具体化である。**
  accepted 較正が実在し binder の exact 一致を通る条件から、3 workload × 1 セル (t48・skew 0.9・rmw 0) の
  3 cell を起こした ({{D:b4-floor-cell-set}})。集合の十分性 (contention 域の網羅) は主張していない。
- **C 群の規則で同条件 (rr50 / silo) の 2 件を分けたのは既裁定の identity だけだった。** 2 件は環境契約の世代 g1 / g2
  そのもので、g1 は D1537 が自己不整合と裁定した記録。挙動基準の条件 5 で g1 を除き g2 を採る (非 silo の 4 件は
  protocol 条件 3 で外れる)。method 文字列の不一致を拒否理由にする案は規律 7 で退けた。較正値は 2026-07 以降
  既知で本 wave も閲覧したこと、床値結果は 1 件も無いこと、「結果を見る前に」を床値結果と読むのは本 wave の
  解釈であることを D に隠さず書いた ({{D:calibration-record-selection-rule}})。
- **段 1 で判明した新事実:** registered 較正は 8 件 (2026-09-15 の insight 時点から増加)。binder は protocol を
  照合しないので、条件 3 (protocol 一致) が無いと mocc / tictoc の較正で silo の cell を束縛できてしまう。
  8 件は floor driver と同じ入口で全件 ADMITTED (段 3 レンズ B が独立に再現)。
- **段 3 の裁定:** レンズ A 所見 = real 8 / refuted 6、レンズ B 所見 = real 11 / refuted 6。real の主要 3 件は
  `reps` の授権範囲、3 cell の性質 (転記でなく選択)、C 群の時系列。refuted の主要 2 件は「§11.1 は候補起草を禁じる」
  (親の過大解釈) と「T-2465 の 4 点に新規授権が要る」。裁定の全文は insight `verbatim/s4-ruling.md`。
- **T-2465:** §11.3 第 2 bullet の追記末と §11.1 の D1812 (c) 段落末へ追記 2 箇所。§5 の値セルは bytes 不変
  (行 154〜167 の sha256 一致)。
- **A-5 は記入せず裁定パッケージで返した** (insight「裁定パッケージ」節)。scope 外で実装しなかった real 所見:
  D1538 の consumer 側限定 (genome 不在 record の内容 hash 許可リスト) が層 3 で未実装。
- **段 6 の敵対レビュー 2 本:** レンズ A (逐語整合) = real 5 / nit 1、レンズ B (実物照合) = real 1 / nit 2。
  SHA・数値・識別子・条件 3 / 5 の裏付け・binder / verifier の実装行は全件一致。real は非保証 (事前性) の転記漏れ、
  費用単位 (7,440 秒は 1 pair・1 セルあたり 2 campaign 合計)、「既裁定だけ」の範囲、A-5 の理由の過大解釈、
  受入記録の未記入、計算ノード job 数の誤りで、いずれも親が本 fragment・D・insight を直した。
- **受入・検査:** `check_docs` rc=0、`spool_fold --dry-run` rc=0 (仮採番 D2088〜D2090)、§5 を parse する
  consumer の test 5 file (実文書を読む test を含む 255 件) は編集前 (login、39.5 秒) と編集後 (計算ノード
  `2285.nqsv`、bnode014、7.6 秒) の両方で全緑。受入全走は本記録 commit を含む最終 tip に対して land 前に 1 回だけ
  投入し、child-green でなければ land しない (受領証は job dir)。
- **段 8 の自己改善:** 候補 0 件。踏んだ拒否 (heredoc・隔離 session の複合 git 形) と fragment の action 順は
  いずれも既知の型で、docs の新規収容も F の再発追記も無い。
- エージェント工数: codex 子 5 本を起動し 5 本とも受理 (段 2 plan 1 / 段 3 consult 2 / 段 6 review 2、いずれも
  read-only、`gpt-6-astra` / `reasoning=medium`)。実装子・fix 子は実装面が無いため立てていない。計算ノード job は
  焦点走 1 request (`2285.nqsv`) と受入全走の分。
- 一次資料: `output/insights/2026-09-17/t2288-floor-spec-prereqs/README.md`。

## 次の一手差分

### 完了

- [T-2465] 事前登録 §11.3 の 4 点 (担当者の指名・対象集合・統計関数・採用証拠の受理) と driver の変更単位を、
  D1641 決定 1〜4 / D1695 (n = 62) / D1453 / D1694 の反映として追記訂正し、§11.1 の D1812 (c) 追記が
  「ユーザー裁定へ返してある」と書く食い違いにも決着の追記を足した (D1887 / D1936 末尾)。既存文は書き換えず、
  決定の効力も変えていない。
  remaining: none
  base: 994bb67c02be36dd05da6d9ec47bcc413bcc0c0e93cea96db77634751d640f50

### 更新

- [T-2288] **P1・較正の再取得なしに閉じられる前提 (A-3 / A-4 / C 群) は閉じた。spec 凍結までに残るのは A-5 と凍結作業**:
  A-3 = `extime 3 / reps 5 / ycsb_max_ope 10` ({{D:b4-floor-perf-config-approval}}、`reps` は AI の選択)、
  A-4 = 3 workload × 1 セル (t48・skew 0.9・rmw 0) の 3 cell ({{D:b4-floor-cell-set}})、C 群 = 5 条件 + 最早順
  ({{D:calibration-record-selection-rule}}、rr50 は g2 `94a4b79f…`)。rr5 の accepted 較正 (1535)、binary record
  (T-2636)、配置規則 (T-2697、`output/env/<env_tag>/binaries/<sha256>` の ignored 複写) は着地済み。
  **残る前提は A-5** (2 窓の `not_before` / `not_after`・`campaign_id`・`seed_hex`・`artifact_relpath` ×2・
  `summary_relpath`・実行設定。本 wave の依頼が値を書かないよう指示したので候補も付けていない — §11.1 は
  無裁定の AI 起草値を既定値として凍結へ入れることを禁じる。裁定パッケージ参照)。凍結前の作業として
  spec を凍結する checkout での binary の `place` 実行、3 spec の作成・`--validate-only`・commit が残り、凍結後の
  工程として床値実測、集約、採用裁定、§5 floor 欄の記入が残る。較正側の照合が通ることまでしか確かめておらず、
  binder 全体 (binary・build receipt) の成功は未実測。
  base: f0a105478d14103f50118c1c7b5d49a77624140a2107d06588db2fddc69fc1a4
