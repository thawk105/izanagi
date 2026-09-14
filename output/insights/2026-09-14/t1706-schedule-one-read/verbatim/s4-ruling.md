# [T-1706] 段 4 裁定 — real/refuted、プラン v2、変異事前登録

基準 commit: f5423e2fff3adb164731963ca33e82ed08d08c4d
裁定 inbox 再走査: `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` 90 件。wave 開始 (2026-09-14 03:23 JST)
以後の新規なし (最新 2026-09-08)。`test_codex_reasoning_ab.py` に関わる
`2026-09-01-codex-session-pruning-breaks-acceptance.md` は末尾で **決着済み**
(案 1 の狭粒度版で着地、land 済み)。本 wave を止める裁定はない。

## 所見の裁定

| # | 出所 | 深刻度 | 裁定 | 措置 |
|---|---|---|---|---|
| A-2 | レンズ A | must-fix | **real・採用** | supervisor の source authority 化を撤回。frozen を 1 回読み、その bytes を sha と解析の両方に使う |
| A-1 | レンズ A | nit | **real・意図どおりと明示** | 「照合後に file が消えたら拒否」は二重読みの副作用。観測契約の変更として公開し、弱化ではないと記す |
| A-3 A-4 | レンズ A | nit | **real・文言のみ採用** | 不在の主張に「確認した範囲」を併記する (F717) |
| A-5 | レンズ A | nit | **real・採用** | A-2 の是正は scope 内 (新しい防壁ではなく、現行の観測対象の維持) |
| B-1 | レンズ B | must-fix | **real・採用** | 差し替え点を helper の内側 (sha 算出直後) へ置く。read 計数は helper の最初の読みから数える |
| B-2 | レンズ B | must-fix | **real・採用** | replay の第三の読みを計数区間に入れる。計数区間は **入口の呼び出し全体** とする |
| B-3 | レンズ B | nit | **real・採用** | 旧コードの赤が狙った理由かを確かめる。差し替え・復元の発火回数を各 1 回で assert |
| B-4 | レンズ B | nit | **real・記録のみ** | 43 定義は波及候補であって検査数ではない。`:9239` `:9881` は validator を stub しており新規負例の代替にならない |
| B-5 | レンズ B | nit | **real・採用** | 変異事前登録へ反映 (下記 M1〜M6) |
| B-6 | レンズ B | nit | **real・採用** | brief 冒頭の断定を弱める。静的に言えるのは「hash と解析の入力が食い違いうる構造」までで、certified 集計まで通ることは未証明 |

refuted はゼロ。**scope 外の real 所見もゼロ** (A-5 の是正は scope 内と裁定した)。
裁定パッケージとしてユーザーへ返す項目は現時点で無し。

## プラン v2 (段 5 の実装契約)

### V2-1 共通 helper

- `_artifact_path_with_bytes(manifest_path, descriptor, label, *, root=None) -> tuple[Path, bytes]`
  を `_artifact_path` の直後に足す。`_artifact_path` は **1 行も変えない**。
- 姉妹 helper は `_artifact_path` と同じ検査順序・rc・reason を保つ:
  descriptor が dict → path 解決 → root 包含 → sha が長さ 64 の str → read の OSError → sha 不一致。
- **helper 内で `read_bytes()` を呼ぶのは 1 回だけ。** `return path, data` とし、
  `return path, path.read_bytes()` のような再読をしない。
- `_load_json_object(path, *, data: bytes | None = None)` に省略可能引数を足す。判定は必ず `is None`。
  既存 caller は無変更。docstring に「`data` は同じ操作で `path` から読んだ bytes でなければならない」と書く。

### V2-2 supervisor (`supervise_pair`) — **プランからの変更点**

段 3 レンズ A の must-fix により、**source bytes を authority にしない**。frozen を 1 回だけ読み、
その bytes を sha と解析の両方に使う。

```python
frozen_schedule = run_root / "schedule.json"
source_schedule_bytes = schedule_path.read_bytes()
if frozen_schedule.exists():
    schedule_bytes = frozen_schedule.read_bytes()
    if schedule_bytes != source_schedule_bytes:
        raise ValidationError("run-root schedule bytes changed", RC_ROUTING)
else:
    frozen_schedule.write_bytes(source_schedule_bytes)
    schedule_bytes = frozen_schedule.read_bytes()
schedule_sha = _sha256(schedule_bytes)
schedule = _load_json_object(frozen_schedule, data=schedule_bytes)
```

