## 規律 1

該当なし。

- C++ 追加は `wfg.cc` と WFG guard 内に限定。CMake は WFG=1 のときだけ `wfg.cc` を追加する（`patches/ss2pl-lock-protocol-study.patch:30`, `:824`）。
- `ShowOptParameters()` は `#if SS2PL_WFG_DIAG` 内（同 `:2688`）。今回の差分に `util.cc` の変更はなく、literal 数も不変。
- `mode_name` の条件は両 macro が未定義なら `0 == 1 && 0 == 0` で偽。通常の CMake 経路では両方を明示定義する（同 `:43`）。WFG=0 では翻訳単位自体が入らない。

## 規律 2 と検証器の不変

該当なし。

runner の差分は `_run_phase_trial` 内のみ。指定された検証器・抽出器・受理関数の変更はない。`wfg_output` は受領証に保存されるだけで、検証入力は従来どおり stdout から抽出した snapshot と `_run_process` の `timed_out`（`tools/pegasus/run_ss2pl_lock_study.py:2892`）。file の不在・破損による代用受理もない。

## C++ 計器の正しさ

該当なし。

- `debug.hh` の include により `cout_mutex` の `extern` 宣言が見える（patch `:2253`、`external/ccbench/include/debug.hh:13`）。`<cstdio>` は確認した標準ライブラリで `<stdio.h>` を取り込み、`flockfile` / `funlockfile` の宣言がある。
- 出力は `cout_mutex` → FILE lock → 1 回の `fwrite` → `fflush` → unlock。短い write／flush 失敗は `ERR` に進む（patch `:2496`）。追加部分に未使用変数、符号比較、nodiscard 戻り値無視の問題は見当たらない。
- lock ID の３出力箇所すべてで `std::hex` 直後に `std::dec` を戻す。後続の thread ID・counter が16進になる経路はない（同 `:2451`, `:2459`, `:2484`）。
- `make_edges` と serializer は同じ immutable snapshot を参照する（同 `:2523`）。辺の生成時に存在した held lock が serializer で消える経路はなく、`held_lock == nullptr` による閉路欠落は構成できない。
- `consecutive >= 3` は非空閉路でのみ成立し、その前に `emitted` が設定される。同一文字列を durable file に渡す（同 `:2527`, `:2537`）。
- terminal は compact 形式、`"tick":null`、空の nodes／edges。stdout には出さない（同 `:2505`, `:2569`）。
- hunk 本体を静的集計し、宣言の420行・65行と一致した。

## mode 正規化

該当なし。

node の要求 mode、保持一覧、edge の両 mode はすべて `mode_name` を通る。`IMPL=1 && KIND=0` では全箇所が `"write"` となり、保持一覧との mode 一致と非両立性の再導出が整合する（patch `:2298`, `:2453`, `:2460`, `:2487`）。

stock の `IMPL=0, KIND=1, WFG=1` では read/write を保持し、C++ `incompatible()` は read/read 辺を作らない（同 `:2307`）。取得 counter の分類も変更されていない。

## D791 判定材料

該当なし。

1. `compatible:false` は計器の申告。保持一覧は registry snapshot の写しで、検証器が lock ID・mode の照合と非両立性の再導出を行う（runner `:2446`）。
2. node と edge は同じ snapshot から生成され、検証器は３枚の node signature と edge topology を比較する（patch `:2539`、runner `:2465`）。
3. commit／abort counter は `begin()` 時に登録される写し。今回の実装に別箇所での上書きはない（patch `:1512`, `:2584`）。裁定どおり、独立した進行監視ではない。
4. timeout は実プロセスの `communicate` の期限超過から取得され、その値で受理する（runner `:2695`, `:2898`）。

欠番 tick の検証や kill までの持続観測を実装したとは評価しない。段4裁定の限定と一致する。

## test の弱体化

- **所見:** パス比較に symlink 表記依存がある。
- **現物の根拠:** [test_ss2pl_lock_study.py:1570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/orchestrator/tests/test_ss2pl_lock_study.py:1570) は未解決の `binary.parent` と比較する一方、runner `:2856` は `binary.resolve()` を使う。
- **成立条件:** test に渡る `tmp_path` が未解決の symlink を含む場合。通常の pytest 経路での発生は今回未確認。
- **影響（1行）:** 正しい出力先でもテストが偽陰性になりうるが、production の受理集合・成果物には影響しない。
- **是正案:** 当該 test の fixture 入力を `tmp_path.resolve()` に正規化する。assert と期待する配置契約は維持する。
- **区分:** nit

その他の弱体化は該当なし。軸行は全項目を含み、workload 行は実形式と同じタブ区切り・順序。負例は実検証器の `None` を要求し、恒真 assert や `pytest.raises` の誤用はない。差替えは `_run_process` のみで、受理関数を成功固定していない。`json.dumps(result)` もあり、既存 test の削除行・期待値変更はない。fixture は合成と明記されている。

## probe

該当なし。

`selftest` は合成正例・保持一覧欠落の負例を実 parser／検証器に渡す（`s5-b-implementation.diff:79`）。実走は `_run_phase_trial` の返却値をそのまま保存し、probe 側で受理判定を作らない（同 `:227`）。

arm S の build record も丸ごと保存する。S は `PERFORMANCE_ARMS` に含まれ、`build_target` が `wfg_absence` を付けるため、不在性の記録は結果に残る（runner `:38`, `:2145`）。

## 総括

**must-fix：該当なし。GO（静的設計レビューとして）。**

nit はテストの symlink パス比較１件。ファイル変更・pytest・C++ build・実走は行っていない。WFG=0 の不在性実測と実 stdout による fixture 差替えは、段4裁定どおり後続段の未完了事項である。