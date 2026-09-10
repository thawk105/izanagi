# 段 9 — T-193 (二重正本) のユーザー裁定と、本 branch を land しない決定

## 裁定 (2026-08-01、ユーザー)

**main を正本にする。** `codex/dev-wave-improve` の実装 (50 path) は land せず廃棄する。

## 裁定の材料 (本 wave が実測で作ったもの)

| 観点 | main (T-192 / D103、`site_policy` + `dispatch_compute`) | branch (`pegasus_policy` + `test_dispatch`) |
|---|---|---|
| 受入実績 | 計算ノードで 4012 passed | 15 failed / 4086 passed (15 赤は自 wave が入れたもの) |
| 本番動作 | 稼働中。provenance checker が既に消費者 | **FR-1 により submit も resume もできない** |
| resume 経路 | 無い (同期 dispatch のみ) | 有る |
| accounting の group 束縛 | **無い** (`_accounting_present` は Request ID と Started/Ended/Elapse だけ) | 本 wave で追加した |

### FR-1 (branch 側を失格にした決め手)

`DispatchPolicy` は `@dataclass(frozen=True)` で第 1 field が `policy_path: Path`。`load_policy` は
`policy_path=policy_path.resolve(strict=True)` を入れるため、**同一 bytes の policy でも path が
違えば `!=` になる**。製品は repo 側 `load_policy()` の policy を渡し、snapshot 側は snapshot root から
load するので `policy != snapshot_policy` が恒真になり、`qsub_argv` / `monitor_job` /
`resume_dispatch` の 3 gate が常に発火する。

親の実測 (同一 bytes を別 path へ複写して比較):

```
same policy_sha256 = True
same account       = True
policies equal     = False
```

テストは `_synthetic_snapshot` が snapshot root 内へ policy を書いて同じ path から load するため、
この欠陥は永久に露見しない。

## merge を完了できなかった理由

最新 main (`18d7fc3`) の wave-side merge は 10 件の衝突を出し、うち 8 件は同一関数内での
**API 真っ向衝突**だった (機械的な両立が不可能)。

下記は実際の衝突出力である。`git diff --check` が行頭の衝突マーカーを検出するため、
**可逆な最小正規化として各行へ `| ` を前置した** (可視文字は不変。復元は各行の先頭 2 文字を除く)。

```
| <<<<<<< HEAD (branch)
|     return max(1, pegasus_policy.resolve_test_workers(None, observation))
| =======
|     return max(1, site_policy.default_test_jobs(site, cap=_NPROC_CAP))
| >>>>>>> 18d7fc3 (main)
```

衝突先: `tools/run_tests.py` (4 hunk)、`hooks/guard_bash.py`、
`orchestrator/campaign/buildcache.py` (2)、coverage 4 本、`test_hooks.py`、
`test_run_tests_nproc.py`、`docs/worklog.md`。merge は abort し tree は clean に戻した。

## 本 branch から main へ持ち込むもの / 持ち込まないもの

- **持ち込む**: 本 wave の記録一式 (`output/insights/2026-07-30_dev-wave-improve-wave/`)。
  受入・変異台帳・敵対レビュー逐語・裁定・FR-1 の実測がここにある
- **持ち込まない**: 実装 50 path。`codex/dev-wave-improve` (tip `77db32c`) に保存されているので、
  後から参照も復元もできる

## 移植すべき知見 (main 側の実装に対して)

- **移植する**: accounting footer の `Group Name` を policy account へ exact 束縛する。
  main の `_accounting_present` は Request ID と Started/Ended/Elapse しか見ておらず、
  scheduler group を一切束縛していない。本 wave の C2 と同型の欠落である
- **移植しない**: resume の submit-receipt identity 束縛 (C1)。main の dispatcher に
  crash-resume 経路が無いため該当しない
