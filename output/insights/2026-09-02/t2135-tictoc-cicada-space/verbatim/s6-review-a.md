## 読んだ資料

指定された 6 資料はすべて読み取り可能で、静的検査対象として確認した。

- [s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s4-ruling.md:103)
- [s6-integrated.diff](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s6-integrated.diff)
- [s5-author.md](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/artifacts/dev-wave-t2135-tictoc-cicada-space/s5-author.md)
- [genome.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:1)
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/tests/test_campaign.py:1)
- [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/model.py:39)

## 裁定契約の逐条照合

| 項目 | 充足/不充足 | 根拠 |
|---|---|---|
| tictoc の 5 軸 | 充足 | 指定された 5 軸だけを `[0,1]` で定義している。[genome.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:147) |
| tictoc の制約 | 充足 | `_tictoc_no_wait_not_both` は `(1,1)` だけを拒否し、XOR ではない。[genome.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:74) |
| tictoc の生 32・有効 24 | 充足 | 5 ブール軸、制約対象 pair は 4 組中 3 組なので `32 * 3/4 = 24`。test も両方を固定する。[test_campaign.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/tests/test_campaign.py:253) |
| tictoc の `PARTITION_TABLE` 除外 | 充足 | 軸になく、notes に死にフラグと検索範囲を記載。[genome.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:159) |
| tictoc の `SLEEP_READ_PHASE` 除外 | 充足 | 軸になく、計測撹乱ノブと一次資料位置を記載。 |
| tictoc の導出不能軸なし | 充足 | notes に bare define と残存候補がない旨を明記。 |
| tictoc notes: 除外理由と一次資料の性質 | 充足 | `.cc/.hh`、workload source、共通 header、`transaction.cc:68-70` を明記。 |
| tictoc notes: `(1,1)` の冗長性 | 充足 | `(1,0)` と同一になる理由を `#if/#elif` まで記載。 |
| tictoc notes: silo XOR との差と理由 | 充足 | 内側 spin loop と `transaction.cc:626` の再読込、stale-expected 機構との差を記載。 |
| tictoc notes: 進行性の限界 | 充足 | 完走性・公平性・starvation は未実測と明記。 |
| tictoc notes: YCSB で 24、静的導出 | 充足 | 両方を明記。 |
| tictoc notes: bare define・残存候補なし | 充足 | 両方を明記。 |
| cicada の 5 軸 | 充足 | 指定された 5 軸だけを `[0,1]` で定義している。[genome.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:178) |
| cicada の含意制約 | 充足 | `not PROMOTION or OPT` で `PROMOTION ⟹ OPT` を正しく実装。[genome.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:91) |
| cicada の生 32・有効 24 | 充足 | 5 ブール軸、含意違反 `(0,1)` の 8 genome だけを除外。test も両方を固定する。[test_campaign.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/tests/test_campaign.py:298) |
| cicada の `SINGLE_EXEC` 除外 | 充足 | 軸になく、多版から単版へ測定対象を変える旨を記載。 |
| cicada の `PARTITION_TABLE` 除外 | 充足 | 軸になく、print 専用かつ README と現行コードが不一致と記載。 |
| cicada の delay 3 軸除外 | 充足 | 3 名すべてを列挙し、計測撹乱ノブと記載。 |
| cicada の導出不能軸なし | 充足 | notes に bare define と残存候補がない旨を明記。 |
| cicada notes: `WRITE_LATEST_ONLY` | 充足 | 読み側の可視性は不変、保守側に余分な abort と記載。 |
| cicada notes: promotion の冗長性 | 充足 | `(0,1)` と `(0,0)` は CC/data path が同一と限定している。 |
| cicada notes: 完全 inert としない | 充足 | 起動時 option 表示だけは異なると明記。 |
| cicada notes: fresh configure の限界 | 充足 | default 0 と、既存の非標準 CMakeCache を戻す主張ではない旨を記載。 |
| cicada notes: YCSB で 24、静的導出 | 充足 | 両方を明記。 |
| 2 space の登録 | 充足 | `SPACES` に双方を追加し、登録 identity test がある。[genome.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:205) |
| 旧未登録 test の差し替え | 充足 | 指定された旧 test だけを登録期待へ差し替え、軸・制約・除外・notes test を追加。[test_campaign.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/tests/test_campaign.py:248) |
| 実装しないもの | 充足 | 差分は指定の 2 Python ファイルだけで、gate・台帳・汎用化・凍結成果物変更はない。 |

不充足項目はない。

## 禁止事項の違反

なし。

統合差分と現在の `git diff` が byte 単位で一致することを確認した。変更は `genome.py` と `test_campaign.py` のみで、`_no_wait_xor`、`SILO_SPACE`、`MOCC_SPACE` は差分上の文脈行に現れるだけで変更されていない。既存 test の変更も、明示された未登録 test の差し替えだけである。

## 変異ごとの期待赤 test

- M1 `TICTOC_SPACE.constraints = []`

  赤の完全集合:

  - `test_tictoc_space_has_twenty_four_operable_ycsb_boolean_genomes`
  - `test_tictoc_space_excludes_redundant_double_no_wait_but_keeps_wait_pair`

  有効数が 32、pair が全 4 組になる。

- M2 tictoc 述語を silo XOR に変更

  赤の完全集合:

  - `test_tictoc_space_has_twenty_four_operable_ycsb_boolean_genomes`
  - `test_tictoc_space_excludes_redundant_double_no_wait_but_keeps_wait_pair`

  有効数が 16、pair が `{(0,1),(1,0)}` になる。

