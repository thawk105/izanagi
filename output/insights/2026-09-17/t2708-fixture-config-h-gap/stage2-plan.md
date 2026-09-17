## 忠実性の増分の定義と P1・P2 の反証

以下、参照名を短縮する。

- `T` = `orchestrator/tests/test_s8b_oracle_driver.py`
- `H` = `orchestrator/campaign/s8b_holdout_freeze.py`
- `M` = `orchestrator/campaign/t080_freeze_migration.py`
- `G` = `orchestrator/campaign/s8b_oracle_driver.py`

**忠実性は「実 repo 全体との一致」ではなく、fixture の構築規則で射影した期待集合との差で定義する。** また、index 集合と production scan 集合を分ける。

期待集合は、構築時点の次の集合から求める。

| 構成要素 | 期待集合への扱い・アンカー |
|---|---|
| `orchestrator/` | `T:1380` の copytree が複製する実体。全階層で `__pycache__` と `*.pyc` を除く。tracked だけでなく untracked／ignored 実体もコピーするため、実 repo の `ls-files` と単純には一致しない |
| `output/` | `T:794` の tracked regular ＋非 ignored untracked regular。`T:830` の receipt／draft 2 path を除く |
| basis file | `T:1431` の historical blob と `T:1433` の現行 operational file を追加・上書きする。path 集合の追加と bytes の意図的差を別記する |
| submodule | `T:1443` で生成される `.gitmodules` と gitlink。scan 集合では gitlink 自体を除き、`T:1450` で checkout した **known pin** の regular file 集合を加える |
| scan 除外 | 上記を production の regular-file 規則で正規化し、既定 scan では `H:45,608` の `output/s8b-freeze/` を除く |

比較対象を次のようにする。

1. fixture の `git ls-files -s -z`：path・mode 集合を比較する。symlink と gitlink を通常ファイルに混ぜない。
2. fixture の `H:370 enumerate_repository_files(root)`：tracked regular、可視 untracked regular、pin 済み ccbench regular の集合を比較する。
3. `search_repository` が除外適用後に読む集合：欠落・余剰の双方を出す。

A＝現行、B＝取り込み後として、期待する主結果は次である。

- `B − A = {orchestrator/tests/fixtures/sort_swo_masstree/config.h}`
- `A − B = ∅`
- 射影した期待集合に対する欠落が 1 件減る。
- `search.file_count` が 1 増える。
- 既存 file の bytes・mode、submodule pin は変わらない。

**P1：現在の ignore 起因の 1 件説を支持するが、419 件の説明だけでは集合全体の一致は証明できない。**

静的確認では、指定範囲の tracked-and-ignored は 419 件、`orchestrator/` 側は `config.h` だけだった。隠しファイルと ignored path を含めた探索では、`output/` 配下に `.gitignore` は見つからず、`orchestrator/` には次の 2 件があった。

- `orchestrator/tests/fixtures/sort_swo_masstree/.gitignore:8`：`/config.h`
- 同 `doc/.gitignore:1`：TeX 生成物等の規則。今回、追加の tracked-and-ignored は検出されなかった。

したがって、親が確認した root `.gitignore:25` 由来の 418 件について、複製先の別 `.gitignore` が再び隠すという具体的反証はない。ただし、次の経路は 419 件の集計だけでは覆えない。

- `T:1382` の名前による copy 除外は Git の tracked 状態に関係しない。
- `orchestrator/` の copytree は Git 可視集合を入力にしていない。ignored 実体の持込みや、既定の symlink dereference が集合・種類を変えうる。
- `T:827` は output のコピー集合を保証するが、その後の新規 index 化まで保証しない。将来、可視な nested `.gitignore` が加われば同型の穴ができる。
- basis 復元は path を追加・上書きする。その path が ignore 規則に一致すれば同型の脱落がありうる。
- submodule 内部は clone 済み index を使うため、superproject の `add -A` による同型脱落ではない。一方、実 repo の現在の submodule checkout と fixture の known pin は区別する必要がある。

**P2：現在の `config.h` の追加による判定変更の反証なし。report 全体の同一性とは区別する。**

`config.h` は 10,448 bytes。`H:64` の三軸キーの文字列はすべて 0 件だった。`H:68` の検索式はこれらの文字列を必須とするため、軸別 hit・conjunction・positive control を増やさない。

