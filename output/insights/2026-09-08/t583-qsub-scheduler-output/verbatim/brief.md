# 段 1 brief — [T-583] qsub の -o / -e を repo 外の file path にする

## scope

`tools/pegasus/submit_certify.sh` が `qsub` へ渡す引数へ `-o` / `-e` を足し、その返り先を
**repo 外の file path** にする。同 script の他の挙動 (preflight 4 capture、pre-submit.json /
submit-receipt.json の payload、dirty gate、`--rratio` 検査、export 変数) は変えない。
同じ commit へ「移した先が repo 外であること」を検査する負例テストを入れる。

## 確定済みユーザー裁定

- D1291 (2026-08-29): `submit_certify.sh` が `qsub` へ渡す `-o` / `-e` を repo 外の file path に
  する。**直すのは投入時の引数 1 箇所である。**
- 引数の指示: 負例を同じ commit へ入れる。他の挙動は変えない。Codex role=author (D95) を守る。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 実測した事実 (brief 前の裏取り)

1. `tools/pegasus/submit_certify.sh:176` は現在 `qsub_cmd=(qsub -v "$export_spec" "$JOB_SCRIPT")`
   で、`-o` / `-e` を**一切渡していない**。既定では NQSV が submit directory (= qsub 実行時の
   cwd = repo root) へ `.o<ID>` / `.e<ID>` を返す。
2. `docs/pegasus-runbook.md` §8 投入前チェックリストに既に規範がある — repo を submit directory に
   する job は `qsub -o <file> -e <file>` で repo 外へ向ける。`-o` / `-e` には **directory ではなく
   file path** を渡す (directory は `NQScrereq: [BSV EINVAL] Not a regular file.` で受理されない)。
   job script に絶対 path を書く形は採らない (機体固有値を repo へ持ち込むため)。
3. repo 外 root の既存 precedent (3 箇所で同一形):
   - `tools/pegasus/submit_b10_backoff_shape.sh:136`
   - `tools/pegasus/submit_floor.sh:564`
   - `tools/pegasus/floor_campaign.sh:56`
   いずれも `"$(dirname "$(dirname "$GIT_COMMON_DIR")")/izanagi-job-evidence"` を既定 root にし、
   `GIT_COMMON_DIR` は `git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir`。
   共有 git dir 起点なので worktree からでも同じ root を指す。実在も確認済み
   (`/work/1/SFC/tanab/izanagi-job-evidence/`)。
4. 封じ込め検査の既存 precedent: `submit_b10_backoff_shape.sh` の `provision_durable_root` は
   `"$root" != "$REPO_ROOT" && "$root" != "$REPO_ROOT/"* && "$root" != "$GIT_COMMON_REPO" &&
   "$root" != "$GIT_COMMON_REPO/"*` を要求し、symlink 成分と realpath 一致も見る。
   同 script は `--durable-root` override を持ち、テストがそこから負例を撃つ。
5. 負例テストの既存 precedent が同じ test file にある:
   `orchestrator/tests/test_pegasus_calibration_workload.py:139`
   `test_submitter_rejects_an_unregistered_ratio_before_side_effects` — script を実走し
   rc=2 と副作用不在を主張する。
