## 所見

- **A1 — must-fix — [conftest.py:2542](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py:2542)**
  `rmtree` が失敗すると、保存済みの生成エラーへ到達せず、終了処理のエラーが先に表面化する。`_finish_memo_sessions` の「最初のエラーを保持する」契約ともずれる。join、削除、生成エラーの回収を個別に行い、生成エラーを優先して伝播する形に直す。

- **A2 — should — [test_s8b_oracle_driver.py:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1177)**
  T1 の比較対象は集合・bytes・mtime で、要求にある file mode を見ていない。`stat.S_IMODE(path.stat().st_mode)` を signature に加える。複写を二段にしても、現行コードの `copytree` は metadata を保つため、時点差以外の集合・bytes・mode・mtime 差は静的には見つからなかった。

- **A3 — should — [test_s8b_oracle_driver.py:1136](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1136)**
  T1 は別名で複写した conftest と、`importlib` で取得した test module を使う。hook 本体は通るが、pytest が収集した module と別物になり得るため、本番の module 状態との一致までは証明しない。親の焦点走で本番 controller の import と `ROOT` 一致を確認し、その射程を記録する。

- **A4 — should — [t2273pi_ab_analyze.py:407](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/probe/t2273pi_ab_analyze.py:407)**
  B の事前 collection file が無い場合、各走自身の collection を基準にする。対内 E1 比較は残るが、「投入前に固定した A/B collection」との照合は弱まる。系列投入前に A/B 両 file と `expected-added-nodes.json` を必須とし、差集合がその入力と一致することを検査する。

controller と worker の hash 式・root は通常 checkout では一致する。`ROOT` は双方とも `__file__.resolve()` 由来で、symlink 自体は不一致要因ではない。`result.json` の生成失敗は worker の 180 秒 timeout と終了時の保存エラーで赤になる。受入以外は `_early_memo_selected` が起動を抑え、dir が無ければ従来の直接複製へ戻る。新しい環境変数の継承経路は無い。probe の移植元 slug・job dir・import 名の取りこぼし、赤の自動 infra 化、5 分判定や四区分の明白な逸脱は見つからなかった。

## 変異の再照準

以下の old は、M6 を除き各対象ファイル内で一意。M6 は単独の呼出し文字列が定義側にも現れるため、示した二行を単位に置換する。

| ID | old → new の案 | kill 理由 |
|---|---|---|
| P0 | `one point at configure_node` → `single point at configure_node` | 等価、SURVIVED |
| M1 | `_t080_copy_visible_output(root / "output")` → `_copy_git_visible_output(ROOT, root / "output")` | T2 の helper 回数が builder 回数より少ない |
| M2 | `shutil.copytree(directory / "output", destination)` → `_copy_git_visible_output(ROOT, destination)` | T1 の変更後 bytes が混入 |
| M3 | `shutil.copytree(directory / "output", destination)` → `shutil.copytree(directory / "output", destination, copy_function=shutil.copy)` | T1 の mtime 不一致 |
| M4 | `if getattr(config, _T080_VISIBLE_OUTPUT_JOB_ATTR, None) is not None:\n        return` → guard 削除、かつ `directory.mkdir(exist_ok=False)` → `directory.mkdir(exist_ok=True)` | 現案は二度目の `mkdir` 衝突に mask される。二置換なら T1 の spy が **2 回**を検出 |
| M5 | `module._copy_git_visible_output(module.ROOT, directory / "output")` → `shutil.copytree(module.ROOT / "output", directory / "output")` | T1 の実関数 spy が 0 回 |
| M6 | `_start_early_memo_job(node)\n        _start_t080_visible_output_snapshot(node)` → `_start_early_memo_job(node)` | T1 で helper 前の `result.json` が現れない |
| M7 | `shutil.rmtree(job["directory"])` → `pass` | T1 の finish 後も dir が残る |

## GO 判定

**修正後 GO** — A1 を直し、mode 検証と事前 collection 固定を補ってから、親の実走で import・終了順序を確認する。

## 総括

静的検査のみで、テストは実走していない。複製経路の通常時の内容・metadata 契約は概ね維持される。主な不足は終了時のエラー優先順位、T1 の mode 検証、計測前 collection 固定、M4 の mask である。