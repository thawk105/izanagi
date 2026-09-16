# [T-2668] repo 直下に一時 dir を作る test の残り 2 箇所を repo 外 / ignore 済み path へ移す

- 日付: 2026-09-16
- branch: `worktree-dev-wave-t2668-tmpdir-outside-repo` (base = local main 8f17db598)
- 実装 commit: cc6e1fc54 (Codex author gpt-6-astra / medium、親 Claude manager)
- 一次資料: F998 (`docs/failures.md`)、起票 = worklog archive entry 1526 の [T-2668]

## 1. 依頼と着手前の実測

依頼は「`test_t316_sandbox_probe.py:1736` の `TemporaryDirectory(prefix=".t316-live-", dir=_REPO)` を repo 外
(または `output/` 配下の ignore 済み path) へ移し、`git grep -n "dir=_REPO" -- orchestrator/tests` で同型の
生成箇所を先に数えて同じ修正で閉じる。被害者 test の hold 登録は禁止。本題の移設だけ」。

| 対象 | 着手時点の状態 | 本 wave の扱い |
|---|---|---|
| `test_t316_sandbox_probe.py` `s6_bindable_root` fixture | **済**: 9d9df64f1 (2026-09-16 10:28、F999 の wave) が `main checkout の親/.izanagi-t316-live` へ移設、main 着地済み | 触らない (stale carry) |
| `test_hooks.py:1513` `mkdtemp(prefix="t2146-hardlink-", dir=_REPO)` (hardlink test) | 指定 grep の残り 1 件。tmp_path が authority と別 device のときだけ発火する分岐 | 9d9df64f1 と同じ形で `main checkout の親/.izanagi-t2146-hardlink` へ |
| `test_s1_9pair_figure_provenance.py:1055` `TemporaryDirectory(prefix=".s1-current-provenance-", dir=ROOT)` (test_p9) | 性質検索 (`dir=ROOT`) の純増 1 件。production `plot_s1_9pair._repo_path` (195 行) が REPO_ROOT 外を `path leaves repository` で拒否 | `.gitignore` 済みの `output/runs/` 配下へ (親 provisional 裁定 P1、前例 `test_codex_worker_launch.py:56`) |
| `test_calibration_freeze_authority_contract.py:2172` `dir=str(ROOT)` | plain runner (`__main__`) 専用。pytest 受入は tmp_path fixture を使う | 対象外 |
| `test_run_tests_testops_observation.py:1083` `dir=_REPO.parent` | repo 外 | 対象外 |

いずれの一時 dir 名も `.gitignore` 対象外 (`git check-ignore` で実測)。rglob 型の被害者
(`test_certified_writer_authorization_caller_inventory_is_closed`) は既に repo 直下の dot-dir 剪定と OSError 耐性を
持つので、残る被害者は `git status --porcelain --untracked-files=all` の bytes 不変を要求する族 (F999) である。

変更対象 2 file を path key で pin する hash 台帳・test は 0 件 (`freeze-permanent-design-s2.md` の W-0 表は歴史
記録、`freeze_nodes/` は不在、conftest `_REAL_REPO_NODE_INVENTORY` に test_p9 は未収載)。

## 2. 裁定と scope

- (P1) s1 の site を `output/runs/` 配下へ = 採用 (依頼文の「または `output/` 配下の ignore 済み path」)。
- 新 gate・新 test 関数・`.gitignore` 追加・production 変更・fallback 分岐・被害者の hold 登録 = 不採用 (scope 外)。
- 各移設先に「意図した場所に出来た」ことの assert を 1 行ずつ置く (9d9df64f1 の fixture 内 assert と同型)。
  これは変異 matrix の kill 経路であり gate の新設ではない。
- 軽量版: 段 2・3 と段 6 のレビュー子は省略 (設計択一は P1 のみで根拠つき、正しさ防壁の本体と受理集合に触れない)。

## 3. 同 device 前提の実測 (probe は job dir、repo へ入れない)

hardlink test は「tmp_path の device ≠ authority の device」で発火し、移設先が authority と同じ device で
なければ `os.link` が EXDEV となり synthetic fallback (弱い検査) へ落ちる。両 venue で実測した。

| venue | host | `/tmp` st_dev | `/work/1/SFC/tanab` st_dev | authority st_dev | 分岐 | `os.link` (移設先 → authority) |
|---|---|---|---|---|---|---|
| login | pegasus02 | 2304 | 743766374 | 743766374 | 発火 | 成功・同 inode |
| 計算ノード (generic dispatch) | bnode009 | 66309 | 743766374 | 743766374 | 発火 | 成功・同 inode |

したがって移設後も実 authority file の inode 検査を通る (synthetic fallback へ落ちない) ことが両 venue で確かめられた。

