# [T-2496] `run_trial` 経路の git 呼び出しへ hard timeout を入れる

- 日付: 2026-09-14
- wave: `dev-wave-t2496-git-timeout` / branch `worktree-dev-wave-t2496-git-timeout`
- 実装 commit: `1697a5970b6c6c084a10b3c5d13eca73ded656d1` (起点 main = `7dc4ecc39`)
- 起票元: entry 1389 (2026-09-09) の段 6 レンズ B must-fix 2。D1847 の却下選択肢
  「executor へ hard timeout を足す」を別項として起票したもの。

## 何を変えたか

`orchestrator/campaign/trial_registry.py` の private helper `_git` は、同 module の git 呼び出し
16 箇所すべてが通る単一の choke point でありながら、`subprocess.run` へ timeout を渡していなかった。
止まった git を打ち切る手段が無く、`max_wall_s` は実行中の syscall を中断しない協調的検査にすぎない。

- `_GIT_TIMEOUT_S = 300.0` を置き、`_git` に keyword-only 引数 `timeout_s: float = _GIT_TIMEOUT_S` を
  足して `subprocess.run(..., timeout=timeout_s)` とした。
- `subprocess.TimeoutExpired` を捕え、既存の fail-closed 例外
  `TrialRegistryError("[git-operational] git command timed out after {timeout_s:g}s")` を
  `from exc` 付きで送出する。**停滞は受理されず拒否される。**
- 既存 16 呼び出しは二引数のまま。0 / 非 0 終了時の挙動 (rc・stdout・stderr の bytes) は不変。

同型の前例は `tools/dev_waves/git_state.py:176` の `_run` (同じ `timeout_s` 既定引数 →
`subprocess.run(timeout=)` → 業務例外への変換)。

## 予算 300.0 秒の位置づけ

**実測で安全を証明した値ではなく、無期限待ちを打ち切るための暫定運用値である。**

この checkout (10,369 commit / 24,757 tracked file) の login node、load 57〜81 での実測:

| 呼び出し形 | 実測 (秒) |
|---|---|
| `rev-list --all --topo-order --reverse` | 5.031 / 5.868 / 6.954 / 4.015 |
| `ls-tree -r -z --full-tree HEAD` | 1.653 |
| `log --format=%H --reverse --full-history HEAD -- <registry>` | 3.709 |
| `log --format=%H --diff-filter=A --full-history HEAD -- <lifecycle>` | 3.185 |
| `cat-file blob HEAD:<file>` | 0.440 |

CPU 時間はいずれも 0.2 秒未満で、I/O 待ちが支配する。300.0 は観測最大 (6.954 秒) の約 43 倍で、
`tools/ruleops.py` の `GIT_TIMEOUT_CAP_SECONDS` と同じ literal である。**ただし D265 は ruleops に
ついて「BASE 20 秒 + 作業量比例、CAP 300.0」を裁定したのであって、この経路の固定 300 秒を
裁定してはいない。** 標本は 4 点で、観測 regime は login node の load 57〜81 である。
worklog 1483 は同じ共有 FS で load 147 を記録している。

## 保証すること・しないこと

**保証するのは 1 回の git 呼び出しの上限だけである。** 次はいずれも縛らない。

- `_assert_attempt_registry_history_append_only` (`trial_registry.py:2587` 付近) の loop。
  `rev-list --all` の全 commit を回し、各 commit で全 tree の `ls-tree -r` と blob ごとの
  `cat-file` を行うが、**この loop に deadline 検査は無い**。
- `flock` の待ち、通常の file I/O、`fsync`。
- 孫 process。`subprocess.run` の timeout は直接の子を kill するだけである
  (Python 3.10 の `subprocess.py` 実装を段 3 レンズが確認)。
- attempt の予約は `started_monotonic` の設定より前に行われるため、計時開始前の走査がある。

**「`run_trial` の全経路が有界になった」とは言えない。**

## 受理集合への影響

受理は広がらず、狭まる方向にだけ動く。同 module の `except TrialRegistryError` 10 箇所のうち
例外を握り潰すのは `_looks_like_attempt_genesis` (2578 行付近) だけで、その `try` は
`_decode_json` しか囲まず `_git` から到達しない。CLI 入口は `parser.error` で fail-closed。
`p3_autonomous_workload_trial.py` 側でも、`mark_experiment_indeterminate` は最後に `raise cause` し、
`_finish_trial` の complete 条件は `fatal_error is None` を要求する。段 3・段 6 の 4 本の子が
独立に辿り、受理へ転じる経路は見つからなかった。

**既存性質として残る問題 (この差分が作ったものではない):** 例外処理中の attempt 終端記録が
失敗すると後続の lifecycle 後始末へ届かない (`p3_autonomous_workload_trial.py:5233` 付近)。
非 0 rc でも同じで、timeout は新しい発火条件を足すだけである。

## 追加したテストと変異 matrix

`orchestrator/tests/test_trial_registry.py` へ 4 node を足した (新規 test file は作っていない)。

| node | 役割 |
|---|---|
| `test_git_timeout_raises_operational_error_with_cause` | 正例。PATH shim (`exec sleep 2`) を `timeout_s=0.25` で打ち切り、原因例外と予算値を検査 |
| `test_git_timeout_preserves_success_result` | 負例。production 既定値で rc=0 の完了が落とされないこと |
| `test_git_timeout_preserves_nonzero_result` | 負例。production 既定値で rc=23 と出力 bytes が保たれること |
| `test_git_timeout_default_reaches_subprocess_run` | 機構。既定値 300.0 が実際に `subprocess.run` へ届くこと |

変異 matrix (`mutation-spec.json` / `mutation-report.json`、runner は `-k git_timeout` の 4 node):
**baseline = PASSED (4 passed / 5.28 秒)、6/6 KILLED、SURVIVED 0、MISMATCH 0。**

| id | 変異 | 期待赤 = 観測赤 |
|---|---|---|
| M1-drop-timeout-kwarg | `timeout=timeout_s,` を削除 | 正例 + 機構 |
| M2-swallow-timeout | timeout を握り潰して正常な `CompletedProcess` を返す | 正例 |
| M3-default-disables-budget | 既定値を `None` にして本番だけ無効化 | 機構 |
| M4-reject-completed-nonzero | `check=False` → `check=True` (承認外の過剰拒否) | 非 0 rc の負例 |
| M5-hardcoded-budget | `timeout=timeout_s` を `timeout=30.0` へ (既定値を迂回) | 正例 + 機構 |
| M6-drop-stdout-capture | `stdout=subprocess.PIPE` → `None` | 負例 2 件 |

4 node すべてが少なくとも 1 つの変異で赤になる。**M4 と M6 は段 6 の敵対レビューを受けて
差し替えた変異である** — 当初登録した「予算を 0.001 秒にする」変異は、shim が 1 ms 以内に
終われば負例が緑のままになりうる**タイミング依存の期待**で、`DW-M08` の完全集合要件を満たさなかった。

## 実走

- 変更した test file の単独走: `orchestrator/tests/test_trial_registry.py` rc=0、252 passed、16.42 秒。
- consumer 焦点走: `focus-consumers` として 20 file (producer・spawn-site 登録簿・attempt registry・
  reflux・s8c 事前登録・layer3 ほか) を走らせた。結果は worklog エントリに記す。
- `python3 tools/check_ai_provenance.py` rc=0 (9831 件、新規違反なし)。

## 子の逐語

段 2 plan、段 3 consult 2 本 (sol = 正しさ境界 / luna = 整合・実効性)、段 5 author、
段 6 review 2 本の出力は `verbatim/` に置く。
