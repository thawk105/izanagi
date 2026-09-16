## 所見

**must-fix は確認できませんでした。should は以下の2件です。** 書き込み・pytest・configure・コンパイルは実行していません。

以下、`probe` は指定されたレビュー対象 `test_t2630_scan_boundary_reach.py` を指します。

**B6-1 — configure の制限時間と保存証拠が、他の subprocess 観測と異なる。区分: should**

- **根拠:** `probe:221–231`、`orchestrator/campaign/condition_meaning_gate.py:302,1581–1623,1713–1735`、`probe:364`。
- **real と主張する理由:** configure は `obs.command(timeout=300)` を通らず、gate 内の **120秒**制限を使う。成功時の stdout/stderr は保存されず、失敗時も例外内の stderr 末尾500 bytes が中心となる。scratch 削除後は CMake の診断ファイルも失われる。これはコード上確定している。ただし120秒超過や configure 失敗が実際に発生したとは主張しない。
- **scope 内の対応:** 実行記録に120秒制限を明記する。失敗診断が必要なら、probe 側で削除前の CMake 診断ファイルを証拠へ保存する。
- **成果物影響:** configure 失敗による TU node の赤について、依存不足・警告・時間超過を後から詳しく検証できない場合がある。

**B6-2 — コマンド timeout 時に compiler の子孫を回収する処理がない。区分: should**

- **根拠:** `probe:80–89,257–259,340–364`。
- **real と主張する理由:** `subprocess.run(timeout=300)` は直接起動したプロセスを終了させるが、このコードには `g++` 配下の `cc1plus` 等をまとめて終了・待機する処理がない。例外を段階結果として保存した後も観測を続けるため、timeout 時には子孫の処理と次の観測・scratch 削除が重なる余地がある。通常終了で残るという指摘ではない。
- **scope 内の対応:** timeout が起きた run は、子孫の終端と scratch の残留を確認してから再投入する。
- **成果物影響:** timeout 後の追加観測には、先行処理の残留による資源競合や後始末失敗が混ざり得る。

## 計算ノード実行の前提の検証

| 対象 | 確認結果 |
|---|---|
| env・cwd | tests の allowlist に `TMPDIR`・独自証拠変数はない。`inherit` は計算ノード側 `os.environ` の継承。cwd は request の repo root（`dispatch_compute.py:118–132,1442–1453,1622–1635`）。probe の固定証拠 root と内部 TMPDIR 設定はこの契約に整合する。 |
| site・compiler | 4 node 全てが `_detect_site_under_test` を要求し、autouse の site 差替えを回避する（`probe:392–411`、`conftest.py:238–255`）。実 hostname が `bnode…` なら `gcc/g++` を選び、`which`・実体 path・version/hash を記録する（`buildcache.py:1861–1865`、`probe:125–138`）。 |
| PATH | dispatcher が保証する追加は Python executable の directory。`cmake/git/objdump` の存在は保証しない。cmake・git 不足は必須観測を失敗させる。objdump 不足は追加観測の失敗として残り、4 node の合否には入らない。 |
| 共有 filesystem | runbook §6 は `/work` の永続性、実体 path、当該 cache root を記載する。ただし今回の compute からの可視性・書込み可否は未実測。probe は証拠 directory 作成、cache 読取り、configure で実際に確認する。`df` の引数には PREFIX が含まれない（`probe:279–293`）。 |
| 過去実績 | `s4-ruling.md` は bnode006／1832.nqsv の実績を採用している。本レビューではその receipt を独立確認していないため、今回の環境保証には読み替えない。 |
| conftest・guard | 未登録 node でも protocol は node 文脈を設定する。独立 clone の common-dir path/inode が共有 checkout と異なれば guard を通る（`conftest.py:2222–2240`、`patchharness.py:315–328`）。対象 node の growth/flaky hold 登録は見つからない。 |
| import | `p3_s4_loop` は広い import 連鎖を持つが、確認した module 本体に import 時の build・計測開始はない。今回の compute での import 成功自体は未確認。 |

署名・spec の照合結果は次のとおりです。

- **relay による署名欠落は成立しない。** `_failed_nodes` は `-rf` の `FAILED … - …` に対応する。harness は receipt から **job stdout 全文**を読む（`mutation_harness.py:1253–1268,1660–1689`）。receipt 表示自体も子ログの relay 対象ではない（`dispatch_compute.py:4174–4175`）。
- 全段成功・差分なしの経路では、`T2630 bytes=` は静的に **126行**。成功 relay の4 KiBを超えるが、上記の全文読取りを壊さない。
- spec の4種類の node 名は probe と一致する。`-n 0` で group marker があっても並列 worker は起動しない。harness 側にも group suffix の正規化がある。
- **M3a:** `BACKOFF_FIXED=-1` では追加した `#undef/#define` は非選択枝に入り、stock に macro 効果を与えない。variant では backoff header の後にある `transaction.cc:278–279` の条件へ届く構造である。
- **M4/M4b:** 挟み込みは include 行列を変えないため、`assert_includes_match_head` の比較対象は同じ（`source_digest.py:2129–2149`）。適用成功は実装報告にあり、本レビューでは再実行していない。
- M4 の object compile 失敗は追加観測に留まり、TU bytes 比較を止めない。裁定の「compile 不能の対照」と整合する。

## 時間と残骸

**300秒は1 run の保証ではありません。** configure 4回は各120秒、前処理・object compile・objdump は各最大4回、別途 clone・digest・TRACE 観測・inventory・diff 生成がある。各 command の上限を足しても、run 全体が300秒以内、またはwalltime 1時間以内とは証明できません。

`estimated_run_seconds=300` は見積り表示用です。baseline＋8変異で **9 run／2700秒**、さらに collection の別 dispatch が必要です（`mutation_harness.py:3163–3175`）。段3報告の「計9 request」は、現specでは **collection込み10 request** に更新が必要です。8100秒は各 runner の外側制限であり、全matrixの制限ではありません。queue待ち3600＋walltime3600＋grace600＝7800秒とは整合します。

`_inventory` は `.git`、ignored/untracked、通常ファイルを含めて前後2回読み、hash を計算します（`probe:106–121`）。71件の旧生成物も除外されません。ただし総ファイル数・現在の総bytes・compute上の所要時間は未実測で、秒数の断定はできません。

通常終了では以下が成立します。

- checkout の登録先は独立 clone の `.git`。worktree remove と残留検査の後、外側が scratch 全体を削除する。
- TMPDIR は元の値または未設定状態へ復元する。
- build directory は同じ genome の reference/current 間で再利用するが、毎回 configure と明示的な `-c` を実行し、object を先に削除する。既存objectを成功扱いする経路はない。
- evidence 名は hostname・秒単位時刻・PID。`lru_cache` により通常は1 processで1回だけ作る。同名衝突時は `exist_ok=False` で失敗し、上書きしない。

walltime kill では finally の実行を保証できず、scratch と途中までの証拠が残り得ます。worktree 登録の残留先は独立 clone 内です。`/tmp` fallback の自動清掃は、このコードからは保証できません。

## 総括

**静的レビューで本走を止める根拠は見つかりませんでした。** B6-1・B6-2 は異常時の証拠と後始末に関する should です。

台帳の期待署名一致だけでは到達原因まで確定しません。親の実走結果では、保存された resolve 成否・TU diff の対応箇所・追加 compile 観測を併せて読み、環境失敗を到達結果として扱わないことが必要です。