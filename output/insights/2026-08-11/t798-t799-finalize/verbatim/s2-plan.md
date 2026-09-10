## 総括

実装方針は、transaction state を厳格な v2 schema にし、`absent → applied → committed → absent` の単一 lifecycle に固定する。`apply_fold()` は state を削除せず、land が fold commit 後に `committed` へ遷移させ、既存 postcondition と `verify_declared_fold_commit()` が全部通った後だけ `finalize_fold()` が削除する。

入力 closure は plan が実際に読んだ値を hash 化し、resume では transaction 自身による before→after／fragment GC を正規化して同じ入力値へ戻した上で再計算する。単純に現 filesystem を hash すると正常な partial resume まで必ず不一致になるため、この正規化は schema 契約の一部とする。

静的検査のみ実施した。書込み・pytest・checker 実走は行っておらず、検査を「緑」とは報告しない。worktree は clean。

重要な P2 攻撃点が 1 件ある。現行 commit 呼出し [tools/dev_wave_land.py:1911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1911) と、その直後に追加する `applied → committed` 書換えは別 filesystem operation なので、その間の SIGKILL では `phase=applied` かつ main が fold commit という、確定受理 2 形の外側が残る。受理集合を広げず commit-first も scope 外という条件下では、この窓をゼロにはできない。本 plan はその形を明示的に拒否するが、段 4 では「検出可能な残骸として許容するか」を real な残余リスクとして裁定する必要がある。

## 1. transaction state schema 契約

JSON は UTF-8、正準 compact JSON (`sort_keys=True`, separators `(",", ":")`) 1 行 + LF。top-level と全 nested object は下表の field 集合と完全一致させ、余分・欠落・型 coercion を拒否する。`str(...)`、`bool(...)`、`int(...)` による現在の暗黙変換は廃止する。

```json
{
  "version": 2,
  "phase": "applied",
  "transaction_id": "<64 lowercase hex>",
  "origin": {
    "kind": "land",
    "base": "<git object id>",
    "tested_tip": "<git object id>",
    "wave_ref": "refs/heads/...",
    "rollback_ref": "<git object id>"
  },
  "input_closure_sha256": "<64 lowercase hex>",
  "fold_date": "2026-08-11",
  "fragments": [
    {
      "path": "docs/spool/worklog/....md",
      "authored": "2026-08-11",
      "wave": "wave-name",
      "seq": 1,
      "content_sha256": "<64 lowercase hex>",
      "allocations": [["T:slug", "[T-826]"]]
    }
  ],
  "gc_paths": ["docs/spool/worklog/....md"],
  "projected_worklog_bytes": 12345,
  "rotation_path": null,
  "targets": [
    {
      "path": "docs/worklog.md",
      "before_exists": true,
      "before_sha256": "<64 lowercase hex>",
      "after_sha256": "<64 lowercase hex>",
      "after_bytes_b64": "..."
    }
  ]
}
```

