---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-fig3b-arc-status
seq: 1
---

## 新規

### {{F:guessed-sha-in-git-ref-command}}. 40 hex の SHA を `rev-parse` の出力から写さず頭から推測で補完し、存在しない object を指す git 操作を投げた [捏造/幻覚] [手順漏れ]

- 事象: 2026-09-20 に独立 2 例。(1) [T-2790] wave で `git worktree add ... <sha>` の sha を短縮 sha から補完して存在しない object を
  fetch し、独立 clone を 1 回無駄にした。(2) 本 wave (fig3b) で変異用 clone の `git update-ref refs/heads/main <sha>` に推測の
  40 hex を書いて `nonexistent object` で失敗し、clone を作り直した。いずれも実害は clone 1 回の再作成で、成果物・判定は変わらない。
- 根本原因: 短縮 sha を見た後に 40 hex 引数を手で組み立てた (先頭 9 桁だけが本物で残りは埋め文字)。git は短縮 sha を受けるのに
  「40 hex 必須」という思い込みから補完した。
- 恒久対応: memory `worktree-discipline` (2026-09-20 追記「worktree add の sha は 40 hex を rev-parse から」) と
  `mutation-discipline` (update-ref 後の reset --hard)。行動規律: SHA を引数に書く command は、直前の `git rev-parse <ref>` の
  出力を逐語で写すか、短縮 sha をそのまま渡す (補完しない)。
- 再発検知: `nonexistent object` / `bad object` の失敗を見たら推測 SHA を疑い、`git rev-parse` の出力と比較する。

## 再発

### F42

- **再発: 2026-09-20** — wave dev-wave-fig3b-arc-status。新設した `orchestrator/tests/test_plot_arc_status.py` が自走 harness も allowlist
  記載も持たず、受入全走 1 回目 (3 shard) を `test_plain_runner_coverage.py` の 1 件赤にした。親は `DW-O26` (新規 test file を足す走は
  file 集合列挙のメタテストも焦点走に含める) を段 9 前に読みながら、焦点走 2 回とも新 test file 単独で回した。author とレビュー B は
  目録型 test を `plotting` / `provenance` の語で検索して「見つからない」と報告した (file 名を列挙する型は語検索で必ず落ちる、
  [T-2737] と同じ)。fix2 (Codex、`__main__` + `pytest.main` の 2 行) の後に焦点走を新 test + `test_plain_runner_coverage.py` +
  `test_check_subprocess_bytecode_guard.py` で回して閉じた。費用は受入全走 1 回分 + fix 子 1 本 + 焦点走 1 回。

### F521

- **再発: 2026-09-20** — wave dev-wave-fig3b-arc-status。新設 test の T7 が `subprocess.run([sys.executable, ...], env={...})` に
  bytecode guard を持たず、受入全走 1 回目を `test_check_subprocess_bytecode_guard.py::test_real_repo_clean` の赤にした (上の F42 再発と
  同じ走)。`python3 tools/check_subprocess_bytecode_guard.py --repo <worktree>` は数秒で rc=1 を返したのに、受入前の関門として
  `check_docs.py` と `check_ai_provenance.py` しか回していなかった。fix2 で env dict literal に `PYTHONDONTWRITEBYTECODE` を足し、
  checker rc=0 を login で確認してから受入を取り直した。
