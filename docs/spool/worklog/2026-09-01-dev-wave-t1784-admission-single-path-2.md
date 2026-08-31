---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1784-admission-single-path
seq: 2
title: [T-1847] 受理記録の置き場所を driver ごとの要求 path 1 本に固定した (コード + テスト、branch worktree-dev-wave-t1784-admission-single-path、変異 matrix = baseline PASSED・2/2 期待一致・KILLED 2・SURVIVED 0・MISMATCH 0)
---

## 本文

- **依頼引数の主目的 (1) は既裁定に覆されていた。** 起動時の照合で、依頼が挙げた
  「§5 残り 9 欄の型検査 (D1000)」は本 wave 開始の約 1 時間前 (2026-09-01 00:09 JST) に
  land した D1332 で「見送る」と決着済みと判明した。D1332 の再訪条件は「記入時の型の誤りが
  実際に 1 件観測されたとき」であり、成立していない。実装せず scope 外とした。
  依頼文は archive worklog (990) の T-1784 本文をそのまま運んでおり、その本文が
  2026-08-26 以降更新されていなかったことが原因である。1115 が記録した carry stub の
  stale 化と同型で、今回は**項本文**の側で起きた。
- 依頼の (2)「active record の単一性」は T-1847 = D1050 (2026-08-26 ユーザー裁定) で
  「正となる置き場所を 1 本に固定する」と既に決着し実装待ちだった。これを実装した。
  設計判断は {{D:admission-required-path-per-driver}} と
  {{D:admission-required-path-naming-not-normative}}。
- **段 3 の 2 レンズが親 brief の事実誤りを 1 件検出した。** 親は brief に「§5 は 1 欄も未記入」と
  書いたが、現物は `n = 201、検定単位 = block` が記入済み、`実行責任者 = thawk105` が
  部分記入済みで、10 欄中 2 欄が埋まっている。D1332 の拘束は変わらない (再訪条件は記入の
  有無ではなく型の誤りの観測) が、親が添えた補助理由は事実と違っていた。裁定で訂正した。
- **段 3 の 2 レンズは path 固定の是非で割れた。** 一方は「literal path を人間が先に固定するまで
  実装するな」とし、他方は「driver ごとの 3 path は §5.1 と §10 と両立し文書改訂は不要」とした。
  親は後者を採り、前者の懸念は命名から規範語を外すことと docstring の非保証明記で閉じた。
- **段 6 レビュー A が変異事前登録の誤りを検出した。** 親が登録した「mapping の値を差し替える」
  変異は、正例 fixture が要求 path に record を置く以上 enforcement テストも落とすため、
  期待 node が不完全だった。DW-M07 の本走前再検証に従い、方向の違う 2 件
  (関門の除去 = 過小拒否側、比較の反転 = 過剰拒否側) へ差し替え、probe で観測 node を集めてから
  完全集合で本走した。
- **変異の実測。** 関門を除去した変異の失敗 node は**厳密に 1 件** (新設 enforcement テスト) で、
  単一理由性が実測で確定した。比較を反転した変異は 86 node へ波及し、受理集合を狭める wave が
  DW-M01 で要求する過剰拒否の対照として検出力を示した。後者は過剰決定なので、単独変異による
  単一理由性の証拠からは外し、広域の冗長対照として記録する。
- **段 6 レビュー B が焦点走の漏れを 3 file 検出した。** shared fixture を経由する間接 consumer
  (`test_p3_s4_loop.py` と sort / trigger 版) が親の 5 file から漏れていた。参照検索でしか
  見つからない型で、8 file へ広げて再走した。
- **scope 外の real 所見を 1 件返す。** raw record producer は admission sidecar の
  `admission_record_repository_path` を要求 path と照合せず、key の存在しか見ない。certified 経路は
  sidecar bytes 全体を検証済み record から再構築した値と byte 比較するため閉じているが、
  raw producer の証拠検証はこの欄を意味検証しない。本 wave の変更が作った欠陥ではなく
  (変更前は要求 path 自体が無く照合対象が存在しなかった)、別機構の scope なので実装せず
  {{T:b4-raw-sidecar-required-path-check}} として返す。
- 検査: 変更前 baseline 焦点 3 file = 122 passed / rc=0。変更後 焦点 5 file = 161 passed / rc=0、
  焦点 8 file = 643 passed / rc=0 (いずれも計算ノード dispatch)。
  `check_ai_provenance.py` は message 事前検査・全史監査とも rc=0。
- 子の工数: plan 1 本、consult 2 本、author 1 本、review 2 本の計 6 本。実装子は sandbox の
  scheduler socket 制約で pytest を実走できず (rc=16)、緑を 1 件も主張しなかった。
  テストの実測はすべて親が計算ノードで行った。

## 次の一手差分

### 完了

- [T-1847] 受理記録の正となる置き場所を driver ごとの要求 path 1 本に固定し、
  中央検証器へ関門を入れた。変異で単一理由性を実測した。
  remaining: none
  base: 23a76dc6756a93f4e1c3b951ea50b2ced882e8efe1c676804d3698692c03ed1a

### 更新

- [T-1784] **P1・機構側は完了**: 3 期待値の admission record 機構 (D998) に加え、
  受理記録の置き場所固定 (D1050) を実装した。**§5 残り 9 欄の型検査は D1332 で見送りと
  決着済みであり、機構側の未了項目ではない。** 残るのは §5 の全欄を実際に埋めて commit する
  作業だけで、これは本 task の scope 外 (§5.1 の解除条件と人間の指名が要る)。
  base: 441dc5d15b4cb6a1624549d5cfa4a169378bec1b4be661b9c98677e6f0c27047

### 新規

- {{T:b4-raw-sidecar-required-path-check}} **P3・新規**: raw record producer が admission sidecar の
  `admission_record_repository_path` を driver の要求 path と照合しない。key の存在しか見ないため、
  他欄を保ったまま path だけ旧値へ変えた sidecar でも `protocol_ok` を満たせる。
  certified 経路は sidecar bytes 全体を byte 比較するので閉じている。
  raw arm-source の証拠に対して同等の照合を足すか、証拠の射程を明記するに留めるかを裁定する。