束縛経路は次のとおり。

| 経路 | 判定・比較するもの |
|---|---|
| `H:714 _assert_search_pass` | holdout conjunction が空、positive control が正。file 数を比較しない |
| `H:1029 verify_document` | live scan を実行して pass を確認。`H:1049` は**保存済み** count の型・非負性検査であり、live count との一致検査ではない |
| `M:1709 _draft_reconstruct_holdout` | projected document hash と semantic scan hash。`M:1741` の hash 入力に `search` は含まれない |
| `M:1750 _rerun_draft_reconstruction` | reconstruction を再実行して一致比較するが、live file 集合・count は reconstruction に入らない |
| `M:1889 _assert_receipt_does_not_pollute_scan` | scan と `_assert_search_pass`。file 集合・count の比較なし |
| `M:2191 _verify_holdout_live_scan` | candidate 集合、match convention、candidate ID、expressions、pass 条件。file 集合・count の比較なし |
| `M:1427,1461` | projected document／basis 由来 field を再導出。live file 集合・count は比較しない |

known-axes の候補探索も `s1_known_axes_freeze.py:350,385,471` の `output/campaigns/` glob であり、この `config.h` は候補にならない。

ただし、取り込みを basis commit 前に行えば **fixture の basis tree／commit OID は変わる**。`M:1967` の `migration_basis_commit` を含む fixture receipt の bytes 同一まで主張してはならない。

## probe 設計 (測る量・手順・N・統計量・file:line)

**fixture は 1 回だけ構築すればよい。** `T:1364` を `issue_receipt=False` で呼び、同じ working tree の index 上の可視性だけを切り替える。取り込み有無で 2 回 copytree する必要はない。

1. **構築前の記録**
   - source HEAD、Git／Python、環境、submodule pin、対象 path 集合を記録する。
   - `config.h` の bytes hash・size と、コピー対象の `.gitignore` を記録する。
   - 構築前後で source snapshot が変わっていないことを確認する。HEAD 同一だけでは untracked／working bytes の不変証明にならない。

2. **現行 fixture を 1 回構築**
   - `T:1364 _build_t080_stub_free_e2e_repo(tmp, issue_receipt=False)`。
   - `T:1460` で発行前に戻る。
   - A の index を fixture 外に保存する。
   - 構築所要は参考値として記録するが、採否の A/B 根拠にはしない。

3. **取り込み操作を測る**
   - 実 repo で `git ls-files -z -ci --exclude-standard -- orchestrator output`。
   - その NUL 出力を fixture の `git add -f --pathspec-from-file=- --pathspec-file-nul` に渡す。
   - `perf_counter_ns` で「列挙」「add」「一連の wall」をそれぞれ測る。
   - `_run_git` (`T:380`) は text 出力を `.strip()` するので、この NUL 転送には使わない。bytes の subprocess と `T:369` の sanitized Git 環境を使う。
   - 各反復前に A の index を復元する。復元時間は取り込み時間に含めない。
   - hard-code 案も比較するなら、同じ A index を起点に単一 path の `add -f` を交互に測る。

   **P3 の重要な修正：一般解が処理するのは 1 path ではなく現在 419 path。** 418 件は集合増分を生まなくても、source 列挙・fixture 側の確認・index 更新の費用がある。「add 1 file だから ms 級」とは推定できない。

4. **scan の対比較**
   - A：`config.h` が index にない状態。
   - B：取り込み後。集合差が対象 1 件だけであることを確認する。
   - 切替は fixture の index のみ。file bytes は変更・削除しない。
   - 各状態で `H:592 search_repository(root)` を `files=None` のまま呼ぶ。列挙・read・decode・prefilter を含めて測る。
   - index 切替、集合検査、JSON 保存は timed 区間外とする。
   - `GIT_INDEX_FILE` をプロセス全体に設定する方法は避ける。`H:383` の submodule Git 列挙にも同じ index 指定が伝播するため。
   - semantic report と `M:1741` の hash が等しく、report 差が期待した `file_count +1` に限られることを確認する。

