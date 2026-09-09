# 段 4 裁定 — [T-2503]

段 4 直前の再走査: local main は wave 開始時の `7f17e1c63` から 0 commit。新しいユーザー裁定なし。

## 所見の裁定

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A1 | 束縛が証明するのは「Python preflight 時点の spool ↔ worktree `.pbs` 一致」までで、実行された命令列の同一性ではない | real | 採用 (説明を狭める) | 内 |
| A2 | Python 側照合は shell 後の再照合と standalone preflight を追加で守る | refuted | — | — |
| A3 | 恒真ゲートではない (shell と Python の間に時間差がある) | refuted | — | — |
| A4 | 負例は対象変異を確実に区別する | refuted | — | — |
| A5 | 正例**単独**では比較行を固定しない (比較行を消しても正例は通る) | real | 採用 (説明を狭める + M3 で露出) | 内 |
| A6 | login node の単体テストは計算ノードの PBS 統合を代表しない | real | 採用 (記録に明記) | 内 |
| A7 | `site_policy.socket` と `probe.socket` の取り違えは無い | refuted | — | — |
| A8 | 規律 2 の緩和は無い | refuted | — | — |
| A9 | brief の commit 履歴 (P1) は一次資料と一致 | refuted | — | — |
| A10 | brief の pin 不在・receipt 主張が子へ射影されておらず再検証不能。「必ず赤」は過大 | real | 採用 (下記に一次証拠を再掲、断定を条件化) | 内 |
| A12 | `.pbs` の `BOUND_PATHS` は 4 件で `condition_meaning_gate.py` を含まず、その file は Python の dirty 検査より前に import される | real | **不採用 (実装しない)** | **外・裁定候補** |
| B1-1 | consumer 閉包は plan の列挙より広い (driver ID / perf inventory / hooks registry / runbook 投影) | real | 採用 (影響一覧に明記、実装は変えない) | 内 |
| B1-2 | bytes pin 不在の結論は維持可能 | refuted | — | — |
| B2-1 | 受入台帳・conftest の一次確認 | real (子側は射影外) | 採用 (親が一次資料で確認済み。下記再掲) | 内 |
| B2-2 | helper の git subprocess に timeout が無い | real | **採用 (実装へ反映)** | 内 |
| B2-3 | hooks / docs はこの変更では赤にならない | refuted | — | — |
| B2-4 | 「login node で受入」は不正確。実行場所は正規 runner が決める | real | 採用 (brief の表現を訂正) | 内 |
| B3-1 | 負例の構造は成立 | refuted | — | — |
| B3-2 | git 環境の隔離が最初の git 実行より後になっている | real | **採用 (実装へ反映)** | 内 |
| B3-3 | `delenv` の `raising=False`、author/committer identity、template dir、cwd の明示が不足 | real | **採用 (実装へ反映)** | 内 |
| B3-4 | `.gitignore` は不要。status 空の assert は fixture 健全性に有用 | refuted (+提案採用) | 採用 (assert を入れる) | 内 |
| B4 | plan に scope 逸脱は無い | refuted | — | — |
| B5-1/2 | commit・hash・monkeypatch 行番号は一致 | refuted | — | — |
| B5-3 | 「必ず落ちる」は条件化が要る | real | 採用 (A10 と同じ処置) | 内 |
| B6 | 対象変異は正例でも殺されるので、負例固有の検出力を帰属できない | real | **採用 (変異事前登録で node を分離)** | 内 |
| B7 | 所有範囲は 2 file だけ | refuted | — | — |

## A10 / B2-1 / B5-3 への処置 — 親が持つ一次証拠 (子の射影外だったもの)

- pin 閉包: `git grep -ln d7607e0aaf0a13ecdd319776a2b84414d79413cf8269a61df051070de7bce802` → 0 件。
  `git grep -ln 32644847ac6e93ce8ed7a09374a759af3cc82ef0` → 0 件。
  `grep -n t316 orchestrator/tests/test_frozen_artifacts.py` → 0 件。
  repo 全体 (`.codex/worktrees/` を含む) の path 検索でも、追加の bytes pin は 0 件。
