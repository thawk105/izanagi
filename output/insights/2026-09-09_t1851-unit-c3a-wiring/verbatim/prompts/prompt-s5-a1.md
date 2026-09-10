単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (書込み可。ここだけを編集する)**: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a1`
- **親の段 4 裁定 (これが scope の正本)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s1-brief.md`
- 段 2 plan: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s2-plan.md`
- 段 3 レンズ A: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s3-lensA.md`
- 段 3 レンズ B: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s3-lensB.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a1/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a1/CLAUDE.md`

# 段 5 子 A1 — launcher に封印 pre-probe の二段入口を作る

## 所有 path (これ以外を 1 行も変えない)

- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

**docs は編集しない。commit しない。`git add` もしない。** 親が行う。

## 実装する境界 (親が固定した。勝手に変えない)

```python
def probe_floor_attempt_preconditions(
    *, post_probe: FloorPostProbeCapability,
) -> FloorAttemptPreProbe: ...

def launch_probed_floor_attempt(
    reservation: FloorAttemptReservation,
    registry_genesis: FloorAttemptRegistryGenesis,
    measurement: FloorMeasurementCapture,
    *,
    pre_probe: FloorAttemptPreProbe,
    classified_at: Callable[[], str],
    terminal_builder: Callable[[OpenedFloorAttempt], FloorAttemptTerminal],
) -> FloorAttemptLaunchResult: ...
```

- `probe_floor_attempt_preconditions()` は既存 `_assert_owned_post_probe_capability()` と同じ強さで
  capability を検査し、launcher 私有の固定 probe を**1 回だけ**実行して封印 object を返す。
- `FloorAttemptPreProbe` は launcher 私有型。読み取り公開するのは `competing: bool` だけ。
  raw probe mapping と capability は外から読めない形で保持する。
- `launch_probed_floor_attempt()` は封印 object を `probe_before` として使い、**内部で probe を
  やり直さない**。`probe_after` は封印 object が保持する capability で従来どおり取る。
- 封印 object は**一回限り**。同じ object で 2 回 launch したら `FloorAttemptLauncherError` で拒否する。
  caller が自作した object、別 capability 由来の object、type を偽装した object も拒否する。
- 既存 `launch_floor_attempt()` は**署名も挙動も変えない。** 内部実装を共有してよいが、
  competing pre-probe を渡されたときの現在の挙動 (capture せず、`probe_before.competing=True` の
  terminal を作る) は `launch_probed_floor_attempt()` でも**そのまま維持する**。

## 現行挙動の明記 (実装前に出力へ書くこと)

`_launch_floor_attempt()` の現在の順序 (`_checked_reservation_policy` → `_ensure_registry_genesis` →
`_reserve` → `probe_before` → competing なら capture 省略 → `probe_after` → `classify_attempt`) を
file:line で書き、二段化後にどの順序になるかを対で書く。**受理・拒否の集合が変わらないことを示す。**

## 新設する test (自分で走らせて nodeid と件数を報告する)

正例と負例を分け、**実体を名指しする**。依存先を stub して通す形にしない。

- 封印 pre-probe が 1 回だけ probe を実行すること (副作用回数を数える)
- 封印 object の再利用が拒否されること
- caller 自作 object・偽装 type が拒否されること
- `launch_probed_floor_attempt()` が内部で probe をやり直さないこと (probe 呼び出し回数で示す)
- clean pre-probe で従来と同じ terminal・classification になること
- competing pre-probe で capture が走らず、従来と同じ terminal になること
- 新入口が `registry` / `sealed_terminal_recorder` を引数に露出しないこと、
  固定 sealed recorder を使うこと (既存 `test_certified_wrapper_...:2222-2230` と同じ強さで)

## 禁止

- 既存 test の期待値を変えない。反転・緩和・skip・削除をしない。赤なら実装側が誤りとする。
  期待値が誤りだと判断したら**実装を変えず報告して止まる**。
- 受理集合を指示外に変えない。`FORMULA_ID`、凍結成果物、`attempt_registry_core.py` に触れない。
- launcher の perf 述語の**新しい直接 call** を作らない
  (`test_official_perf_closure.py` の AST inventory が落ちる)。
- 期待値へ揮発 payload (working tree hash、時刻、pid など) を焼き込まない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 検査 (自分で実走する)

作業 root は書込み可である。**`tools/run_tests.py` は sandbox では rc=16 になるので使わない。**
自走 harness を使う。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a1
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py
```

- 緑は**実走した nodeid 数と範囲を併記**する。走らせていないものを緑と書かない。
- 新設・改名した test の単位は、親の名指しを網羅と見なさず、**自分で制約 meta-test を洗い出して**
  走らせる (公開 API の署名 pin、import 集合 pin、AST 走査 test など)。
- 実走不能なら `closed` と申告せず「実装済み・未実走」と書く。

## 出力形式

```
## 総括
(3-5 行)

## 現行挙動と二段化後の順序 (file:line で対)

## 実装した内容

## 新設した test (nodeid / 正例・負例)

## 実走結果 (command と passed/failed の実数)

## 所有外への波及可能性 (静的列挙)
(所有外 caller、共有 fixture、consumer test)

## 期待赤 (親 docs 未 land 由来のものがあれば)

## 残った懸念
```
