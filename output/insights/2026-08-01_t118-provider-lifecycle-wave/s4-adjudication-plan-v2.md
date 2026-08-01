# 段 4 裁定 + プラン v2 + 変異事前登録 — [T-118]

親裁定。段 3 の 2 本 (A=正しさ境界 / B=到達性・scope 誠実性) はともに **NO-GO**、
BLOCKER 計 6 件 (重複 1 件を含む)。以下は親が real/refuted と採否を確定した結果である。

## 0. 親 brief の訂正 (親の誤りを先に固定する)

| brief の記述 | 裁定 | 訂正後の事実 |
|---|---|---|
| 事実 1「25 箇所中 23 箇所は後始末済み、漏れは 4 箇所」 | **real 所見 (親の誤り)** | 25 箇所中、後始末が**全く無い**のは 4 箇所。残り 21 箇所 (23 は算術誤り) は**正常系だけ**後始末する。うち少なくとも 3 箇所は例外経路で漏れる — 親が一次資料で再確認済み (下記 §1) |
| 事実 2「repo 全体で rmtree ゼロ」 | **partial** | `neutral_root` に限定すれば正。literal な全体主張は偽 |
| 事実 3「残留 40,280 個」 | **stale** | これは conftest が `/dev/shm` を指していた**撤去前**の観測。現行構成の正本は `output/insights/2026-08-01_t229-devshm-removal.md:110-121` (job `874781`, bnode042): 全走後 `/tmp` に **4.91 GiB / 174 entry**、`prefix histogram は s8b-selector-* が支配的`、`/tmp` は `systemd-tmpfiles-clean.timer` で **10 日保持** = tmpfs より長い |
| 事実 3「s8b-selector- 5,626 は production 由来」 | **partial (両レンズ一致)** | 漏れているのは production **コード**だが、それを踏んだ**実行主体は pytest** である。campaign 実走数として転記してはならない |
| 事実 6 / (P3) 「テストごとに cache miss する」 | **refuted** | `real_repo_receipt()` は `real_repo_receipt_memo.py:144` の `@functools.lru_cache(maxsize=1)`、`gettempdir()` も `tempfile.tempdir` を一度だけ解決する。**因果は成立しない** |
| 事実 8「login node の pytest は機械拒否される」 | **partial** | Claude surface (`hooks/guard_bash.py`) だけ。`AGENTS.md:31` が「`.codex` には hook が未配線なので機械的に止まらない」と明記。**実装子 prompt で明示的に禁じる** |
| (P2) の理由「失敗時 forensic」 | **refuted (親の誤り)** | owner が例外経路でも無条件 close するので forensic は残らない。cwd を即時削除しない**本当の理由**は既存 pin (`test_s8b_prediction_runner.py:557`, `653-659`) が 2 回の invocation 後に両 cwd の空性を assert していることである |

(P3) の**結論は維持する** (TMPDIR 一括 redirect は採らない)。ただし理由を差し替える:
(a) `patchharness.py:101-115` が共有 submodule の排他 lock を `TMPDIR` に置くため、session 固有
TMPDIR は**排他 scope を狭める** (レンズ B が発見)、(b) pytest 外の production 実走は依然漏れる
(隠蔽であって修正でない)。

## 1. scope 裁定

### scope 内 (本 wave で実装する)

provider neutral tree の lifecycle という**単一機構**と、その owner 配線。

- `orchestrator/campaign/s8b_prediction_runner.py` — `ClaudeHeadlessProvider` の lifecycle
- `orchestrator/campaign/claude_projected_provider.py` — `ClaudeProjectedRoleProvider` の lifecycle
- `orchestrator/campaign/p3_autonomous_workload_trial.py` — owner 配線 (**条件付きでなく必須**、
  レンズ B [major] を採用)
- 上記 3 つに対する回帰 guard test

### scope 外 real (実装しない、裁定パッケージでユーザーへ返す)

