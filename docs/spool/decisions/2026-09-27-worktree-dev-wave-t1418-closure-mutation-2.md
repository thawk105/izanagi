---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-27
wave: worktree-dev-wave-t1418-closure-mutation
seq: 2
---

## {{D:mutation-commit-injection}}. contract-loader 閉包の member を変異させるときは、変異 harness の commit 注入モード (`--inject commit`) で走らせる

**決定:**
- `tools/mutation_harness.py` に opt-in の `--inject {file-swap,commit}` (既定 file-swap) を置く。commit モードは detached HEAD の木でだけ起動し、1 変異ごとに注入 bytes を固定 identity (`mutation-harness@invalid`) の一時 commit M にして runner を走らせ、終了後に固定 HEAD H へ戻す (`reset --soft H` と touched の `restore --source=H`)。branch ref は動かさない。
- runner の前に M を検査する (親がちょうど H、H..M の変更 path が touched と一致、M の blob が注入 bytes と一致、作業木 clean、detached)。runner の後は、dispatch の orphan 判定を先に行い、hold でなければ HEAD==M・detached・bytes==M blob を再検査してから記録する。orphan hold では M を保持したまま停止する。
- 起動時に HEAD の author email が harness identity なら、モードを問わず fresh / resume / plan-only とも拒否する (kill で残った変異 commit を固定 HEAD として受理しないため)。
- ledger は v4 のまま。commit モードだけ procedure の `source_policy` / `restore_policy` を別の固定文言にし、既存の完全一致照合で resume をモードに束縛する。既定 file-swap の挙動と文言は変えない。wrapper (`tools/mutation_worktree.py`・`tools/mutation_fanout*.py`) は変えず、commit モードは harness を detached の登録 worktree (または detach した独立 clone) へ直接当てて使う。
- 閉包の一致検査 (`orchestrator/campaign/ident.py` → `contract_loader_binding.capture_contract_loader_binding`) と fixture は 1 byte も変えない。

**理由:**
- 閉包 member を file-swap で変異させると、disk と現 HEAD blob の一致検査が変異の中身と無関係に先に落ち、owner test の赤が値の層か drift かを区別できない。本 wave の実 dispatch で、loop.py の等価コメント変異と `sort_oracle_contract_id` 転送落としの値変異が、どちらも `contract-loader-drift` で同じ owner test を落とした。commit モードでは等価変異が SURVIVED、値変異は owner test だけが `KeyError: 'sort_oracle_contract_id'` で赤になった (`output/insights/2026-09-27/t1418-commit-injection/README.md`)。
- 一致検査を通すのではなく、検査が正しく一致する状態 (HEAD blob == disk) を作るだけなので、検査の受理集合は変わらない。
- F424 が名指しした `ratified_enforcement_source` fixture は b4ff38f6b で既に no-op であり、現行の drift 源は ident / contract_loader_binding である。

**却下した選択肢:**
- fixture 側 (または ident / binding 側) に変異検査用の opt-out を作る — D1712 が「変異中だけ contract loader 束縛を無効化する」を規律 2 違反として却下済み。
- ledger を v5 に上げて変異 commit の SHA を記録する — 木は `repo_head` と `injection_diff_sha256` で決まり、判定に新しい値を足さない。reader・wrapper・fanout の同時改修が要る。
- wrapper / fanout へ `--inject` を中継する — 本 wave の完了判定に不要。wrapper は並行 churn で共有木検査が破れるため、閉包の変異は harness 直当てで走らせる。

**適用範囲:** 新規 capture 経路 (現 HEAD に束縛) の drift だけを外す。既存の v2 campaign.lock を検証する経路は lock に記録された commit に束縛されるため (ident.py の `verify_against_lock`)、固定 commit の lock を使う test は commit モードでも drift で落ちる。変異 commit object は共有 object store に gc まで残る。
