判定は **GO**、must-fix は **0 件**です。4 変更面は申告どおりで、production gate と現行の機械受理集合は変更されていません。以下は静的監査結果です。

### 1. 3 分類の裏取り

「機械 gate が拒否する」5 項目はすべて現行実装と一致します。

| 項目 | file:line と規則 ID | 判定 |
|---|---|---|
| 生の前処理指令 | [diff_quarantine.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/diff_quarantine.py:51)、同 `:491-496`。`DiffRejectSubtype.HOLE_ESCAPE / content-directive` | 正しい |
| 新しいヘッダ取り込み | hole 内の `#include` は同 `:491-496` の `HOLE_ESCAPE/content-directive`。hole 外は同 `:443-487` の `FRAME_ALTERED` または `OUTSIDE_REGION`。さらに [source_digest.py:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/source_digest.py:669) が include 集合を HEAD と照合 | 正しい |
| 新しいマクロの追加 | `#define` は [diff_quarantine.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/diff_quarantine.py:491) の `HOLE_ESCAPE/content-directive` | 正しい |
| 新しいグローバル変数の追加 | hole 外は `FRAME_ALTERED/OUTSIDE_REGION`。hole は [sort_swo_oracle.py:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/sort_swo_oracle.py:486) で外形を単一の非修飾 `sort(...)` 文に限定し、同 `:1450-1454` で `OracleRejectKind.STRUCTURE / not-a-single-sort-statement` として環境解決前に拒否 | 正しい |
| `//`・`/*`・行末 backslash | [diff_quarantine.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/diff_quarantine.py:503) から `:522`。`HOLE_ESCAPE/content-comment-line`、`content-comment-block`、`content-line-splice` | 正しい |

部分執行側にも格下げ誤りはありません。

- 非決定性は、[sort_swo_oracle.py:1083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/sort_swo_oracle.py:1083) と同 `:1221-1252` の `relation-varies-within-process` / `relation-varies-across-process-order` による有限観測です。完全執行ではありません。
- 副作用は [coder_effect_gate.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/coder_effect_gate.py:58) の有限 `host-effect.*.v1` 規則群と oracle の `corpus-mutated-by-comparator` に限られます。
- ループは同 `:527-562` の `host-effect.unconditional-loop.v1` と実行 timeout が対象で、全ループ禁止ではありません。
- 例外は [sort_swo_oracle.py:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/sort_swo_oracle.py:775) と同 `:1051-1061` の `candidate-comparator-threw` が観測した送出に限られます。内部処理された例外まで完全執行する規則はありません。

非検査側も正しいです。型・関数の追加を禁止理由として拒否する rule ID はなく、単一文検査とコンパイル成功はこの policy の検査ではありません。説明配置は [projection_guard.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/projection_guard.py:32) で `justification` が optional、[p3_s4_loop_sort.py:371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/p3_s4_loop_sort.py:371) でも欠落時に空文字列となるため、非検査です。

### 2. 禁止の保存と読まれ方

[role 本文:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/.claude/agents/coder-v4-autonomous-sort.md:84) の禁止5 bulletは、`a160f4aa` と現在の blockを抽出して byte 比較し、完全一致しました。追加・削除・並べ替え・改行変更はありません。

新設文も禁止を限定していません。

- 冒頭で「すべて生成時に守る必須禁止」と宣言しています。
- 続けて「機械が検査しないことは許可を意味しない」と明記しています。
- 末尾でも「部分的・非検査項目も禁止は不変」「gate 通過は契約充足の証拠ではない」と再確認しています。

coder LLM にとって十分に強い二重の否定です。部分執行という事実は示しますが、破ることへの許可や推奨には読めません。追加補強は不要です。

### 3. 偵察 firewall

新しい節は項目単位の粗い分類に留まり、機械が捕える具体形と通過する具体形の境界、有限 corpus の穴、構文上の回避条件を開示していません。一方で規則 IDまで辿れば分類を裏付けられるため、元の「実態より広い保証」も残っていません。must-fix はありません。

### 4. 段3所見の閉鎖表

| 所見 | 状態 | 根拠 | 成果物影響 |
|---|---|---|---|
| A1 説明配置の誤分類 | **closed** | `justification` 配置を「機械 gate が検査しない」へ正しく分類 | 違反 proposalを機械保証済みとして材料レポートへ記録する誤りを防ぐ。機械受理集合は不変 |
| A2 内部処理された例外の禁止脱落 | **closed** | 禁止5 bulletをそのまま保存し、例外送出全体を部分執行と記述 | policy 上の受理集合を広げず、certified 候補への禁止を維持 |
| A3 auditor 未結線 | **partial** | 「auditor が拒否する」という虚偽の保証は完全に除去。ただし auditor 自体への残余契約結線はscope外のまま | 現行受理集合は不変。材料レポートで残余を auditor 保証済みと書いてはならない |
| A4 caller 閉包 | **partial** | role 文脈は live coder proposal に閉じるが、S6/freezeとの射程差の正式記録は段7義務として未了 | 受理集合は不変。記録しないと材料レポートが全 sort materializationへ過剰一般化する |
| A5 adapter 代行 | **partial、commit待ち** | 2026-08-18の直接ユーザー裁定によりD105 waiver経路は成立。renderer byte parityも一致 | adapterはdormantでcertified値は不変。ただし正しいtrailerが無ければland資格を失う |
| B1 許可への誤読 | **closed** | 冒頭・末尾の二重明示と「必須禁止」により非検査を許可と読む余地を十分抑止 | 機械受理集合は不変。coderが残余禁止を破る誘因を低減 |

regressed は0件です。A3の根本配線、A4の段7記録、A5のcommit trailerは未完ですが、現在の4枚に対するmust-fixではありません。

### 5. 他の変更面

- source SHA-256、ledger、adapter内2箇所のpinはすべて `fbabef...7ca9a` で一致しました。
- adapterはrenderer期待値と **14940 bytesで完全一致**し、semantic digestも再生成値です。
- テスト削除は対象関数のdecorator、5 parameter、本体の14行だけです。production predicateは無変更で、現在の受理集合・certified値は変わりません。将来の過剰拒否を検出する5 nodeの検出力喪失は段7で記録が必要です。
- waiver理由 `codex-sandbox-readonly-dotcodex` は識別子形式に適合します。[D105:4682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/decisions.md:4682) に従い、最終trailer blockにはこのwaiverだけでなく、代行した主体の `AI-Agent: ...; role=author` も必要です。commit前なので現時点では未検証です。

pytest、`check_codex_agents.py`、`check_docs.py`、buildはこのレビューではすべて未実走であり、緑とは判定していません。実施したのはdiff、source、pin、renderer期待byteの静的照合だけです。

## 総括

- **GO**。
- must-fixは **0件**。
- 機械拒否側5項目はすべて現行mainの規則と一致。
- 部分執行・非検査側にも完全執行項目の誤格下げなし。
- 禁止5 bulletは基準mainからbyte不変で、意味上の限定もなし。
- 許可への誤読と偵察firewallの問題は閉じている。
- A3根本配線とA4記録は残余、A5は正規waiver trailerのcommit前確認が必要。
- pytest、checker、buildは未実走。