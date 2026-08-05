---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-token-economy
seq: 3
---

## 新規

### {{F:acceptance-repo-write-race}}. 受入全走の最中に repo へ成果物を書き、実 output snapshot 検査を自分で赤にした [手順漏れ]

- 事象: dev-wave token-economy の受入全走 (2026-08-05 12:45〜12:57、request 889879) が
  **4 failed / 6,194 passed**。失敗はすべて `orchestrator/tests/test_s8b_floor_campaign.py` の
  `assert repo_before == _real_output_snapshot()` である。差分が到達しえないファイルだったため
  `DW-O18` に従い単独再走したところ **199 passed / 2 skipped / 0 failed** で再現しなかった。
- 根本原因: **フレークではなく自分の書き込み。** 待ち時間を使って段 7 の逐語凍結を進め、
  走行中の 12:46 に `output/insights/2026-08-05_token-economy-compact-carry/` を作成した。
  これらのテストは実 repo の `output/` が campaign 実行前後で不変であることを検査するため、
  親が同時に書けば必ず赤になる。当初「別 wave の全走との干渉」を疑ったが誤りだった。
- 恒久対応: 受入全走の投入後は、完了まで repo 配下 (特に `output/`) へ書かない。
  待ち時間の作業は repo 外の wave 成果物ディレクトリに限り、逐語凍結と fragment 作成は
  全走の前か後に置く。記録 commit を先に済ませてツリーを固定してから全走を投入する。
- 再発検知: 受入結果が `test_s8b_floor_campaign.py` の `_real_output_snapshot` 系だけで赤のとき、
  実装差分でなく走行中の `output/` 書き込みをまず疑う。単独再走で緑なら本件型である。

## 再発

### F24

- **再発: 2026-08-05** — 別機序で再発した。段 6 焦点再レビューで、codex の出力 `.md`
  (13,253 bytes、末尾に結論あり) は書かれたのに完了マーカー `.done` が作られなかった。
  ジョブ中断により detached wrapper が `echo $? > .done` に到達せず落ちたためである。
  成果物だけを見ると完成しており、途中書きと区別できない。`DW-O01` の「完了は `.done` と
  exit code だけで判定する。ログの grep も完了通知も判定にしてはならない」が防壁として働き、
  採用せず再走した (孤児成果物は `s6-refocus-orphan.md` として保存)。
  同日さらに、変異 harness の完了を待つ背景タスクが `.done` 生成前に「完了」通知を返し、
  成果物を直接確認して実行中と判明した事例もある。**恒久対応は既存の `DW-O01` で足りる**
  — 完了判定を `.done` + exit code に限る規律を、通知が先行した場合にも例外なく適用する。

### F87

- **再発: 2026-08-05** — dev-wave token-economy の変異本走で、9 変異中 5 件 (M01〜M05) と
  再照準した M07b が `MISMATCH` になった。いずれも **期待 node はすべて赤で、加えて更に多くの
  node も赤** (actual ⊋ expected) であり、親が期待 node を新設テストだけから導いて過少列挙した。
  検出力は登録より強い方向であり偽 SURVIVED ではない。`_match_key` の完全一致契約
  (`KILLED` は `failed_keys == expected_keys`) がこれを MISMATCH として顕在化させた。
  逐語は `output/insights/2026-08-05_token-economy-compact-carry/mutation-ledger.json`。
