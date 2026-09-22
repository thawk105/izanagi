実装は未完です。hook の拒否により追記を停止しました。現状の `run_probe.py` は投入できません。

1. 作成ファイル（すべて指定ディレクトリ内）

   - [v3check.py](output/runs/t2854-ccbench-v3/probe/v3check.py)：276 行。v3 の構造・witness・内容検査、CLI。
   - [selftest.py](output/runs/t2854-ccbench-v3/probe/selftest.py)：148 行。正常 fixture と単独変異の自己試験。
   - [run_probe.py](output/runs/t2854-ccbench-v3/probe/run_probe.py)：463 行。コマンド記録、依存準備、source 展開、前処理・binary 比較、走行・圧縮保存の部品。**実行入口・段階制御・変異 harness・一部補助関数が未追加**。
   - `mutation-spec.template.json`：未作成。

2. 自己確認

   ```text
   python3 output/runs/t2854-ccbench-v3/probe/v3check.py --selftest
   rc=0
   v3check selftest: 146/146 passed; failures=0
   ```

   初回は 145/146。thread file 全体の削除が `structure` で先に落ちていたため、欠落時は指定の `witness` を優先するよう修正しました。

   3 ファイルとも Python の `compile()` による構文確認は成功。`run_probe.py --help` は入口未実装のため未確認。build・benchmark・投入は行っていません。

3. 裁定との差・未完箇所

   - C0〜C6 の統合制御、D1/M1〜M5 harness、spec 雛形が未完成です。
   - 前処理の include 活性比較は入退場 marker の行番号を除いています。「置換可能なのは root だけ」という指定との整合修正が必要です。
   - 計算ノード向け部品は未実走で、受入成立は主張しません。
   - tracked file の編集、git index・HEAD の更新は行っていません。

4. 親が anchor を確定するときの注意

   C2 の実 bytes で、以下の逐語と出現数 1 を照合してください。

   - D1：commit 失敗 block 終了後、quit 判定 block 直前。成功数の TLS counter と `storeRelease(const_cast<bool&>(tx.quit_), true)` を挿入。
   - M1：`set_tpcc_tx_type(get_tx_type(query.type));` の呼出し。
   - M2：quit 判定を囲む `#if !TRACE`。D1 適用後にも一意であること。
   - M3：v3 W 呼出しの table 引数。v2 側や R/X 側を巻き込まないこと。
   - M4：v3 C 呼出しの tx_type 引数。
   - M5：setter 後の `#line 56`。

5. 所有外への依存

   - 現在の直接 import：`s3_mocc_lock_coverage._normalize_objdump`。正規化仕様の変更が C3 比較へ影響します。
   - subprocess：`fetch_third_party.py hydrate` の argv・`source_root` JSON、現行 `verify.py` の CLI・認定 JSON。
   - CCBench：protocol CMake 宣言、compile database、target 名、flag 名、v3 schema、stdout counter。
   - witness は repo 関数を import せず、確認した `_parse_commit_witness` 相当をローカル実装しています。

## 総括

- v3 検査器と自己試験を実装し、146 件すべて成功しました。
- 計算 probe は部品までで未完。変異 harness・spec・実行入口の完成が必要です。
- 計算ノードでの確認はすべて未実走です。親は hook 拒否の扱いと未完箇所を解決してからレビュー・投入してください。

停止原因：PreToolUse の `guard_bash` が `run_probe.py` 後半への heredoc 追記を拒否しました。理由は「保護対象パスと不透明構文の同居を分類できないため fails-closed」。同じ追記を別経路で再試行していません。