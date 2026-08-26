---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1719-nproc-parity
seq: 3
title: [T-1719] 対測定 driver の環境不等価を本番へ寄せて試走を緑にし、本走 42 走を完走して [T-1563] を閉じた (コード + テスト + 計測、branch worktree-dev-wave-t1719-nproc-parity、変異 matrix = baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「作業用複製を受入 suite が要求する環境等価性まで揃え、試走を緑にしてから本走
  (6 block) を回し [T-1563] を閉じる」。台帳が挙げていた残り 2 原因のうち、
  **(ii) の見立ては機構として誤っていた**。台帳は「本番受入が通る dispatch の allowlist と
  同じ絞り込みを入れれば閉じる」と書いていたが、実測では allowlist は login 親から
  計算ノードへ「渡す値」を絞るだけで、計算ノードの子は job 環境をそのまま継承する。
  本番が緑になる実際の機構は `run_tests.py` が dispatch 前に**記録用の環境変数を除去する**
  ことだった。**(i) の C++ oracle 側は、依存が test 所有 fixture へ移った別 wave の commit で
  既に閉じており、試走の複製がそれより前だっただけ**である。

- **環境不等価は 1 つ閉じるごとに次が見える構造だった。** 試走を 8 回投入し、
  赤の内訳が毎回入れ替わった (30 → 3 → 21 → 21 → 0 で別条件停止 → 1 → 0)。
  閉じた不等価は 6 件で、いずれも {{D:study-env-parity-toward-production}} に従い本番へ寄せた —
  一時領域の場所と深さ、記録用の環境変数、arm を渡す環境変数の自己漏れ、PATH の全置換、
  interpreter を symlink 畑で前置していたこと、`/proc` 走査中に消えた process の
  2 つ目の例外型が読取失敗扱いだったこと。

- **緑の走行に一度も当たったことのない関門が 2 つ見つかった。** 単独性判定器は
  緑になった瞬間に初めて発火し、**測定対象自身の子孫 70 件を外乱と誤認**した
  (入れ子 pytest 29、C++ compile 22、daemon 化した git の自動 gc 11 ほか)。
  恒真ではなく「常に赤」の型である。帰属手段は実測で絞った —
  この計算環境の job scheduler は job ごとの cgroup を作らず全 process が同じ service cgroup を
  共有するので cgroup は使えず、`setsid` した子は自分の session を持つので session id も使えない。
  {{D:study-isolation-attribution-by-descent}} で親子関係の閉包と job 固有 path の論理和にした。

- **本走 1 回目は予算配分の欠陥で止まった。** {{F:even-split-of-an-uneven-budget-kills-the-heavy-half}}。
  arm の予算を shard へ均等に割っていたが仕事量が約 2 倍偏っており、
  3 arm すべてで重い側の配分が実測所要を下回っていた。
  {{D:study-shard-budget-proportional}} で比例配分へ変え、相対余裕が両 shard で一致した。

- **本走 2〜6 回目は、毎回別の 1 件だけの非帰属フレークで止まった。**
  到達走数は 0 → 5 → 3 → 13 → 7、実測は測定走 33 回中 5 件 = 約 15%/走。
  **ユーザーが「並列数を上げたら落ちるフレークは、そのフレークが間違っているのでは」と
  指摘したことで方針が変わった。** 落ちた検査を読み直すと、いずれも守りたい性質ではなく
  環境の偶然を主張していた ({{F:tests-that-assert-the-environment-not-the-property}})。
  親は当初これを「非帰属だから環境の問題」で止めており、
  **repo 自身が同じ族を [テスト代表性] としてテスト側の欠陥に分類していることへ立ち返れていなかった。**
  フレーク登録による回避はせず、5 件を性質を保ったまま直した。

- **ただし個別修正だけでは閉じないことも実測した。** 受入 suite を静的走査すると、
  小さい絶対時間・順序・識別子の一致を主張する候補は 244 箇所 / 68 file あった
  (確定的で問題ない箇所を含む上限値)。個別修正と並行して
  {{D:study-bounded-retry-of-red-cells}} を入れ、記録値は緑の走行からだけ取るという性質を
  保ったまま測定側を頑健化した。この機構は既存検証器の暗黙の時系列前提と矛盾し
  ({{F:a-retry-feature-contradicted-a-validator-time-assumption}})、fix 子が
  「test 側だけでは解消不能」と判断して**実装を変えずに報告して止まった**ことで表に出た。

- **この赤は測定固有ではない。** `default_test_jobs` は計算ノードで cap 無しに全コア数を返すので、
  **本番受入も同じ飽和状態で走る**。実際、同時間帯に別 wave が受入を 4 回投げて 1 回だけ緑を得ており、
  その実測値を引き継いで F273 へ再発追記した (彼らの緑の受領証が tested_tip を pin していたため
  彼ら自身の land には入らなかった)。

- **本走は 7 回目で完走した。** 42 走すべて緑、測り直し 0 回、受領証の不変条件 13 項目すべて true。
  6 block すべてで対比の符号が一致した。arm 内のばらつき (最大 2.8 秒) は
  arm 間の差 (15〜23 秒) より一桁小さい。

  | 並列数 | 平均所要 | 6 block の範囲 |
  |---|---|---|
  | 16 | 203.14 秒 | 202.87 - 203.37 |
  | 32 | 210.65 秒 | 209.60 - 211.02 |
  | 48 | 226.22 秒 | 224.41 - 227.16 |

  主対比 (32 対 48) は平均 **-15.58 秒** (6 block すべて負、-16.38 〜 -14.81)、
  副対比 (16 対 48) は平均 **-23.09 秒** (6 block すべて負、-24.05 〜 -21.54)。
  **worker 数を増やすほど遅い**、という向きで一貫している。

- **射程は受領証に明示した。** 既定 worker 数の変更根拠には使わない (除外 estimand)。
  既知の非等価 3 件 (HOME/XDG が走ごとに cold isolated、複製が scratch filesystem 上、
  2 shard が同一ノードで直列かつ shard 順は counterbalance されない) があるため、
  **内部比較としては妥当だが本番の絶対所要への外挿には使えない**。受領証自身が
  `absolute_wall_extrapolation` と `internal_comparison_scope` の 2 文でこれを分けている。

- **親の誤りを 2 件記録した。** 1 つは他 session へ台帳の F 番号を記憶から伝え、
  行番号での照合を後回しにして 2 点誤った案内をしたこと
  ({{F:relayed-a-ledger-number-from-memory-without-checking-lines}})。相手が junit の本文まで
  読んで反証を返して直った。もう 1 つは試走と変異 matrix を同時に走らせ、
  変異側の dispatch 成果物が canonical repo の出力 directory へ書かれて
  試走の「元の repo が変わっていないこと」の検査に当たったこと。

- **待ち手が空で即座に戻る事象を 3 回観測した** (焦点走・fix 子・変異 matrix)。
  いずれも producer は生存しており、pid を確認して張り直せば正常に進んだ。
  気付かずに完了扱いすると、走っていない結果を読むことになる。

- **変異は 5 回投げた。** 1 回目は過剰決定で MISMATCH、2 回目は変異自体が測定装置
  (計算ノードへの投入経路) を壊して test が 1 件も走らず、3 回目で全 12 件が完走、
  4 回目で全件一致、5 回目を最終 tip で再走して確定した。
  **測定装置を壊す変異は結果を出さない**ので、実効 gate へ再照準する必要がある。

## 次の一手差分

### 完了

- [T-1719] 対測定 driver の環境不等価 6 件を本番へ寄せて閉じ、試走を
  `status=complete` にした。本走 42 走も完走し受領証を得た。
  remaining: none
  base: 0fcdb477b760d3ae058a67590670811d44db951a2c253c8619a0059be5755eb3

- [T-1563] 本走 42 走を完走し、worker 数と受入 shard 所要の対測定を得た。
  16 = 203.14 秒 / 32 = 210.65 秒 / 48 = 226.22 秒 (各 6 block 平均)、
  主対比 32 対 48 = -15.58 秒、副対比 16 対 48 = -23.09 秒、6 block すべて符号一致。
  **既定 worker 数の再裁定はユーザー手番**であり、D103 決定 (3) と D532 のどの範囲を
  supersede するのかを併せて諮る必要がある点は変わらない。
  remaining: none
  base: cea207c6d38c636c988202a9bd0aefe7886f3ccda7b1fe357512c5f0e2f7ed31

### 新規

- {{T:overspecified-test-family-triage}} **P1・新規**: 受入 suite の
  「環境の偶然を assert する検査」族を分類して是正する。本 wave の静的走査では
  小さい絶対時間・順序・識別子の一致を主張する候補が 244 箇所 / 68 file あり
  (確定的で問題ない箇所を含む上限値)、実測フレーク率は本番の動作点で約 15%/走だった。
  本 wave は観測した 5 件だけを直した。**族全体の是正には所有 wave が要る。**
  分類の観点は {{F:tests-that-assert-the-environment-not-the-property}} に記録した。

- {{T:study-absolute-wall-extrapolation}} **P2・新規**: 対測定の既知非等価 3 件
  (HOME/XDG の cold isolation、複製が scratch filesystem 上、shard の直列実行) を
  埋めて本番の絶対所要へ外挿できるようにするか、外挿しない前提で運用するかを決める。
  現行の受領証は内部比較の妥当性と外挿不可を 2 文に分けて明示している。