5. **反復数と統計量**
   - 事前固定の warm-up 2 対、計測 **N=20 対**を目安とする。
   - 対の順序は AB、BA を交互にして先行効果を均す。
   - A／B 各中央値、各対の `B−A`、その中央値・四分位範囲・最小最大、正負の対数、生データを返す。
   - 主比較は「中央値の差」ではなく**対の差の中央値**。
   - ノイズに埋もれた場合は「増分を分離できなかった」とする。負の差を 0 に丸めたり、ms 級と断定したりしない。
   - 初回取り込みは object が未作成の可能性があり、反復後は温まる。初回値は別記し、単発の採否根拠にしない。

**13 scan の静的内訳は次のとおり。正常な default 発行・検証経路の回数である。**

| 呼出し | 内訳 | 回数 |
|---|---|---:|
| draft (`T:1571`) | reconstruction の明示 scan `M:1727`、verifier 内 `H:1029`、pollute 検査 `M:1985` | 3 |
| 明示 validate (`T:1574`) | rerun reconstruction `M:2022` の 2 回、pollute 検査 `M:2023` | 3 |
| finalize (`T:1575`) | 内部 validate `M:2035` の 3 回、pollute 検査 `M:2048` | 4 |
| verify (`T:1600`) | `M:2343 → M:2201` | 1 |
| gate (`T:1601`) | `G:599 → G:169` の verify、`G:299 → M:2490` の adapter | 2 |
| 合計 | 発行部分 10、後続 verify／gate 3 | **13** |

`issue_receipt=False` の構築自体はこの 13 scan を実行しない。

所要モデルは `取り込み操作 + 13 × scan 増分` として提示できるが、**発行 wall の実測値ではない**。draft／receipt の有無による scan 入力差、commit 処理等の増分を含まない。`H:558` の prefilter と call-local memo がある一方、`H:618` の read／decode は残るため、10 KB から時間を直接換算しない。

fixture 全体の A/B を行わない判断は、本題の微小増分を分離する目的には妥当。ただし全体 wall の不変証明にはならない。実走場所は、提示された共通規律に従い**計算ノード**とする。brief の login node 指定はそのまま実行条件に採用しない。

## probe の実装形 (import 可否・模擬差)

**静的には pytest 外から直接呼べる。実 import の成功は未確認。**

- `T:1364` は通常の Python 関数で、pytest fixture 引数を要求しない。
- `T:31` のため pytest パッケージ自体は必要。
- `T:49–59` が import 時に tempfile 環境を検査する。`TMPDIR`・`TEMP`・`TMP` を import **前**に repo 外の書込可能領域へ設定する。
- `tempfile.gettempdir()` の選定には書込可能性確認が伴いうる。本 read-only 段では実 import しない。
- `T:943–961` は xdist 環境変数があると shared base に参加する。standalone probe では `PYTEST_XDIST_TESTRUNUID` を外す。
- `T:5` の `in_sealed_fixture_process` は `s8b_v2_freeze_fixture.py:92` で decorator として定義され、fork は wrapper 呼出し時。同 builder には付いていない。
- `T:61–108` と直接参照した test module 群に、builder 呼出しを conftest fixture の実行へ依存させる経路は確認できなかった。pytest の autouse fixture は通常 import では実行されない。

配置は author が一時的に `tools/<probe>.py` を作り、親が実走前に **job dir の `tools/<probe>.py`** へ退避する。cwd は worktree root、起動は指定どおり `python3 -B -m tools.<probe>` とする。

ただし、退避しただけではその module は見つからない。job dir を `PYTHONPATH` に追加し、`tools.<probe>` の解決先が退避先であることを実走前に確認する。tmp、結果、index 保存物は source repo の外に置く。

import が失敗した場合、copytree＋init＋add の模擬へ黙って切り替えない。模擬で省かれるものは少なくとも basis 復元、submodule pin、output の厳密な可視性、Git 環境、history 検査である。F29 に対応する報告として、**実経路／模擬した部分／省いた部分／観測から言えないこと**を明記する。F29 本文は今回の射影にはなく、逐語照合は未実施。

## 採用時の最小差分と変異事前登録案

変更位置は **`T:1451 add -A` の直後、`T:1452 basis commit` の前**。本 wave では変更しない。