frozen の読みは両枝とも **ちょうど 1 回**。現行 (fresh 枝 2 回 / 既存枝 3 回) より減るが、
**観測対象は frozen のまま**であり、破損した frozen を拒否する現行の力を失わない。
`run-root schedule bytes changed` の rc と reason は変えない。

### V2-3 replay (`_replay_manifest`)

```python
schedule_path, schedule_bytes = _artifact_path_with_bytes(
    manifest_path, manifest.get("schedule"), "schedule"
)
schedule = _load_json_object(schedule_path, data=schedule_bytes)
...
schedule_sha = _sha256(schedule_bytes)
```

`:11152` の `_sha256(schedule_path.read_bytes())` を置き換える。`:11153` の
`manifest schedule_sha256 mismatch`、`:11162` の supervisor-frozen path 検査、
`:11364` の mtime 検査、`:11366` の launch sha 比較はいずれも残す。

### V2-4 make-packets (`make_packets`)

```python
schedule_path, schedule_bytes = _artifact_path_with_bytes(
    manifest_path.resolve(), schedule_descriptor, "schedule"
)
schedule = _load_json_object(schedule_path, data=schedule_bytes)
```

inline descriptor 枝 (`Mapping` かつ `slots`) と descriptor 無しの旧 packet-only 枝は変更しない。

### V2-5 gate の禁止 (署名で書く)

**禁止:** 3 入口の schedule 経路で `_load_json_object(<path>)` を `data=` 無しで呼ぶこと。
**禁止:** 姉妹 helper の内部で `read_bytes()` を 2 回以上呼ぶこと。

**通る正例:** 正当な schedule (`_schedule` fixture が生成するもの) を一切変更せずに
`supervise_pair` / `_replay_manifest` / `make_packets` を通すと、現行と同じく受理され、
receipt の `schedule_sha256` も現行と同じ値になる。

### V2-6 受理集合について公開する事実 (A-1)

- **固定 input に対する受理集合は不変。** 呼び出し中に変化しない schedule file では、
  受理・拒否・rc・reason がすべて現行と一致する。
- **呼び出し中に変化する input に対しては、挙動が変わる。それが本修正の目的である。**
  具体例: descriptor 照合の後に file が消えると、現行は `cannot read JSON object` で拒否するが、
  修正後は最初の読みで得た bytes で続行する。これは「弱化」ではなく、
  **認証した bytes をその後の file の状態から切り離す**という契約そのものである。
  この 1 行を負例テストの docstring と worklog に書く。

## 変異事前登録 (DW-M01、実装前に登録)

| ID | 位置 | 変異 | 期待 kill |
|---|---|---|---|
| M1 | supervisor の `_load_json_object` 呼び | `data=` を削除 | 差し替え負例が B を検証し、duplicate slot_id 拒否が消える |
| M2 | replay の `_load_json_object` 呼び | `data=` を削除 | 返却 slots に replacement marker が残る |
| M3 | packets の `_load_json_object` 呼び | `data=` を削除 | B が検証され packet が生成される |
| M4 | 姉妹 helper の return | `return path, data` → `return path, path.read_bytes()` | 入口全体の read 計数が 2 になる |
| M5 | replay の sha 算出 | `_sha256(schedule_bytes)` → `_sha256(schedule_path.read_bytes())` | 入口全体の read 計数が 2 になる |
| M6 | supervisor の sha 算出 | `_sha256(schedule_bytes)` → `_sha256(frozen_schedule.read_bytes())` | frozen の read 計数が 2 になる |

- 各変異は実装後に **単一理由性** を確認する (F820)。同じ入力を拒否する層が前後・内側に無く、
  赤理由が 1 つに絞れること。絞れなければ登録せず実効 gate へ再照準する (F28)。
- M4・M5・M6 は **read 計数** でしか死なない。したがって負例テストは
  **内容 assertion と read 計数 assertion を両方**持たなければならない。
- 正例 (受理側) も各入口 1 本ずつ登録する。V2-5 の正例がそれに当たる。

## 段 5 の分割

編集 path が production 1 / test 1 で素集合に割れないため **実装子は 1 単位**。
所有 = `tools/codex_reasoning_ab.py` + `orchestrator/tests/test_codex_reasoning_ab.py`。
