## 所見

- **B-01｜must-fix｜`scripts-v1/launch_one.py:75–78`**
  根拠: Cicada 登録の正例は、F に存在しない既存の `#if TRACE` 枝を探して失敗する。段 4 の erratum E1 は「末尾に新しい TRACE 枝を追加」と訂正済みだが、script に反映されていない。
  放置すると: Cicada job は正しさの走行後に必ず失敗し、計算費用と一次資料を無駄にする。
  推奨: E1 の合成枝を作る実装に直す。

- **B-02｜must-fix｜`scripts-v1/run_judge.sh:25–32`**
  根拠: D297 の `rc` を file に記録するが、最後の `printf` が成功するため script 自体は rc=0 で終わる。
  放置すると: D297 が不合格でも dispatch の `.done` は `0` となり、失敗した成果物を緑と誤認しうる。
  推奨: 記録後に D297 の `rc` で終了する。

- **B-03｜must-fix｜`scripts-v1/dispatch_one.sh:6–17`、`submit_all.sh:14–22`**
  根拠: `.done` の書込みに終了 trap がなく、`cd` 失敗や shell の中断では作られない。一方 `.pid` は残り、再投入を拒否する。`.done` がある場合も失敗 rc と成功 rc を区別せず再投入を拒否する。
  放置すると: 失敗 job だけをやり直す段 4 の方針が機能せず、失敗時の切り分けと復旧が手作業になる。
  推奨: 終了時に rc と時刻を確実に記録し、失敗分の再投入手順を設ける。

- **B-04｜should｜`scripts-v1/submit_all.sh:18–30`、`tools/pegasus/dispatch_compute.py:3623–28,3979–4007`**
  根拠: wrapper は 6 dispatch を非同期に起動するので直列待ちではない。ただし 6 本が同じ repo の dispatch 制御領域を共有し、投入操作は lock で直列化される。scheduler が別ノードへ配置する保証もない。曖昧な投入から orphan hold が残れば、後続は rc=16 で止まる。
  放置すると: 「6 job が同時に別ノードで走る」という前提が崩れ、計算開始時刻と失敗理由を読み違える。
  推奨: 投入 receipt の job ID・配置ノード・hold 状態を 6 本分照合してから並行実行を主張する。

- **B-05｜should｜`scripts-v1/launch_one.py:129–53,172–216`**
  根拠: 各正しさ job は依存準備、build、走行、verifier を同一ノードで直列実行する。Silo は二つの workload も直列。Cicada はさらに登録検査二つが続く。MOCC の 48 thread・100 万 record cell は verifier の実測がなく、`timeout=900` 秒だけが上限である。
  放置すると: MOCC と Cicada は 5 分目安を超えうる。特に verifier 中も計算ノードを占有し、見積り 180–300 秒／180–360 秒の根拠が弱い。
  推奨: 各段の実測秒を先に取り、5 分を超える直列段を分離して見積りを更新する。D297 の約 1 時間 × 2 本は依頼で明示された例外として記録する。

- **B-06｜should｜`scripts-v1/launch_one.py:38–42,151–54,178–89`**
  根拠: `subprocess.run(..., timeout=...)` が時間切れになると `call()` は rc・所要秒を返さず、`result.json` には例外文字列だけが残る。stdout と stderr は残るが、どの段が何秒で上限に達したかの構造化記録が欠ける。
  放置すると: walltime 超過や verifier 停滞の切り分けが難しくなる。
  推奨: timeout も段名、上限、経過秒、専用 rc を receipt に保存する。

- **B-07｜should｜`scripts-v1/mk_synth.sh:23–59`、`submit_all.sh:30`**
  根拠: A/B′ の OID と hunk manifest は生成するが、bundle、manifest、各 job report、検査器の commit と SHA-256 を結ぶ索引表は生成しない。`dispatch_one.sh:10` の `sha256sum "$@"` は引数に directory や値を含むうえ、失敗を握りつぶす。
  放置すると: 後続 wave が一次資料と実行入力の同一性を追跡しにくい。
  推奨: login 側で索引表を生成し、各 report の確定後に SHA-256 を追記する。

- **B-08｜should｜`tools/check_trace0_preprocess_identity.py:1171–75`**
  根拠: Cicada file は 32 文脈を比較する一方、report 上位の `expected_context_count_per_file` は従来の 16 のまま。file 別に足した `expected_context_count` と矛盾する。`actual_context_count` は `contexts` の長さで復元できる。
  放置すると: consumer とレビュー担当者が比較件数を誤読し、report の保守負担が増す。
  推奨: 上位 key を path 別の意味に直し、file 別 key は期待数だけに絞る。

- **B-09｜nit｜`tools/check_trace0_preprocess_identity.py:575–674`**
  根拠: Cicada の値列挙を既存 genome ループの内側に入れたため、差分の大半が既存比較処理のインデント替えになった。機能追加量に対してレビュー対象が大きい。
  放置すると: 今後の検査器変更で既存比較処理の差分を追いにくい。
  推奨: `(genome, old defines, new defines)` の文脈を先に列挙する小関数を置き、比較本体は一重のループに戻す。

- **B-10｜nit｜`scripts-v1/run_ci_build.sh:45–89`**
  根拠: 前例の CI build script にある依存 pin 照合と三つの clone をほぼ再実装している。正しさ側も `_prepare_dependencies` で依存を準備するため、job ごとに clone が重なる。
  放置すると: script の保守面と計算ノード上の準備時間が増える。
  推奨: CI 本体は前例を共通化して呼び、今回固有の tip 照合と受入条件だけを追加する。

## 正しいと確認した点

- 検査器テストの Cicada fixture は小さく、16 値組合せ × 2 overlay の集合一致、4 macro の負例、未知 macro、比較件数不足を扱う。
- `submit_all.sh` は dispatch 完了を直列に待たず、6 process を起動する。
- `mk_synth.sh` は A/B′ の OID、hunk manifest、A の修正 blob 一致を記録する。
- 親の焦点テスト 4 file は **336 passed**。計算 job は未実走のため、その成否は確認していない。

## 総括

現状の script 群は投入可能な完成形ではない。特に **E1 未反映**と **D297 失敗の rc 消失**を直し、`.done` と失敗時の再投入、一次資料の索引を整えてから計算を投入すべきである。