# 段 4 裁定 — [T-2496] `run_trial` 経路の hard timeout

段 2 plan と段 3 の 2 レンズ (sol = 正しさ境界 / luna = 整合・実効性) を裁定する。

## 所見の裁定

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| 1 | 追加テストが全て `timeout_s` を明示するため、**本番既定値だけを無効化する変異が生き残る** | sol「正例の恒真性」/ luna「plan の実効性」(独立に一致) | **real・採用 (must-fix)**。既定値と、その既定値が `subprocess.run` へ実際に届くことを検査する node を足す |
| 2 | 負例が rc=0 だけなので、**返り値 rc や bytes を壊す変異を検出しない** | sol「負例の恒真性」 | **real・採用 (縮小)**。非 0 rc の負例を 1 本足す。rc=0/1/128 の 3 本は受入枠を無駄に使うので採らない |
| 3 | 実 repo 負例に `timeout_s=1.0` を課す根拠が無く、**短い予算が間欠赤を生む** (本 wave の問題設定と逆行) | luna「テスト所要」 | **real・採用**。正常完了側の負例は production 既定値 (引数を渡さない) で走らせる |
| 4 | **D265 は固定 300 秒を裏付ける裁定ではない** (ruleops は BASE 20 + 作業量比例、CAP 300) | luna「予算の値と形」 | **real・採用 (記述の是正)**。値 300.0 は維持し、記録では「実測で安全を証明した値」ではなく暫定運用値と書く |
| 5 | brief の「集約の終端は `max_wall_s` のまま」は**補足不足**。履歴 loop に deadline 検査は無く、attempt 予約は `started_monotonic` 設定より前 | sol「親 brief の誤りと誇張」/ luna「plan の実効性」 | **real・採用 (記述の是正)**。段 7 の記録に具体例まで書く |
| 6 | partial report の payload に `"status": "complete"` が残りうる | sol [疑い] | **real だが scope 外**。既に [T-2497] として起票済み (worklog entry 1389)。本 wave では扱わない |
| 7 | A-1 は**投入中 job の有無だけでは確認不足**。checkout・expected HEAD・receipt の source binding・完了後の再検証まで見る | luna「A-1 source closure」 | **real・採用**。段 9 の land 直前手順に入れる。過去測定のやり直しは不要 (D111) |
| 8 | subcommand 別の予算分岐は今回不要 | luna | **採用**。固定値を維持する |
| 9 | 300 秒待つと受入の 5 分枠を一発で消費する | luna [疑い] | **real だが対処しない**。現状は無期限待ちであり 300 秒で打ち切る方が厳密に良い。受入床の保護は別課題で、`DW-G05` により成果物への影響を書けない追加は must-fix にしない |
| 10 | brief が挙げた行番号 (呼び出し 16 箇所・捕捉 10 箇所) に不一致は無い | sol | **確認済み**。訂正不要 |
| 11 | `subprocess.run` の timeout は直接の子だけを kill し、孫は残る | luna (`/usr/lib/python3.10/subprocess.py:503`) | **real・採用 (記述の是正)**。保証の限界として記録する |

refuted に落とした所見は無い。plan の方向 (既定値付き keyword-only 引数 + 例外変換) はそのまま採用する。

## プラン v2 (確定)

**実装面 (Codex `role=author` が書く)。親は編集しない。**

1. `orchestrator/campaign/trial_registry.py`
   - `_GIT_ENV_ALLOW` (256〜263 行) の直後に `_GIT_TIMEOUT_S = 300.0` を置く。
   - `_git` (967〜977 行) に keyword-only 引数 `timeout_s: float = _GIT_TIMEOUT_S` を足し、
     `subprocess.run(..., timeout=timeout_s)` とし、`subprocess.TimeoutExpired` を捕えて
     `TrialRegistryError("[git-operational] ... timed out after ...")` を `from exc` 付きで送出する。
   - 既存 16 呼び出しは二引数のまま変えない。新しい例外型・retry・部分結果・cache は作らない。
   - 前例に合わせる: `tools/dev_waves/git_state.py:176` の `_run` が同型 (`timeout_s` 既定引数 →
     `subprocess.run(timeout=...)` → `except subprocess.TimeoutExpired` → 業務例外)。
