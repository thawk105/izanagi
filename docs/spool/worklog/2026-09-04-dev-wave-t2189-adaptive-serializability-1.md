---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2189-adaptive-serializability
seq: 1
title: [T-2189] 調整済み adaptive backoff の直列性を認証した — 24 trace・1.46 億 txn・anomaly ゼロ。ただし wave 中に verifier の意味論が変わり 2 度認証した (コード + テスト + insight、branch worktree-dev-wave-t2189-adaptive-serializability、変異 8/8 が事前登録どおり)
---

## 本文

- **ユーザー依頼:** 調整済み adaptive backoff の直列性を trace-enabled 走行 + verifier で通す。
  性能計測用ビルドは一切変えない。anomaly は即 reject。verifier は「どの trx 間のどの依存で
  G2 が出たか」を構造化して返す。1 ノード直列で流さず条件を割って複数ノードへ投入する。
- **結果は `output/insights/2026-09-04_t2189-adaptive-serializability-certification.md`。**
  24 件すべて certified、anomaly 0。txn 145,904,299 / 辺 2,275,338,484 / abort 189,132,818。
- **同じ認証を 2 度行った。** 1 度目 (attempt-1、24 ノード、job 971189 / 972815-972837) の直後に
  main へ verifier の意味論変更が着地した。「証明面を持たない protocol が certified を
  名乗れないようにする」と「証明面の判定を build の source snapshot へ束縛する」の 2 件で、
  10 module のうち 6 つが変わった。規律 7 の「意味論の版の変更」に当たるため、
  新版で取り直した (attempt-2、job 977197 / 977221-977243)。
  **attempt-1 は取り消していない** — その版における事実として有効で、identity を事前固定して
  あるため参照可能である。**生 trace を保持していたので走行の再現は不要だった。**
- **親の裁定自身に欠陥があった。** 非空振り条件の abort witness に verifier の
  `abort_reasons` を選んだが、その `A` 行は段 8a の characterization 専用計装 patch だけが
  emit し、素の trace-enabled build は出さない。実 emitter 由来の r8 fixture を通して
  `abort_reasons = {}` を実測し確定した。**このままなら実走 24 件すべてが reject されていた。**
  witness を stdout の `abort_counts_` (pipeline が「verify 中に abort-path が実行された証拠」と
  定義するもの) へ差し替えた。着想は正しく、field の選択だけが誤っていた。
- **段 3・段 6 の敵対検査が実のある欠陥を出した。** 段 3 で 6 件 + 4 件、段 6 で 7 件 + 4 件。
  うち緩い方向 (偽の認証を作れる型) が 2 件あった — group receipt が未検証の status-only JSON を
  certified と数えられたことと、0 件や部分成功でも receipt を作れたことである。
- **自分の検査が機構を通っていなかった箇所が 1 件。** 並行 publish の予約機構は、先行ケース用の
  test double が復元されずに残っていたため一度も実行されていなかった。テストは緑に見えていた。
  `entered_real_implementation False` を子が実測して判明した。
- **group の同一性束縛を binary bytes からソース内容へ移した。** 24 件が同一 binary SHA を
  持つ要求は、cache key に job ごとの admission receipt が入り 24 台が独立にビルドする以上、
  原理的に成立しない (実測でも 24 種すべて別)。一方 `source_bytes_sha256` と
  `genome_sha256` は 24 件で 1 種だった。束縛の対象を非意味的な代理から主張そのものへ移した。
- **セッション異常 (自分の欠陥) 3 件。**
  (1) 受入走行中に worktree へ docs を書き、走行前後の同一性要求を壊しかけた。退避して復元した。
  (2) 新 verifier での再検証を login node で走らせた。200 万 txn の検査は計算ノードの仕事で、
  8 時間 CPU 0.1% で停滞し成果ゼロで停止させた。
  (3) 完走した job を `qstat` で待つ待ち手を書いた。`qstat` は終了後も成功を返し続け、
  2 時間半空回りした。結果ファイルを見る方式へ直した。
- **取り込みで 2 度同じ関門に当たった。** main 側と wave 側が `test_ccbench_spawn_sites.py` を
  両方変更しており、自動 merge の結果が両親のどちらとも異なるため provenance が Codex
  role=author を要求する。しかし **merge が staged の間は Codex 子を起動できない**
  (authority docs が authority commit と異なり子が fail-closed する)。merge ではこの file を
  main 側と byte 一致にし、wave 側の entry は clean な木で当て直す順に組み替えて抜けた。
- Codex の利用枠が段 6 の途中で尽き、5 日待った。親が代筆せず、従量経路へも切り替えなかった。

## 次の一手差分

### 完了

- [T-2189] 調整済み adaptive backoff の直列性を認証した。24 trace すべてで anomaly ゼロ。
  attempt-2 (現行 verifier) が現行コードでの認証であり、attempt-1 は旧版における事実として残す。
  remaining: none
  base: eeb745fd64db7d5d49c7050f1ff9254c4ed98f1fe6b7ad31c3317d5a67875f6c

### 新規

- {{T:t2189-multi-env-certification}} **P3・新規**: 本認証は Pegasus 48 コアの単一環境である。
  別環境での認証は未実施。環境を跨ぐ転移は主張していない。
