判定は **NO-GO** です。現行実装自体は裁定どおりですが、事前登録変異 **M6 がテストを生存します**。以下は静的判定であり、pytest・mutation harness は実走していません。

## 最重要所見

**M6 の producer 流用変異を MF3a テストが殺せない。**

- **判定: real**
- 根拠: テストモジュールは収集時に `S` を先に import します（[test_s1_direct_comparison.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:35)）。producer の monkeypatch はその後のテスト実行時です（[test_s1_direct_comparison.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:487)）。裁定どおり allowlist 定義を import 時の `frozenset(s1_measurement_freeze.CONFIGURATIONS)` に置換すると、現行 producer の同じ6値（[s1_measurement_freeze.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_measurement_freeze.py:40)）を既に snapshot 済みです。後から7値目を加えても `_PREPARE_CELL_CONFIGURATIONS` は6値のままで、[prepare_cell の拒否:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:506)が通常どおり発火し、テストは緑のままです。固定集合の等価テスト（[test_s1_direct_comparison.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:425)）も現行6値同士なので通ります。
- **成果物影響**: 将来 producer に7個目が追加された際、変異実装はその値を自動認可し、4分岐外から flags-only の `src_token` を生成して（[s1_direct_comparison.py:545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:545)、[同:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:570)）、certified 候補の受理集合を拡張し、材料レポート・試行台帳に未承認 configuration とその参照を載せます。
- **最小対処**: producer を7値に monkeypatchした後で、`s1_direct_comparison.py` を別 module 名として隔離 importし、その fresh module の `prepare_cell` で拒否を確認してください。M6 適用時にこの node だけが checkout sentinel 到達で赤になることも確認します。

このため、[impl.md:13](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/impl.md:13)および[impl.md:33](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/impl.md:33)の「MF3／producer monkeypatch を網羅」は実コードと食い違います。

## M1〜M8 静的 kill 判定

ここで `refuted` は「殺せない疑いを反証できた」の意味です。

| 変異 | 判定・file:line | 赤の単一理由 | 未封鎖時の成果物影響／最小対処 |
|---|---|---|---|
| M1 | **refuted**。[代入: p3_s4_loop.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:211)、[test:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_p3_s4_loop.py:212) | 削除すると padded 側だけ `edited`/`diff` が exact 側と異なり、[232–233相当:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_p3_s4_loop.py:232)で赤。 | 同一述語の source/token/variant が分裂。対処不要。 |
| M2 | **refuted**。[guard:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:211)、[sort test:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_p3_s4_loop.py:236) | guard を外すと sort comparator に trigger canonicalizer が適用され、拒否または逐語 bytes 改変だけで赤。 | sort の受理集合・source 参照が変化。対処不要。 |
| M3 | **refuted**。[return:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:110)、[synthetic test:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_trigger_gate_binding.py:240) | 注入した raw emitter 値と `text.strip()` の戻り値だけが相違。 | binding digest と材料 source の対応がずれる。対処不要。 |
| M4 | **refuted**。[重複検出:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:89)、[import負例:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_trigger_gate_binding.py:253) | overwrite 変異では期待する import-time `RuntimeError` だけが消える。 | emission 順依存の source/binding 参照になる。対処不要。 |
| M5 | **refuted**。[拒否:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:506)、[unknown test:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:466) | 拒否削除時は有効 flags の未知値が checkout sentinel（[473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:473)）へ到達。 | 未承認 configuration が certified 集合・レポート・台帳へ混入。対処不要。 |
| M6 | **real**。[ruling.md:114](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/ruling.md:114)、[test:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:487) | import 後 monkeypatch のため赤が存在しない。 | 最重要所見どおり。fresh import に修正。 |
| M7 | **refuted**。[unknown 3値:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:466) | `"system-gate"` だけ拒否する変異では、残る2値が checkout sentinel に到達。 | 未列挙値が材料レポート・台帳へ混入。対処不要。 |
| M8 | **refuted**。[stock literal:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:54)、[flags-only正例:436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:436) | `stock_common` を削ると正例が allowlist で拒否されるだけ。 | stock control が受理集合から消え、certified 比較・レポート・台帳が欠落。対処不要。 |

## must-fix と恒真性

- **MF1 — refuted（静的には充足）**: synthetic index は検証対象外で構築した raw 値を期待値にし、7種を独立列挙しています（[test_trigger_gate_binding.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_trigger_gate_binding.py:26)）。重複 key 負例も実在します。自己オラクルではありません。
- **MF2 — refuted（静的には充足）**: 実 `quarantine` の `edited_text`/`working_diff` を7種で byte-exact 比較しています（[test_p3_s4_loop.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_p3_s4_loop.py:223)）。別テストは本番 `source_digest.resolve` を直接呼びます（[test_s1_direct_comparison.py:510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:510)、[source_digest.py:879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/source_digest.py:879)）。toolchain 不在時は skip せず fail します（[test_s1_direct_comparison.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:192)）。
- **MF3 — real（部分充足）**: 固定6値の本番実装と複数未知値拒否は正しい一方、producer 独立性の behavioral 証明だけが未充足です。
- **恒真性 nit**: [test_s1_direct_comparison.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:528)と[同:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:542)の `pipeline.variant_id` 比較は、直前の token 等価と同じ関数の再呼出しから自動的に成立し、独立保証を追加しません。**成果物影響なし**—token 等価自体は固定済みです。最小対処は削除、または別途固定した独立 golden に置換です。

## 既存テスト・報告・scope

- **既存期待値変更の疑いは refuted**: テスト差分の削除は `test_p3_s4_loop.py` の7行だけで、旧 trigger fixture 構築を新 helper（[test_p3_s4_loop.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_p3_s4_loop.py:106)）へ移したものです。既存 assert の反転・緩和・skip・削除はありません。
- `git status` は production 3ファイル＋test 3ファイルだけで、docs・output・凍結成果物の変更はありません。
- collect-only の203 node は既存ログに実在しますが、[impl.md:23](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/impl.md:23)どおりテスト本体は0件です。実走済みとする架空 nodeid や偽緑の主張はありません。
- SP1/SP2/SP3 は正しく scope 外のままです。`diffq_variant_id` は raw implementation hash のまま（[p3_s4_loop.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:241)）で、build admission/pipeline の畳み込みも変更されていません。
- **nit**: [impl.md:8](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/impl.md:8)のリンクは `p3_s4_loop.py:202` ですが、正準化代入は現在211行です。成果物影響なし。リンク更新だけで足ります。

## 総括

- **NO-GO**。
- M6 の exact な事前登録変異が、import 順序のため MF3a を生存する。
- 現行 production 実装は裁定どおりだが、producer 独立性が regression として固定されていない。
- MF1・MF2、M1〜M5・M7・M8 は静的には単一理由で kill 可能。
- 既存期待値の緩和・skip・削除および scope 外実装はない。
- pytest は未実走であり、緑とは認定していない。