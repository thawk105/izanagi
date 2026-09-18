## 判定と検算結果

**公開稿は NO-GO。主計時を取り直す必要を示す問題は見つかりませんでしたが、P1 の根拠は一次資料と矛盾しており、公開前に修正が必要です。**

静的検査と保存 JSON の算術検算だけを行いました。selftest・pytest・bench・verifier は再実行していません。

本走について独立に再計算した結果は次のとおりです。

| 項目 | 再計算結果 |
|---|---:|
| T_trace | 3.343941605 秒 |
| T_count | 16.857903951 秒 |
| T_verify | 421.706717790 秒 |
| 3 区間の和 | 441.908563346 秒 |
| 割合 | 0.7567% / 3.8148% / 95.4285% |
| 入力規模 | 48 file、204,048,743 行、6,520,332,111 bytes |
| verifier 単価 | 24.6200 μs/txn |

README の丸めと一致します。smoke の時間・規模も記録と一致しました。probe の SHA256、verifier 全 module の保存 SHA256 と現在のファイルの一致も確認しました。trace 原本全体の再ハッシュ・再計数は行っていません。

以下では `README` を今回の insight README、`probe` を job dir の `probe/verifier_cli_timing_probe.py` と略記します。

## 1. real / must-fix — P1 の「backoff.hh はコンパイル対象外」は誤り

`external/ccbench/cc/silo/include/transaction.hh:9` は `backoff.hh` を**無条件に include**しています。同ファイルの L51 に `Backoff backoff_`、L69 にその構築があります。さらに `external/ccbench/common/runner.hh:55,179` にも include と構築があります。

`transaction.cc:42,719` の `#if BACK_OFF` が除くのは `Backoff::backoff()` と `leaderBackoffWork()` の**呼出し**です。ヘッダ全体をコンパイル対象から外すものではありません。

また、patch は cache 変数だけでなく `ccbench_universal_definitions` に `BACKOFF_FIXED` と `BACKOFF_NOINLINE` を追加しています（`patches/silo-backoff-fixed.patch:19`）。現行 patch の未定義検査も include 経路上にあります。

当時の `0a07481b8:patches/silo-backoff-fixed.patch` も読み、SHA256 が campaign.lock の `36cd974c56c6…` と一致することを確認しました。この誤りは現行 patch との差に起因しません。

ただし、**stock に `CCBENCH_BACKOFF_FIXED` を渡さない選択自体は妥当**です。stock Options.cmake に対応変数・定義の配線がありません。当時の patch では `BACKOFF_FIXED=-1` が stock 分岐を選び、`BACKOFF_NOINLINE=0` です。今回確認した範囲で、patch が BACK_OFF=0 の backoff 動作を変更する証拠はありません。

修正すべき箇所は README:34、HANDOFF.md:12,27、s4-ruling.md:30 です。例えば次の範囲に限定してください。

> backoff.hh はコンパイル対象に残る。BACK_OFF=0 により backoff と leader 更新の呼出しが除かれ、campaign none の追加定義は stock 分岐を選ぶ。これは backoff 動作の対応の説明であり、コンパイル入力全体や生成 binary の同一性の証明ではない。

「bytes 同一性は主張しない」だけでは、直前の誤った source 説明を救えません。

## 2. real / should — build 差をもう一段具体化する

README:34 の「plain cmake」「bytes 同一性は主張しない」は方向として適切ですが、「compile 面の同一性」という結びは強すぎます。

probe:86 は `CCBENCH_CCACHE=OFF`、launcher 空、`CMAKE_CXX_FLAGS=` 空を指定します。一方、buildcache の binary path policy は macro prefix map、条件に応じた debug prefix map、`CMAKE_SKIP_RPATH=ON` を追加します（`orchestrator/campaign/buildcache.py:1914`）。当時の同関数にもこの配線があります。

これらを README に短く列挙し、「一致を確認したのは workload と列挙した主要 define」と限定することを勧めます。今回の値を変更する所見ではなく、campaign と同一 build 条件という読みを防ぐ修正です。binary の SHA 差の原因をここから断定することもできません。

## 3. refuted — 主計時・argv・C 行計数に観測を無効にする不一致はない

`bench_argv`、`verifier_argv`、`count_c_lines` は依頼に対応しています。main の記録は rr95・1M records・48 threads・extime 3・2100 clocks/μs です。commit witness、C 行数、verifier txn 数はすべて 17,128,612、batch witness は 0 でした。

`timed_process` では次の対応を確認しました。

- 出力 file の open は計時外（probe:118）。
- start は Popen 直前、returned はその復帰直後、end は wait4 復帰直後（L120–138）。
- 正常経路の reaper は wait4 だけで、watchdog は wait/poll しません。
- watchdog の起動と親のスケジューリング遅延は wall に含まれ、join は含まれません。
- `start_new_session=True` の起動費用も主値に含まれます。

stdout の file 直結は pipeline の pipe 捕捉と異なるため、I/O 待ちや親子の実行順が同じとは限りません。今回は bench stdout 21 行・stderr 空ですが、差の大きさは未測定です。**probe の wall 観測としては成立し、pipeline の厳密な再現とはしない**という整理が妥当です。

`communicate_window_s` は時間境界の「近似」としてなら適切です。実際の communicate、pipe 排出、timeout 判定を再現した値ではありません。900 秒と120 秒の差は今回の3.344秒では打切り結果を変えません。

## 4. real / should — CLI と pipeline の差の説明を補う

`--ccbench-root` に build 元の checkout root を渡すのは正しいです。`model.py:119` は `<root>/cc/silo/CMakeLists.txt` の `SOURCES` と対応ソースを読みます。probe は checkout の存続中に CLI を実行しています。

ただし README:117 の差は capability と WAL だけではありません。

