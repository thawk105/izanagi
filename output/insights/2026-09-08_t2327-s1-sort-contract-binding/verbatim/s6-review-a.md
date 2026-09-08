## must-fix

- **real** — [source_digest.py:2231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/source_digest.py:2231): stock 短絡が sort binder より先にあります。  
  再現入力: `configuration="sort_best"`、oracle は PASS、適用後 tree の `current == baseline_digest` となる stock 同一 comparator。契約を `C1` から `C2` へ改版しても、両方とも `_resolved_src_token(...) -> STOCK` です。そのため [s1_direct_comparison.py:1201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s1_direct_comparison.py:1201) の `variant_id` と [s8b_materialization.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_materialization.py:119) の `src_token`、`variant_id`、`binding_sha256` は改版前後で同一です。campaign ID と WAL directory は宣言変更で分離されますが、要求された variant/cache 分離は成立しません。  
  **成果物影響:** 新契約の sort_best が旧契約と同じ variant identity と build-cache binary を再利用し、freeze binding にも契約改版が現れません。

## nit

なし。

## refuted

- **refuted** — campaign 宣言と oracle 値の自然な不一致経路。`config_for` は [s1_direct_comparison.py:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s1_direct_comparison.py:472) で実行中定数を宣言へ入れ、oracle receipt も [同:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s1_direct_comparison.py:901) で同じ定数との一致を要求します。改版後の通常 resume は新しい campaign ID の layout を選ぶため、旧 lock を再利用せず新 campaign になります。oracle receipt 由来の明示値は通常経路では宣言値と同値です。
- **refuted** — prepare/evaluate 間の不整合受理。通常経路では同じ `with prepare_cell` 内の checkout、pin、site cxx を使い、evaluate が [pipeline.py:1145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/pipeline.py:1145) で再解決します。途中変異や cxx 差は [同:1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/pipeline.py:1178) の token 不一致で拒否されます。retry は checkout を含む prepare 全体を再実行します。注入 `evaluate_fn` はテスト seam であり、production 再解決の代替ではありません。
- **refuted** — `resolve_evidence` が以前の拒否入力を新規受理する仮説。両窓口とも同じ tracked-status allowlist、include、conditional-macro 検査を通ります。`resolve_evidence` はさらに tracked diff の整合を検査するため、安定した入力の受理集合を広げません。
- **refuted** — 非 sort_best 漏れと backoff 相互排他。契約 ID は [s1_direct_comparison.py:914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s1_direct_comparison.py:914) の sort_best oracle PASS 後だけ設定され、s1 は `backoff_grammar_version` を同時に渡しません。
- **refuted** — F-P3/F-P4 以外の投影内 consumer 取り残し。直接 driver は token、variant、evaluate へ同じ値を渡します。`prepared_binding -> binding_from_prepared` は prepared の束縛済み token をそのまま variant と binding hash に使用し、再 resolve/build 境界を持ちません。F-P3/F-P4 は既知所見として除外しました。
- **refuted** — D1630 違反。`resolve()` / `src_token()` の public seam は不変、oracle import は関数内のまま、入口 gate の追加もありません。
- **refuted** — 非 stock の旧 freeze binding が黙って受理される仮説。契約変更で token、variant、binding hash が変わるため、旧値を期待する照合は拒否側へ倒れます。射影内に旧 token literal はありません。

## 総括

静的検査のみで、pytest は実走していません。  
通常の非 stock sort_best は identity、evaluate、cache に同じ契約 ID が届きます。  
追加 consumer 取り残しは投影内では見つかりませんでした。  
must-fix は stock 同一 bytes の短絡による契約改版分離の欠落 1 件です。