| field | 値域・観測者 | 書く時点 | resume 時の照合 | 不一致 |
|---|---|---|---|---|
| `version` | `type(value) is int` かつ厳密に `2` | state 初回作成時 | `_load_state()` が `2` と完全一致 | `TransactionError`。v1 migration はしない |
| `phase` | `"applied"` / `"committed"` のみ | 初回は `apply_fold()` が `applied`。fold commit 成功直後に land が `committed` | active branch、`_discover()`、`mark_fold_committed()`、`finalize_fold()` が各期待相と比較 | `TransactionError`。land は `RC_FOLD_RECOVERY_FAILED` へ畳む |
| `transaction_id` | SHA-256 64 lowercase hex | plan 時に観測入力から算出、初回 state 作成時 | state の immutable payload を正準化して再計算 | `TransactionError("transaction_id が payload と不一致")` |
| `origin.kind` | `"land"` / `"standalone"` | plan 時 | kind 別の Git 実体照合を選択 | `TransactionError` |
| `origin.base` | Git OID 40/64 lowercase hex。land は lock 内の `locked_main`、standalone は plan repo の HEAD | plan 時 | object が commit として存在し、`tested_tip` の ancestor。standalone は現在 HEAD とも一致 | `TransactionError` |
| `origin.tested_tip` | land は検証済み wave HEAD、standalone は plan repo HEAD | plan 時 | applied では main HEAD、committed では main HEAD の親。land-origin では現在の wave HEAD/ref とも比較 | `TransactionError` |
| `origin.wave_ref` | `git symbolic-ref --quiet HEAD` の full ref | plan 時 | land-origin は現在の wave symbolic ref、standalone-origin は plan/apply repo の symbolic ref | `TransactionError` |
| `origin.rollback_ref` | land/standalone とも本変更では `origin.base` と同値。別 field として厳密に束縛 | plan 時 | commit object の存在・ancestor 関係・rollback 引数との一致 | `TransactionError` |
| `input_closure_sha256` | 下記 closure payload の SHA-256 | plan が全入力を一度だけ読んだ後 | transaction-owned path を plan 前の値へ正規化して再計算 | `TransactionError("plan 入力 closure が変化")` |
| `fold_date` | 実在 ISO date | plan 時 | transaction payload の再 hash、生成済み target bytes と結び付ける | schema/hash 不一致として `TransactionError` |
| `fragments` | list。各 object は上記 6 field exact、path/seq 順序・一意性も検査 | plan 時 | present なら content hash、missing は全 target after 後だけ state の hash で正規化。supervised wave 照合にも使用 | `TransactionError` |
| `gc_paths` | sorted unique list。`fragments[*].path` と完全一致 | plan 時 | present/missing と fragment hash、target 状態との保存則を照合 | `TransactionError` |
| `projected_worklog_bytes` | bool でない非負 int | plan 時 | transaction ID 再計算。`docs/worklog.md` after bytes 長とも整合検査 | `TransactionError` |
| `rotation_path` | `null` または安全な `docs/archive/worklog-*.md` | plan 時 | non-null なら target に exact 1 件存在し、plan 前 closure からは除外 | `TransactionError` |
| `targets` | sorted unique list。nested field exact。SHA は64桁、base64は strict decode | plan 時 | after bytes hash、現在値が before/after のどちらか、`before_exists` も厳密比較 | `TransactionError` |

### `transaction_id` payload

`version`、`phase`、`transaction_id` 自身、raw の `after_bytes_b64` は除外する。phase 書換えで ID が変わらず、raw bytes は `after_sha256` によって束縛する。

```python
{
    "fold_date": plan.fold_date,
    "origin": {
        "kind": ...,
        "base": ...,
        "tested_tip": ...,
        "wave_ref": ...,
        "rollback_ref": ...,
    },
    "input_closure_sha256": plan.input_closure_sha256,
    "fragments": [
        {
            "path": ...,
            "authored": ...,
            "wave": ...,
            "seq": ...,
            "content_sha256": ...,
            "allocations": [[key, value], ...],
        },
        ...
    ],
    "gc_paths": [...],
    "projected_worklog_bytes": ...,
    "rotation_path": ...,
    "targets": [
        {
            "path": ...,
            "before_exists": ...,
            "before_sha256": ...,
            "after_sha256": ...,
        },
        ...
    ],
}
```

各 list は path/key の決定的順序に正規化し、compact JSON の SHA-256 を `transaction_id` とする。これにより origin/closure だけでなく、`before_exists`、GC 対象、rotation target など state を後編集しても ID 不一致になる。

### 入力 closure

正準 payload は次に固定する。

```python
{
    "files": {
        "<repo-relative POSIX path>": "<sha256(raw bytes)>",
        ...
    },
    "worklog_rotate_bytes": <positive int>,
}
```

`files` に入れる全集合:

- `docs/worklog.md`
- `docs/decisions.md`
- `docs/failures.md`
- `docs/phase3.md`
- `docs/archive/README.md`
- plan 時点の全 `docs/archive/worklog-*.md`
- `docs/spool/FOLDED.md`
- plan 時点の全 fragment

resume 正規化は以下に限定する。

- target が before/after のどちらかなら closure 値には `before_sha256` を使用。
- transaction fragment が present なら実 hash 一致を要求し、missing なら「全 target after」の場合だけ state 内 `content_sha256` を使用。
- plan が新設する `rotation_path` は入力集合から除外。
- transaction 外の canonical/archive/新 fragment は現在 bytes をそのまま hash。追加・削除・変更は closure 不一致。
- target 第三状態や、target が before のまま fragment が missing なら closure 計算前に拒否。