- pipeline は build admission・genome・source evidence の束縛を検査し、保存された source snapshot を渡します（`core.py:200,353`）。
- CLI は渡された checkout をその場で読みます。
- T_verify は interpreter 起動、import、引数解析、JSON 生成・出力、process 終了まで含みます（`cli.py:68`、probe:78,325）。

共通の検証本体を使うことと、pipeline の検証段全体と同じ意味・同じ費用であることは分けてください。今回の目的は CLI 単独計時なので、追加の実装や再測定は不要です。

また、worker 数16は既定の選択値です。`parse.py:628` には並列実行失敗時の fallback があり、保存値だけで16 workerの正常完走まで証明したとは書けません。

## 5. real / should — verifier 直前の追加読出しを条件として明記する

probe:311–326 の順序は、C 行計数 → 全行数計数と SHA256 → verifier です。pipeline にない inventory が、verifier の直前に trace 全体を追加で読みます。

README:66,78 は別計時であることを記載していますが、**計時外の読出しでも page cache 状態に影響し得る**点が抜けています。「追加 inventory 後の入力に対する CLI 時間」と一文足すのが適切です。pipeline にも C 行計数があるため、追加 pass の効果量や高速化は断定できません。

421.707秒は有効な観測です。ただし、追加処理を和から除くだけで pipeline 相当の条件になるわけではありません。

## 6. real / should — maxrss は process tree の同時使用量ではない

README:79,116 の「子孫込みの最大値」は、子孫の値が反映される点では誤りではありません。しかし、43.95 GiB を CLI と worker 全体のメモリピークと読めます。

ローカルの `getrusage(2)` / `wait4(2)` の説明と照合しました。待たれた子孫の accounting は反映されますが、`ru_maxrss` は同時に生きる process 群の RSS 合計の最大値ではありません。CPU 時間の加算と同じ意味では扱えません。

> 43.95 GiB は wait4 の ru_maxrss。待たれた子孫の最大 RSS が反映され得るが、process tree の同時合計 RSS や cgroup peak は測っていない。

という表記を勧めます。数値自体の修正は不要です。

## 7. real / should — 「比較ではない」と数値比の併記を整理する

README:99 は441.909 / 1408.8 =31.4%という比較を行いながら、「比較でも差分でもない」と否定しています。L100 の1/36も、実測時間と契約上限の比であり、速度比として意味を持ちません。

D2144を置き換えないという境界は明記されており、過去の判定の昇降格も見つかりません。ただし規律7に沿って明瞭にするなら、31.4%・1/36を削り、**異なる時点・code・node・計時範囲の数値の併記であり、速度向上や当時の内訳を推定しない**と書くのが適切です。

特に今回の3区間の和と、過去のWAL反復区間は含む処理も一致しません。

## 8. real / nit — total_cycles は原値を転記できる

README:90 の `total_cycles` 欄は「JSON anomalies 空」となっていますが、保存された `verifier.json` には `"total_cycles": 0` があります。空の witness 一覧から代用せず、`0 / 0` と転記してください。

今回の certified=true と矛盾する問題ではありません。

## 親 brief・条件・過剰実装の確認

campaign.lock の `identity_preimage` を解析し、pin、records、threads、extime、clocks_per_us、read-heavy の4項目、none の BACK_OFF/BACKOFF_FIXED を確認しました。数値の食い違いはありません。numactl なしは `env_contract.py:250` と一致します。`/scr` 配置は既往 insight §3 の記録と整合しますが、campaign.lock 自体が過去の実配置を証明するわけではありません。

親 brief・裁定の実質的な誤りは上記P1です。smokeと本走を同一jobにまとめた変更は運転script・dispatch記録・READMEに現れており、本走が1反復であることを損ないません。

probe の site確認、単独性確認、create-only保存、timeout、途中記録は指定仕様内です。verifier受理集合の変更、D2144の書換え、代表値・CC性能の確定、追加の一般的な台帳やgateは見つかりませんでした。

## 総括

**判定：NO-GO（公開文書のP1根拠修正が必要）。観測値の棄却・再測定を要求する所見はありません。**

| 番号 | real/refuted | 優先度 | 根拠の file:line | 放置時に残る値・主張の問題 |
|---|---|---|---|---|
| 1 | real | must-fix | `README:34`、`transaction.hh:9,51,69`、`silo-backoff-fixed.patch:19`、`s4-ruling.md:30`、`HANDOFF.md:12,27` | 「ヘッダ対象外・cache変数のみ」というP1の根拠が誤ったまま残る。 |
| 2 | real | should | `README:34`、`probe:86`、`buildcache.py:1914` | campaignとのcompile条件の同一性を過大に読める。 |
| 3 | refuted | must-fix相当の疑義を棄却 | `probe:72,78,110,156`、`pipeline.py:409` | 主計時・argv・計数の不一致による3.344秒／421.707秒の訂正は不要。 |
| 4 | real | should | `README:117`、`core.py:200,353`、`cli.py:68`、`parse.py:628` | CLI固有費用、source束縛、worker選択値の限界が不十分。 |
| 5 | real | should | `probe:311`、`README:66,78` | inventory後のcache状態という421.707秒の条件が曖昧。 |
| 6 | real | should | `README:79,116`、`probe:102` | 43.95 GiBを全worker同時合計ピークと誤読できる。 |
| 7 | real | should | `README:97,99,100` | 31.4%・1/36が、否定文付きの速度比較として残る。 |
| 8 | real | nit | `README:90`、`report.py:137` | total_cyclesの直接記録値0が転記されない。 |

**読めなかった資料：なし。** 必読資料と追加の campaign.lock は読めました。レビューは読み取りと算術検算のみで、ファイルへの出力・変更は行っていません。