### [B] `v3` 受入 receipt の並行 wave が `v4` land で拒否される

再現/影響: 本 wave 以前に発行された `dev-wave-acceptance-receipt/v3` は、land 側の exact field 集合と schema version が `v4` になると拒否される。[dev_wave_land.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_land.py:499) [dev_wave_land.py:544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_land.py:544)

並行 wave を停止して receipt を消化する運用、または旧 v3 の legacy branch を残す移行計画が必要。現状のままでは blocker。

### [B] land 側で registry 証拠の意味閉包が成立していない

再現/影響: 計画の受入 receipt は `ratified_nodeids` と SHA 類を投影するが、`checked_on` や `entries_used` を持たない。land が checker receipt 本文を読まないなら、期限切れ・未登録 nodeid を含む構造上正しい receipt を意味的に拒否できない。

`checker_receipt_sha256` を再読して検証するか、期限・登録集合を受入 receipt へ投影して land でも検査する必要がある。

### [B] `_PINNED_GUARD_PATHS` は registry の書込み禁止ではない

再現/影響: [check_codex_hooks.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_codex_hooks.py:296) は working bytes と HEAD blob の drift を検査するだけで、[guard_write.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/hooks/guard_write.py:238) は `hooks/` と成果物 tree 以外を拒否しない。Codex 子は `tools/acceptance_red_registry.json` を直接変更できる。

`check_codex_hooks.py` への追加だけを「人間だけが書ける防壁」と扱わず、実効 gate を `guard_write` / `guard_bash` に追加するか、P1 を未解決のまま実装しないこと。

### [B] I2 の「完全に同一」と receipt schema bump は両立しない

再現/影響: `tested_main` に registry が無い場合、受理集合・分類・rc は現行と同じになる。しかし checker receipt は `registry` field、受入 receipt は v4 の追加 field を持つため、receipt bytes は必ず変わる。

正しい表現は「受理集合・分類・rc は同一、receipt bytes は変更」である。さらに不正 registry は計画どおり rc=2 とするなら、「読めない場合も全件 attributable」という I2 の文言も分離して裁定が必要。

### [M] exact field のテスト consumer が列挙から漏れている

再現/影響: [test_dev_wave_wait.py:1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/orchestrator/tests/test_dev_wave_wait.py:1475) の root field 集合、同ファイル [592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/orchestrator/tests/test_dev_wave_wait.py:592) の `_RedCheckResult` fixture、[test_dev_wave_land.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/orchestrator/tests/test_dev_wave_land.py:236) の receipt fixture も更新が必要。

schema literal の更新だけでは、fixture の exact 集合拒否や dataclass 引数不足が先に発火し、新設 gate のテストにならない。

### [M] loader の直接 CLI import 契約が未定義

再現/影響: `check_acceptance_reds.py` は直接 `python3 tools/check_acceptance_reds.py` で起動され、repo root を `sys.path` に追加していない。`from tools.acceptance_red_registry import ...` は CLI で失敗し、相対 import は既存の spec import と衝突し得る。

同じ directory からの安全な import または明示的な loader を定め、直接 CLI とテスト import の両方を静的検査対象にすべき。失敗すると赤受入だけが checker rc=2 になる。

### [M] Git blob 読込み面の負の corpus が不足している

再現/影響: `O_NOFOLLOW` は不要だが、Git tree mode `120000` 等の symlink、`ls-tree` 非 0、複数 record、`cat-file -s` 超過、blob 読込み失敗は raw bytes loader のテストでは検出できない。

mode 検査、サイズ確認後の blob 読込み、空出力と Git command failure の区別を、それぞれ checker integration で確認しないと、読込み失敗を missing 扱いする fail-open や巨大 blob capture が残る。

### [M] 事前登録変異の単一理由性が未確定

再現/影響: 1、2、4 はそれぞれ wave-tip 混入、期限切れ、prefix 一致の valid fixture があれば単独で落ちる。3 は registry load を `_probe_nodes` より前に置き、probe sentinel を持たせないと後段失敗に置換される。

5 は registry nested field 以外を完全に valid にした checker receipt、6 は producer を通さず全 v4 field を埋めた land receipt が必要。そうでなければ exact schema や producer validation が先に発火し、mutation が本来の理由で落ちた証拠にならない。

### [n] 親 brief の probe anchor が不正確

再現/影響: [brief.md:32](/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1116-known-red-registry/brief.md:32) の `check_acceptance_reds.py:1206` は worktree add 呼出しの途中であり、呼出し開始は 1202、対象 command は 1204-1205。

レビューの停止要因ではないが、`_probe_nodes` の生成点を示す anchor としては 1202-1205 が正確。

### [n] `_SCHEMA_VERSION` の宣言位置が receipt 範囲と混同される

再現/影響: 親 brief の [41行](/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1116-known-red-registry/brief.md:41) は `_SCHEMA_VERSION` と receipt 構築範囲を併記するが、宣言自体は [check_acceptance_reds.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_acceptance_reds.py:22)、receipt への代入は 1469。

実装対象の案内としては分けて記載した方が誤読がない。

## 総括

NO-GO。  
`child-green` は、v4 の追加 field を空/null で生成し land が検査すれば着地可能。  
registry が無い tested main の赤は、従来どおり attributable となり、新しい自己救済経路は生まれない。  
`ratified-known-red-only` も、wait と land が旧 status と新 status だけを許せば伝播経路は閉じる。  
ただし並行中の v3 receipt 拒否、land 側の registry 意味閉包、I2 の bytes 矛盾が blocker。  
pytest・実測・Web 検索は行っていない。