### phase 遷移

| 遷移 | writer | 条件 |
|---|---|---|
| `absent → applied` | `apply_fold()` | Git origin、closure、clean preflight が mutation 前に全て一致 |
| `applied → applied` | `apply_fold()` resume | before/after 収束のみ。state bytes の不用意な再生成はしない |
| `applied → committed` | land の `mark_fold_committed()` | commit 成功、現在 HEAD が `tested_tip` の単一親 child、全 target after、全 GC missing |
| `committed → absent` | land の `finalize_fold()` | 全 postcondition と `verify_declared_fold_commit()` 成功後 |
| `applied/committed → absent` | `_rollback_fold()` | ref/index/path の全 restore point が成功したときだけ |
| その他 | 誰も書かない | `committed → applied`、unknown phase、standalone finalize は拒否 |

## 2. `tools/spool_fold.py`

### data model と origin

[tools/spool_fold.py:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:135) 付近:

```python
@dataclass(frozen=True)
class FoldOrigin:
    kind: str
    base: str
    tested_tip: str
    wave_ref: str
    rollback_ref: str
```

`FragmentReceipt` に `base` / `tested_tip` / `wave_ref` を追加する。`FoldPlan` には必須 field として `origin`, `input_closure_sha256`, `phase` を追加する。state decode 時の欠落を default で補わない。

`FoldPlan.as_dict()` [tools/spool_fold.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:157) の dry-run 公開 schema は変更せず、origin/phase/closure は transaction 内部契約に留める。これにより既存の exact CLI payload pin [test_spool_fold.py:2567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:2567) を不要に壊さない。

### `_discover()`

現行 [tools/spool_fold.py:936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:936) を次へ変更する。

```python
def _discover(
    repo: Path,
    *,
    state_gate: bool,
    accept_complete_active: bool = False,
) -> tuple[...]:
```

- `validate_spool_tree()` [tools/spool_fold.py:1041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1041) だけ `accept_complete_active=True`。
- `plan_fold()` は false。state 存在中に次 transaction を計画しない。
- state を strict load し、後述の受理表で「全 target after・全 GC missing・phase と HEAD 形が一致」の場合だけ `transaction-active` を抑止して通常 layout/receipt 検査へ進む。
- schema/closure/第三状態は `Issue(code="transaction-state")`、正常だが未完の partial applied は `Issue(code="transaction-active")`。
- 現在の「state があれば無条件 return」[tools/spool_fold.py:949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:949) は exact predicate に置換する。

### receipt

[tools/spool_fold.py:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1330):

- 新規 receipt exact set を `{allocations, authored, base, content_sha256, seq, tested_tip, wave, wave_ref}` にする。
- `base` / `tested_tip` は Git OID、`wave_ref` は full symbolic ref として検査。
- 既存 `FOLDED.md` には旧 5-field receipt が大量に存在するため、parser は「旧 exact set」または「新 exact set」の二つだけを受理する。新 field を個別 optional にしたり `required <= set(record)` にしたりしない。
- generator [tools/spool_fold.py:2089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2089) は今後必ず新 exact set を出す。既存 receipt の推測 backfill はしない。

### `_load_rotate_limit()`

[tools/spool_fold.py:1806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1806) の [except 節:1822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1822) を `except BaseException as exc` にする。

`SystemExit(0)`、`KeyboardInterrupt` を含め必ず `SpoolValidationError(code="rotate-limit")` へ畳み、既存 `finally` による `sys.modules` と `sys.dont_write_bytecode` 復元を維持する。

### `plan_fold()`

現行 [tools/spool_fold.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1932):

```python
def plan_fold(
    repo: str | os.PathLike[str] | Path,
    *,
    fold_date: str | None = None,
    origin: FoldOrigin | None = None,
) -> FoldPlan:
```

