## 所見ごとの対応

- **P1 `duplicate_entry_number` — partial:** 書き換え元・先を checker が「番号付き」と分類する archive に限定しました。合成木と実際の archive 名で選別を確認済みです。
- **P2 `mixed_newlines` — partial:** 2 本の番号付き archive の ID 付き「次の一手」に宙吊り carry を追加してから、それぞれ CRLF・CR 単独に変換します。合成木で注入結果を確認済みです。
- **P3 `visibility` — partial:** 指定順の comment、fence、可視 carry、行内 comment を追加しました。合成木では可視 carry だけが checker のトップレベル項目として抽出されました。

いずれも**旧 checker の `fault_reached: true` は未実走**です。親が行う本番 clone 比較で最終確認が必要です。

## 変更点

[equiv_real.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-probe/wave-probe/equiv_real.py) の故障注入処理のみ変更しました。docs 編集・commit は行っていません。

## 実走結果

合成木で状態 0〜6 の故障関数呼び出しがすべて成功しました。`--help` は rc=0、必須引数なしは rc=2、構文検査と `git diff --check` は成功。一時領域 `wave-probe/_scratch/` は削除済みです。

## 総括

3 件の注入修正は実装済みです。判定が検査へ届いたことの確定は、親の計算ノードでの 7 状態比較結果を待ちます。