- M3 `CICADA_SPACE.constraints = []`

  赤の完全集合:

  - `test_cicada_space_has_twenty_four_operable_ycsb_boolean_genomes`
  - `test_cicada_space_requires_inline_opt_for_promotion`

  有効数が 32、pair が全 4 組になる。

- M4 制約を逆向きの `OPT ⟹ PROMOTION` に変更

  赤の完全集合:

  - `test_cicada_space_requires_inline_opt_for_promotion`

  有効数は 24 のままだが、pair は `{(0,0),(0,1),(1,1)}` になる。

- M5 cicada に `SINGLE_EXEC` 軸を追加

  赤の完全集合:

  - `test_cicada_space_has_twenty_four_operable_ycsb_boolean_genomes`
  - `test_cicada_space_excludes_semantic_dead_and_measurement_axes_and_names_ycsb_scope`

  生 64・有効 48となり、除外軸 assert にも抵触する。

- M6 tictoc に `PARTITION_TABLE` 軸を追加

  赤の完全集合:

  - `test_tictoc_space_has_twenty_four_operable_ycsb_boolean_genomes`
  - `test_tictoc_space_excludes_dead_and_measurement_axes_and_names_ycsb_scope`

  生 64・有効 48となり、除外軸 assert にも抵触する。

- M7 `SPACES` から tictoc と cicada を削除

  赤の完全集合は、今回追加された 7 test すべて:

  - `test_tictoc_and_cicada_are_registered`
  - `test_tictoc_space_has_twenty_four_operable_ycsb_boolean_genomes`
  - `test_tictoc_space_excludes_redundant_double_no_wait_but_keeps_wait_pair`
  - `test_tictoc_space_excludes_dead_and_measurement_axes_and_names_ycsb_scope`
  - `test_cicada_space_has_twenty_four_operable_ycsb_boolean_genomes`
  - `test_cicada_space_requires_inline_opt_for_promotion`
  - `test_cicada_space_excludes_semantic_dead_and_measurement_axes_and_names_ycsb_scope`

pair の assert は恒真ではない。`[0,1]` の 2 軸だけなら 4 pair が生成され、現在期待する 3 pair は制約適用後にだけ成立する。7 変異すべてに赤 test があり、変異していない現物について静的に必然的に落ちる test は見つからない。pytest は実走していない。

## must-fix

なし。

指定された各変異は少なくとも 1 test に検出され、現物の受理集合、軸、登録、notes は裁定契約と一致している。

## nit / backlog

- 裁定の M4 説明は逆向き制約の pair を `{(0,0),(1,1)}` 側と記すが、正確な集合は `{(0,0),(0,1),(1,1)}`。期待する赤 test は変わらず、現成果物への影響はない。
- cicada の notes test は `fresh configure` を確認する一方、「既存の非標準 CMakeCache を戻す主張ではない」という R11 の限定句自体は assert していない。現物には記載済みであり、現在の成果物影響はないが、将来その句だけが消える回帰は検出しない。
- notes test は明記どおり語句検査であり、C++ 一次資料の状態は検査しない。これは裁定で既知の backlog とされた範囲で、現在の受理集合への影響はない。

## 回帰・波及の自力検索結果

`orchestrator/` と `tools/` を、指定されたシンボル、import、辞書反復、登録数・登録済み一覧の期待値について検索した。

- production で `SPACES` または `space_for` を使用する外部 consumer はない。`SPACES` の参照は [genome.py:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:214) の lookup と未知 protocol のエラー表示だけ。
- `GenomeSpace` の生成箇所は `genome.py` 内だけ。`TICTOC_SPACE` と `CICADA_SPACE` の外部参照は今回追加された test だけ。
- 既存の `space_for` consumer は `test_campaign.py` の silo/mocc 明示参照だけ。辞書全体を反復しないため登録追加の影響はない。
- `SILO_SPACE` の直接 consumer は `p2_2.py`、`sanity_silo.py`、`search_baselines.py`、`guided.py`、`replay.py`、`s1_known_axes_freeze.py`、`tools/check_trace0_preprocess_identity.py` など。`SILO_SPACE` 自体が不変なので波及しない。
- `SPACES` を辞書として反復する箇所、外部の `sorted(SPACES)`、登録 protocol 数を数える箇所、旧 `['mocc','silo']` を焼き込んだ期待値はいずれも見つからない。
- 未登録 protocol のエラー文に含まれる登録済み一覧は 4 protocol へ増えるが、その文字列を固定する consumer/test はない。

`Genome.canonical()` は軸名順の `name=value` をカンマ結合し、protocol と `|` で結ぶ。[model.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/model.py:56) 新しい軸名はすべて英大文字と `_` だけで、`=`、`,`、`|` を含まない。値も整数 0/1であり、`protocol_from_floor_genome()` の分解・再 canonical 照合を通る。

## 総括

裁定契約に対する不充足、禁止変更、must-fix は見つからなかった。
7 変異はいずれも検出され、M7 は登録 test だけでなく追加 7 test 全件が赤になる。
pair 集合 assert はブール値域から自動成立する恒真式ではなく、制約の向きと有無を実際に検査する。
外部の `SPACES` 反復、登録数依存、固定済み登録一覧はなく、既存 production consumer への回帰は見つからない。
pytest・build・benchmark は実走しておらず、本報告は静的検査結果である。