1. **例外経路の temp 漏れ (production 3+ 箇所)** — レンズ A BLOCKER-1、親が裏取り済み:
   - `orchestrator/campaign/s3_lock_coverage.py:75` `_run_trace` — `subprocess.run(timeout=RUN_TIMEOUT_S)`
     が `TimeoutExpired` を投げると 2 つの `rmtree` をどちらも通らず、呼び手 `:164` の `try/finally` は
     `_run_trace` が**返った後**にしか入らない
   - `orchestrator/campaign/s2_verify_calibration.py:110` `_run_once` — 同型
   - `tools/run_tests.py:717` — `mkdtemp` 直後の `os.chmod` が投げると代入前に漏れる
   - 同型の疑い: `s5_permutation_coverage.py:71`、`s8a_trigger_coverage.py:136`、
     `s8a_trigger_freq.py:81`、`s1_verify_extime_calibration.py:243`
   - **除外理由**: 失敗形が別 (lifecycle 不在ではなく例外経路)、対象が計測 driver 群で
     計測経路に触れるため独立 brief と独立の変異事前登録を要する。`DW-G03` の族一般化条件
     (独立 2 例) は満たすので、族として 1 タスクに束ねるのが妥当
2. **テスト側の素の `mkdtemp` 60 箇所 / 18 ファイル** — レンズ B の代案 (TMPDIR を動かさず、
   既知 prefix の `mkdtemp` 返値を ledger へ記録し teardown で exact path を削除する fixture) を
   推奨案として添える
3. **generic な残留検出器の不在** — レンズ B [nit]。全走後の prefix 別新規 entry を測る仕組みが無い

### T-118 の扱い (レンズ B BLOCKER-1 を採用)

**T-118 は閉じない。** worklog には `部分解消・未完` と書き、
「provider neutral tree の lifecycle を実装し `s8b-selector-*` / `izanagi-projected-*` の
新規残留を対象化した。例外経路の production 漏れとテスト側 raw mkdtemp 族は残るため open」
と射程を明記する。後続は新 ID で採番する。

## 2. BLOCKER への裁定と設計 (プラン v2)

### B1. 削除 identity (レンズ A BLOCKER-2) — **real、採用**

`resolve()` した path を削除対象にしてはならない。同一 UID の並行 process が `mkdtemp` 直後の
`N` を symlink へ差し替えると、`resolve(strict=True)` が別の実 path (`artifact_root` を含みうる) を
返し、finalizer がそれを再帰削除する。脅威モデルは越権攻撃ではなく**自分の並行 pytest worker**
だが、成果物影響 (proof chain の不可逆破壊) が致命的なので採用する。

- **削除対象は `mkdtemp()` の生返値 (作成時 identity) を保持したものだけ**とする。
  `resolve()` 済みの値は repository 外判定と `mcp_config_path` の組み立てにのみ使う
- 削除直前に、対象が symlink でないことを検査する (`shutil.rmtree` は symlink を拒否するが、
  依存せず明示する)
- 削除直前に、`artifact_root` の解決結果が削除対象の内側でないことを assert する (非交差)

### B2. 例外契約と再試行 (レンズ A BLOCKER-3) — **real、採用**

`weakref.finalize.__call__` は callback 実行**前**に registry から自身を pop するので one-shot であり、
`rmtree(ignore_errors=True)` が黙って失敗しても二度と再試行されない。また `finally: close()` が
送出すると、元の戻り値・元の例外を上書きして**受理集合を変える**。

- `close()` は**決して送出しない**。削除失敗は捕捉して `self.cleanup_error` に記録するだけとする
- **削除が成功したときだけ** finalizer を `detach()` する。失敗時は armed のまま残し、
  次の `close()`・GC・interpreter shutdown で再試行できるようにする
- `close()` は idempotent とする (二重呼び出しが no-op)
- finalizer の callback は**module-level 関数**とし、`self` や bound method を捕捉しない
  (捕捉すると owner が永久に生き残り fallback が発火しない = 段 2 プランが挙げた最大リスク)

### B3. positive control の分離 (レンズ A BLOCKER-4 = レンズ B BLOCKER-2) — **real、採用**

「close 前に guard を呼んで `AssertionError` を期待する」形は**偽 green** である。close 前は cwd も
存在するので、root assert を削除しても cwd assert が発火して `pytest.raises` が緑のまま通る。