| 案 | 利点 | 制約 |
|---|---|---|
| hard-code：対象 path の `add -f` を 1 行追加 | 今回の 1 件を最小差分で修復。コピー済み bytes を使い、source を読み直さない | 将来の同型 path は救わない |
| 一般解：source の `ls-files -ci` を force-add | 同じ構築対象内の複数欠落を扱える | 現在 419 path を処理。NUL 転送、空集合、除外・非コピー path の扱いが必要で、文字どおり 1 行の変更ではない |

**P4 の無条件な一般解には反証がある。** `ls-files -ci -- orchestrator output` は、「fixture に実際にコピーされた集合」ではない。receipt／draft は `T:830` で除外され、`*.pyc` 等は `T:1382` で除外される。将来これらが tracked-and-ignored になれば、素通し force-add は存在しない path を指定しうる。現在それが発生したという証拠ではなく、一般解の成立条件の欠落である。

一般解を採るなら、入力を構築時 snapshot の regular-file 集合に対応させ、明示的な非コピー対象を区別する必要がある。「存在しないものを全部黙って捨てる」方式はコピー失敗まで隠すため避ける。追加の一般化 helper は本プランに含めない。

D2086 の proto 実装は main 未採用なので、現行 builder が構築ごとに source を読むこと自体は矛盾しない。ただし、将来 proto に組み込む際、**各 key の add 直前に実 repo を再列挙すると proto の session snapshot と世代がずれる**。一般解では ignore 対象の集合も proto 構築時に捕捉する必要がある。hard-code はこの追加 snapshot 状態を要しない。

採用 wave の変異事前登録案：

- アンカー：取り込み箇所 `T:1451` と、可視性検査群 `T:1633` の近傍。
- 実 builder の未発行 fixture を使い、対象 path が regular index entry と `enumerate_repository_files` の双方に含まれること、source と bytes が一致することを検査する。
- 変異：追加した取り込み処理を削除する。
- 期待結果：対象 path の membership assert で赤。現行の「scan 判定は通る」だけでは変異を殺せない。
- 一般解を選ぶ場合は、任意の tracked-and-ignored path を持つ**合成 source**も用意し、config.h だけの hard-code への退化を検出する。実 repo の tracked file は変異しない。
- scanner／verifier を stub せず、実装上のコマンド文字列だけを検査する test にしない。

## DW-G05 と変更しない一覧

**現在の config.h の欠落が certified 選択・判定・実 repo のレポート／台帳を変えるという反証なし。** 現在の bytes は三軸 hit を生まず、確認した受理経路は live file 数を束縛しない。

ただし「すべての成果物 bytes が不変」という意味なら成立しない。probe の scan report は `file_count` が変わり、採用後に新しく作る fixture の basis OID と receipt の basis 束縛値も変わる。将来この path に conjunction が入ったとき、現行 fixture が見落とす検出力の差は残る。

本段で変更しないもの：

- production 3 file：`s8b_holdout_freeze.py`、`t080_freeze_migration.py`、`s8b_oracle_driver.py`
- test 全体、docs
- fixture の `.gitignore` と `config.h`
- 実 repo の凍結成果物・receipt、その他の tracked bytes

probe の repo commit、追加 gate、helper の一般化、docs 編集は本プランに含めない。

## 未確定事項

- 正規化した期待集合との差が、本 source snapshot でも厳密に対象 1 件だけか。419 件の静的集計だけでは完結しない。
- 一般解／hard-code の取り込み所要、scan 増分、その分散。**本段では時間測定していない。**
- standalone import と退避後の `-m tools.<probe>` 起動の実成功。
- 原典 F29 の逐語要件。
- 採否の時間許容値。D2086 の高速化採否基準を、忠実性向上の費用許容値へ自動転用しない。
- fixture の完全な発行 A/B はこの probe に含めないため、receipt／gate 全経路の実走同値性を緑とは報告しない。

## 総括

P1 は今回の ignore 起因の欠落について支持できるが、構築規則で射影した集合比較が必要。P2 は現在の bytes に対して反証なし。P3 の 13 scan は確認できたが、一般解は 419 path を処理するため ms 級という推定は未成立。P4 は snapshot と非コピー対象の扱いを補わない限り一般解とはいえない。

段 5 へ渡す案は、**実 builder を 1 回呼び、同じ fixture で index を切り替える N=20 対の probe**。集合差、semantic report 差、取り込み所要、scan 所要を別々に返し、採否へ進む。コード変更・pytest 実行・緑の主張は行っていない。