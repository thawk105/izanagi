# 段 4 裁定 追補 1 — 世代文書 {G} 検査の path 選択 (2026-09-20 20:2x JST、焦点走 1 の赤 1 件への対処)

## 事実

- 焦点走 1 (`focus/focus-impl-1.log`、request 13500.nqsv、10 file、249.8 s): **974 passed / 13 skipped / 1 failed**。赤 = 既存
  `orchestrator/tests/test_s8b_ratified_verify.py::test_generation_two_rejected_before_artifact_io` (sealed fixture、production emitter の g1 → g2 chain)。
- 失敗本文: `[binding-chain-mismatch] output/s8b-freeze/holdout_freeze.v2.g1.json の introduction set != {G}` — 段階 6 に足した世代文書 {G} 検査
  (裁定 §2-2 項 3、`_gen_path(ratified.generation_number)`) が投げた。
- この既存 test は、g2 の `RatifiedFreeze` の **`generation_number` だけを 1 に射影**し (`generation_commit` は g2 の G のまま、resolver も scope 1 へ
  monkeypatch)、「generation-scope 以外の gate はすべて green」を pin する。新検査は `_gen_path(1)` = g1 の世代文書 (導入 = g1 の G) の導入集合が
  g2 の G と一致することを要求するので、この射影 fixture では構造的に満たせない。**既存 test の期待値は誤りではなく、裁定 §2-2 項 3 の path 選択
  (`generation_number` から引く) が、`generation_number` ↔ G の束縛を段階 6 で新たに課す形になっていた**ことが原因 (本差分に帰属)。

## 裁定 (追補)

世代文書 {G} 検査の path を `ratified.generation_number` から引かず、**`ratified.generation_commit` (G) 自身が追加した path から引く**:

- `_added_paths(gen_commit, root)` (既存 helper、H-pure、非 merge commit の diff-tree) の追加 path 集合のうち `_GEN_RE`
  (`^output/s8b-freeze/holdout_freeze\.v2\.g([1-9][0-9]*)\.json$`) に一致する path が **ちょうど 1 つ** であること (0 個 / 2 個以上は
  reason `binding-chain-mismatch` cause `generation-introduction` で拒否)。
- その path の H における導入集合 (`_immutable_introductions(graph, path, oid, root)`、oid は `_tree_mode_oid(head, path, root)`) が **== {gen_commit}** であること
  (不一致は同 reason / cause)。
- `generation_number` と path 中の世代番号の一致は要求しない (その束縛は段階 2 の `generation_number != 1` 拒否と段階 7 の active chain 再解決が担う)。
- G が merge commit なら `_added_paths` の追加集合は空になり 0 個で拒否 (fail-closed。現物 G は非 merge、V1a で批准側も保証)。

受理集合の含意: (受理) G が世代文書 1 file を追加し、その file の導入が G だけ — 現物 G `32ba8cae4` (g1.json のみ)、独立 fixture (default / option とも g1.json)、
production emitter の g1 / g2 chain (各 G が自世代の 1 file)。(拒否) `generation_commit` を A に偽装 (A が追加するのは approval record で `_GEN_RE` 不一致 → 0 個)、
G を「世代文書を追加しない commit」に偽装、世代文書を 2 file 同時に追加する commit、世代文書が別 commit で先に導入されている (削除→再作成)。
既存負例 `test_floor_source_introduction_must_be_exact_generation_commit` (wrong_g=A) と新 `test_t2810_generation_introduction_independent` の期待
(reason `binding-chain-mismatch` / cause `generation-introduction`) は不変。`test_generation_two_rejected_before_artifact_io` は無変更で緑になる見込み
(fix2 後の焦点走 2 で実測)。

γ 的な代替 (世代文書 {G} 検査を丸ごと外し、既存負例の期待 cause を段階 7 の `scan-exemption-invalid` に変える) は「既存 test の期待値を変える」ので採らない。
`resolve_active_generation` を段階 6 で呼ぶ案は段階 7 と二重で、段階 6 の H-pure な独立性 (resolver の結果を使わない) を崩すので採らない。

## 変異事前登録の更新 (§3 M12)

M12 の old 文字列は fix2 後の新 block に差し替える (「世代文書 {G} 検査 block 全体の削除」の意味は不変)。M12 の帰属は RA-1 のとおり
「拒否段階 / cause の契約検出」として別枠に記録する。他の変異 (M0〜M11、M13、M14) は fix2 で old 文字列が変わらないことを spec 生成器で再検証する (DW-M07)。

## 実行

fix2 = Codex fix 子 (子木 `t2810-unit-impl`、branch `dev-wave-t2810-unit-fix2`、base = fix1 終端 commit `7d6040c8c`)。編集は
`orchestrator/campaign/s8b_ratified_freeze.py` の段階 6 の世代文書 {G} block だけ。test は編集しない (既存の期待が満たされるのが目的)。
fix2 統合後: 焦点走 2 (焦点走 1 の 10 file + DW-O26 の consumer 7 file = 17 file)、held 診断走、変異 (probe → final)。