6. `submit_floor.sh` は逆に scheduler 出力を **repo 内 output/** へ置いている
   (`assert_safe_output_path` が `OUTPUT_ROOT` 配下を要求)。precedent は割れているが、
   D1291 は「repo 外」と明示しているので 3 の側を採る。
7. **pin 閉包 (DW-O09)**: `tools/pegasus/submit_certify.sh` を key にする pin を全列挙した結果、
   bytes を凍結する golden / FROZEN_MANIFEST / generator hash pin は**不在**。file 全体の
   sha256 (`4dc8dcf4db5ba577239a0f39d3d5183078fdd66a5e0b50fca1b5756ca08c7163`) を literal で
   持つ file も repo 内に無い。path を key に持つのは次の非凍結 consumer だけ:
   - `orchestrator/tests/test_pegasus_tools.py` (shell 構文・symlink 拒否の parametrize、694 行の
     module 抜粋)
   - `orchestrator/tests/test_pegasus_calibration_workload.py` (source 文字列の逐語 assert)
   - `orchestrator/tests/test_hooks.py` / `orchestrator/tests/test_check_docs.py` /
     `tools/pegasus/admission_registry.json` (admission class = `local-ok`。今回の変更は class を
     変えない)
   - `orchestrator/tests/acceptance_duration_ledger.json` (所要時間台帳、node id は不変)
8. **編集面の重複 (起動時検査)**: 全 worktree の作業ツリー dirt と `main...HEAD` を走査した。
   `tools/pegasus/submit_certify.sh` を触っている稼働 wave は無い。
   `dev-wave-t1259-qsub-env-delivery` だけが `docs/pegasus-runbook.md` で main と差があるので、
   **本 wave は runbook を編集しない** (規範は既に載っており追記不要)。
9. `DW-O13` (gate 入力の実在): 負例が使う入力は「repo 内を指す root path」で、実環境で到達可能
   (実際に今まで repo root へ返っていたのがこの型)。恒真ではない。

## 不変条件 (壊してはいけない)

- `usage()` の `[--job-script PATH] [--rratio 20|50|80]` の行は**逐語で残す**
  (`test_submitter_exposes_only_the_calibration_whitelist` が `in source` で見ている)。
- `':(exclude)output'` を含む dirty gate、`RRATIO` の 3 値検査、`IZANAGI_CALIBRATION_RRATIO`、
  `pre-submit.json` / `submit-receipt.json` の schema と field は 1 byte も変えない。
- preflight 4 capture の順序と「どれか失敗なら qsub へ進まない」性質を変えない。
- `-o` / `-e` は **file path** であること (directory を渡さない)。
- 新しい root は絶対 path で、repo root / git common repo の内側であってはならない。
- `--dry-run` は qsub を実行しない性質を保つ。
- 規律 2: 正しさゲートを緩める方向の変更をしない。

## 成果物の形

1. `tools/pegasus/submit_certify.sh` — `-o` / `-e` の追加、repo 外 root の導出、封じ込め検査、
   負例が撃てる override 引数。
2. `orchestrator/tests/test_pegasus_calibration_workload.py` — 正例 1 本 + 負例 1 本。
3. 段 7 の spool fragment (worklog / decisions は不要なら worklog のみ)。

## 親の provisional 裁定 (割れうる前提 = 攻撃対象)

- **(P1)** 返り先の既定は
  `"$(dirname "$(dirname "$GIT_COMMON_DIR")")/izanagi-job-evidence/calibration-certify"` の下の
  `"$NONCE.scheduler.stdout"` / `"$NONCE.scheduler.stderr"` とする。
  理由: 3 の precedent と同形で機体固有値を repo へ持ち込まず、NONCE で衝突しない。
  攻撃点: 別 root 名 (`pegasus/` 既存 subdir の再利用など) の方が良いか。既存 `attempts` 側との
  対応づけが切れないか。
- **(P2)** 負例を実物へ当てるため `--scheduler-output-root PATH` を 1 つ足し、repo 内を指したら
  rc=2 で qsub 前に止める。理由: 述語だけの source 文字列 assert は「機構を通らない緑」になる
  (記憶: 機構の正例・負例は実体を名指しする)。precedent は `--durable-root`。
  攻撃点: これは「引数 1 箇所」を超える scope 拡大か。override 無しで負例を撃つ手段があるか。
- **(P3)** root の provision は `mkdir -p -m 0700` + symlink 成分拒否 + realpath 一致まで行う
  (precedent 4 と同形)。攻撃点: これは仮想リスク向けの過剰な gate で scope 外か。
  最小形は「repo 内なら拒否」の 1 判定だけで足りるのではないか。
- **(P4)** receipt (`pre-submit.json` / `submit-receipt.json`) には scheduler path を記録しない。
  理由: 「他の挙動は変えない」。攻撃点: 記録しないと後から job 出力を辿れないのでは。

## 分割方針

変更面は 1 script + 1 test file と小さい。段 5 は Codex 実装子 1 本 (role=author)。
段 2 は plan 1 本、段 3 は敵対相談 2 本 (レンズ: ①scope 逸脱と precedent 整合、
②負例の恒真性と実環境での到達可能性)。