- `origin is None`: plan repo の HEAD、symbolic HEAD、ref SHA を Git から観測し、`kind="standalone"`、`base=tested_tip=rollback_ref=HEAD` を作る。detached HEAD、ref/HEAD 不一致は `SpoolValidationError`。
- land origin: exact `FoldOrigin` を受け、plan repo の HEAD/ref が `tested_tip`/`wave_ref` と一致すること、`base`/`rollback_ref` が実在 commit で ancestor であることを確認する。
- canonical、archive、receipt、fragment raw bytes、rotate limit を一度だけ読み、それらと同じ snapshot から output と closure hash を作る。closure 計算のための再読で TOCTOU を作らない。
- receipt record に origin の durable 3 値を追加。
- `_plan_transaction_id()` [tools/spool_fold.py:1919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1919) は上記 immutable payload 全体を受ける形へ変更する。
- noop でも origin は観測するが state は作らない。

### state load/apply/finalize

[tools/spool_fold.py:2168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2168)〜[2255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2255):

- `_plan_state()` は v2 exact JSON を生成。
- `_state_plan()` は型 coercion を廃止し、nested field、path、順序、一意性、base64/hash、origin、closure、transaction ID を検証。
- `_load_state()` は version 2 と exact top-level set 以外を拒否。
- `load_active_plan()` は phase を含む `FoldPlan` を返し、transaction ID と正規化 closure を検証する。

[tools/spool_fold.py:2277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2277):

- signature は維持。
- state 無しでは origin HEAD/ref と closure を mutation 前に照合してから `phase=applied` state を durable write。
- state 有りでは strict v2、同じ transaction ID、`phase=applied` のみを受理。
- target/GC の既存 fail-closed 保存則は維持。
- state 削除 [tools/spool_fold.py:2357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2357)〜[2362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2362) を削除する。

直後へ public library API を追加する。

```python
def mark_fold_committed(
    repo: str | os.PathLike[str] | Path,
    plan: FoldPlan,
    *,
    fold_commit: str,
) -> FoldPlan:
    ...
```

- state ID と `phase=applied` を CAS 的に確認。
- HEAD=`fold_commit`、`HEAD^=origin.tested_tip`、全 target after、全 GC missing、closure 一致を確認。
- `phase` だけ `committed` に変え atomic write。updated plan を返す。

```python
def finalize_fold(
    repo: str | os.PathLike[str] | Path,
    plan: FoldPlan,
    *,
    fold_commit: str,
) -> None:
    ...
```

- state ID、`phase=committed`、HEAD/親、complete tree、closure を再確認。
- state unlink + parent directory fsync。
- CLI [tools/spool_fold.py:2497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2497) からは呼ばない。standalone は `applied` state を残す。

## 3. `tools/dev_wave_land.py`

### origin の取得と計画

3 個の独立観測値は以下。

| 値 | 取得位置 | 実体検証 |
|---|---|---|
| `base` / `rollback_ref` | `locked_main = preflight.locked_main` [dev_wave_land.py:2201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2201) | `_verify_heads()` が main HEAD/ref を照合 [dev_wave_land.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:602) |
| `tested_tip` | request を SHA 正規化 [dev_wave_land.py:2105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2105) | wave HEAD との一致 [dev_wave_land.py:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:611)〜[615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:615) |
| `wave_ref` | `preflight.wave_ref` [dev_wave_land.py:2202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2202) | symbolic ref と ref SHA の一致 [dev_wave_land.py:610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:610)〜[613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:613) |

plan 呼出し [dev_wave_land.py:2268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2268) を次にする。

```python
origin = fold.FoldOrigin(
    kind="land",
    base=locked_main,
    tested_tip=tested_tip,
    wave_ref=wave_ref,
    rollback_ref=locked_main,
)
plan = fold.plan_fold(repository.wave, fold_date=fold_date, origin=origin)
```

### locked preflight と active branch

`_locked_preflight()` の active state load [dev_wave_land.py:1298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1298) は strict v2 load を使う。

現在の `_main_is_allowed()` gate [dev_wave_land.py:1331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1331) は、committed recovery に限り次の exact 形も許す。

- state phase が committed。
- state/request tested tip が一致。
- current main が tested tip の単一親 child。
- complete tree、closure、origin が一致。
- `verify_declared_fold_commit()` がその current main を fold commit として受理。

一般の「tested tip の child」は許さない。

provenance audit 分岐 [dev_wave_land.py:2132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2132) は active transaction の場合に入らないようにする。committed state では main != tested tip なので、現状のままだと finalize 前に外部 provenance checker へ流れ、既存 active recovery 契約を壊す。

