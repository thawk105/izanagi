## レビュー範囲

対象は runner v3（SHA-256 `8a44e23875655d24d515d56b9d334e93b2f7a3b6f8646e85d969060022036ce7`）。指定 diff をメモリ上で v2 に適用し、v3 と一致することを確認した。

以下の「成立」は**不具合または検査の弱さを指摘する攻撃が成立した**という意味。import・署名確認、`prerun --help`、verifier 9 ファイルの hash 照合は実行した。selftest・build・計算ノード経路は今回実行していない。

## must-fix

- [must-fix] verify_phase_runner.py:930 — bench 失敗後に同じ反復の bench を再生成する — 成立 — L930–936、再開側 L900–901、事前登録 §5 L327–328。
  `range(attempt, 3)` により、`bench_failed` の直後に attempt-2 を実行する。事前登録は「bench を再生成しない」と明記している。
  **本走で bench が失敗すると、禁止された追加の自己シード process／trace を生成し、その追加 verdict が集計対象になる。**
  author 報告 L22 は矛盾を開示しているが、提示された P1〜P9 に例外裁定はない。失敗記録を残すだけでは実行規則との不一致は解消しない。

- [must-fix] verify_phase_runner.py:983 — identity 不一致の失敗 record を集計が読み落とす — 成立 — 書出し L977–983、読取り L1172–1185、件数算出 L1048・1083。
  `verify` の identity 不一致は `<job>/result.json` に書くが、collector は `<job>/rep-*/attempt-*/result.json` だけを読む。job ledger についても `execution_status` を判定へ反映しない。
  **本走の identity 不一致が規約不適合件数から脱落し、その後 `--resume` で正常な反復を揃えると、失敗 record が残ったまま pass になり得る。**
  失敗 record を規約不適合の開示・判定へ接続する必要がある。selftest の identity 負例は既存 slot 内の変更なので、この出力位置の不一致を検出しない。

## should

- [should] verify_phase_runner.py:1593 — 「6 s 超過なら 10 s を実行しない」を実行ループで検査していない — 成立 — L1584–1596、実際の分岐 L864–875。
  テスト自身が `skipped_calibration(..., 10, ...)` を呼び、その constructor が返す `not_run` を確認している。実際の `if reason:` を壊しても、このケースは落ちない。
  L1424 の「後続行を除外」も入力が最初から2行で、超過が最後の行なので除外を検査できていない。
  また L1373–1374・1381 の「校正 anomaly」は L1354 の `good()`、つまり `phase='verify'` の fixture を使っている。

- [should] verify_phase_runner.py:1407 — 期待値の自己参照と複数の拒否理由が負例の検出力を弱める — 成立 — L1407–1408、L1645–1649、L1662–1665。
  configure の期待 define を実装と同じ `defines(c)` から作るため、例えば TRACE を別の define に置換しても個数と包含の検査は通る。
  preservation 負例は既に wall=2000 で不適格なので、保全条件を外しても通る。
  bundle mismatch 負例は同時に before/after drift でもあり、期待 identity 照合を削除しても drift 検査だけで通る。L1363 の spy は実関数へ委譲しており、固定値 stub ではない。

- [should] verify_phase_runner.py:715 — `verify --resume` の照合に `in_judgment_set` がない — 成立 — L715–722、対照として reverify の L734–737。
  `target`・`gate`・`bundle_sha256` と期待 identity は照合するが、`in_judgment_set=false` の既存 record を再開入口で拒否しない。
  最終 collector は混入を拒否するため誤 pass には直結しないが、不正な既存集合を受け入れたまま残りの本走を進められる。再開前照合へ追加すべき。

- [should] verify_phase_runner.py:613 — setup+hydrate+build の2400秒は hard deadline ではない — 成立 — L601–614、`s3_mocc_lock_coverage.py:101`・`:224`。
  2400秒との比較は全処理終了後だけ。hydrate 120秒、依存の configure/build/install 各300秒、runner configure 各300秒、warmup 1200秒、build 900秒が個別に動く。
  これらの許容時間の和は3600秒を超えるため、試走の1時間予約に対する上限保証にはならない。
  D2160 の約31秒と warmup 数分という見込みなら収まるが、静的検査から完走を保証できない。これは v2 から継承した制約である。

## 実行経路・bindings・schema の照合

**項目1の import／署名不整合攻撃は不成立。** `helpers()` 全13群を import でき、指定された属性も実在した。`quarantine` は指定 keyword を受け取り4要素を返す契約で、先頭要素の `passed` を確認する呼出しも一致する。`checkout`・`applied`・`resolve_evidence`・`_prepare_dependencies` の位置引数／keyword に不一致はない。

**項目2の試走経路破損攻撃は不成立。** L558–615 は setup → hydrate → checkout → applied → quarantine → identity前 → warmup/build → identity後。L831–832 の `prerun` 分岐から bench／verifier は呼ばれない。ExitStack を閉じて scratch を削除し、通常の例外では `failure_reason` と `prerun.json` を残す。identity drift は rc=1。既存 output は L754 の `mkdir` で拒否するため上書きしない。ただし予約段階の失敗では新しい試走 record は作られない。

launcher の argv は `prerun --help` と一致する。`--ruling` は任意、`--bundle` は不要、cache／scratch／output／gate は受理される。generic dispatch の clean env と runner の明示 env に、静的に確認できる衝突はない。

