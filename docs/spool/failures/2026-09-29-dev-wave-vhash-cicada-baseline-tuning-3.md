---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-cicada-baseline-tuning
seq: 3
---

## 新規

### {{F:print-function-defined-not-called}}. 印字関数の定義を「実行時に必ず印字される」と取り違え、run の binding 照合を全 run 必須にした [手順漏れ] [恒真ゲート]

- 事象: VHash 比較相手 Cicada の較正 wave の段 1 brief (P8) に「`#ShowOptParameters()` 行は util.cc:326-336 が必ず印字」と書き、driver はその行がちょうど 1 行あることを全 run で要求した。実物では Cicada の `ShowOptParameters()` は定義だけで、CCBench 全体の呼出しは `cc/ss2pl/ss2pl.cc:117` の 1 件だけだった。段 2 plan・段 3 相談 2 本・段 5 author も見逃した。計算ノードへ投入する前の親の自己レビューで見つけ、fix で照合を compile command の -D 照合へ置き換えた (投入前なので計算の空費はなし)。
- 根本原因: 印字の実在を関数定義の grep で確かめ、呼出し側 (実行経路) を確かめなかった。`DW-O13` の「field の実在では足りない、実環境で取りうる値を実測」を、コード読みの段階で「実行経路に乗るか」まで当てなかった。
- 恒久対応: memory `print-function-must-be-called-to-count`（印字・計測の関数は定義でなく呼出しを grep し、実行経路に乗ることを確かめてから照合の入力にする）。`docs/dev-wave/operations.md` の `DW-O13` (入力の実在は実環境の値で確かめる) の適用例。
- 再発検知: binding や照合の入力を「stdout の行」「ログの行」にするとき、段 1 で呼出し元の file:line を brief に書けなければ未確認として扱う。

## 再発

### F733

- **再発: 2026-09-29** — VHash 比較相手 Cicada の較正 wave の段 6 fix-4 で、「既存テストの期待値を変更しない」と書いたため、同じ wave で新設した test の `len(j2) == 5` (裁定が 4 job へ変える挙動を写した期待) と衝突し、子は何も変えずに停止した (1 巡空費)。fix-4b で「この wave で新設した 2 本の test file に限り、裁定の fix 行が変える挙動を直接写した期待だけ更新を許す」と名指しして通った。

### F753

- **再発: 2026-09-29** — VHash 比較相手 Cicada の較正 wave で、local main 取り込みの merge commit の provenance 事前検査 (`--message-file`) と `git commit -F` を同じ応答内の並列 tool 呼出しにしたため、事前検査が赤 (両親と異なる実装面 `orchestrator/tests/test_official_perf_closure.py` に Codex role=author が無い) なのに merge commit が作られた。受入・land に使う前に気づき、Codex 子の merge 合成監査を経て message を amend した。`DW-O17` の「tool call を分ける」は順に呼ぶ意味で、並列呼出しは分けたことにならない。