active branch [dev_wave_land.py:2203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2203):

- `phase=applied`: main=request/state tested tip。partial/complete transaction を `apply_fold()` で収束後、commit 経路へ。
- `phase=committed`: main は exact fold child。再 apply、再 stage、再 commit を全部省略し、postcondition + finalize だけ行う。
- request tested tip、stored tested tip、現在 wave HEAD は全一致。
- land-origin は stored/current wave ref も一致。
- standalone-origin は stored symbolic ref を main 側へ照合し、land wave は request tested tip と一致させる。standalone apply 自体を閉じない。
- rollback 用 `rollback_ref` は hard-coded `tested_tip` [dev_wave_land.py:2260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2260) でなく state の `origin.rollback_ref`。
- active recovery の `index_tree` は現在 index の `write-tree` ではなく、stored rollback ref の tree object を取得する。committed crash 後に現 fold treeを rollback treeとして保存しない。

### `_fold_main_locked()`

現行 [dev_wave_land.py:1839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1839):

1. planned/new または active applied:

   - `apply_fold()`
   - docs/pending 検査
   - stage closure 検査
   - commit [1911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1911)
   - HEAD 取得 [1920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1920)
   - 直ちに `plan = fold.mark_fold_committed(..., fold_commit=fold_commit)`

2. active committed:

   - `fold_commit = current HEAD`
   - apply/stage/commit/phase 書換えを全て skip

3. 共通 postcondition:

   - parent = tested tip
   - main symbolic ref/ref SHA
   - wave HEAD/ref
   - main tracked clean
   - wave clean
   - pending fragment 0
   - `verify_declared_fold_commit()` [1946](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1946)
   - success `LandResult` を先に構築
   - `fold.finalize_fold(..., fold_commit=fold_commit)`
   - その後は fallible operation を置かず return

### rollback

`_rollback_fold()` [dev_wave_land.py:1745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1745) の基本順序は維持する。

- applied/committed のどちらでも、ref/index/path restore が全部成功した場合だけ state を削除する現行条件 [1784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1784)〜[1789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1789) を保持。
- failure 中は phase を書き戻さない。rollback 不完全なら観測した phase の state をそのまま残す。
- active resume では stored rollback ref/tree を渡す。
- state symlink/directory の現行 fail-closed 挙動を維持。
- T-800/T-801 の restore ordering や追加 lifecycle 改修には踏み込まない。

## 4. state 存在時の受理集合

| state / Git / tree 形 | `_discover()` | land | 緩めた場合に壊れる成果物値 |
|---|---|---|---|
| regular file、v2 exact schema、ID/closure/origin 一致が前提 | 次行へ | 次行へ | 欠落 field を許すと base/tip/wave 帰属と closure gate が無効化 |
| `phase=applied`、main=`tested_tip`、各 target は before/after、GC present。partial | 拒否。docs gate を走らせない | 受理して apply を収束 | partial canonical を正式台帳として検査すると T/D/F 採番と receipt が半適用値になる |
| `phase=applied`、main=`tested_tip`、全 target after、全 GC missing | 受理 | 受理。再書込みせず commit へ | この exact 条件を外すと fragment GC と canonical receipt の保存則が崩れる |
| `phase=committed`、main が `tested_tip` の exact fold child、全 target after、全 GC missing | 受理 | 受理。postcondition + finalize のみ | parent/shape を緩めると任意 commit を fold commit として proof chain に載せる |
| `phase=applied` だが main が fold child | 拒否 | 拒否、RC27 | 緩めると phase 遷移の欠落を黙って補い、受理集合が第三形へ広がる |
| `phase=committed` だが main=`tested_tip` | 拒否 | 拒否、RC27 | commit 未作成なのに durable fold 済みとして state を消し得る |
| committed だが current main が任意 child、merge commit、親不一致 | 拒否 | 拒否 | fold commit path/parent 帰属が壊れる |
| target に before/after 以外、symlink、非 regular | 拒否 | 拒否 | canonical への第三者変更を上書きし、台帳値を消す |
| target が before を含むのに GC missing | 拒否 | 拒否 | fragment を失ったまま canonical が未反映になる |
| committed なのに target partial または GC present | 拒否 | 拒否 | commit tree、working tree、receipt の三者が不一致になる |
| archive、rotate limit、canonical 非 target、新 fragment 等で closure 不一致 | 拒否 | 拒否 | archive 跨ぎ最大 T と実採番の対応が壊れ、重複 T を作れる |
| stored/request/current tested tip 不一致 | 拒否 | 拒否 | 別 wave の採番・receipt を今回の fold commit に帰属できる |
| land-origin wave ref 不一致 | 拒否 | 拒否 |同じ commit を指す別 wave identity へ receipt を付け替えられる |
| version 1、unknown phase、field 欠落/余分、型 coercion が必要 | 拒否 | 拒否 | 新 gate が旧 state 消費時だけ silent disable になる |
| state が symlink/directory/不読 | 拒否 | 拒否 | Git admin 外 payload や非 atomic state を transaction として消費する |

