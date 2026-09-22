**NO-GO。must-fix は M2 の診断発火を確認せず KILLED にできる点です。C++ の変更自体を壊す攻撃は成立しませんでした。**

以下、`R` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/review`、`CC` は指定 worktree の `external/ccbench` を指します。行番号は物理行です。静的レビューであり、build・前処理・benchmark・自己試験の再実行はしていません。

**1. must-fix — M2 が診断閾値へ到達しなくても KILLED になる**

根拠: `R/probe/run_probe.py:593`、`:599`、`R/mutation-spec.json:13`、`CC/common/runner.hh` の時間経過後の quit 設定。

閾値到達の確認は `kind == 'diag'`、すなわち D1 にしかありません。M2 は別プロセスで再走するため、D1 が 1000 commit に到達した事実は M2 の到達を保証しません。

成立する経路は次です。

- D1 は閾値に到達して PASS。
- M2 は両 worker とも 1000 未満のまま通常の 1 秒終了を迎える。
- commit 中の worker が、時間終了で立った quit を旧順序の判定で読み、計数を飛ばす。
- `first_reason == 'witness'` なので M2 は KILLED。

これは旧計数の不一致を検出していますが、裁定が要求する**診断による決定的な境界試験**の成立証拠ではありません。また `witness` は欠落ファイル・stdout 不正なども含む広い理由で、harness は `C > commit_counts_` 自体も要求していません。

M2 にも閾値到達、正常終了、正常な stdout、`C == E`、`C > commit_counts_` を要求してください。診断専用の発火記録を残せば帰属はさらに明確になります。

**成果物への影響:** D1 が発火していない M2 走を、裁定 §4 の境界変異を殺した証拠として採用できます。

**2. should — 「単独変異」と「単一理由」が区別されていない**

根拠: `R/probe/selftest.py:143`、`R/probe/v3check.py:102`、`:110`、`:239`。

自己試験が確認するのは `first_reason` と `passed` だけです。たとえば正常 NewOrder frame の種別を 2 にすると、`content-txtype` に加えて Payment の表条件から `content-table` も付きます。C の構造破損も、後続の frame・witness 違反を派生させます。

したがって `146/146` は「各単独変異が期待する先頭理由で拒否された」証拠であり、「全負例が単一理由である」証拠ではありません。M4 も先頭理由は正しい一方、理由集合は単一になりません。裁定の KILLED 定義は先頭理由一致なので、これ自体による誤 kill はありません。

**成果物への影響:** 検出の帰属を「単一理由」と報告すると証拠を過大評価します。理由集合も記録・確認するか、報告を先頭理由の確認に限定すべきです。

**3. should — C1/C2 の分割内容は probe が照合していない**

根拠: `R/probe/run_probe.py:222`、`:224`。

親子関係と pin→C2 の最終差分 3 file は検査しますが、pin→C1 が header 2 file、C1→C2 が silo 1 file であることは検査しません。C1 に silo 変更を混ぜ、C2 で修正してもこの照合は通ります。

親が別途分割を検証すれば閉じます。probe の証拠だけで「単位 1 を独立して載せられる C1」を保証したとは書けません。

**成果物への影響:** 最終 C2 の TRACE=0 比較は有効でも、再利用用 C1 の内容保証が欠けます。

**規律 1 の照合**

8 本とも、直後の物理行は pin の指定行と一致しました。これは表示した原文による静的照合です。

| 候補の `#line` 所在 | 指定 N | 直後の物理行／pin の N 行目 | 判定 |
|---|---:|---|---|
| `R/files/include/tpcc.hh:30` | 27 | 空行 | 一致 |
| 同 `:63` | 56 | 空行 | 一致 |
| 同 `:119` | 110 | `if (loadAcquire(tx.quit_)) return;` | 一致 |
| 同 `:122` | 111 | `tx.result_->local_commit_counts_++;` | 一致 |
| `R/files/cc/silo/transaction.cc:660` | 635 | 空行 | 一致 |
| 同 `:692` | 658 | `memcpy((*itr).rcdptr_->body_.get_val_ptr(), (*itr).body_.get_val_ptr(),` | 一致 |
| 同 `:722` | 679 | `maxtid.absent = true;` | 一致 |
| 同 `:745` | 700 | `gc_records();` | 一致 |