## 4. Codex author 子の実走と sandbox の制約

- s1 test_p9: sandbox 内で 1 passed。M3 相当の in-memory 変異は追加 assert で赤化 (子の反実仮想)。
- hardlink test: sandbox 内では移設先 `/work/1/SFC/tanab/.izanagi-t2146-hardlink` の `mkdir` が `EROFS` で落ちる
  (sandbox の書込範囲外)。t316 の fixture (9d9df64f1) と同じ露出であり fallback は足していない。
  親が sandbox 外で実走: 計算ノード request 1837.nqsv、**2 passed** (両 node、tip = 作業ツリー = cc6e1fc54 の内容)。

## 5. 変異 matrix (tip cc6e1fc54、runner = `python3 tools/run_tests.py --force-dispatch <2 node> -q -rf`、dispatch)

事前登録 (段 4) = M1・M2・M3 + 等価変異 1 件。spec は `mutation/mutation-spec-final.json`、台帳は
`mutation/mutation-out-final.json.gz`、attempt 記録は `mutation/mutation-attempt-final.json.gz`。

**本走 (2026-09-16 20:25〜20:34 JST、request 1924〜1936.nqsv): baseline PASSED、負例 3/3 KILLED、等価変異 1 件
SURVIVED (登録どおり)、MISMATCH 0、期待 node 完全一致。** harness rc=0。

| id | 変異 | 期待 | 結果 | kill の根拠になる赤 (単一の層) |
|---|---|---|---|---|
| m01 | `shared_root = (main_repo.parent / ".izanagi-t2146-hardlink").resolve()` → `Path(_REPO).resolve()` | KILLED | KILLED (131 秒) | `_validate_shared_root` の `ShardError("artifact-root-in-control-container")` (hardlink test) |
| m03 | test_p9 の `dir=scratch_root` → `dir=ROOT` | KILLED | KILLED (28 秒) | `assert Path(temp).parent == scratch_root` (test_p9) |
| m04 | **等価変異**: `ROOT / "output" / "runs"` → `ROOT.joinpath("output", "runs")` | SURVIVED | SURVIVED (43 秒) | — (harness の SURVIVED 検出の正例) |
| m02 | mkdtemp の `dir=shared_root` → `dir=_REPO` | KILLED | KILLED (59 秒) | `assert Path(same_device_root).parent == shared_root` (hardlink test) |

**erratum (m01 の赤 message)**: 段 4 の登録では `ShardError("artifact-root-inside-repo")` と予告したが、実測は
`artifact-root-in-control-container` だった。wave worktree は main checkout の `.claude/worktrees/` (制御 container) の
下にあり、`_validate_shared_root` は制御 container 検査を repo 内検査より先に行う。層は同じ関数 1 つで単一理由性は
保たれる (main checkout で同じ変異を走らせれば `artifact-root-inside-repo` になる)。

**m02 の副作用**: `dir=_REPO` の変異では mkdtemp 直後の assert で落ちるため後始末 (`finally`) に届かず、wave worktree
直下に空 dir `t2146-hardlink-yzepum6z/` が残った (空 dir なので status には出ない)。本走後に親が `rmdir` した。
変異固有の副作用であり、本来の code では `finally` が `os.rmdir` する (共有 root `.izanagi-t2146-hardlink/` は本走後
空だった = 後始末が効いている)。

## 6. 実走した test

| 対象 | tip | venue | 結果 |
|---|---|---|---|
| 焦点 2 node (hardlink test、test_p9) | 作業ツリー (= cc6e1fc54 の内容) | 計算ノード 1837.nqsv | 2 passed / 4.77 秒 |
| device probe (§3) | — | login pegasus02 / 計算ノード bnode009 | 分岐発火・os.link 成功 |
| 変異 matrix | cc6e1fc54 | dispatch | §5 |
| `tools/check_ai_provenance.py` 全史 | cc6e1fc54 | login | 10603 件、新規違反なし、rc=0 |
| 受入全走 | 本記録 commit を含む最終 tip | dispatch (受入 shard) | **本記録の時点では未実施。** land 前に 1 回だけ投入し、child-green でなければ land しない (結果は land の receipt に残る) |

## 7. 波及と残件

- `same_device_root` は対象 test のローカル変数で他 test と共有しない。`test_hooks.py` の module import に
  `tools.acceptance_shards` (→ `tools/dev_wave_land.py`) の依存が加わる (t316 test と同じ)。
- 移設先 `.izanagi-t2146-hardlink/` は `.izanagi-t316-live/` と同様 `main checkout の親` に残る (mkdtemp した
  子 dir は test が後始末する)。
- 残件なし。F998 へ supersede 追記 (spool fragment)。