## 5. テスト計画

### 新規 nodeid と一行変異

| nodeid 案 | 殺す一行 |
|---|---|
| `test_state_v2_schema_is_exact_and_v1_is_rejected` | `_load_state()` の `version == 2` guard |
| `test_state_v2_rejects_missing_extra_and_coerced_nested_fields` | `set(state) == REQUIRED_STATE_FIELDS` の exact-set guard |
| `test_transaction_id_binds_origin_closure_and_before_exists` | transaction payload の `"input_closure_sha256": ...`、`"origin": ...`、`"before_exists": ...` を各 parameter case で1行ずつ |
| `test_plan_fold_observes_standalone_head_and_symbolic_ref` | standalone origin の `wave_ref = observed_ref` 代入 |
| `test_plan_fold_rejects_land_origin_not_matching_wave_head` | `origin.tested_tip != observed_head` の raise 行 |
| `test_input_closure_rejects_archive_change_before_state_write` | fresh apply の closure equality guard |
| `test_input_closure_rejects_rotate_limit_change_before_state_write` | closure payload の `worklog_rotate_bytes` 行 |
| `test_input_closure_resume_normalizes_owned_after_and_missing_gc` | target after を `before_sha256` へ正規化する行 |
| `test_apply_keeps_phase_applied_state_after_complete_gc` | 初回 state の `"phase": "applied"` 行 |
| `test_mark_fold_committed_is_applied_to_committed_cas` | phase を `"committed"` に置換する行 |
| `test_finalize_requires_committed_phase` | `phase != "committed"` の raise 行 |
| `test_finalize_removes_state_only_after_complete_shape` | complete-tree guard |
| `test_discover_accepts_only_complete_applied_and_committed_shapes` | `_discover()` の `all(target == "after")` predicate |
| `test_receipt_v2_contains_observed_base_tip_wave_ref` | receipt generator の `"base": plan.origin.base` 等を各1行 |
| `test_receipt_parser_accepts_exact_legacy_or_exact_v2_only` | v2 exact field-set guard |
| `test_load_rotate_limit_wraps_system_exit_and_restores_import_state` | `raise SpoolValidationError(...) from exc` 行 |
| `test_land_passes_exact_observed_origin_to_plan_fold` | land の `origin=origin` 呼出し行 |
| `test_active_applied_transaction_resumes_and_commits_once` | applied branchの `fold.apply_fold(...)` 行 |
| `test_active_committed_transaction_skips_apply_and_commit` | committed branchの early phase 分岐行 |
| `test_active_committed_transaction_rejects_wrong_parent` | `parent == stored tested_tip` guard |
| `test_fold_phase_is_committed_before_declared_postconditions` | commit 後の `mark_fold_committed(...)` 行 |
| `test_fold_state_finalized_only_after_declared_shape_passes` | declared success後の `finalize_fold(...)` 行 |
| `test_committed_recovery_skips_external_provenance_checker` | active state を provenance audit から除外する condition |
| `test_rollback_uses_stored_rollback_ref_and_preserves_state_on_failure` | active branchの `rollback_ref=plan.origin.rollback_ref` 行 |
| `test_applied_state_with_already_advanced_fold_child_is_rejected` | strict phase/HEAD matrix の reject 行。P2 の残余窓も固定 |

### 実際に読んで確認した既存 break

`test_spool_fold.py`:

