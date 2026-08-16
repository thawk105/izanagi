# [T-1250] — 版を束縛した第 4 世代の条件契約 record の変異台帳と逐語

wave branch = `worktree-dev-wave-t1250-decider-version-generation`。
統合 commit = `53b0139044707a9f21b84fc49068fd1deecfb92c`。
変異は `tools/mutation_worktree.py` (固定 commit の使い捨て worktree) から
`tools/mutation_harness.py` を `--runner-mode dispatch` で起動した。runner argv には
`--force-dispatch` と `-rf` を含む (`DW-M07` / `DW-M08`)。

## 走行の履歴

| 走 | 目的 | spec | 結果 |
|---|---|---|---|
| 第 1 走 | probe (期待 node の導出) | `mutation-spec-probe.json` | baseline PASSED。6 件を全件 `SURVIVED` 期待で登録し、観測された失敗 node を集めた。6 件すべてが失敗を出した (`MISMATCH` はこの登録形の当然の帰結であり欠陥ではない) |
| 第 2 走 | 本走 (中止) | `mutation-spec.json` の旧版 | **起動前に中止。変異は 1 件も実行していない。** 下記「node ID の空間差」を参照 |
| 第 3 走 | **本走** | `mutation-spec.json` | baseline PASSED、**6/6 KILLED、MISMATCH 0**、wrapper rc=0 |

probe を挟んだ理由は、harness が `KILLED` 期待に**完全な期待 node 集合**を要求し、
期待 node が空の `KILLED` spec を起動前に拒否するためである (`DW-M07`)。

## node ID の空間差 (第 2 走の中止理由)

harness は 2 つの経路で node 文字列を扱う。

- `_failed_nodes()` は runner stdout の `FAILED ` 行を読む。pytest-xdist の `loadgroup`
  scheduler が有効なとき、`xdist_group` marker の付いた test の nodeid は
  `<path>::<name>@<group>` へ書き換えられており、この形のまま記録される。
- `_collect_expected_nodes()` は `--collect-only` の出力と突き合わせる。こちらに
  `@<group>` 接尾辞は現れない。

`_normalize_node()` は `::` の右側をそのまま保持するので接尾辞を落とさない。したがって
probe が記録した `...::test_x@s8c-preregistration-candidate` をそのまま期待 node に書くと、
**実在する node が「pytest collection に実在しない」と判定されて起動前に中止される。**
逆に接尾辞を落とすと、記録側が接尾辞付きのままなので集合が一致せず `KILLED` にならない。

本走は runner argv へ `-n 0` を加えて直列化し、両経路の表記を素の nodeid に揃えることで
解決した (`tools/run_tests.py` の `_xdist_requested()` は `-n 0` で False を返し、
xdist を engage しない)。期待 node は probe の観測値から機械生成しており、手で写していない。

## 変異と単一理由性

| ID | 変異 | 期待 KILL node 数 | 単一理由性 |
|---|---|---|---|
| M01 | 第 4 世代を wave 前の形へ戻す (schema v1 化 + `decider_version` key 除去) | 3 | 過剰決定。履歴不変検査が同時に発火する |
| M02 | 第 4 世代の `decider_version` を `s8c-decider/v2` へ | 3 | 過剰決定。同上 |
| M03 | 正本 doc の追記を除去し第 4 世代は据え置き | 2 | 保護 hash 不一致の単一理由。契約継続性検査は正しく生存する |
| M04 | 第 4 世代の `supersedes_sha256` を第 2 世代の hash へ | 3 | 過剰決定。同上 |
| M05 | §6 条件 4 を弱め、第 4 世代の条件 hash・集約 hash・normative・protected を整合的に再計算 | 3 | 過剰決定。同上 |
| M06 | 判定器の定数 `DECIDER_VERSION` だけを `s8c-decider/v2` へ | 6 | **版比較へ到達する唯一の変異。** freeze は valid のまま、候補連鎖検査も生存する |

### M06 が本 wave の中心的な証拠である

M01 / M02 / M04 / M05 は第 4 世代の bytes を変えるため、候補 commit と親 commit で
同一 path の blob OID が 2 つになり、`generation-mutated` が版の比較より先に発火する。
すなわちこれらの変異は**版束縛の検出力を証明しない** — 履歴不変検査に mask される。
段 3 の敵対相談レンズ A がこの mask を実装前に指摘し、親が M06 を追加登録した。

M06 は record を一切触らず走っているコードの定数だけを変えるので、freeze は valid のまま
版の比較へ到達し、`test_repository_tip_binds_current_decider_version_without_activation`
だけが実 repository 側で倒れる (`test_candidate_freeze_matches_contract_and_generation_chain`
は生存)。

### M06 が契約継続性検査を倒さないことが、R2 修正の実測裏付けである

段 6 の敵対レビューは、第 4 世代の版を**現在の定数**と比べる assert が将来の正当な版 bump を
機械的に塞ぐと指摘した。修正後は歴史的 literal を持つので、M06 (= 正当な bump の縮図) が
`test_generation_4_changes_revision_procedure_without_changing_condition_contract` を
倒さない。この生存は欠陥ではなく、修正が意図どおり効いたことの証拠である。

### 契約継続性検査の単独理由性は構造的に取れない

「§6 の条件を弱め、第 4 世代も整合的に作り直す」攻撃 (M05) は、freeze も版束縛も候補検査も
通り抜ける。親は変異前にこの整合的な record を計算で構成し、集約 hash が第 3 世代と食い違い、
変化した条件が 4 番だけであることを確かめている。しかし固定 HEAD の変異 harness では、
record の bytes を変えた時点で履歴不変検査が同時に発火するため、**この検査を単独理由で殺す
変異は作れない**。着地後の改竄に対しては `generation-mutated` と冗長である。
非冗長な価値は「発行の時点で条件を弱めていない」ことを恒久記録として固定する点にあり、
それは harness が到達できない層である。証明ではなく限界としてここに記す (`DW-M03`)。

## 逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 敵対相談 2 本、段 4 裁定、段 5 実装子、
段 6 敵対レビュー 2 本、段 6 fix の出力を置く。いずれも
`tools/check_codex_output.py` が rc=0 で受理したものである。
