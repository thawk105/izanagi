# 段 1 brief — [T-419] 択 (c) seam + 検査網の補強

base main = `98df871b` / branch = `worktree-dev-wave-t419-seam-checknet` / 2026-08-16 19:40 JST

## 確定済みユーザー裁定 (authority = ユーザー、2026-08-16 /rulings 全件 第 2 回 #3)

択 (c) = 上位の較正・凍結権限束を待たず **seam と検査網の補強だけ先に land**。受理集合は一切変えない。
従属 3 問は 3 件とも狭める側 — (i) `effective_clock.method` の恒真比較を実体一致へ /
(ii) 自己不整合な旧較正を歴史 resolver が検証済みとして受理し続けるのを止める /
(iii) 第 2 世代を active にする根拠を `quality.status=accepted` だけに置かない。

## 親の前提実測 (全て本 worktree の HEAD `98df871b` で実行)

- M-A pegasus の active は g1 (`contract e576e9cd…`、`calibration 753f535a…`、`attestation_mode=required`)。
  registered catalog は pegasus に **2 世代** (g1, g2 `1346c20b…`/`94a4b79f…`)、ever-active は g1 のみ。
- M-B 自己整合の再計算: g1 = 48 標本中 **1 本が帯外** (3080.935、帯 [2058.98, 2143.02])、g2 = **0 本**。
  両者とも `quality.status=accepted`。
- M-C `_verify_entry_calibration` (`env_contract.py:486`) は **active 経路 (`:540`) と歴史 resolver
  (`_ensure_calibration_verified`, `:601`) の共有**。ここを狭めると active 側も落ちる。
- M-D 歴史 resolver の非テスト consumer は 6 件。うち `wal.py:1064`
  (`validate_commit_contract_bindings`) は **live campaign の COMMIT 監査経路**であり、
  歴史成果物専用ではない。他は floor campaign / oracle report / reflux closure /
  ratified freeze / autonomous trial completeness。
- M-E **(i) は D329 の反転である。** D329「取得方法の名前は provenance であって判定に使わない」
  (2026-08-12、ユーザー裁定) は、当時 exact 一致だった同比較が実投入 `905941.nqsv` を拒否し、
  第 1 世代の登録が構造的に attestation を通れなくなった実測を受けて commit `c9c6da84` で外したもの。
  **8/16 の裁定パッケージ (brief / plan / 敵対 2 レンズ / s4 / 控え / worklog 579 / F339) は
  D329 にも 8/12 裁定にも一度も言及していない** (全文検索 0 件)。
- M-F 既存被覆 (性質で検索): 自己整合の既知例外つき検査は
  `test_env_contract.py:839` に**既に存在する**が (a) test 層のみ (b) 走査は `ec.REGISTRY` =
  **active view の 2 件だけ**で、registered 済み・未 active の g2 は 1 件も見ていない。
  production 側に自己整合の検査は無く、活性化の根拠検査も `quality.status` 以外に無い。
- M-G 凍結 pin 閉包: `FROZEN_MANIFEST` が pin するのは成果物 bytes (floor_protocol.json 等) で、
  編集面 (`env_contract.py` / `certified_writer_admission.py` / `env_contract_activation.py`) の
  source bytes を pin する live な台帳・trust root は 0 件 (hit は過去 wave の変異 spec / 台帳のみ)。

## scope

- **S1 seam**: floor protocol path を literal (`certified_writer_admission.py:206-210`) から
  **authority 解決の単一 seam** へ移す。caller は path を渡せない (A-07 の受理拡大を構造的に閉じる)。
  今日の解決結果は現行 path と bytes 一致 = 受理集合不変。
  成果物影響: 未実装だと世代前進時に admission が他世代の protocol を読み、
  拒否理由が `contract_sha256 不一致` に化けて床値 v2 の起動不能の原因が診断できない。
- **S2 (ii)**: 歴史 resolver に自己整合の再計算を入れ、**明示列挙した既知 1 組 (g1) 以外の
  自己不整合較正を fail-closed で拒否**する。共有 `_verify_entry_calibration` は触らない (M-C)。
  成果物影響: 未実装だと新規登録された自己不整合較正が runtime で「検証済み」として通り、
  certified 選択の env 由来性が偽の保証を持つ。
- **S3 (iii)**: **activation admission** を新設し、次以降の活性化に `quality.status=accepted` 以外の
  根拠 (自己整合の再計算 0 件・content-addressed path・acquisition receipt の束縛) を必須にする。
  現 serial 1 は forward-only で不変。成果物影響: 未実装だと g2 活性化の根拠が自己申告 1 語になる。
- **S4 検査網**: 自己整合・policy 同一性の走査を **registered catalog (3 件)** と ever-active へ広げ、
  active view のみの走査を置き換える。純増検出力 = **未 active の g2 が初めて走査対象に入る**、
  および production 層での検出 (今日は test 層のみ)。
- **(i) は実装しない。M-E を添えてユーザー再裁定へ返す** (`DW-S04`「裁定時の未見事実」)。
  併せて 択 (c) 本文の「受理集合は一切変えない」と (i) の「全 attestation が落ちる」が
  同一裁定内で矛盾している点も返す。

## 不変条件

- 受理集合を**広げない**。今日通っているものを落とさない (S1〜S4 はいずれも今日の挙動を変えない)。
- 凍結成果物の bytes を 1 byte も変えない。`FROZEN_MANIFEST` は触らない。
- `_verify_entry_calibration` の共有部分と active 権限経路は変更しない。
- 規律 2 を緩めない。既存テストの期待値を緩和・反転・skip しない。
- 活性化 (serial 前進) は行わない。

## 攻撃対象の provisional 前提 (親の暫定裁定)

- **(P1)** S2 の「既知 1 組の明示列挙つき縮小」は、裁定文「受理し続けるのは止める」の実装として
  正当である。無条件 strict は M-D により live campaign の COMMIT 監査を落とすため採らない。
- **(P2)** S3 は `DW-G04` を満たす。発火条件を満たす実 artifact = 登録済み g2 の較正 file であり、
  正例 (g2 は通る) と負例 (自己不整合な合成世代は落ちる) が両方とも実在する。
- **(P3)** S1 の seam は authority 解決に限れば受理集合を広げない。generation record が未確定でも
  「現行 1 世代しか解決しない」形なら作り直しにならない (A-07 への親の反論)。
- **(P4)** (i) を返すことは裁定の不採用ではなく `DW-S04` の差し戻しである。

## 成果物の形

コード + テスト (実装面は Codex `role=author`)、変異 matrix、insights 逐語、spool fragment
(worklog / decisions / failures)、(i) の裁定パッケージ。

## 並列分割方針

編集ファイル所有を素集合に割る。単位 A = `env_contract.py` + `env_contract_activation.py` 系
(S2/S3)、単位 B = `certified_writer_admission.py` + floor 側 (S1)。S4 のテストは各単位に同梱。
依存があるため A を先行させ、所有パス限定 patch を B へ展開する。

## 実測・受入の環境

pytest の焦点走は Pegasus login node の bounded local (`tools/run_tests.py`、`--force-dispatch` なし)。
変異 matrix は `tools/mutation_worktree.py` + runner=dispatch (`--force-dispatch` 必須)。
受入全走は `tools/dev_wave_wait.py acceptance` で lease を claim してから投入する。
