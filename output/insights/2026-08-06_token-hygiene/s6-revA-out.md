**NO-GO** です。must-fix は 3 件あります。pytest は Pegasus ログインノード規律により実行していません。

### 1. real / must-fix — 既定上限では sidechain を探索しない

[_discover_paths](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:160) は、現在 directory の root JSONL をすべて列挙してから subdirectory へ降ります。25 本目で即 return するため、Izanagi project root への実呼び出し結果は次でした。

- selected=25 / limit_reached=True
- root_files=25
- sidechain_files=0

`--include-sidechains` は探索を変えず、探索後の合算値を追加するだけです。上限未到達の fixture しかないため、[sidechain test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/tests/test_claude_session_ledger.py:202) はこの欠陥を殺しません。

一方、段 3 の 4 directory へ個別に限定すると、実装は正しく 4 本を拾い、87 model calls / 入力 5,548,966 / 出力 63,208 を再現しました。つまり再帰処理自体ではなく、通常の project-root＋既定上限の選び方が壊れています。

放置時: `sidechains.model_calls/raw_input_tokens/output_tokens` が 0 となり、確認済みの 87 / 5,548,966 / 63,208 を丸ごと落とします。

### 2. real / must-fix — dedupe identity が不完全

[_request_key](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:200) は各 record を独立に `requestId` または `message.id` へ写します。

- 同じ response の一部 record だけ `requestId` が欠けると、`message.id` key と `requestId` key に分裂し、二重計上します。保存される `key_source` は以後未使用です。
- 全 session・全 file・root/sidechain が、生の文字列だけを key にする 1 個の辞書へ入ります。[root/sidechain 衝突検出](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:578) は既に merge した後で、しかも `request_crosses_sidechain` は strict failure 対象ではありません。
- 同一 side 内の file 横断衝突は報告すらされません。

限定 8 ファイルでは、`requestId` 欠損＋`message.id` fallback が 1 record、非連続重複が 125 箇所あり、後者は正しく dedupe されました。file 横断衝突と mixed-key response は観測しませんでしたが、許容入力に対する誤計数経路はコード上確定しています。

放置時: mixed-key は model calls と全 token を二重計上し、file/root-sidechain 衝突は model calls を 1 減らして token を最後に読んだ側へ誤帰属させます。

### 3. real / must-fix — 「最終 usage」が時系列上の最終とは限らない

[usage 更新](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:347) は、file の探索順・行順で最後に読んだ usage を採ります。

- event timestamp の逆転を検出せず、file 横断時は pathname 順が「最終」を決めます。
- 最終 assistant record に usage が無ければ、以前の usage を無警告で使用します。
- `usage_final_below_prior_max` は最終値が過去最大より小さい場合だけ検出します。timestamp 逆転で値が同じ／大きい場合や terminal usage 欠損は検出できません。
- [時間窓選択](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:565) も同じ `usage_meta` を使うため、token だけでなく窓内外まで誤ります。

実データの `output_tokens=1 → 247` は [対象 sidechain](/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/304d8136-cae0-4945-a9af-f8203a9dc953/subagents/agent-a8772d85c98a7402b.jsonl:4) の連続 2 record で再現し、実装は正しく 247 を採りました。ただし限定 8 ファイルには timestamp 逆転・output 回帰・最終 usage 欠損がなく、危険形は未実測です。

放置時: 古い usage の input/output token を採り、その model call を誤った時間窓へ出し入れします。

### refuted / backlog

- **時間窓:** 実データの最終 timestamp `07:49:47.676Z` は `--since` 同値で包含、`--until` 同値で除外されました。報告どおり `[since, until)` です。長い session を 3 秒窓へ絞ると対象 1 request・247 output だけでした。
- **timestamp/mtime 混在:** request ごとの fallback と件数報告は実装されています。限定標本では usage record の timestamp 欠損が 0 件だったため、実データでの mtime fallback は未確認です。
- **synthetic:** 8 ファイルでは全ゼロ `<synthetic>` が 4 件あり、3 件は rate-limit error、1 件は非 error でした。したがって除外集合は「rate-limit 件数」より広いものの、出力は正しく「synthetic 全ゼロ応答」と呼んでいます。非 synthetic の全ゼロ error と synthetic 非ゼロは未観測のため backlog です。
- **model/tool 分離:** 4 sidechain で 87 model calls 対 136 tool calls。0-tool response が 4、複数-tool response が 43、最大 4 tools で、実装値と独立集計が一致しました。この疑いは refuted です。
- **観測／推測:** 実データへの text 出力に「固定 base」「1 往復」「費用」「課金」「枠」は 0 件でした。曲線値も出していません。限定標本に compaction 境界がなかったため、実データでの境界検出だけは未確認です。

## 総括

**(a) 判定: NO-GO。**

**(b) must-fix**

1. `--max-files` を root transcript だけで使い切らず、bounded なまま root/sidechain の双方を探索・報告する。  
   放置時: sidechain の 87 calls / 5,548,966 input / 63,208 output が 0 になります。

2. `requestId` と `message.id` の alias、session/file provenance、root/sidechain 衝突を明示的に解決し、曖昧時は fail-closed にする。  
   放置時: response が二重計上されるか、別 response が 1 件へ潰れます。

3. event timestamp と terminal usage の完全性を検査し、順序逆転・最終 usage 欠損を無警告で集計しない。  
   放置時: input/output token と時間窓帰属が同時に誤ります。

**(c) 実データ確認範囲**

- 確認済み: 指定 4 sidechain＋対応 root 4 本、計 8 ファイル・約 12.7 MB。2,445 assistant records / 1,205 request keys。段 3 の 4 本と `1→247`、非連続 dedupe、境界、synthetic、tool 分離を確認。
- 未確認: 実データ上の file 横断 ID 衝突、mixed-key response、timestamp 逆転、最終 usage 欠損、mtime fallback、非 synthetic error、compaction。
- pytest は未実走であり、緑とは報告しません。