2. `orchestrator/tests/test_trial_registry.py` (挿入点 = 5246 行の既存 git-operational テスト直後、
   5249 行の decorator より前) に 4 node を足す。

| node | 入力 | 検査 |
|---|---|---|
| T1 正例 | PATH shim (2 秒 sleep、`exec` で shell を置換)、`timeout_s=0.25` | `TrialRegistryError` が `[git-operational]` を含み、`__cause__` が `subprocess.TimeoutExpired` で `timeout == 0.25` |
| T2 負例 | 即座に stdout/stderr の sentinel を出して rc=0 で終わる shim、**予算は production 既定値 (引数を渡さない)** | 例外が出ず `returncode == 0`、stdout/stderr の bytes が一致 |
| T3 負例 | 即座に sentinel を出して rc=23 で終わる shim、**production 既定値** | 例外が出ず `returncode == 23`、stdout/stderr の bytes が一致 |
| T4 機構 | `_git` を二引数 (production の形) で呼ぶ | `_GIT_TIMEOUT_S == 300.0` であること、かつその値が `subprocess.run` へ実際に届くこと |

- T4 の「届くこと」は、他に観測 seam が無いため `monkeypatch.setattr(R.subprocess, "run", recorder)` で
  kwargs を捕える (DW-O14 の最後の手段。理由を記録する)。recorder は `CompletedProcess` を返すだけとし、
  テストを甘くする方向の細工はしない。
- T2・T3 が排除するのは「timeout 対応が正常完了まで一律に拒否する」「rc・stdout・stderr を壊す」変異であり、
  **300 秒が全負荷条件で十分だという主張ではない**。
- 追加 node の合計所要は 5 秒以内を狙う (正例の実待ちは約 0.25 秒)。実所要は焦点走で測る。

## 変異事前登録 (DW-M01、実装前に確定)

runner は**追加 4 node に焦点を絞る**。期待 node はその焦点集合における完全集合である。

| id | 変異 | 期待赤 (完全集合) | 期待 | hang_risk |
|---|---|---|---|---|
| M1-drop-timeout-kwarg | `subprocess.run` から `timeout=timeout_s,` を削除 | T1, T4 | KILLED | false |
| M2-swallow-timeout | `raise TrialRegistryError(...) from exc` を `return subprocess.CompletedProcess([], 0, b"", b"")` へ置換 (受理を広げる向き) | T1 | KILLED | false |
| M3-default-disables-budget | 既定値を `timeout_s: float \| None = None` へ (本番だけ無効化) | T4 | KILLED | false |
| M4-budget-too-small | `_GIT_TIMEOUT_S = 300.0` を `= 0.001` へ (承認外の過剰拒否) | T2, T3, T4 | KILLED | false |
| M5-hardcoded-budget | `timeout=timeout_s` を `timeout=0.25` へ (既定値を迂回) | T4 | KILLED | false |

- M4 が「受理集合を縮小する wave に要る過剰拒否の正例」対照で、T2・T3 がその正例である (DW-M01)。
- M5 は T4 が恒真でないことの対照である。
- hang しない設計: 正例 shim の sleep は有限 2 秒なので、timeout を外した変異は停止せず assertion failure になる。
- 実装後に単一理由性を確認する (DW-M01)。module scope の fixture が既定予算で git を呼ぶ場合、
  M4 の期待集合が崩れるので、その時点で M4 を登録から外し erratum を残す。

## scope の確認

他 module の git helper、`executor`、汎用 watchdog、監視 framework、`max_wall_s` の意味変更、
新しい gate・検査・台帳・一般化はいずれも実装しない。所見 6・9 は scope 外として記録だけ行う。

## 保証しないこと (段 7 に逐語で残す)

- 縛るのは **1 回の git 呼び出し**であり、`run_trial` 全体の壁時計上限ではない。
- `_assert_attempt_registry_history_append_only` (2587 行) は全 commit × 全 blob を反復するが、
  この loop に deadline 検査は無い。attempt 予約は `started_monotonic` の設定より前に行われる。
- `flock` の待ち、通常の file I/O、`fsync` はこの timeout で縛られない。
- `subprocess.run` の timeout は直接の子を kill するだけで、孫 process は残りうる。
