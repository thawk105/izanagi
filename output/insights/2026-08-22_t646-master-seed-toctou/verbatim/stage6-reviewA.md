## レビュー結果

実所見は **0件**。全項目、攻撃したが崩せなかった。

1. **挿入位置 — refuted**

   [`s8b_holdout_freeze.py:1365`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:1365) で HEAD blob を取得し、1368–1371 で byte-exact 比較している。floor protocol の parse（1372）、`build_schedule`（1451）、candidate write（1867）より前である。

   攻撃シナリオ（HEAD の `master_seed=A`、worktree の canonical JSON だけ `B`、関連 artifact は `B` に整合）では `FreezeError` で停止し、schedule も candidate も生成されない。`generate` 冒頭の output validation は検査のみで、書込みではない。

2. **`head` の束縛 — refuted**

   [`s8b_holdout_freeze.py:1694`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:1694) で `rev-parse HEAD` の文字列を一度だけ取得し、40桁 SHA 検証後、1724 で keyword として渡している。`_validate_floor_inputs` 内で再捕捉していない。

   攻撃したが崩せなかった。

3. **既存 `_blob_at_head` の再利用 — refuted**

   [`s8b_holdout_freeze.py:319`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:319) は HEAD 側の blob bytes を返し、1368 の比較は canonical 化前の raw bytes 同士で行う。JSON の内部整合性を保った working-tree-only mutation でも検出できる。

   commit-verify、mode、replace-object の未検査は残るが、裁定済み scope 外であり、本目的の正しさを損なわない。

4. **例外・メッセージ — refuted**

   [`s8b_holdout_freeze.py:1369`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:1369) は既存の `FreezeError`（144）を使い、CLI の catch（1923–1925）で fail-closed に処理される。`measurement_closure` の既存メッセージ（1668–1670）とも表現が整合している。

5. **caller / consumer — refuted**

   [`s8b_holdout_freeze.py:1856`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:1856) は従来どおり `build_v2_g1_candidate` を呼び、実際の write は比較・全検証後の1867である。CLI（1917–1921）も同じ経路を通る。リポジトリ内に `_validate_floor_inputs` の別 caller はない。

   正常な reseal 後の HEAD blob 一致ケースも既存正例経路を維持している。攻撃したが崩せなかった。

6. **docs / commit — refuted**

   working tree の差分は次の2ファイルだけだった。

   - `orchestrator/campaign/s8b_holdout_freeze.py`
   - `orchestrator/tests/test_s8b_holdout_freeze.py`

   docs の差分、staged change、未追跡ファイルはなく、新規 commit も作成されていない。

## 総括

- real: 0件
- refuted: 6件
- 判定: 段4裁定どおりの fix が、意図した working-tree-only protocol mutation を fail-closed に拒否している。