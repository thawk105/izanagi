# 段1 brief — [T-646] floor_protocol.json master_seed TOCTOU

**scope**: carry [T-646] (`docs/archive/worklog-phase3-0808-306.md:469-473`) が今も
現行 driver で再現するかを確定し、再現する経路があれば `output/s8b-freeze/floor_protocol.json`
の `master_seed` を検証済み bytes (git blob / receipt.source_commit) 由来に固定する。
[T-647] は明示的に scope 外 (ユーザー指示)。production 変更が要るなら
`orchestrator/campaign/s8b_floor_campaign.py` 系のみを対象とし、CCBench/variant には触らない。

**確定済み事実 (P1、段3 攻撃対象、詳細と実測ログは
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t646-master-seed-toctou/handoff.md`)**:
主経路 (`run_campaign`/CLI `main()`、`s8b_floor_campaign.py:5588-5675,7075-7097`) は
`_require_supplied_protocol_authority` が `resolve_current_floor_protocol`
(HEAD の git blob由来、working tree bytes を lineage authority に使わない) と供給
protocol の byte-exact 一致を副作用前に要求しており、commit `cca78d3d` (2026-08-17,
[T-419](3)/[T-1255]) 以降 T-646 の主張どおりの working-tree-only 書換えは fail-closed
拒否される。実測 (`load_protocol`→`validate_protocol`→`run_campaign` を実 production
関数で通した使い捨て repro) で確認済み。PBS 側 (`tools/pegasus/floor_campaign.sh:1160-1186`)
も `resolve-current-protocol` 経由で `PROTOCOL_PATH` を得ており静的パス直渡しではない
(`:731-745` で receipt.source_commit との一致も別途検査済み)。

**未確定 (P2、段2 の主目的)**: `_floor_contract.build_schedule` の他呼出し
`s8b_ratified_freeze.py:1881`、`s8b_holdout_freeze.py:1444`
(commit cca78d3d が resolver 配線対象外とした「証明鎖歴史錨定」「producer write-path」) の
`protocol` 引数の出自を file:line で遡り、raw working tree 読み込みが残っていないか確認する。
`grep -rn "_FLOOR_PROTOCOL_REL\|floor_protocol.json" --include=*.py orchestrator/` の
全 hit (非 test) を「resolver 経由」「固定 commit git blob」「raw 読込」「無関係」に分類する。

**不変条件**: 正しさゲート (規律2) を緩めない。修正が要る場合、通る正例
(正当な reseal コミット後の resolve は成功する) を必ず添える。fail-closed 方向のみ強化する。

**成果物の形**: 段2 plan は上記 P2 の分類結果表 + (real なら) file:line 単位の修正案、
または「両経路とも安全」の根拠を返す。

**成果物影響 (DW-G05)**: P2 が real (raw working tree 読込が残る) のまま放置すると、
その consumer の受理 (`RatifiedFreeze` 検証 or holdout freeze 発行) が working-tree-only
書換えで欺ける可能性が残る。P1 の主経路は既に安全なので、放置してもライブ campaign 起動
(実際の測定 schedule) 自体への影響はない — 影響があるとすれば proof-chain 検証/producer
write-path 限定。

**分割方針**: 単一 codex plan (read-only)。分割不要 (対象2ファイルは独立小箇所)。
