単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

作業木 (あなたが編集してよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-impl
所有 path (これ以外を編集しない): `orchestrator/tests/test_s8b_oracle_driver.py`
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s4-ruling.md — **親の段 4 裁定。「プラン v2」「変異の事前登録」が実装仕様の正本。** 所見表の A1 の裁定 (snapshot は gate を足さず docstring で明記) も従うこと。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s2-plan-out.md — 段 2 plan (参考。v2 と食い違えば v2 が優先)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-impl/orchestrator/tests/test_s8b_oracle_driver.py — 794〜1000 (列挙・複製・`_T080SharedBases`・`_t080_join_shared_bases`・`_t080_stub_free_e2e_repo`)、1036〜1230 (shared base test 群)、1390〜1470 (consumer AST 検査・builder)、1899〜2000 (全件性検査)。

## 実装すること

s4-ruling.md の「プラン v2」1〜4 をそのまま実装する。要点:
1. `_T080SharedBases.copy_visible_output(self, source_root, destination)` を足す。session の共有置き場の下に source_root ごとの写しを **1 回だけ**、flock 下で、**実関数 `_copy_git_visible_output(source_root, <写し>/output)` を呼んで**作る。完成 marker (`ready.json`、`output` の外、`*/complete.json` の glob に掛からない名前) を pending → rename で置く。marker が無い残骸は `_t080_remove_tree` で消して作り直す (`get()` と同型)。完成後は lock を離して `shutil.copytree(<写し>/output, destination)` (既定引数) で複製する。docstring に「写しは session で 1 回の snapshot であり、生成後の output/ の変更は後続 builder に反映しない。列挙・除外・全件性の検査は実関数が実 repo に対して行う」を書く。
2. builder (`_build_t080_stub_free_e2e_repo` 内、現 1458 行) は `_T080_SHARED_BASES` が None でなければ `_T080_SHARED_BASES.copy_visible_output(ROOT, root / "output")`、None なら従来どおり `_copy_git_visible_output(ROOT, root / "output")`。
3. test: 新規 1 本 + 既存 `test_t080_shared_base_builds_real_builder_once_across_processes` への assert 追加 (v2 §3 のとおり)。新規 test は小さい git repo と test 局所の `_T080SharedBases` (tmp_path 配下) を使い、実 repo を読まない・書かない。観測は `mock.patch.object(..., wraps=<実物>)` で実物へ委譲する形に限る (実関数を stub しない)。
4. 変えないもの: `_copy_git_visible_output`・`_git_visible_output_paths` の本体、`test_t080_output_copy_visibility_matches_production_enumeration` とその全件性検査 2 か所、既存 test の期待値、`get()`・`close()`・`_t080_join_shared_bases`、単独走の経路。仮想リスク向けの gate・検査・一般化・互換層を足さない。

## 規約 (DW-S05-B / DW-S05-C)

- 現行の受理・拒否挙動: builder は共有 session 下でも単独走でも実 repo の output/ を直接複製する。本変更は共有 session 下の複製元だけを写しに替え、fixture に届く集合・bytes・mtime を変えない。これ以外の受理集合変更をしない。
- 既存 test の期待値を変えない。xfail 化・skip・削除・緩和をしない。fixture へ現行 hash を差し込む等、test を甘くして緑にしない。期待値へ揮発 payload (tree hash、絶対 path、時刻の絶対値) を焼き込まない。
- 機構の正例は実体を名指しし、依存先を stub しない (新規 test は実 `_copy_git_visible_output` と実 `_T080SharedBases` を通す)。
- 例外文を比較する場合は `str(exc) == msg` の完全一致を避け、先頭行または `match=` で比較する。
- 変異の事前登録 M1〜M5 (s4-ruling.md) を、実装後の自分の test が**単一理由で**殺すかを静的に確認し、殺せない変異があれば理由と、どの assert を足せば殺せるかを報告する (変異そのものは実行しなくてよい。親が harness で走らせる)。
- テストの実走: repo root (= 作業木) を cwd に `PYTHONPATH=. python3 -m pytest -q -rf -p no:cacheprovider orchestrator/tests/test_s8b_oracle_driver.py -k "shared_base or visible_output or output_copy"` 程度の焦点走をしてよい。`test_t080_shared_base_builds_real_builder_once_across_processes` は実 builder を回して数分かかりうる。走らせられなければ「実装済み・未実走」と書く。緑は実走した nodeid と範囲を併記する。子の実走は親の全走を代替しない。
- 新設 test の名前が file 集合列挙・nodeid 台帳・consumer AST 検査 (1390〜1435 行付近の `helper_consumers` 等) に波及しないかを自分で洗い出し、関係する meta-test を走らせる。
- 報告に、所有外 caller・共有 fixture・consumer test への波及を静的に列挙する。

## 出力形式

- `## 変更` (関数・行・要旨)
- `## 実走` (コマンド、nodeid、結果。未実走はそう書く)
- `## 変異の帰属` (M1〜M5 それぞれ: kill する node、単一理由か、mask の有無)
- `## 波及` (所有外 caller・fixture・meta-test)
- `## 総括` (3〜6 行)