**項目3の指定された bindings 欠落攻撃は不成立。**

| 記録 | runner の格納箇所 |
|---|---|
| pin、patch SHA-256、verifier各ファイル SHA-256 | L562–565 |
| toolchain path／version hash、compiler実体／version | L571–576 |
| 述語逐語、genome flags／canonical | L579–582 |
| configure define／warmup・build argv | L567、L602–606 |
| build前後 SourceEvidence 9 field | L542–546、L597・610 |
| binary SHA-256 | L607–608 |

これらは成功した `prerun.json` と通常の `result.json` に入る。reverify は binary／configure の原本情報を引き継ぐ。verifier 9ファイルは提示された hash 一覧と全件一致した。

ただし、**これだけで§12の発効束全体は完成しない**。runner は `pin.CURRENT_PIN` と gitlink の一致を記録・照合せず、patch／runner の raw bytes 保存、承認情報、node種類、保全先空き容量、校正予約の根拠も単独では揃えない。親の事前照合・保存物・裁定パッケージで補完する項目であり、新しい機械 gate が必須だとは解釈しない。

**項目4は一部成立。** `REQUIRED` と `new_result` の key は整合し、`target`／`gate`／`bundle_sha256`／`in_judgment_set` が存在する。通常 record の key typo で常に `undetermined` になる経路は見つからなかった。問題は上記の失敗 record の読取り位置と resume の欠落である。

## selftest 被覆の判定

親ログは `ok` が120件、L131–132 が `PASS 120/120 cases`・`rc=0`。author 報告 L11 と一致する。ただし120件を同数の独立した失敗検出能力とは扱えない。

| 要求ケース | 静的な被覆評価 |
|---|---|
| 1800.0／1800.001 | L1346–1350 の正負例あり |
| 6秒超過→10秒 not_run | helper単体のみ。実行分岐の被覆不足 |
| 共通部分が空 | L1611–1616。理由文字列まで確認 |
| 10→6、6でも予算超過 | L1597–1610。実 `select_extime` を確認 |
| 校正 anomaly→失格 | ケースあり。ただし上記の phase 誤設定 |
| 校正 rc=3→失格 | L1617–1622。正しい calibration fixture |
| 校正 certified=false→pass | L1623–1627。開示件数も確認 |
| 校正未完走→pass＋開示 | L1628–1633、collector L1469–1471 |
| 本走未完走／重複／identity不一致 | L1375–1389。ただし実際の失敗出力位置は未被覆 |
| `in_judgment_set=false` | L1564–1568、L1634–1644 |
| workload gate／述語逐語／flags | L1574–1580。凍結JSONとの外部照合あり |
| bundle schema | L1670–1679 に6種類の拒否例。ただしidentity負例は理由が重複 |
| `--extimes` 拒否 | L1692–1699。変換関数の正負例あり |

## timeout と v2 回帰

verifier timeout は通常の校正／本走 L690、reverify L856、保全済み trace の再開 L919 の全経路で **3600秒**。bench は L664 の **120秒**。1800秒は適格判定境界であり、kill境界と混同していない。

`preserve`・`restore`・`validate_file`・`timed_process`・`run_verifier` は v2 と AST が同一。restore は圧縮保存物の SHA-256／bytes を L513、展開後原本を L526 で照合する。重複manifest拒否、再検証1回制限、原本result hash／bench／preservation の照合も維持されている。これらの改版による破損攻撃は不成立。ただし、v2の bench 再生成契約をB-8へそのまま持ち込んだ点は must-fix のとおり。

## 総括

**NO-GO：runner v3 を校正・本走まで含めて受け入れるには修正が必要。** 指定 `prerun` の静的経路には投入を妨げる不整合を見つけていないが、計算ノードでの完走は未検証。

**must-fix 2件／should 4件／nit 0件。**

| 攻撃項目 | 成立／不成立 | 結果 |
|---|---|---|
| 1 import・署名 | 不成立 | 13群の実在と呼出し形が整合 |
| 2 prerun経路・argv | 不成立 | 分岐・cleanup・rc・launcherが整合 |
| 3 bindings | 不成立 | 指定された記録項目あり。発効束の外部補完は必要 |
| 4 record schema | 成立 | identity失敗recordの読落とし、resume照合漏れ |
| 5 selftest | 成立 | 自己参照、拒否理由の重複、実行分岐未被覆 |
| 6 timeout・時限 | 成立 | verifier値は適合。2400秒は事後検査のみ |
| 7 v2残骸 | 成立（非動作箇所のみ） | 下記のコメント・負例・fixture名 |
| 8 regression | 成立（B-8適合性） | 保全／復元は維持。bench再生成が新規則と衝突 |

項目7の grep 結果：

- `CANDIDATES`、`--candidate`、`silo-backoff-fixed.patch`、旧PIN、旧SCHEMA、独立した数値 `600`、tuple `(3, 6, 10)`：**無し**。
- `BACKOFF_FIXED`：L1408、禁止defineの負例。
- `3,6,10`：L343、共有chooserの説明。L1693、拒否入力。
- `fixed-5`：L1444・1456・1515、selftestのディレクトリ名。
- 部分文字列 `600` は `3600` に一致：L690・856・919・1359・1448。旧600秒閾値の残存ではない。