- receipt: `output/env/pegasus/t316-sandbox-backend/0:900383.nqsv/receipt.json` と `0:900427.nqsv` の
  `execution_binding.runtime_sha256` は `runtime_pbs_spool` =
  `44a359857b8ec49d7d15d6a385e3b3c3138a40946d9b2ed7de7de39758531b32` であり、同 dict の
  `tools/pegasus/probes/t316_sandbox_backend_probe.pbs` と同値。
- job body: `t316_sandbox_backend_probe.pbs:65-80` が `$0` の sha256 を committed `.pbs` の blob と照合する。
- 受入台帳: `conftest.py:1571-1591` が duration 不在を `None` にし、`:1631-1664` が未知を既定 cost で
  並べる (レンズ A が一次資料で確認)。収集は拒否されない。
- **断定の条件化:** 「次に計算ノードで走らせると必ず赤」ではなく、
  「job body の先行関門をすべて通過した実行では、spool の bytes が worktree の `.py` と一致しない限り
  当該比較で決定的に拒否される」と書く。以後の記録もこの表現を使う。

## A12 の裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

`tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54-59` の `BOUND_PATHS` は 4 件で
`orchestrator/campaign/condition_meaning_gate.py` を含まない。一方
`t316_sandbox_backend_probe.py:36` は module import 時にその file を import し、Python 側の
dirty 検査 (`:2330-2335`) はその後に走る。したがって dirty な condition gate は、
どちらの束縛関門よりも前に import-time のコードを実行しうる。取りうる形は
(a) shell の `BOUND_PATHS` へ 5 件目を足す、(b) Python の import を dirty 検査の後へ遅らせる、
(c) 現状を既知限界として記録する。本 wave の scope 外につき実装しない。

## プラン v2 (実装子への確定指示)

**編集してよい file は 2 つだけ。**

1. `tools/pegasus/probes/t316_sandbox_backend_probe.py`
   - `_BOUND_RELATIVE_PATHS` の直前に
     `_RUNTIME_PBS_RELATIVE_PATH = "tools/pegasus/probes/t316_sandbox_backend_probe.pbs"` を置く。
   - tuple の 3 番目の要素をその定数参照に置き換える。**tuple の値と順序は変えない。**
   - `repo_pbs = repo_root / _BOUND_RELATIVE_PATHS[1]` を
     `repo_pbs = repo_root / _RUNTIME_PBS_RELATIVE_PATH` にする。
   - 例外文言、`runtime_sha256` の key 集合、他の関門はいずれも変えない。
   - 比較が何を保証するかを 1〜2 行の comment で書いてよい (A1/A5 の処置)。
     「Python preflight 時点で runtime spool と worktree の `.pbs` の bytes が一致すること」まで、と書く。
     それ以上 (実行された命令列の同一性) を主張する語を使わない。

2. `orchestrator/tests/test_t316_sandbox_probe.py`
   - helper `_prepare_execution_binding_repo(tmp_path, monkeypatch)` を `_run()` の直前に置く。
   - **git を 1 度でも呼ぶ前に**環境を隔離する: `GIT_DIR` `GIT_WORK_TREE` `GIT_INDEX_FILE`
     `GIT_COMMON_DIR` `GIT_OBJECT_DIRECTORY` `GIT_ALTERNATE_OBJECT_DIRECTORIES`
     `GIT_CONFIG_COUNT` `GIT_CONFIG_PARAMETERS` `GIT_AUTHOR_NAME` `GIT_AUTHOR_EMAIL`
     `GIT_COMMITTER_NAME` `GIT_COMMITTER_EMAIL` `GIT_TEMPLATE_DIR` を
     `monkeypatch.delenv(name, raising=False)` で外し、`GIT_CONFIG_GLOBAL=os.devnull`、
     `GIT_CONFIG_NOSYSTEM=1` を設定する。commit は `-c user.name=... -c user.email=...
     -c commit.gpgsign=false` と空 template (`--template=` に空 dir) で行う。
   - **すべての git subprocess に明示 timeout を付ける** (例 `timeout=60`)。`git -C <repo>` で木を明示する。
   - 5 つの bound path を**互いに異なる bytes**で作り、`.py` と `.pbs` の bytes が異なることを
     helper 内で assert する。commit 後に `git status --porcelain --untracked-files=all` の
     stdout が空であることも assert する。
   - runtime spool と `PBS_NODEFILE` は **repo 外**に置く。hostname は
     `monkeypatch.setattr(probe.socket, "gethostname", lambda: "compute-test.example")` で固定し、
     nodefile にも同じ名前を書く。`PBS_JOBID` は `_JOB_ID_RE = ^[A-Za-z0-9._:-]+$` に合う値にする。
   - `IZANAGI_T316_EXPECTED_WORKTREE_ROOT` と `_execution_binding` へ渡す `repo_root` は
     同一の resolve 済み `Path` を使う。
   - test を 2 本、**この名前で**追加する。
     - `test_execution_binding_binds_runtime_spool_to_pbs` (正例): spool の bytes を `.pbs` と
       同じにして呼び、dict が返ること、`binding["runtime_sha256"]["runtime_pbs_spool"]` が
       `.pbs` の sha256 と一致することを確認する。
     - `test_execution_binding_rejects_runtime_spool_matching_python_instead_of_pbs` (負例):
       spool の bytes を `.py` と同じにして呼び、
       `pytest.raises(ValueError, match="^runtime PBS bytes differ from worktree PBS bytes$")`
       で受ける。**例外型だけでなく文言の完全一致で受ける。**
   - `git` が無い環境で skip しない。`shutil.which("git") is not None` を assert して明示的に赤にする。
   - 既存 test・既存 helper・`_run_injected`・`:1282` の monkeypatch は変更しない。