- `trace.hh` の追加全体は既存 `#if TRACE` 内。新 include はありません。
- `tpcc.hh` の追加 include・setter は `#if TRACE` 内。成功後の quit 判定は TRACE=0 で残ります。
- silo の追加変数と使用箇所は TRACE 条件内で整合しています。
- `ERR` は論理行 `tpcc.hh:88`、silo `transaction.cc:106`／`:690` を維持します。include 復帰後の呼出元の行番号も変えません。
- cicada／ermia／mocc／mvto／oze／si／ss2pl／tictoc の TPC-C entrypoint、および si／mocc の transaction consumer について、新 helper の名前衝突・未使用変数・未使用引数による新規 `-Werror` 経路は静的には見つかりませんでした。実 flag での警告ゼロは未実証です。

**規律 2・v3・YCSB**

根拠: `R/files/include/tpcc.hh:110`、`:123`、`R/files/include/trace.hh:138`、`R/files/cc/silo/transaction.cc:601`、`:742`。

- silo の成功 commit は writePhase を一度通り、C を一度出し、workload の成功計数へ一度到達します。TRACE=1 では途中の quit return が消え、TRACE=0 の計数順序は保存されます。
- C の順序は `txid thid epoch tid nR nW nS nQ tx_type`。件数は出力する同じ集合のサイズ、nS/nQ は 0。表は各要素の `get_storage(storage_)` です。
- v3 と v2 は排他的分岐です。旧 v1 C helper の追加呼出しはありません。
- X は entry、UPDATE retention、DELETE retention の 3 箇所。判定条件と INSERT 除外は保存され、全 X の後に E、その直後に context clear があります。
- abort 後に context が残ること自体はあります。しかし retry は次の begin 直後に setter を通ります。begin 前の quit return は次の C を出さないため、古い種別を次の committed frame に付ける経路は見つかりませんでした。
- YCSB は setter を呼ばず初期 context=0 のため、既存 v2 の出力式を選びます。形式・出力式の bytes を変える経路は見つかりません。別実行間の取引内容まで一致するという意味ではありません。
- `orchestrator/verifier/model.py:45` が探す旧 `emit_lock_violation(` は 3 箇所とも literal `#if TRACE` 内に残ります。証拠面検出を失う攻撃は不成立です。

**probe・変異の判定順**

| 対象 | 静的判定 |
|---|---|
| D1 | commit 失敗分岐を抜けた後、旧 quit 判定の前に挿入。閾値到達時は自 thread が quit を立てる |
| M1 | 最初の v2 C で `schema`。後続診断が増えても先頭理由は維持 |
| M2 | 診断発火時は C/E 出力後に計数を飛ばすので `C > commit_counts_`。ただし所見 1 の発火確認欠落あり |
| M3 | 表 6→5 でも構造・witness は変わらず、最初の NewOrder の表対応で `content-table` |
| M4 | 種別と操作群の不一致を先に登録するため `content-txtype`。その後 `content-table` も付く |
| M5 | `#line 56` 削除で、次の復元より前にある ERR の展開行がずれる。9 TPC-C consumer の前処理比較で拒否する設計 |

anchor 出現数 1、no-op 拒否、差分保存、pristine bytes 復元と SHA-256 照合、各結果の flush は実装されています。build 失敗は ERROR、理由違いは WRONG_REASON であり、KILLED に混ぜる経路は見つかりませんでした。

`v3check` の構造→witness→内容という拒否順にも、登録 M1／M3／M4 の先頭理由を別理由へ変える必然的な欠陥は見つかりませんでした。ただし実 producer の他の異常が同時に出れば別理由になり、その場合は正しく拒否されます。