- `test_interrupted_transaction_resumes_before_and_after_targets` [1747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:1747) は [1779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:1779) で state 削除を pin。削除せず、`phase=applied`、同一 ID、complete tree を exact assert するよう置換する。
- state を直接生成する `test_n16_transaction_rejects_third_state` [1725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:1725) と上記 resume test は v2 origin/closure を含む helper に寄せる。
- standalone apply 後に次 fragment/plan を作る次の既存テスト群は、state が残るため finalize 無しでは active transaction/closure mismatch になる。

  - `test_parallel_fold_implicitly_carries_task_added_by_earlier_wave` [546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:546)
  - `test_parallel_new_then_existing_update_uses_substantive_base_digest` [563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:563)
  - `test_compact_carry_uses_explicit_prior_across_ordinal_gap` [850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:850)
  - `test_two_worklog_fragments_use_immediate_prior_ordinals` [886](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:886)
  - rotation 後の再 plan test [980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:980)
  - `test_failure_supersede_replay_guards_exact_and_changed_fragments` [1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:1518)
  - `test_n12_second_fold_after_gc_is_noop` [1609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:1609)
  - receipt replay tests [1623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:1623)、[1635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:1635)
  - deferred append replay [2314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:2314)

これらは期待値を削らず、test-only helper で apply→Git fold commit→`mark_fold_committed()`→`finalize_fold()` を完遂してから第2 transactionを始める。親 brief の「壊れる pin は1本だけ」は、state 存在下の次 plan まで含めると成立しない。

`test_dev_wave_land.py`:

- `_FakeFoldModule.plan_fold()` [1927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:1927)、failure override [2157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:2157)、real wrapper [2318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:2318) は `origin` keyword を受ける必要がある。
- `_FakeFoldModule` [1913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:1913) に `mark_fold_committed()` / `finalize_fold()` の call recorder が必要。
- `_rollback_fold_fixture()` の直接 `FoldPlan` 構築 [1958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:1958) は必須 origin/closure/phase と新 transaction payload に合わせる。
- synthetic receipt [2062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:2062) は新 receipt exact shapeへ更新する。
- active tests [2998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:2998)、[3034](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:3034) は fake plan に phase/origin を持たせる。後者の「provenance checker を起動しない」という期待は維持し、committed caseも追加する。
- rollback 成功時の state 削除 pin [2763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:2763) は rollback contract と一致するため維持する。

## 6. 段 5 の所有分割

| worker | 排他的所有 |
|---|---|
| A | `tools/spool_fold.py`、`orchestrator/tests/test_spool_fold.py` |
| B | `tools/dev_wave_land.py`、`orchestrator/tests/test_dev_wave_land.py` |
| 親 | 必要なら `docs/spool/README.md`。実装子は docs を触らない |

file ownership は素集合にできる。ただし意味上の共有 interface は次の5点で、段4確定版を両者へ同文で渡す必要がある。

- `FoldOrigin` の field exact set
- `FoldPlan.phase/origin/input_closure_sha256`
- `plan_fold(..., origin=...)`
- `mark_fold_committed(..., fold_commit=...)`
- `finalize_fold(..., fold_commit=...)`

B 側 fake module もこの interface を完全実装する。A/B が独自名や Mapping 形式へ逸脱すると integration conflict になるため、schema/API 契約だけは先に固定する。

## 7. やらない範囲

- [T-799] (b) の standalone apply 封鎖、新 finalize/inspect CLI。
- 旧 v1 transaction state の migration、推測補完、optional-field 読取り。
- historical receipt への base/tip/ref 推測 backfill。
- 第二 journal の新設。
- T-800/T-801 の rollback ordering・lifecycle 全般。
- commit-tree/update-ref を使う commit-first 再設計。
- archive 跨ぎ T 重複を `check_docs.py` 側で新設検査すること。
- `verify_declared_fold_commit()` の path 集合・commit message・content 検査への拡張。現行 path 形状 [git_state.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_waves/git_state.py:47)、[git_state.py:913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_waves/git_state.py:913) は不変。
- `core.hooksPath=/dev/null` [git_state.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_waves/git_state.py:37) の変更や hook 依存。
- docs の段5実装子編集、commit、テスト実走、性能測定。