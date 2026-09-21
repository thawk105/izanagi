# 段 1 pin 閉包 (DW-O09) — 親がまとめた結論 (調査は read-only の子 1 本、要点は親が現物で再確認)

base = `36fb14a3d`。変更前 sha256: `plot_a1_sized_paired.py` `b2750799…`、`test_plot_a1_sized_paired.py` `b289ec70…`、
`docs/paper-story/figures/README.md` `34d22907…`、`tools/plotting/README.md` `c7481836…`。

## 実行時に照合される pin

1. `orchestrator/tests/test_plot_a1_sized_paired.py:25` が生成器を `importlib` で直接 exec する (唯一の生成器実行 pin)。
2. `docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.provenance.json` の `generator.sha256` = `b2750799…` は**記録であって照合されない**。
   `validate_repo_closure` (生成器 399〜410 行付近) は `generator.path` だけを見て sha256 を再照合しない。
   `test_generator_comment_change_preserves_provenance_closure` (test 370〜378 行) がこの性質を明示的に検査している。→ 生成器の bytes を変えても fig9 の凍結 provenance は書き換え不要。
3. `validate_repo_closure` の `provenance["schema"] == SCHEMA` (`izanagi-a1-sized-paired-figure-provenance/v1`)、`provenance[key] == value` (load_leaf の全 key)、
   着地 png/pdf の SHA-256、artist / caption の再投影一致。**attempt-0001 の load_leaf 返り値の key 集合・値と `_caption` の出力は不変でなければならない。**
4. fig9 着地 test (`test_landed_fig9_repo_closure_and_caption_when_present`、test 471〜486 行) は `prefix.parent / "README.md"` を相対構築で読み、
   H1 見出し `# \`<basename>\` — ` で自節を切り出し、`## 着地 bytes の SHA-256\n` 節の `^- \`<file>\` SHA-256: \`<64hex>\`$` がちょうど 1 行 × 3 file、
   `prov["caption"] in readme` を要求する。**自節だけを見る**ので fig14 / fig15 節を足しても fig9 は影響を受けない。fig13 (`test_plot_b10_waiting_grid_forest.py:623〜635`) も同型。
   他図 (fig2 / fig5〜7 / S1a / B7 / B10 等) の test も同 README の自節を同型に照合するので、既存 H1 見出しと区切り (`\n# `) を崩さない。
   同 README には照合されない `## 着地 bytes の SHA-256 (記録)` variant (fig3b 系・fig10 系) もある。fig14 / fig15 は照合される方 (fig9 / fig13 型) を使う。
5. `test_pinned_input_hashes_match_results_document` (415〜420 行) と `test_real_leaf_loads_and_matches_results_document` (455〜467 行) が
   attempt-0001 稿 `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` の `### 5.1`〜`### 5.2`・`### 2.1`〜`### 2.2` を生きた pin として持つ
   (稿は凍結物で変えない)。attempt-0002 稿も同じ節構造 (`### 2.1` / `### 2.2` / `### 5.1` / `### 5.2` の見出しを実測で確認済み)。

## 照合されない / 予算なし

- `tools/plotting/README.md`: 実行時 pin 0 件 (`orchestrator/tests/`・`tools/check_docs.py` への grep 0)。byte / 行数予算なし。
- `docs/paper-story/figures/README.md`: `tools/check_docs.py` の `LIVING_DOCS` に入らず (paper-story 系は追記型で lint 対象外)、byte / 行数予算・exact pin なし。
- `fig14` / `fig15` (basename・`Figure 14/15`・`図14/15` の全形): tracked 全体で 0 件 (偶然の部分一致 1 件のみで無関係)。未予約。

## 新規 test node の登録台帳

- 唯一の該当: `orchestrator/tests/acceptance_duration_ledger.json` (`duration_seconds_by_nodeid`、現在 26,605 node、`nodeid_count` 一致必須)。
  消費者 = `orchestrator/tests/conftest.py` (xdist 順の重み)、`tools/acceptance_shards.py` (shard 割付の重み)。
  gate = `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` (収集 node に対する被覆 ≥ 90%)。
- 先例: fig13 wave は新 test file の node を登録せず着地し、後の [T-2825] の refresh (`26387b617`) で登録された (`git log -S`)。
- F902: main の余裕が薄いと新 node を足す wave が被覆 gate を赤にする。是正は `python3 tools/update_acceptance_duration_ledger.py --add-only <実走 JUnit>` だけ (手編集禁止)。
  台帳は実装面 (D95 決定 2、Codex author が producer を走らせる)。
- **親の provisional 裁定 (P9):** 被覆の余裕を login の `pytest --collect-only` で実測中 (段 4 で確定)。余裕が十分なら登録しない (fig13 先例、依頼の「台帳の追加は scope 外」)。
  足りない場合だけ段 6 で Codex author が `--add-only` で登録する。
- **実測 (2026-09-21 20:59〜21:00 JST、login、worktree base `36fb14a3d`):** `python3 -m pytest --collect-only -q orchestrator/tests -p no:cacheprovider` rc=0、
  27,049 node 収集 (46.21 s、log = job dir `collect-only.log`)。台帳との交差 26,558 → 被覆 98.18%。90% を割るまで未登録 node をあと 2,459 本足せる。
  本 wave の追加 node は数十本の見込みなので **P9 = 登録しない** (段 4 で確定扱い)。