**触ってはいけない:** `test_hooks.py`、`test_official_perf_closure.py`、`docs/pegasus-runbook.md`、
`orchestrator/tests/acceptance_duration_ledger.json`、`.pbs` job body、既存 receipt、凍結 manifest、docs 全般。

## 変異事前登録 (B-057)

base = 修正後の HEAD。走行単位は `orchestrator/tests/test_t316_sandbox_probe.py`。
node 記法は `orchestrator/tests/test_t316_sandbox_probe.py::<name>`。
以下では正例を `POS` = `test_execution_binding_binds_runtime_spool_to_pbs`、
負例を `NEG` = `test_execution_binding_rejects_runtime_spool_matching_python_instead_of_pbs` と略す。

| ID | 位置 | 変異 | 期待 | 期待 node (完全集合) | 単一理由性 |
|---|---|---|---|---|---|
| M1 | `_execution_binding` の `repo_pbs = repo_root / _RUNTIME_PBS_RELATIVE_PATH` | `_BOUND_RELATIVE_PATHS[1]` へ戻す (欠陥の再導入) | KILLED | `NEG`, `POS` | 比較対象が `.py` になること以外に赤理由が無い。前段の関門 (job id / commit / dirty / nodefile) は同じ入力を拒否しない |
| M2 | 同上 | `_BOUND_RELATIVE_PATHS[0]` (`condition_meaning_gate.py`) へ向ける | KILLED | `POS` | 正例の spool (= `.pbs` bytes) が別 file と一致しないため。負例は変異後も同じ文言で raise するので緑 = 正例が担う役割の証拠 |
| M3 | 同上の比較 `if _sha256_file(runtime_pbs) != _sha256_file(repo_pbs):` | 条件を `if False:` にして検査を消す | KILLED | `NEG` | 比較が消えることだけが理由。正例は緑のまま = 負例が「比較の存在」を固定している証拠 (A5 の処置) |
| M4 | 例外文言 `"runtime PBS bytes differ from worktree PBS bytes"` | `"runtime PBS mismatch"` | KILLED (**diagnostic sensitivity pin** 枠。受理集合は変えない) | `NEG` | 文言だけが変わり、拒否/受理の集合は不変。DW-M08 に従い kill でなく診断感度の pin として記録する |
| M5 | `runtime_hashes["runtime_pbs_spool"] = _sha256_file(runtime_pbs)` | `_sha256_file(repo_pbs)` へ | **SURVIVED (等価変異として事前登録)** | (なし) | 比較を通った時点で `runtime_pbs` と `repo_pbs` の bytes は必ず一致するため、この置換は観測上等価。検出できないことを事前に宣言し、事後の言い訳にしない |

変更前 HEAD (修正前) では `_execution_binding` の直接被覆が 0 件なので、M1〜M4 のいずれも検出されない。
この差が本 wave の追加検出力である。

## 分割

実装子 1 本 (workspace-write)。段 6 は敵対レビュー 2 本 + 変異 matrix + 受入再走。
