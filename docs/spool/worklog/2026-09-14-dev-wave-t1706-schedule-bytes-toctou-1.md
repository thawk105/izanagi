---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t1706-schedule-bytes-toctou
seq: 1
title: [T-1706] A/B 装置の schedule を 3 入口すべてで一度読みにし、認証した bytes を検査と集計へ束縛した (コード + テスト、branch worktree-dev-wave-t1706-schedule-bytes-toctou、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は `tools/codex_reasoning_ab.py` の 3 入口 (`supervise_pair` / `_replay_manifest` /
  `make_packets`) を「一度だけ読み、その同じ bytes から descriptor SHA と schedule を導く」形へ
  限定修正すること。**仮想リスク向けの gate・検査・台帳・一般化の追加は依頼により scope 外。**
  Codex author = D95。実装は `687a7ad076478b336f61ee5ab673335b7a60e2bd`。
- **段 3 の敵対レンズが、段 2 の起草案そのものに退行を見つけた。** 起草案は `supervise_pair` で
  source bytes を authority にしていたが、現行は run root の frozen copy を観測している。
  source へ移すと、正当な source を保存した直後に frozen を壊れた JSON へ上書きされても
  launch まで進んでしまう (現行は `cannot read JSON object` で止まる)。
  **読み回数を 1 にするという数の要件だけを見て、その 1 回が何を観測しているかを見なかった**のが
  原因で、裁定で「frozen を 1 回読み、その bytes を SHA と解析の両方に使う」へ差し替えた。
  設計判断は {{D:schedule-authenticated-bytes-one-read}}、失敗の型は
  {{F:one-read-swaps-the-observed-artifact}}。
- **もう 1 本のレンズは、負例の差し替え点と read 計数の区間を突いた。** 差し替えを helper の
  return 後に置くと helper 内部の再読を撃てず恒真な緑になり、計数を部分区間にすると replay の
  3 度目の読みを取りこぼす。裁定で差し替えを SHA 算出の境界へ、計数区間を**入口の呼び出し全体**へ
  移した。
- **変異の単一理由性 (F820) は、gate を負例から正例へ移して満たした。** 負例は拒否理由が
  過剰決定である (duplicate slot_id に加えて manifest SHA 不一致・launch SHA 不一致・unknown slot が
  重なる)。正例は入力が呼び出し中に一切変化しないので、2 回目の読みが起きても返る bytes は同一で、
  **観測できる差は read 回数だけ**になる。負例は suite に残すが単一理由の変異証拠には数えない。
  段 6 のレビュー 2 本が独立に指摘し、焦点再レビューが 6 経路すべてで静的に確認した。
- **焦点再レビューが M4 の登録先制約を先に出した。** `supervise_pair` は姉妹 helper を通らないので、
  helper 内部の再読を入れる変異は supervisor では発火しない。登録先を replay / packets に限った。
  probe 走の実測がこれと一致し、M4 は 4 node (replay と packets の正負例) を落とした。
- **段 5 の実装子は sandbox でテストを走らせられたが、1 件だけ環境由来で止まった。**
  既存 node が Unix socket の `bind()` で `PermissionError` を返し、`-x` のため 576 node が未実走に
  なった。**親環境では再現せず**、焦点走で当該 node を含めて緑だった。
- **段 6 の fix は 1 件。** 新設 2 関数が module scope の共有 fixture を consume するのに実 repo node の
  登録簿へ入っておらず、`test_real_repo_group_collection_exactly_matches_canonical_nodes` が赤に
  なった。fix 後の焦点走は **1093 passed / 4 skipped / 赤ゼロ** (fix 前は 900 passed / 1 failed)。
- **受理集合について公開する事実を裁定で明文化した。** 呼び出し中に変化しない input に対する
  受理集合は不変で、変化する input に対しては挙動が変わる — それが本修正の目的である。
  descriptor 照合の後に file が消えた場合、従来は再読の失敗で拒否したが以後は続行する。
  これは検査の弱化ではなく、認証した bytes をその後の file 状態から切り離す契約そのものである。
- **不在の主張には成り立つ範囲を併記した (F717)。** 現行 bytes を pin する live consumer は 0 件で、
  範囲は tracked 全体の path 検索・`tool_sha256` / `apparatus-pin` の key 検索・現行 sha の値検索・
  事前登録 §8.3 slice の全 field 走査である。旧装置 bytes の歴史 pin は 1 件存在し D1285 で更新対象外。
  `_validate_schedule` を通る取込み経路が 3 箇所で全数であることは 3 者が独立の方法で数えて
  一致したが、**validator を通らない動的参照や外部 consumer の不在までは保証しない。**
- **未実測として残すもの。** model・price・slot 集合を任意に変えた schedule が、launch receipt・
  attempt ledger・adjudication の後続照合まで通って certified な集計を成立させることは
  実証していない。負例が実証したのは各入口の validator 通過までである。
- **段 8 の自己改善候補 1 件は「実施しない」で閉じた。** 候補は「待ち手が出す
  `/proc/<pid>/stat` 不読の縮退行は失敗ではなく、その後も `.done` を待って正しくブロックする」
  という 1 行 (本 wave の 7 回の待ちすべてで同じ行が出て、うち 1 回は 2 分 21 秒ブロックしてから
  戻った)。収容先の `DW-C01` は単節予算 1000 bytes に対し現状 995 bytes で、
  **安全記述を削らずに収める余地が無い。** D782 に従って D730 の手順を適用したが、
  独立実例が 1 件で例外収容の 3 件に届かないため上限は引き上げない。
- Codex 子 8 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1 / focus 1)。全件
  `outcome=accepted`、model=gpt-6-astra、effort=medium。argv 誤りによる即死はゼロ。
- 成果物と生証拠 = `output/insights/2026-09-14/t1706-schedule-one-read/`。
  変異 report の全文は repo 外の job directory に残した。

## 次の一手差分

### 完了

- [T-1706] 3 入口を一度読みへ直し、認証した bytes から descriptor SHA と schedule を導くようにした。
  変異 6 件すべてが新テストで死に、焦点走は赤ゼロ。
  remaining: none
  base: 1fa35cfd52b24e9269abb63f81c3bef66077d3947a8d8ecc656a62a9d47c912c