- 各 predicate (root 消滅 / 各 cwd 消滅 / `artifact_root` 存続 / artifact bytes 不変 /
  外部 marker 存続 / 非交差) ごとに、**その predicate だけが偽で他は全て真**の入力を作り、
  guard が赤くなることを確認する負例を置く

### B4. 第 3 ファイルは必須 scope (レンズ B [major]) — **real、採用** (上記 §1)

`run_trial(providers=...)` で注入された provider は caller 所有なので close してはならない
(ownership 分岐)。`_provider_set` の途中失敗では、生成済みの provider を明示 close して再送出する。

### B5. gate 到達層の正直な限定 (レンズ A [major]) — **real、採用**

guard が届くのは「明示 close の正常/異常」「参照破棄後の fallback」「静止した削除境界」
「owner の close 呼び出し」「partial construction」「owned/injected 分岐」までである。
**届かない層**: cleanup error 後の再試行実挙動、interpreter shutdown 中の live object、
fork child の atexit、並行 invoke/close、close 後の再 invoke、scope 外 callsite。
worklog と guard の docstring に、この**届かない層**を明記する。

## 3. 変異事前登録 (`DW-M01`、実装前)

各変異は「その位置より前に同じ入力を拒否する検査がないこと」「無効化時の赤理由が一つに絞れること」を
実装後に harness の anchor 検査で確認する。

| ID | 変異 | 期待 kill 元 (canonical) |
|---|---|---|
| M1 | `close()` を no-op 化 | 明示 close guard |
| M2 | `weakref.finalize` の登録を削除 | fallback guard |
| M3 | finalize callback を bound method (`self.close`) に変える | fallback guard (owner が生き残る) |
| M4 | 削除対象を作成時 identity から `resolve()` 済み path へ戻す | symlink 差し替え負例 |
| M5 | `close()` の例外抑止を外し送出させる | close-never-raises guard |
| M6 | 削除成功前に `finalizer.detach()` する | 再試行 guard |
| M7 | `__init__` の `except BaseException` cleanup を除去 | init 失敗 parametrized guard |
| M8 | `seal()` の `finally: close()` を除去 | owner guard (強参照保持版) |
| M9 | `run_trial()` の owned-close を除去 | owner guard |
| M10 | `run_trial()` が injected provider も close する (**過剰拒否側の正例**) | ownership 分岐 guard |
| M11 | `_provider_set` の partial-failure close を除去 | partial construction guard |
| M12 | invocation ごとに cwd を即時削除する | 既存 pin `test_s8b_prediction_runner.py:557` / `653-659` |
| M13 | guard の root 消滅 assert を削除 | predicate 分離負例 (root) |
| M14 | guard の `artifact_root` 存続 assert を削除 | predicate 分離負例 (artifact) |
| M15 | guard の artifact bytes 不変 assert を削除 | predicate 分離負例 (bytes) |
| M16 | 削除対象を `self.artifact_root` へ差し替える | 非交差 assert |

M16 の封じ込め: guard test の `artifact_root` は `tmp_path` 配下に置く。実 `output/` を
削除対象にする変異は**走らせない**。

`DW-M08` の新旧両走: 本 wave は production も変えるため「テスト強化だけの wave」ではないが、
guard の純増検出力を示すため、M13〜M15 は変更前 HEAD 版テストでも走らせて差分を記録する。

## 4. 実装単位

**単一単位**とする。理由: 3 ファイルが共通 helper (`_create_neutral_root` 相当) と `close()` 契約を
共有し、分割すると単位 B が単位 A の完了待ちになり並列化できない (段 2 プランの判断を採用)。

## 5. 実装子への追加拘束 (段 3 の所見から)

- **login node で pytest を直接走らせてはならない** (`.codex` に hook 未配線 = 機械的に止まらない)。
  テストを走らせる必要があるときは `python3 tools/run_tests.py <args>` を使う
- 受理集合 (拒否条件) を増やしても減らしてもいけない。`close()` は新しい拒否を作らない
- `artifact_root` 配下 (payload / envelope) を削除・改変する経路を作ってはならない
- 既存 assert (`test_s8b_prediction_runner.py:557`, `569-574`, `653-659`) を弱めない