内容照合は有限の特徴検査です。たとえば全 R の表を範囲内の別番号へ置換しても、R は値域検査のみなので通り得ます。これは C4 が指定した W の特徴照合の限界であり、今回の仕様違反とは判定しません。任意の表誤記まで検出済みとは報告できません。拡張する場合は**裁定パッケージ候補**です。

**前処理・binary 比較**

根拠: `R/probe/run_probe.py:248`、`:288`、`:315`、`:354`、`:495`。

- 期待集合は TPC-C 9 source と silo／si／mocc transaction の各 4 workload、合計 12 source／21 entry。source 単位に重複排除せず、target と組にして compile database と照合します。
- argv は出力・依存生成・`-c` を除き、define／include／標準／警告／最適化を保持します。opaque な response file と `-Wp,` は拒否します。提示された構成で必要な flag を落とす具体例は見つかりませんでした。
- 展開出力は `-E -P -dD`。正規化は source/build root の置換のみで、一般の文字列・数値・`__LINE__` 展開を消しません。
- include 活性は順序付きの file 入退場 marker を比較します。行番号を捨てるため、これ自体は include 位置の一致証明ではありません。また include guard 等で再入場を生じない重複 directive までは観測しません。裁定 C1 が許す marker 方式の限界として扱うべきです。
- 無条件 `trace.hh` include の負例を 9 entry で要求する点は適切です。未実走なので検出成功は未確認です。
- source/build path は等長で、追加比較用 compile flag はありません。objdump 正規化は命令行・関数見出しの先頭アドレスだけを除き、operand・即値・分岐先・関数名を保持します。nm／strings の禁止文字列照合も通過条件へ接続されています。

**実行環境と失敗処理**

根拠: `R/probe/run_probe.py:65`、`:107`、`:189`、`:390`、`:489`、`:623`、`:708`。

必要な入力は CLI、trace 環境は子プロセスに明示設定します。repo import 用 path も設定され、親の `PYTHONPATH` や trace 環境への依存は見つかりませんでした。compiler は PATH から解決して policy の version digest と照合するため、clean env で異なる compiler が選ばれれば停止します。

bundle は verify、指定 OID は親子関係と commit 解決、最終差分は 3 file を照合します。ただし所見 3 の分割検査はありません。実際の投入 argv は資料に無いため、旧 plan の `--candidate-oid`／`--out` をそのまま使うと、現 CLI とは不一致で起動できません。

`/scr` 固定、一意な scratch、開始時・trace 前の空き容量検査、benchmark の 512 MiB/file 制限、120 秒 timeout と process group kill があります。非ゼロ終了、上限到達、例外、未実行段を部分結果の合格に変える経路は見つかりませんでした。`all_pass` は C0〜C6 の完了後だけ立ちます。C7 の親 selftest と C8 の受入は別証拠です。

## 総括

- **NO-GO。must-fix:** 所見 1。M2 自身の診断発火と、期待する向きの計数不一致を KILLED の必要条件にする。
- **should:** 所見 2 の単一理由という表現・検証範囲を訂正し、所見 3 の C1/C2 分割を親または probe で照合する。
- **攻撃不成立:** C++ の TRACE=0 漏れ、8 本の行番号復元ミス、新規未使用名、二重 C、abort/retry の種別誤帰属、X/E/clear の順序破壊、YCSB v2 出力式の変更、旧 X 証拠面の消失。
- **攻撃不成立:** build 失敗の kill 化、期待理由不一致の kill 化、復元失敗の見逃し、部分実行の `all_pass` 化。
- **未実証:** 実 toolchain の警告ゼロ、21 entry の実比較、binary 同一性、実 trace・witness、D1／M1〜M5。親の `selftest.log` は 146/146 の記録ですが、計算ノードの証拠を代替しません。

読取り用 Python 照合コマンドは、`external/ccbench` と heredoc の併用を分類不能とする `guard_bash` に拒否されました。別経路で再実行せず、通常のファイル表示で照合しました。書込みは行っていません。