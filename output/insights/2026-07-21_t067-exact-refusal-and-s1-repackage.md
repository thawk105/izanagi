# [T-067] 拒否理由の exact 化 + S-1 系 2 件の再パッケージ — 逐語と変異台帳 (2026-07-21)

対象 wave: `/dev-wave` (branch `worktree-dev-wave-ruling-ac`、基準 commit `3ca2130`)。
task-run: `20260721-s1-oracle-hosyu-b-d07a2403`。ccbench pin `d706650`。

当初 scope は [T-068] (方式 B 実装) + [T-066] (恒真隠蔽除去) + [T-067] (拒否理由 exact 化) の 3 件。
**実装したのは [T-067] のみ**。[T-068] [T-066] は実装せず裁定パッケージへ戻した (理由は下記および worklog)。

---

## 1. 段 1 の実測 (裁定前提の確認)

| 項目 | 実測値 |
|---|---|
| 公式 gate `gate_check(REAL_FREEZE)` の拒否 | ちょうど **4 件** (`allowed=False`) |
| 内訳 [1] | `holdout-freeze-verify: FreezeError: design_source sha256 不一致: recorded=1829af7f… actual=5fbdd7ef…` |
| 内訳 [2] | `known-axes-freeze-verify: FreezeError: frozen_at_head が現行 HEAD の commit ancestor でない: 2066ce6b…` |
| 内訳 [3][4] | `floor-null` / `budget-null` (v1 freeze の設計どおり) |
| holdout の `frozen_at_head` `2e20d441` | **repo に存在しない** (dangling、blob 救済も不能) |
| **holdout の `generator`** | **記録 `1910fff3…` / 実際 `41c0b6a7…` = MISMATCH** |
| ancestry 後段 `ccbench_pin` 照合 | **PASS** |
| ancestry 後段 `build_document` 機械再構成照合 | **PASS** |
| `s8b_oracle_driver.py` の pin | freeze JSON 3 件・`FROZEN_MANIFEST` 8 件・全 repo hash 検索で**不在** |
| `FreezeError` の raise 箇所 | 77〜81 箇所。**全 message が literal 前置きで始まる** |
| 受入ベースライン | **2351 passed / 19 skipped / 0 failed** (rc=0) |

### 新規に判明した事実 (D71/D72 が記録していなかったもの)

1. **holdout freeze の破損は 1 件でなく 2 件。** D71 (7)(a) は `design_source` のみを記録していたが、
   `generator` も外れている。検査順は design → known_axes → generator で fail-fast のため、
   **design を修復すると次に generator が現れる**。checker 自身が freeze 後に編集されており、
   S-1 と同じ**自己ハッシュ構造**に入っている。
2. **ancestry の後段 2 検査が恒久的にマスクされる。** `verify_document()` は ancestry で abort するため、
   例外を握り潰す素朴な格下げでは `ccbench_pin` 照合と機械再構成照合が**二度と実行されない**。
   ancestry は dangling である限り必ず先に落ちるので、将来 `ccbench_pin` がドリフトしても
   「ancestry 失敗」に見えて格下げされる = 恒久的 fail-open。
3. **ancestry 判別は git 障害と非 commit object を巻き込む。** `s1_known_axes_freeze.py:751-754` が
   `_run_git` の `FreezeError` を丸ごと ancestry 文言へ貼り替えるため、git 不在・repo 破損・
   権限エラー・実在 blob SHA (非 commit) がすべて同じ文言になる。
4. **`verify_document` は ROOT 固定。** generator hash・ccbench pin・ancestry のすべてがモジュール定数
   `ROOT` を使い、注入可能なのは `source_resolver` のみ。

---

## 2. 段 3 敵対相談の結論 (2 本とも NO-GO)

- **レンズ 1 (正しさ境界)**: ブロッカー = ancestry 判別の広さ / observation の伝播不足。
  受理集合の正味差分表を作成し、「格下げで新たに受理されるのは意図内 2 件 + **意図外 2 件**
  (実在 blob/非 commit tag、git 操作障害)」と判定。CC 選択結果への誤り波及は**構成できない**と明記。
- **レンズ 2 (整合・実効性)**: ブロッカー 10 件。node 名の golden 固定、`_synthetic_freeze` の外部 consumer、
  変異表の大半が無効、期待赤集合の誤り、caller map の誤りを指摘。
  代案として **P1''** (single parse + shadow 再検証) を提示。

## 3. 段 6 敵対レビューの結論 (2 本とも NO-GO)

- **レンズ A (正しさ・恒真性)**: 親の [T-068] 不実装の**理由付けが誤り**と指摘。
  4→3 で `allowed=False` は裁定時点で既知であり、新事実ではない。
- **レンズ B (整合・裁定妥当性)**: 部分一致が 11 個残存 ([T-067] 未完)、literal の環境脆弱性、
  親裁定の自己矛盾、変異 kill の誤分類を指摘。

**親はレビュー所見をすべて受け入れ、修正ラウンドを 1 回追加した。**

---

## 4. 変異台帳 (B-057)

ハーネス契約: 置換対象が厳密に 1 箇所でなければ**停止**、赤くなった**テスト名を毎回記録**、
ANSI 除去、**新テストと旧テスト (git HEAD 版) の両方**で測って差分を出す。

| 変異 | 層 | 新テスト | 旧テスト | 判定 |
|---|---|---|---|---|
| 対照 (変異なし) | — | 緑 | — | — |
| **M1'** 件数保存の置換 (`floor-null` の文言変更) | `set` | **赤** (2 node) | **緑** | 検出 (新のみ) |
| **M2** `budget-null` の重複 append | `len` | **赤** (2 node) | **緑** | 検出 (新のみ) |

**旧テストが両方とも緑**である点が [T-067] が買った検出力そのもの。

**M2 の帰属は両層同時変異で確定**: `len` 比較あり → 赤 / `len` 比較を除去 → 緑。
ゆえに kill は `len` 比較に帰属する (`set` 比較は重複を吸収するため)。

### 計上の射程 (正直な限定)

**M1'/M2 は B-057 の kill には数えない。** dev-wave の kill 基準は
「受理集合または fail-closed 挙動が期待方向へ変わった」であり、両変異とも `allowed` は
変異前後とも `False` で受理集合は変わらない。変わるのは**構造化された拒否理由集合**である。
よって **diagnostic sensitivity pin** として記録する。

初回に登録した M1 (unique な refusal を「追加」) は `len` と `set` を同時に壊す**過剰決定**で
あったため、レビュー指摘を受けて件数保存の置換変異 M1' へ差し替えた (erratum)。

### 修正の positive control (実測)

修正 1 (揮発 payload を期待値から外す) が効いていることを実測で確認した:
`docs/phase3-8b-descriptor-design.md` に 1 行追記 → **テストは緑のまま** (修正前なら赤)。
doc は復元済み。

---

## 5. 実装の実測

- 変更ファイル: `orchestrator/tests/test_s8b_oracle_driver.py` の **1 ファイルのみ**。
- helper 2 種: `_assert_exact_refusals` (件数 + 集合の完全一致、hermetic fixture 用、**11 箇所**)、
  `_assert_refusal_reasons` (件数 + 理由 prefix の 1:1 対応、実 repo 依存で揮発する箇所用、**3 箇所**)。
- `result["refusals"][0]` に対する部分一致は **0 件**になった。
- node 名は維持 (`conftest.py` と `test_real_repo_serialization.py` の golden 2 面に固定されているため)。
- **親の受入全走 (shim なし)**: **2351 passed / 19 skipped / 0 failed** (rc=0)。ベースラインと同一。

### 実装子の実走に関する注記

実装子は sandbox の read-only `.git/.../index.lock` 制約で全走が落ちた。初回ラウンドでは
`/tmp` shim を噛ませて緑を報告したため、**親が shim なしで再走**した。修正ラウンドでは実装子自身が
「全走について緑とは主張しません。本実走は親の全走を代替しません」と明記した。

---

## 6. [T-067] の未完部分 (次 wave へ)

`_v2_refusal_reason()` parser 経由の検査、extime helper の部分一致、
および `status == "refused"` だけで理由集合を固定していない 2 テストが残る。
`test_required_existing_claim_refuses…` は所有 PID が単独走 (`2`) と xdist 走 (`35`) で
**変動する**ため意図的に prefix 検査とした (コメント済み)。

---

## 7. 逐語 (以下、各段の出力をそのまま凍結)

以下は段 2 (プラン起草)、段 3 (敵対相談 2 本)、段 6 (敵対レビュー 2 本)、
段 5 実装子の完了報告 2 回分の**逐語**である。編集していない。


---

### 段2 codex プラン起草

## 結論

実装は **GO（P1 の前提だけ一部否認し、実装形を修正）** です。

`verify()` の例外を単純に握り潰す案は不可です。known-axes JSON を consumer が一度だけ読み、公開 `verify_document()` を通したうえで、ancestry 例外だけを observation 化し、元 checker と同じ順序で `ccbench_pin` と機械再構成を再検査します。

編集対象は指定どおり次の素集合です。

- 単位 A: `s8b_oracle_driver.py`、`test_s8b_oracle_driver.py`
- 単位 B: `test_s1_measurement_freeze.py`

凍結成果物、`s1_known_axes_freeze.py`、`s8b_holdout_freeze.py`、`FROZEN_MANIFEST` は変更しません。

## provisional 裁定への回答

| 裁定 | 判定 | 根拠 |
|---|---|---|
| P1 | 条件付き採用 | 後段 2 検査の実行は必須。ただし「公開 API だけで元の検査順を完全再現できる」は誤り。`build_document(ccbench_pin=None)` だけでは ccbench drift が全文比較と過剰決定になるため、consumer 側で現 pin 取得を複製する。 |
| P2 | 採用 | `FreezeError` かつ `str(exc).startswith(...)` に限定する。`in` は不可。 |
| P3 | 採用 | checker SHA-256 `1d4d45a3…` を test 側に literal pin する。ただし既存 generator 検査とも重なるため、変異 kill ではなく「複製見直しを要求する診断 guard」と位置付ける。 |
| P4 | 採用・補強 | `GateDecision.observations` を追加するだけでなく、`run_block()` の completed／budget-refused／post-gate refusal にも保持する。 |
| P5 | 採用 | 公式 gate は 3 件の literal 集合へ固定。列挙された 7 個の `any(startswith)` をすべて exact 集合検査へ変える。 |
| P6 | 採用・実装形修正 | `K.build_document` の monkeypatch と動的 `rev-parse`／現行 generator hash 注入を廃止する。実 `build_document()` と外部 literal digest を組み合わせる。 |
| P7 | 採用 | holdout の `design_source` 破損は残す。fixture で現行 hash を注入して隠さない。 |
| P8 | 採用 | 単位間のコード依存なし。双方が immutable な checker SHA を参照するだけなので並列実装可能。 |

## 単位 A

### 1. `GateDecision` と ancestry 後段検査

対象: [s8b_oracle_driver.py:16](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:16>)、[同:81](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:81>)

置換前:

```python
from dataclasses import asdict, dataclass

@dataclass
class GateDecision:
    allowed: bool
    refusals: list[str]
```

置換後:

```python
from dataclasses import asdict, dataclass, field

@dataclass
class GateDecision:
    allowed: bool
    refusals: list[str]
    observations: list[dict[str, str]] = field(default_factory=list)
```

`default_factory` により既存の `GateDecision(True, [])` は壊しません。一方、`asdict()` を使う全 CLI/refusal 出力には空配列を含む `observations` が追加されます。

### 2. consumer 側の後段検査 helper

対象: [s8b_oracle_driver.py:160](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:160>) の `_resolve_recorded_path()` 直後へ追加。

置換前:

```python
def _resolve_recorded_path(path_text: str, *, root: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path
```

置換後:

```python
_KNOWN_AXES_ANCESTRY_PREFIX = (
    "frozen_at_head が現行 HEAD の commit ancestor でない"
)


def _resolve_recorded_path(path_text: str, *, root: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def _current_known_axes_ccbench_pin() -> str:
    args = ["rev-parse", "HEAD"]
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=s1_known_axes_freeze.ROOT / "external/ccbench",
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise s1_known_axes_freeze.FreezeError(
            f"git {' '.join(args)} に失敗: {detail.strip()}"
        ) from exc
    return completed.stdout.strip()


def _verify_known_axes_post_ancestry(doc: Mapping) -> None:
    actual_pin = _current_known_axes_ccbench_pin()
    if doc.get("ccbench_pin") != actual_pin:
        raise s1_known_axes_freeze.FreezeError(
            f"ccbench_pin 不一致: recorded={doc.get('ccbench_pin')} "
            f"actual={actual_pin}"
        )

    expected_doc = s1_known_axes_freeze.build_document(
        frozen_at_head=doc["frozen_at_head"],
        ccbench_pin=doc["ccbench_pin"],
        python_version=doc.get("python_version"),
        generator_sha=doc["generator"]["sha256"],
    )
    if doc != expected_doc:
        raise s1_known_axes_freeze.FreezeError(
            "freeze JSON の内容が現行 generator による機械再構成と不一致"
        )
```

ここで `ccbench_pin` を独立取得する理由は重要です。`build_document(ccbench_pin=None)` の戻り値だけを使うと、pin 不一致が最終 document 比較でも落ち、pin 検査を削除する単層変異が等価変異になります。上記なら元 checker と同じく:

1. 現 pin 比較
2. recorded pin を override した機械再構成

の独立した二層になります。

`build_document()` は通常 ancestry 成功時には checker 内で一回、ancestry 失敗時には consumer 内で一回だけ実行されます。二重実行はありません。

### 3. `_gate_check_core` の置換

対象: [s8b_oracle_driver.py:197](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:197>)、[同:249-261](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:249>)、[同:288](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:288>)

置換前:

```python
refusals: list[str] = []
freeze: Optional[dict] = None
freeze_sha: Optional[str] = None
```

```python
try:
    known_record = freeze.get("known_axes_freeze") if isinstance(freeze, Mapping) else None
    ...
    known_path = _resolve_recorded_path(known_path_text, root=root)
    s1_known_axes_freeze.verify(
        known_path, source_resolver=lambda relative: root / relative,
    )
except Exception as exc:
    refusals.append(f"known-axes-freeze-verify: {type(exc).__name__}: {exc}")
```

```python
return GateDecision(allowed=not refusals, refusals=refusals)
```

置換後:

```python
refusals: list[str] = []
observations: list[dict[str, str]] = []
freeze: Optional[dict] = None
freeze_sha: Optional[str] = None
```

```python
try:
    known_record = freeze.get("known_axes_freeze") if isinstance(freeze, Mapping) else None
    if not isinstance(known_record, Mapping):
        raise OracleDriverError("known_axes_freeze source record がない")
    known_path_text = known_record.get("path")
    if not isinstance(known_path_text, str) or not known_path_text:
        raise OracleDriverError("known_axes_freeze.path が空でない文字列でない")
    known_path = _resolve_recorded_path(known_path_text, root=root)

    if not known_path.is_file():
        raise s1_known_axes_freeze.FreezeError(
            f"freeze が存在しない: {known_path}"
        )
    try:
        known_doc = _load_json_object(known_path)
    except OracleDriverError as exc:
        raise s1_known_axes_freeze.FreezeError(str(exc)) from exc

    try:
        s1_known_axes_freeze.verify_document(
            known_doc,
            source_resolver=lambda relative: root / relative,
        )
    except s1_known_axes_freeze.FreezeError as exc:
        if not str(exc).startswith(_KNOWN_AXES_ANCESTRY_PREFIX):
            raise
        observations.append({
            "kind": "known-axes-freeze-ancestry",
            "status": "unverified",
            "path": known_path_text,
            "frozen_at_head": known_doc["frozen_at_head"],
            "detail": str(exc),
        })
        _verify_known_axes_post_ancestry(known_doc)
except Exception as exc:
    refusals.append(f"known-axes-freeze-verify: {type(exc).__name__}: {exc}")
```

```python
return GateDecision(
    allowed=not refusals,
    refusals=refusals,
    observations=observations,
)
```

observation は後段検査より先に追加します。したがって、将来 ccbench drift も同時に起きた場合は「ancestry unverified」と「ccbench refusal」の双方が残ります。

### 4. `run_block()` への observation 伝播

対象: [s8b_oracle_driver.py:856-873](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:856>)、[同:954-1021](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:954>)、[同:1077-1087](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1077>)、[同:1300-1313](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1300>)

戻り値 docstring の gate fields に `observations` を追加します。

post-gate で新しい refusal を作る箇所は、置換前:

```python
decision = GateDecision(
    allowed=False,
    refusals=["manifest-verify: 検証済み manifest object がない"],
)
```

置換後:

```python
decision = GateDecision(
    allowed=False,
    refusals=["manifest-verify: 検証済み manifest object がない"],
    observations=decision.observations,
)
```

同様に :990、:994、:1019 の `GateDecision(...)` にも:

```python
observations=decision.observations,
```

を渡します。

budget-refused と最終 return は、置換前:

```python
"allowed": True,
"refusals": [],
```

置換後:

```python
**asdict(decision),
```

とします。これにより completed、protocol violation、internal error、budget exhaustion の全経路で gate observation が落ちません。

### 5. oracle テストの fixture 甘化を除去

対象: [test_s8b_oracle_driver.py:64-97](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:64>)

置換前:

```python
document = _real_document()
design = ROOT / document["design_source"]["path"]
document["design_source"]["sha256"] = _sha256(design)
```

置換後:

```python
document = _real_document()
# freeze に記録された source hash をそのまま使う。
# 現 worktree の hash を注入して provenance failure を隠さない。
```

`_synthetic_freeze()` と `_floor_only_freeze()` の両方から現行 hash 注入を削除します。v2 の対象テストは gate を明示的に fake 化しているか、active 解決で先に止まるため、この注入は不要です。

### 6. checker drift guard と exact helper

対象: [test_s8b_oracle_driver.py:46-62](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:46>)

追加:

```python
KNOWN_AXES_CHECKER_SHA256 = (
    "1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0"
)


def _assert_exact_refusals(actual: list[str], expected: set[str]) -> None:
    assert len(actual) == len(expected), actual
    assert set(actual) == expected, actual
```

`len` も比較するため、同じ refusal の重複追加も検出できます。

追加テスト:

```python
def test_known_axes_post_ancestry_copy_tracks_checker_sha256():
    checker = ROOT / driver.s1_known_axes_freeze.SCRIPT_REL
    assert _sha256(checker) == KNOWN_AXES_CHECKER_SHA256
```

### 7. 公式 gate を 3 件＋observation に固定

対象: [test_s8b_oracle_driver.py:503-507](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:503>)

置換前:

```python
def test_real_freeze_gate_lists_floor_and_budget_null():
    decision = driver.gate_check(freeze_path=REAL_FREEZE, root=ROOT)
    assert not decision.allowed
    assert any(reason.startswith("floor-null:") for reason in decision.refusals)
    assert any(reason.startswith("budget-null:") for reason in decision.refusals)
```

置換後:

```python
def test_real_freeze_gate_has_exact_refusals_and_ancestry_observation():
    decision = driver.gate_check(freeze_path=REAL_FREEZE, root=ROOT)

    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {
        "holdout-freeze-verify: FreezeError: design_source sha256 不一致: "
        "recorded=1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d "
        "actual=5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae",
        "floor-null: freeze.floor が null",
        "budget-null: freeze.budget が null",
    })
    assert decision.observations == [{
        "kind": "known-axes-freeze-ancestry",
        "status": "unverified",
        "path": "output/s1-freeze/known_axes_freeze.json",
        "frozen_at_head": "2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1",
        "detail": (
            "frozen_at_head が現行 HEAD の commit ancestor でない: "
            "2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1"
        ),
    }]
```

### 8. 残りの `any(startswith)` 5 箇所

対象: [test_s8b_oracle_driver.py:787](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:787>)、[同:816-817](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:816>)、[同:1164](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1164>)、[同:2249](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2249>)

それぞれ以下へ置換します。

```python
_assert_exact_refusals(result["refusals"], {
    "freeze-ratify: [no-active] [no-active] live active pointer が無い (v2 未発効)",
})
```

```python
_assert_exact_refusals(result["refusals"], {
    "freeze-ratify: [no-active] [no-active] live active pointer が無い (v2 未発効)",
    "manifest-verify: ManifestError: manifest top-level schema が不一致",
})
```

`test_tampered_freeze_fails_source_verification` は現状 `confirmed_by` 改変より先に holdout ancestry が落ち、テスト名と実際の発火理由が不一致です。入力も次へ変更します。

置換前:

```python
document["confirmed_by"] = document["confirmed_by"] + "-tampered"
```

置換後:

```python
document["design_source"]["sha256"] = "0" * 64
```

refusal は exact に:

```python
_assert_exact_refusals(decision.refusals, {
    "holdout-freeze-verify: FreezeError: design_source sha256 不一致: "
    f"recorded={'0' * 64} "
    "actual=5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae",
    "floor-null: freeze.floor が null",
    "budget-null: freeze.budget が null",
})
```

最後の active-generation テストは:

```python
_assert_exact_refusals(result["refusals"], {
    "freeze-not-active-generation: 与えられた freeze bytes sha256 が"
    "承認束縛済み active 世代と不一致",
})
```

へ変えます。

### 9. `verify` mock seam の移動

対象: [test_s8b_oracle_driver.py:1880](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1880>)、:1920、:1937、:1953、:2281。

置換前:

```python
mock.patch.object(driver.s1_known_axes_freeze, "verify", lambda *a, **k: None)
```

置換後:

```python
mock.patch.object(
    driver.s1_known_axes_freeze, "verify_document", lambda *a, **k: None
)
```

consumer が単一 parse＋`verify_document()` に変わるため必要です。tmp repo には known JSON 自体は存在するので、loader は fake 化しません。

### 10. 新規の focused tests

同 test file に以下を追加します。

- 実 known artifactで ancestry だけが observation になり、後段検査まで完走する。
- `"wrapped: frozen_at_head が..."` は `startswith` を満たさず refusal のまま。
- known JSON の `ccbench_pin` だけを書き換えると、先行検査は ancestry まで到達し、consumer の pin 比較だけで赤。
- known JSON の `what` だけを書き換えると、先行 schema/source/pairing は通り、機械再構成比較だけで赤。
- `_run()` に任意 `GateDecision` を渡せる引数を追加し、completed と budget-refused の双方で sentinel observation が返ることを検査。

## 単位 B

対象: [test_s1_measurement_freeze.py:5-138](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:5>)

### 1. 外部固定値

`hashlib` を追加し、以下を module literal として置きます。

```python
FIXTURE_HEAD = "3ca2130878fa1f4717d6faaa6783f75f73e7c3ab"
FIXTURE_CCBENCH_PIN = "d706650cdb31e442bef45b9b4216951d4fb40969"
FIXTURE_GENERATOR_SHA256 = (
    "1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0"
)
FIXTURE_MATERIAL_SHA256 = (
    "9bdaff9d24e8e222099c05ad4495d5828e9f455b31759ebb0e6dcd96d881b460"
)
FIXTURE_KNOWN_AXES_RAW_SHA256 = (
    "df71e8ca076a66da6223ddfaa030fa32cbcc0ceb30559b08bb018f706e42addb"
)
FIXTURE_PYTHON_VERSION = "fixture-python"
```

### 2. 動的注入と echo monkeypatch の置換

置換前:

```python
"sha256": K._sha256(material_source),
...
"frozen_at_head": K._run_git(["rev-parse", "HEAD"]),
"ccbench_pin": K._run_git(
    ["rev-parse", "HEAD"], K.ROOT / "external/ccbench"),
...
"sha256": K._sha256(K.ROOT / K.SCRIPT_REL),
"python_version": sys.version,
...
monkeypatch.setattr(
    K, "build_document", lambda **_kwargs: copy.deepcopy(known_doc))
```

置換後の要点:

```python
material_source.write_text("fixture material\n", encoding="utf-8")
assert hashlib.sha256(material_source.read_bytes()).hexdigest() == (
    FIXTURE_MATERIAL_SHA256
)
source = {
    "path": source_rel,
    "sha256": FIXTURE_MATERIAL_SHA256,
    "key": "minimal fixture source",
}
```

既存 `entries` を固定材料として使い、外部材料 extractor だけを差し替えます。

```python
monkeypatch.setattr(
    K,
    "_p2_entry",
    lambda workload: (
        copy.deepcopy(entries[workload]["p2_2_flag_opt"]),
        "fixture",
    ),
)
monkeypatch.setattr(
    K,
    "_fixed_gates_from_recon",
    lambda: {
        workload: entries[workload]["system_gate"]["name"]
        for workload in M.WORKLOADS
    },
)
monkeypatch.setattr(
    K,
    "_stock_common",
    lambda: copy.deepcopy(entries["balanced"]["stock_common"]),
)
monkeypatch.setattr(
    K,
    "_trigger_entries",
    lambda workload, _gate: (
        copy.deepcopy(entries[workload]["system_gate"]),
        copy.deepcopy(entries[workload]["ident_all"]),
    ),
)
monkeypatch.setattr(
    K,
    "_backoff_entry",
    lambda workload: copy.deepcopy(entries[workload]["backoff_fixed_best"]),
)
monkeypatch.setattr(
    K,
    "_sort_entry",
    lambda workload: copy.deepcopy(entries[workload]["sort_best"]),
)
```

その後、mock されていない実 `build_document()` を呼びます。

```python
known_doc = K.build_document(
    frozen_at_head=FIXTURE_HEAD,
    ccbench_pin=FIXTURE_CCBENCH_PIN,
    python_version=FIXTURE_PYTHON_VERSION,
    generator_sha=FIXTURE_GENERATOR_SHA256,
)
known_raw = (
    json.dumps(known_doc, ensure_ascii=False, indent=2) + "\n"
).encode("utf-8")
assert hashlib.sha256(known_raw).hexdigest() == FIXTURE_KNOWN_AXES_RAW_SHA256

known_path = tmp_path / "known_axes_freeze.json"
known_path.write_bytes(known_raw)
```

これにより:

- `K.build_document` 本体は実行される。
- 現行 generator hash、HEAD、ccbench pin を fixture へ注入しない。
- producer 出力が変われば外部 literal raw hash で先に赤になる。
- production known-axes の 63 source や共有 submoduleを読まないため、`conftest.py` の reader 集合を変更せず P8 を維持できる。

## 変異テスト候補

| ID | 変異 | 先行検査の確認 | 単一理由 | 登録 |
|---|---|---|---|---|
| M-A1 | ancestry 分岐で常に再送出する | 実 known doc は generator/source/pairing を通って ancestry に到達済み | observation 化されず helper が例外になるだけ | 可 |
| M-A2 | `startswith` を `in` にする | verifier stub が直接 `"wrapped: <prefix>"` を送出し、それ以前の検査なし | wrapped message が誤って downgrade されるだけ | 可 |
| M-A3 | `ccbench_pin` 比較を削除 | copied known doc の pin だけ変更。schema/generator/source/pairing は通る | rebuild には recorded pin を渡すため全文比較は一致し、pin 比較だけが歯 | 可 |
| M-A4 | `doc != expected_doc` 比較を削除 | `what` 値は `_validate_schema`、source、pairing、pin のいずれも検査しない | 最終機械再構成だけが歯 | 可 |
| M-A5 | completed/budget return から `observations` を落とす | fake gate 以下は既存の正常 fixture | sentinel observation の欠落だけ | 可 |
| M-A6 | core return 直前に余分な refusal を追加 | gate は全 refusal を収集して return まで到達する | exact 件数・集合だけが余分な 1 件を検出 | 可 |
| X-1 | `s1_known_axes_freeze.py` の ancestry 検査を無効化 | generator SHA 検査が ancestry より先に落とす | 自己 hash と immutable 制約に阻まれる | 登録不可 |
| X-2 | public `build_document(ccbench_pin=None)` だけを使い pin 比較を削除 | 全文比較でも pin mismatch が落ちる | 過剰決定で削除変異が等価 | 登録不可 |
| X-3 | 機械再構成比較を削除し、入力は ccbench drift にする | ccbench 比較が先に落とす | 後段へ到達しない | 登録不可 |
| X-4 | fixture の literal generator hash を動的計算へ戻す | baseline bytes が同じなら値も同じ | 等価変異。将来 drift 時しか差が出ない | 登録不可 |
| X-5 | `s8b_holdout_freeze.py` の source 検査を無効化 | immutable checker であり、さらに holdout ancestry が後段で落とす | 禁止対象かつ過剰決定 | 登録不可 |

P3 の checker SHA guard は有用ですが、checker 1 byte 変異は generator 検査や単位 B の literal pin も同時に赤くするため、mutation kill には数えず diagnostic guard とします。

## 期待赤の集合

「production だけ先に変え、既存テストを一切変えない」場合、意味上の期待赤は **空集合**です。現行 `test_real_freeze_gate_lists_floor_and_budget_null` は floor/budget しか見ないため、4→3 を検出せず緑のままです。これ自体が T-067 の再現です。

test-first の順序なら、既存テストでは次の 2 件が意図どおり赤になります。

- `test_real_freeze_gate_lists_floor_and_budget_null` を exact 3 件＋observation へ変更したもの
- `test_tampered_freeze_fails_source_verification` を exact 3 件＋observation へ変更したもの

また、`verify()` から `verify_document()` へ seam を移したのに mock を更新しない場合は、次が機械的に赤になります。これは意味上の期待赤ではなく、同一単位内で必ず直す seam 追随です。

- `test_v2_standalone_gate_check_requires_full_floor_validation`
- `test_v2_gate_happy_path_completes_and_binds_env_store_receipt`
- `test_v2_completed_driver_adapter_campaign_is_accepted_by_report`
- `test_v2_floor_disk_swap_after_launch_uses_same_validated_object`
- `test_v2_store_missing_is_refused`
- `test_v2_store_hash_mismatch_is_refused`
- `test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome`

`test_v2_contract_sha256_mismatch_is_refused` は wrong-layer refusal でも `status=="refused"` だけで緑になるため、mock seam は更新対象ですが期待赤には入りません。これも既存テストの masking です。

pytest は実行せず、読み取りと静的照合のみ行いました。

---

### 段3 敵対相談 レンズ1 (正しさ境界)

# 結論: NO-GO

ブロッカーは所見 **1、2**。P1 と P1' なら、記録値を改変しない **P1 の方が安全**です。ただし現在の P1 は ancestry の判別集合が広すぎ、observation の下流伝播も未達です。

## 所見

### 1. ancestry 判別が非 commit object と Git 操作障害まで格下げする

- 対象: brief D72 (8) / P2 / プラン単位 A §3
- 自己判定: **real**。`cat-file` と `merge-base` の全失敗を同じ `FreezeError` へ畳んでいる。[s1_known_axes_freeze.py:89](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:89>)、[同:747](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:747>)。D72 の「不存在 SHA／実在非 ancestor だけ」という記述はコードと一致しない。[decisions.md:2825](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2825>)
- 何が壊れるか:
  - `HEAD:CLAUDE.md` の実在 blob SHA `24c816eec11badb02d224b0b17c145dbda50f82a` を `frozen_at_head` に設定した document は、原 checker で ancestry 文言を送出する。
  - しかし P1 の `ccbench_pin` 照合と `build_document()` 再構成はともに一致する。したがって ancestry observation として格下げされる。
  - root repository の object DB 破損、権限障害、`merge-base` の rc>1 などでも同じ文言になる。submodule Git と通常ファイルが読めれば P1 の後段検査は通り、操作障害を「参考情報」にしてしまう。
  - observation も missing / non-ancestor / wrong-object-type / git-error をすべて `status="unverified"` に潰すため、「なぜ壊れたか」を構造化できていない。
- 推奨修正:
  - `str(exc)` は `f"{prefix}: {known_doc['frozen_at_head']}"` との完全一致にする。
  - その後、別の構造化 Git 検査で分類する。raw object type が `commit` でない場合と Git rc>1 は拒否。不存在 commit と `merge-base --is-ancestor` の rc=1 だけを格下げする。
  - observation に `reason: missing-commit | non-ancestor` を持たせる。`git-error` と `wrong-object-type` は refusal にする。

### 2. observation が report / oracle へ耐久伝播せず、P4 と P8 の scope が不足している

- 対象: P4 / P8 / プラン単位 A §1・§4
- 自己判定: **real**。正本は report / calibration / oracle への構造化伝播を条件としている。[worklog.md:911](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:911>)。プランは `run_block()` の戻り値にしか残さない。
- 何が壊れるか:
  - ancestry だけ格下げして実走が完了すると、CLI stdout には observation が出る。
  - 一方、耐久 WAL の `campaign-start` には observation がない。[s8b_oracle_driver.py:1027](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1027>)
  - report は WAL から observation を生成するが、出力 top-level に gate observation を持たない。[s8b_oracle_report.py:1227](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1227>)
  - judge の verdict にも伝播しない。[s8b_oracle_judge.py:259](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_judge.py:259>)
  - stdout を保存しなければ、後日の certified report / oracle verdict は ancestry 未検証を一切示さない。「沈黙して通さない」を満たさない。
  - calibration provenance には実際に `freeze_frozen_at_head` が保存される経路がある。[s1_verify_extime_calibration.py:193](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:193>)、[同:403](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:403>)。この境界を scope 外とする理由も brief にない。
- 推奨修正:
  - observation を `campaign-start` WAL に耐久化する。
  - `OfficialObservations` と `OfficialVerdict` に構造化コピーし、report/judge のテストまで所有範囲へ追加する。
  - calibration は方式 B の直接 caller 非対応として残すのか、既存 provenance をどう表示するのかを明示裁定する。
  - よって単位 A は driver と driver test の2ファイルだけでは閉じない。

### 3. P1' は同じ path を二度読み、既存の単一 object 契約を破る

- 対象: 代案 P1' 手順 1–3
- 自己判定: **real**。`verify()` は内部で JSON を読み、例外時には document を返さないため、P1' は再読込を必要とする。[s1_known_axes_freeze.py:785](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:785>)。driver 自身は別入力について単一 object 使用を明記している。[s8b_oracle_driver.py:177](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:177>)
- 何が壊れるか:
  - 1回目に bytes A が ancestry で落ちた直後、path を bytes B に差し替える。
  - 2回目は B の `frozen_at_head` を HEAD に置換して検証する。
  - holdout / manifest が先に束縛した bytes と、再検証した bytes が別物になり得る。さらに observation の `detail` は A、`path` / `frozen_at_head` は B という矛盾も作れる。
- 推奨修正:
  - P1' を使うとしても JSON は一度だけ読み、同じ in-memory object を最初と二回目に使う。
  - ただし次の所見4が残るため、P1' 自体を推奨しない。

### 4. P1' の head 差し替えは将来の head-dependent 検査を静かに別対象へ向ける

- 対象: P1' 固有リスク / 「差分が1キーだけ」の緩和策
- 自己判定: **speculative**。現 checker の後段は head を再構成値へ反映するだけだが、同リポジトリには実際に `frozen_at_head` の blob を読む checker がある。[s1_known_axes_freeze.py:759](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759>)、[s8b_ratified_freeze.py:934](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:934>)
- 何が壊れるか:
  - 将来「source bytes は recorded `frozen_at_head` の blob と一致」を ancestry 後へ追加する。
  - P1' は recorded head ではなく現在 HEAD の blob を検査するため、壊れた historical provenance が通る。
  - 「差し替え前後の差分が1キーだけ」という assert は、JSON dict を deepcopy して1キーだけ代入した構築手順から恒真であり、検査対象の意味が変わったことを検出しない。
  - checker SHA pin は赤くなり得るが、literal を機械更新した場合の runtime 防壁にはならない。
- 推奨修正:
  - 記録値を変更しない P1 を選ぶ。
  - checker SHA をテストだけでなく production の対応表として固定し、未知 checker SHA では格下げを拒否する。

### 5. M-A3 / M-A4 の「単一理由」主張は、記述どおりの入力では成立しない

- 対象: プラン §10 / 変異 matrix M-A3・M-A4
- 自己判定: **speculative**。テスト実装は未提示だが、known JSON の1 byte 変更は先に outer holdout の source hash も壊す。[s8b_oracle_driver.py:216](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:216>)、[s8b_holdout_freeze.py:709](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709>)
- 何が壊れるか:
  - known JSON の `ccbench_pin` または `what` だけを変更すると、後段 helper だけでなく `known_axes_freeze sha256 不一致` も発火する。
  - baseline と mutant の双方が outer gate で拒否され、受理集合差による単一理由 kill にならない。
  - M-A1 も現行公式 freeze を使うだけなら 3 件の別 refusal が残り、`allowed=False` は変わらない。
- 推奨修正:
  - outer holdout record と manifest record を変更 bytes に整合させるか、独立 outer verifier だけを明示的に固定した sole-refusal fixture を使う。
  - baseline が受理、対象変異だけで拒否、またはその逆になることを事前に示す。

### 6. P1 の「公開 API だけで再現可能」は誤りで、guard は runtime 防壁ではない

- 対象: brief P1 / P3 / プラン単位 A §2・§6
- 自己判定: **speculative**。現在の複製は原本と一致するが、ccbench HEAD 取得は公開 API ではなく private `_run_git` だけである。[s1_known_axes_freeze.py:89](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:89>)、[同:755](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755>)
- 何が壊れるか:
  - 将来 checker と artifact を正規更新し、新しい ancestry 後検査を追加する。
  - checker SHA test の literal だけ更新して consumer helper を見直さなければ、新 checker が ancestor document で拒否する内容を、non-ancestor document では helper が見落とす。
- 推奨修正:
  - 少なくとも Git 実行は `K._run_git(...)` を直接使い、例外意味論の複製を減らす。
  - production 側に「この checker SHA に対応する後段 adapter」という明示的 allowlist を置く。
  - checker SHA test は有効だが、診断 guard に留まるというプラン自身の評価は正しい。

## 受理集合の正味差分

P1 における正確な差分は次です。

`新規受理 = 他の全 gate が通る ∧ ancestry より前の全検査が通る ∧ line 754 の文言が出る ∧ P1 後段2検査が通る`

| `frozen_at_head` / 状態 | 変更前 | P1 後 | 評価 |
|---|---:|---:|---|
| 不存在の40桁 commit SHA | 拒否 | 受理 | 意図内 |
| 実在する非 ancestor commit | 拒否 | 受理 | 意図内 |
| 実在 blob/tree、非 commit tag | 拒否 | 受理 | 意図外 |
| `cat-file` / `merge-base` の操作障害 | 拒否 | 後段が通れば受理 | 意図外・fail-open |
| 任意の実在 ancestor commit | 受理 | 受理 | 差分なし |
| schema / generator / source / pairing 破損 | 拒否 | 拒否 | 維持 |
| ccbench drift / 再構成不一致 | 拒否 | 拒否 | P1 が維持 |

現行公式 freeze は holdout・floor・budget の3拒否が残るため、gate 全体では変更前後とも拒否です。したがって現物に対する変化は 4→3 だけで、`allowed=False` は変わりません。

P1' はさらに「1回目に読んだ bytes と2回目に読んだ bytes が異なる時系列入力」を新規受理集合へ加えます。

## `FreezeError` message 全列挙と文字列注入判定

[s1_known_axes_freeze.py](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:77>) 内の明示的 `FreezeError` 送出は81箇所です。

- 95–198:
  `git {args} に失敗: {detail}`、
  `source が存在しない: {path_rel}`、
  `repo 外 module は source にできない: {path}`、
  `JSON を読めない: {path}: {e}`、
  `JSON top-level が object ではない: {path}`、
  `WAL を読めない: {path}: {e}`、
  `WAL JSON 不正: {path}:{lineno}: {e}`、
  `WAL record が object ではない: {path}:{lineno}`、
  `campaign.lock がない: {path}`、
  `campaign.lock に search_config がない: {path}`、
  `variant 欠落: {path}`、
  `genome が文字列でない: {path} variant={variant}`、
  `同一 variant の genome が不一致: {variant}`、
  `同一 WAL に COMMIT が重複: ...`、
  `COMMIT fitness_tps が数値でない: ...`、
  `COMMIT 済み variant が 1 件もない`。
- 206–312:
  `{label}: argmax が一意でない ...`、
  `canonical genome を解釈できない: ...`、
  `SILO_SPACE から variant_id を一意に逆引きできない: ...`、
  `P2-2 no-wait flags が既知ラベルに対応しない: ...`、
  `P2-2 WAL がない: workload=...`、
  `P2-2 {workload}: argmax が期待値と不一致: ...`、
  `P2-2 {workload}: genome と variant_id が一致しない`、
  `BACKOFF_FIXED WAL がない: workload=...`、
  `backoff WAL に genome がない: ...`、
  `BACKOFF_FIXED {workload}: no_backoff 点が重複`、
  `... stock_adaptive 点が重複`、
  `... 静的 grid が SWEEP_US と一致しない`、
  `... 参考 2 点が揃っていない`、
  `... argmax=... != expected=...`、
  `... WAL flags と driver 定数が不一致`。
- 332–535:
  `campaign artifact がない: ...`、
  `provenance entries が object でない: ...`、
  `provenance variant_id が重複: ...`、
  `COMMIT variant が provenance にない: ...`、
  `sort remeasure が一意でない: ...`、
  `sort remeasure に full-order COMMIT がない: ...`、
  `write-heavy 本走 provenance に entries.sk_ad.implementation がない`、
  `entries.sk_ad.implementation が文字列でない`、
  `sort main ...: full-order COMMIT がない`、
  `sort ...: argmax=...`、
  `sort provenance implementation がない: ...`、
  `sort comparator が文字列でない: ...`、
  `balanced remeasure campaign が期待値と不一致: ...`、
  `D50 best gate 表を一意に抽出できない: ...`、
  `D50 best gate 表が期待値と不一致: ...`、
  `s8a_trigger_sweep._genome(1) と axis_trigger_gating._BASE が不一致`、
  `{label} provenance に entries.{name}.implementation がない`、
  `{label} entries.{name}.implementation が文字列でない`、
  `trigger gate predicate が main/remeasure で不一致: ...`、
  `ident_all predicate が main/remeasure で不一致: ...`、
  `{label} の CMake 行が一意でない: ...`。
- 579–605:
  `s1b_pairing 検査に必要な entries/list がない`、
  `s1b_pairing entry が不正`、
  `s1b_pairing workload 重複: ...`、
  `s1b_pairing workload 集合が不一致: ...`、
  `entries.{workload} がない`、
  `entries.{workload} の gate/ident_all が不正`、
  `s1b_pairing flags 不一致: ...`、
  `s1b_pairing predicate 差分がない: ...`、
  `s1b_pairing 台帳が entry と不一致: ...`。
- 687–788:
  `sources が list ではない`、
  `source entry が object ではない`、
  `freeze top-level keys が schema と不一致: ...`、
  `selection_rules keys が schema と不一致`、
  `entries workload keys が schema と不一致`、
  `entries.{workload} keys が schema と不一致`、
  `generator schema が不一致`、
  `generator.path 不一致: ...`、
  `generator sha256 不一致: recorded=... actual=...`、
  `source path/sha256 が文字列でない`、
  `source が存在しない: ...`、
  `source sha256 不一致: ...`、
  `sources が 1 件もない`、
  `frozen_at_head が 40 桁 git SHA でない`、
  `frozen_at_head が現行 HEAD の commit ancestor でない: ...`、
  `ccbench_pin 不一致: ...`、
  `freeze JSON の内容が現行 generator による機械再構成と不一致`、
  `freeze が既に存在する: ...` の2形、
  `freeze が存在しない: ...`。

現在の production 到達経路では、判別 prefix から始まるものは line 754 の1件だけです。動的先頭の `{label}` も全 call site が固定ラベルです。`frozen_at_head` 自体は直前に小文字 hex 40桁へ制限されるため、値から prefix を注入できません。

したがって **現行 `startswith` に対する外部文字列注入は構成できません**。ただし `in` へ変えると、prefix を含む root path で `source が存在しない: ... -> <root>` を起こし、P1 の K.ROOT 再構成だけを通す誤格下げを構成できます。M-A2 の方向は妥当です。

## 恒真 guard の判定

- P3 の checker SHA literal: **恒真ではない**。checker 1 byte 変更で赤くなる。ただし test-only。
- T-066 の material hash / raw JSON hash literal: **恒真ではない**。提示された `9bda…`、`df71…` は現行提案出力と一致し、producer assembly の変更で赤くなる。
- T-067 の `len + set` exact helper: **恒真ではない**。余分・欠落・重複を検出する。
- P1' の「差分が `frozen_at_head` 1キーだけ」assert: **意味上は恒真**。自分で deepcopy して1キーだけ代入したことしか確認せず、差し替え後の検査意味を保証しない。

## CC 選択結果への波及

現在のコードから、`frozen_at_head` の格下げだけで誤った CC 選択を生む反例は **構成できません**。

driver は known document を選択入力として使わず、検証結果を捨てているだけです。[s8b_oracle_driver.py:249](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:249>)。calibrator でも head は provenance へ転記されるだけで、構成選択自体は `entries.*.system_gate` から行われます。

構成できる事故は「偽または未検証 SHA を検証済み provenance のように残すこと」と、その observation が report/verdict から消えることです。これは証拠境界の破損ですが、現行データフロー上の誤選択とは区別すべきです。

## provisional 裁定

| 裁定 | 判定 |
|---|---|
| P1 | **条件付き採用**。原 document の後段検査を行う方向は正しいが、所見1・2を直すまで不可 |
| P2 | **否認**。現行文字列注入には安全だが、Git 操作障害と非 commit objectを区別できない |
| P3 | **採用**。有効な診断 guard。ただし production allowlist の代替ではない |
| P4 | **要件は採用、プラン実装は否認**。GateDecision/stdoutだけでは伝播にならない |
| P5 | **採用**。公式3件の literal と exact 集合検査は妥当 |
| P6 | **採用**。置換後は恒真ではない |
| P7 | **採用**。holdout design_source 破損は別問題で、現 wave 後も公式 gate は拒否のまま |
| P8 | **否認**。P4を満たすには report/judge/calibration 境界まで単位Aを拡張する必要がある |
| P1' | **否認**。P1より危険。二重 read と head-dependent 検査の対象差し替えを生む |

**最終判定: NO-GO。ブロッカーは所見 1、2。** P1' を採る場合は所見3もブロッカーです。

---

### 段3 敵対相談 レンズ2 (整合・実効性)

結論は **NO-GO** です。方式 B 自体を覆す必要はありませんが、現 brief／プランのまま実装すると、単位分割・変異事前登録・期待赤のいずれも成立しません。

基準 commit `3ca2130878fa…`、branch、ccbench `d706650c…` は一致しています。pytest は実行していません。

## 所見

1. 対象: brief (P1)「公開 API で後段 2 検査を再現」／プラン §2 — **real**

   根拠: checker の ccbench 現 pin 取得は公開 API ではなく [`_run_git()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:89) であり、実照合は [line 755](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755) です。`build_document()` は公開ですが、現 pin getter はありません。

   何が起きるか: P1 は git subprocess と例外翻訳を consumer に複製します。なお親の「root の意味がずれる」という反論は P1 の提示コードには当たりません。原 checker 自身が generator/git には `K.ROOT`、source だけに `source_resolver` を使っており、[line 724](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:724)、[line 729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:729)、[line 755](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755) の非対称性を、P1 もそのまま再現しています。

   推奨: brief の「公開 API だけ」を撤回する。P1 を採るなら、`K.ROOT` と consumer `root` の分担を明示的にテストする。

2. 対象: 代案 (P1') の step 1〜3 — **real**

   根拠: `K.verify()` は内部で path を読みます（[`verify():785-791`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:785)）。P1' は例外後に同じ path をもう一度読むため、例外を発生させた bytes と、二回目に検証する bytes が別になり得ます。repo は freeze に対して「単一読込・同一 object」を明示的な防壁にしています（[`s8b_freeze_io.py:41`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_freeze_io.py:41)）。

   何が起きるか: 一回目の ancestry 失敗後に known JSON が差し替わると、二回目の別 document が権威になります。既存にも holdout 検証と known 検証の間の窓はありますが、P1' はさらに一窓増やします。

   推奨: P1' をそのまま採らず、次の **P1''** にする。

   1. consumer が known JSON を一度だけ読む。
   2. 同じ object を `K.verify_document()` に渡す。
   3. exact な ancestry 例外だけ捕捉する。
   4. deep-copy の `frozen_at_head` 一キーだけを `K.ROOT` の現 HEAD に変更する。
   5. 同じ source resolver でコピーを `K.verify_document()` に再投入する。
   6. original と copy の差分が一キーだけであることを fail-closed に確認する。

3. 対象: (P1') の将来の head 依存検査リスク — **speculative**

   根拠: 現 checker で ancestry 後にあるのは ccbench pin と機械再構成だけです（[line 755](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755)、[line 759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759)）。現時点で source blob を `frozen_at_head` に結び付ける検査はありません。

   何が起きるか: 将来そのような検査が追加されると、shadow HEAD に対して検査されます。単一キー差分 assert は入力差分しか保証せず、検査意味論の変化は防げません。

   推奨: checker SHA pin は必須です。checker 自己 hash 検査が ancestry より先にあるため（[line 724](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:724)）、checker 変更時は通常まず fail-closed になります。単一キー差分 + checker SHA guard の組合せなら、現 wave の緩和策としては十分です。差分 assert 単独では不十分です。

4. 対象: brief (P2)／プランの `startswith` — **real**

   根拠: 現 checker の ancestry message は完全に決定的です（[line 747](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:747)、[line 754](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:754)）。

   何が起きるか: `startswith` は、同じ語幹で始まる将来の別エラーも格下げします。`in` より狭いだけで、「ancestry ただ一件」と同値ではありません。

   推奨: 次の完全一致にする。

   ```python
   expected = f"{PREFIX}: {known_doc['frozen_at_head']}"
   if type(exc) is not K.FreezeError or str(exc) != expected:
       raise
   ```

5. 対象: brief (P4)／プラン §4・§10 — **real**

   根拠: observation を落とし得る再構築地点は、manifest object 欠落 [line 956](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:956)、preflight 二経路 [line 990](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:990)、claim 拒否 [line 1019](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1019)、budget return [line 1077](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1077)、最終 return [line 1300](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1300) です。

   何が起きるか: プランの新規テストは completed と budget しか対象にしていません。post-gate の四系統から `observations=` を一つ落としても赤くなりません。

   推奨: `GateDecision` を手で作り直さず、`with_refusal()` のような一つの helper に集約する。少なくとも manifest-missing、preflight expected/unexpected、claim refusal に sentinel observation テストを追加する。

6. 対象: brief (P8)／プランの単位 A・B — **real**

   根拠: プランは `test_real_freeze_gate_lists_floor_and_budget_null` を改名しますが、この node 名は [`conftest.py:80`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:80) と独立 golden [`test_real_repo_serialization.py:54`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:54) に固定されています。未収集 golden node は [line 179](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:179) で赤になります。

   何が起きるか:

   - プランどおり改名すると、統合後に collection meta-test が赤になります。
   - real known artifact を読む新規 focused tests は共有 ccbench reader なので、real-repo group へ追加しなければ writer と競合します。
   - `test_s8b_binding_driftguards.py` は test driver の `_synthetic_freeze()` を import しています（[line 43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_binding_driftguards.py:43)、[line 230](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_binding_driftguards.py:230)）。

   推奨: 既存 test 名を維持するか、単位 A の所有に `conftest.py` と `test_real_repo_serialization.py` を追加する。新規 real-reader node も両正本へ追加する。現状の「2 ファイルだけ」は成立しません。

7. 対象: プラン「期待赤の集合」 — **real**

   根拠: production が `verify()` から `verify_document()` へ変わる一方、既存 mock は `verify` にあります（[line 1880](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1880)、[line 1920](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1920)、[line 2281](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2281)）。

   何が起きるか:

   - 「production だけ変更した場合の期待赤は空集合」は誤りです。プラン自身が後段で列挙した七件は実際に赤になります。
   - test-first なら exact 二件だけでなく、ancestry、wrapped、ccbench、`what`、completed observation、budget observation の新規 tests も赤または fixture 構築エラーになります。
   - test 改名による serialization meta-test の赤も未列挙です。
   - 一方、現行公式 gate の 4→3 だけなら既存 [line 503-507](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:503) は floor/budget しか見ないため緑です。これは 2351 passed の親 baseline と整合します。

   推奨: 「production-only」「test-first」「統合後」の三列で node 名を固定し直す。wrong-layer で緑になる contract mismatch も別記する。

8. 対象: 変異事前登録表 — **real**

   | 候補 | 判定 | 理由 |
   |---|---|---|
   | M-A1 | 条件付き | 公式 real gate は holdout、floor、budget で既に拒否されています（[`driver.py:216`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:216)、[`driver.py:263`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:263)）。単に 3→4 refusal になるだけでは kill 不成立。その他がすべて通る fixture で baseline `allowed=True`、mutant `False` を示すなら登録可。 |
   | M-A2 | **登録不可** | `wrapped:` は現 checker が生成できない mock 専用 message です。現 production exception 集合では `startswith→in` は等価変異です（[`K:754`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:754)）。 |
   | M-A3 | 登録可、P1 のみ | pin だけ変えた場合、先行 ancestry で consumer 分岐へ入り、helper の pin 比較だけが拒否します。`build_document` は recorded pin を override されるため最終比較では落ちません（[`K:755`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755)、[`K:759`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759)）。 |
   | M-A4 | 登録可、P1 のみ | `_validate_schema` は `what` の値を見ません（[`K:700`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:700)）。最終 document 比較だけが歯です。 |
   | M-A5 | **gate kill として登録不可** | budget と最終 return の二位置を一 ID にまとめています。また observation 欠落は受理集合を変えません。P4 の構造化伝播 contract test として二分割すべきです。 |
   | M-A6 | **登録不可** | 既に拒否中の公式入力への余分な refusal は診断差分だけです。無条件追加なら正常 v2 の `assert valid.allowed`（[`test:1927`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1927)）でも赤になり、exact test 固有の kill 帰属にもなりません。 |
   | X-1 | 登録不可で正しい | checker 自己 hash が ancestry より先に拒否します。 |
   | X-2 | 登録不可で正しい | current pin を使う全文比較と pin 比較が過剰決定になります。 |
   | X-3 | 登録不可で正しい | pin mismatch が先行します。 |
   | X-4 | 登録不可で正しい | 同一 baseline bytes 上では等価です。 |
   | X-5 | 登録不可だが理由訂正 | ancestry の前に latent な holdout generator mismatch が落とします（[`holdout verifier:709`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709)）。 |

   P1'' を採るなら M-A3/M-A4 の consumer 複製位置自体が消えるため、変異表を全面的に再起草する必要があります。主候補は「二回目の `verify_document()` 呼出しを削除」です。

9. 対象: brief (P5)／[T-067] — **real**

   根拠: 公式 gate の literal 3 集合は runtime 計算ではなく外部固定値で、`len + set` は重複も検出します。これは実効です。しかし oracle 系には別の部分一致が残ります。例として [`test_s8b_binding_driftguards.py:298`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_binding_driftguards.py:298)、[`test_s8b_oracle_driver.py:2264`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2264)、[line 2293](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2293) です。

   何が起きるか: 「列挙した七 assert のみ」が T-067 なら有効ですが、「oracle 系テストの拒否理由を exact 化」が受入条件なら未完です。別 refusal の増加を依然隠せます。

   推奨: T-067 の対象 node を明示列挙する。repo-wide の oracle refusal 検査が対象なら、単位 A の所有ファイルもさらに増えます。

10. 対象: brief (P7)／X-5 — **real**

   根拠: holdout artifact は generator を `1910fff…` と記録しています（[`holdout_freeze.json:13`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s8b-freeze/holdout_freeze.json:13)）が、現 checker bytes は `41c0b6a7…` です。verifier は design、known、generator の順です（[`s8b_holdout_freeze.py:709`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709)）。

   何が起きるか: 現在は design mismatch が先に abort するため一件に見えるだけです。design_source を直すと、次に generator mismatch が出ます。「holdout の別破損は design_source 一点」は誤りです。

   推奨: P7 の scope 外パッケージを「design + generator の二つの source drift」に訂正する。scope 分離自体は可能ですが、本 wave で oracle が復旧するとは表現しない。

11. 対象: brief (P6)／単位 B の置換案 — **real**

   根拠: 現在の `K.build_document` echo 自体は削除されますが、新案は `_p2_entry`、`_fixed_gates_from_recon`、`_stock_common`、`_trigger_entries`、`_backoff_entry`、`_sort_entry` の全 semantic extractor を fixture echo にします。実 `build_document()` が行う主要処理はこれらの呼出しです（[`K:608`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:608)、[line 614](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:614)、[line 621](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:621)）。

   何が起きるか: `axis_trigger_gating` 等の依存実装や材料が変わって production 出力が変化しても、unit B の raw hash は fixture echo のままで緑になり得ます。「producer 出力が変われば raw hash で必ず赤」は過大です。計画中の material/raw/checker literal 自体は現 bytes と一致しており、改善ではあります。

   推奨: semantic extractor ではなく WAL reader・file reader など I/O 境界を fake 化し、real extractor を動かす。難しければ、小 fixture は measurement test 用と明記し、別途 unpatched `K.build_document(overrides...) == immutable artifact` の positive control を置く。

12. 対象: 単位 B の `FIXTURE_HEAD`／`FIXTURE_CCBENCH_PIN` — **speculative**

   根拠: K verifier は commit 実在・ancestry を実 git 履歴へ問い合わせます（[`K:750`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:750)）。ccbench HEAD も実 submodule から取得します（[line 755](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755)）。

   何が起きるか: `3ca2130` を落とす rebase、shallow clone、submodule pin 更新で false red になります。mtime 依存や静かな緑化経路はありません。過去に rebase で dangling SHA を量産した repo なので、単なる理論上の懸念ではありません。

   推奨: このテストの目的が K の git provenance でないなら、`_run_git` を固定応答 + 呼出し引数 exact 検査にするか、「基準 commit を履歴に保持する」環境契約を明文化する。

13. 対象: brief の「`verify()` 直接 caller」列挙 — **real**

   根拠: `s1_report.py` が直接呼ぶのは measurement freeze の `verify()` です（[`s1_report.py:760`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:760)）。`s1_direct_comparison.py` も measurement の `verify_document()` です（[`s1_direct_comparison.py:115`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:115)）。known checker の直接 consumer としては calibration が存在します（[`s1_verify_extime_calibration.py:193`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:193)）。

   何が起きるか: 結論「oracle 以外では破損が残る」は正しいですが、所有・影響範囲の説明が誤っています。measurement は known ancestry に加えて自身の ancestry も持ちます（[`s1_measurement_freeze.py:417`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:417)）。

   推奨: brief の caller map を実コードどおり訂正する。scope を広げる必要はありませんが、残存破損の説明は正確にする。

## P1 と P1' の安全性判定

- **提示されたままなら P1 の方が僅かに安全**です。検査複製はありますが、P1' のような二回目の未束縛 disk read を増やしません。
- **最終推奨は P1''** です。single parse + original/shadow の二回 `verify_document()` にすれば、複製ゼロと同一 object を両立できます。
- P1' 固有の将来リスクは現時点では speculative です。単一キー差分だけでは不足しますが、checker SHA pin と自己 hash の先行検査を併用すれば、この wave では受容可能です。
- したがって「方式 B 自体を却下」は不要です。

## provisional 裁定

| 裁定 | 判定 |
|---|---|
| P1 | **否認**。公開 API 前提が誤り。P1'' へ変更を推奨。 |
| P1' | **現形は否認**。single-read shadow 再検証へ修正すれば採用。 |
| P2 | **否認**。`startswith` でなく型 + 完全 message 一致。 |
| P3 | **条件付き採用**。diagnostic guard であり mutation kill には数えない。 |
| P4 | **趣旨採用、プラン不足**。post-gate 四系統の伝播テストが必要。 |
| P5 | **条件付き採用**。公式 3 集合は実効。T-067 の対象 node を明確化すること。 |
| P6 | **条件付き否認**。外部 literal は正しいが semantic extractor echo が残る。 |
| P7 | **条件付き採用**。scope 外は design と generator の二破損として返す。 |
| P8 | **否認**。serialization 正本と外部 fixture consumer があり、2ファイル所有ではない。 |

## 最終判定

**NO-GO**

ブロッカー所見: **1、2、4、5、6、7、8、9、11、13**。  
特に、P1'' への変更、P2 の exact 化、real-repo serialization 所有の修正、変異表と期待赤集合の再起草が済むまで実装 wave を開始すべきではありません。

---

### 段5 実装子 完了報告 (初回)

実装完了しました。編集は [test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:56) のみです。docs・production・凍結成果物は変更せず、commit も作成していません。指定 node 名も維持しています。

変更内容:

- `_assert_exact_refusals` を追加し、件数と集合の完全一致を検査
- 対象9 assertionを外部固定 literal による exact 検査へ変更
- tampered テストへ、改変と実際の発火理由が無関係である旨の docstring を追加

実測した9箇所の対応は次のとおりです。

- 旧506、507 → R1
- 旧787–788 → R2
- 旧816、817 → R3
- 旧1164–1165 → R4
- 旧2249–2250 → R5
- 旧2264 → R6
- 旧2293–2294 → R7

実測集合:

- R1（4件）

  - `holdout-freeze-verify: FreezeError: design_source sha256 不一致: recorded=1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d actual=5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae`
  - `known-axes-freeze-verify: FreezeError: frozen_at_head が現行 HEAD の commit ancestor でない: 2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1`
  - `floor-null: freeze.floor が null`
  - `budget-null: freeze.budget が null`

- R2

  - `freeze-ratify: [no-active] [no-active] live active pointer が無い (v2 未発効)`

- R3

  - `freeze-ratify: [no-active] [no-active] live active pointer が無い (v2 未発効)`
  - `manifest-verify: ManifestError: manifest top-level schema が不一致`

- R4（4件）

  - `holdout-freeze-verify: FreezeError: generator sha256 不一致: recorded=1910fff38edf0e58f5bff221c29660a8f85dd0ed1b5c980234ec1af098584e5f actual=41c0b6a7b348acb0960b354f80ab79ba3376d4214a73f11d5ee739b04337d4b0`
  - `known-axes-freeze-verify: FreezeError: frozen_at_head が現行 HEAD の commit ancestor でない: 2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1`
  - `floor-null: freeze.floor が null`
  - `budget-null: freeze.budget が null`

- R5

  - `freeze-not-active-generation: 与えられた freeze bytes sha256 が承認束縛済み active 世代と不一致`

- R6

  - `v2-execution: launch-validate: [closure-hit-mismatch] [closure-hit-mismatch] rr80: 現 hit が closure 導出と不一致 (未申告=['sneaky.txt'] 消失=[])`

- R7

  - `v2-execution: launch-validate: FreezeError: git enumerate 失敗 (模擬)`

R4のみ依頼文の `design_source sha256 不一致` と食い違い、現行HEADでの自分の実測は既存の `generator sha256 不一致` でした。実測値を採用し、docstringにもその事実を固定しました。

検証結果:

- 対象7テスト指定: `7 passed`
- `python3 -m pytest -q orchestrator/tests/test_s8b_oracle_driver.py`: `55 passed, 1 skipped`
- `python3 tools/run_tests.py`: sandboxがsubmoduleの `index.lock` 作成を拒否し、巻き戻し失敗1件＋残留patchをexact検査が検出した連鎖2件
- 同じ全走を、`git checkout -- .` のみbyte復元へ置換する一時 `/tmp` shim付きで実行: `2351 passed, 19 skipped, 0 failed`
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし

テスト実行によるsubmodule汚染は復元済みで、`external/ccbench` はcleanです。既存の未追跡handoff/outputには触れていません。

---

### 段6 敵対レビュー レンズA (正しさ・恒真性)

結論は **NO-GO**。静的検査のみ。

1. 対象: 親判断 1（[T-068] 不実装） / **real**

   根拠: ユーザー裁定時点ですでに「方式 B は refusal を 4 件から 3 件へ変える」と明記されています。[worklog:953](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:953)、[worklog:978](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:978)、[worklog:1012](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:1012)。したがって、親の「3 件残って `allowed=False` なので前提が覆った」という理由付け [handoff:76](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:76) は、新事実ではありません。

   一方、ancestry 例外が git 障害まで同じ文言に包み直され、後続の pin・再構成検査へ復帰できないことは実在します。[s1_known_axes_freeze.py:750](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:750)、[s1_known_axes_freeze.py:755](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755)、[s1_known_axes_freeze.py:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759)。

   何が壊れるか: 「直ちに実装しない」は正しいものの、親が既知の 4→3 を根拠にユーザー裁定を撤回扱いするのは不当です。

   推奨修正: [T-068] を「親裁定で不採用」ではなく、後段マスク・git 障害誤分類・observation 伝播不足を新材料とする「ユーザー再裁定待ち」に戻すこと。

2. 対象: 親判断 3（[T-066] を設計択一として返却） / **real**

   根拠: ユーザー裁定はすでに「外部固定の期待値へ置換」と実装方向まで指定しています。[worklog:1010](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:1010)。現 fixture は現行 HEAD・generator hash を動的注入し、候補そのものを `build_document` の戻り値にしています。[test_s1_measurement_freeze.py:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:91)、[test_s1_measurement_freeze.py:113](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:113)。そのため production の最終再構成比較 [s1_known_axes_freeze.py:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759) は `known_doc == deepcopy(known_doc)` です。

   何が壊れるか: generator や再構成結果の退行を fixture が吸収し、既知の恒真ゲートが残ります。

   推奨修正: test-owned の独立 golden を使い、候補と期待値を別起源にすること。`reference_values_note` など先行検査を通る欄を片側だけ変える positive control も置くべきです。これは通常のテスト実装判断であり、再度のユーザー択一を要しません。

3. 対象: `test_tampered_freeze_fails_source_verification` / **real**

   根拠: tamper は [test_s8b_oracle_driver.py:1179](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1179) の `confirmed_by` 変更ですが、verifier はその検査より先に generator hash を検査します。[s8b_holdout_freeze.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709)、[s8b_holdout_freeze.py:739](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:739)、[s8b_holdout_freeze.py:776](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:776)。exact 期待にも tamper 固有の refusal はなく、既存 generator drift 等だけです。[test_s8b_oracle_driver.py:1186](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1186)。

   何が壊れるか: tamper 行を削除しても結果が同じです。`confirmed_by` 整合検査を production から消す変異も、このテストは検出しません。

   追記 docstring は「先行する holdout refusal」という狭義では事実ですが、gate 全体では四理由を集約しており、壊れた positive control を説明しただけです。

   推奨修正: 現行 drift の characterization test と、source・ancestry を通した単一理由の tamper test に分割すること。

4. 対象: 親判断 4（変異 M1/M2） / **real**

   根拠: helper は長さと集合の二条件です。[test_s8b_oracle_driver.py:62](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:62)。M1 の「一意な余分 refusal 追加」は長さと集合を同時に壊すため、単一理由ではなく過剰決定です。M2 の重複追加は集合を変えず、長さだけを壊すので、refusal-list 契約の変異としては単一理由です。

   ただし両変異とも既存 refusal がある入力へ追加するだけなので、`allowed=not refusals` [s8b_oracle_driver.py:289](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:289) は前後とも `False`。親自身も受理集合不変を認めています。[handoff:122](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:122)。これは「受理集合を変える単一理由」を要求する B-057 [dev-wave.md:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/.claude/commands/dev-wave.md:20) の kill には数えられません。

   推奨修正: M1 は件数を維持した refusal の置換変異へ変更し、`set` 比較だけを発火させること。M2 は `len` の診断用 positive control として残せますが、両者とも「受理集合 mutation」ではなく「構造化 refusal 契約 mutation」と明記すべきです。

補足すると、:831 の旧 `len == 2` は helper の長さ検査で保持されており、そこは退化していません。exact 化そのものが production の正しさゲートを弱める経路もありません。4 件期待は現行実装の characterization としては正しいものの、[T-068] の再裁定前に最終仕様として閉じてはいけません。

**NO-GO**

---

### 段6 敵対レビュー レンズB (整合・裁定妥当性)

**NO-GO。** 静的検査では [T-067] の未完、環境依存 golden、親裁定の根拠矛盾、変異 kill の誤分類が確認できる。

監査結果:

- `test_s8b_oracle_driver.py` の `assert` は AST と行検索の双方で **250 個**。
- うち `refusal(s)` を直接参照する assert は 16 個、**部分一致は 11 個残存**。
- node 名は現状維持されている。`REAL_REPO_SERIAL_NODES` と独立 golden は各 28 件で差分なし、oracle の 7 node も各 1 定義だった。[conftest.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:47)、[test_real_repo_serialization.py:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:30)

## 所見

1. 対象: [T-067] / `test_s8b_oracle_driver.py`

   **自己判定: real。**

   部分一致が残っている。`in result["refusals"][0]` が [560](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:560)、571、582、597、608、625、645 の 7 個、`startswith` parser が [1897](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1897)、extime helper が [1924](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1924)–1926 の 3 個、計 11 個である。`_v2_refusal_reason()` は singleton 数だけ固定し、`]` より後ろへ任意文字列を足しても [2354](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2354) と 2378 は緑のまま。

   さらに [542](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:542) と [2403](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2403) は `status == refused` だけで理由集合を全く固定していない。

   壊れるもの: refusal の余分な追加・本文改変・誤った例外翻訳が複数経路で静かに通る。ユーザー指定の完了条件により **[T-067] は未完**。

   推奨修正: 11 個をすべて完全一致へ変更し、status-only の refusal テストも理由を一意化して exact 化する。`_v2_refusal_reason` は全文を比較するか、production を構造化 code/detail にして code と detail を別々に完全検査する。

2. 対象: 固定 literal / [test_s8b_oracle_driver.py:516](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:516)、[同:1186](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1186)

   **自己判定: real。**

   `actual=5fbdd7…` と `actual=41c0b6…` は実 working tree の source bytes そのものを固定している。holdout verifier は design、known-axes、generator の順で fail-fast する。[s8b_holdout_freeze.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709)–712。したがって正当な文書編集、checker 更新、path 移動、改行変換でも診断 payload だけが変わって false red になる。

   逆に known-axes checker は ancestry で停止し、submodule pin と再構成検査へ到達しない。[s1_known_axes_freeze.py:750](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:750)–766。記録 SHA が引き続き non-ancestor である限り、rebase や `external/ccbench` 更新が起きても同じ ancestry literal のまま静かに緑になる。

   壊れるもの: repository 状態の無関係な変化で赤になり、同時に ancestry より後段の本物の drift は隠れる。exact string 化しても検査順による masking は解消していない。

   推奨修正: 固定 bytes・固定 commit graph を持つ tmp Git repository で exact 契約を検査する。実 repo canary は別テストに分け、volatile SHA 本文でなく構造化 refusal code と件数を固定する。

3. 対象: [test_tampered_freeze_fails_source_verification](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1173)

   **自己判定: real。**

   入力で変えているのは `confirmed_by` だが [1179](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1179)、固定した発火理由は既存 generator drift である [1187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1187)。generator は `confirmed_by` 検査より先に落ちる。[s8b_holdout_freeze.py:711](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:711)、[同:739](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:739)

   壊れるもの: `confirmed_by` の整合検査を削除しても、このテストは generator mismatch で緑のまま。docstring で過剰決定を告白しても positive control にはならない。

   推奨修正: 無関係な generator/design/ancestry をすべて通した hermetic fixture を作り、`confirmed_by` の対応欄不一致を単一理由で発火させる。source verification を試す意図なら改変対象自体を source bytes に変える。

4. 対象: 親判断 1 — [T-068] 不実装

   **自己判定: real。**

   不実装を一時停止として扱うことは妥当だが、ユーザー裁定を「前提が覆った」として最終的に上書きする根拠は成立していない。承認記録は方式 B の成果を明示的に **4→3** としている。[worklog.md:997](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:997)、[同:1012](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:1012)。段1でも `allowed=False` のままと既に確認済みだった。[handoff:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:18)。それを段4で「gate が開かないので前提が覆った」とした [同:76](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:76) のは自己矛盾である。

   一方、ancestry が後段の `ccbench_pin`・再構成検査を永久に隠す新事実 [handoff:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:25) と、observation 伝播条件 [decisions.md:2828](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2828) は実装停止に足る。

   壊れるもの: 正しい新 blocker と、誤った「利得ゼロ」論が混ざり、ユーザー承認済み裁定を親が無断で失効させる。

   推奨修正: [T-068] を「不採用・消化」ではなく **新事実によるユーザー再裁定待ち**へ戻す。4→3でも `allowed=False` なのは既知だったと訂正し、後段 masking・git 障害巻き込み・必要な observation 伝播範囲を新しい判断材料として提示する。

5. 対象: 親判断 2 — 期待集合を 4 件で固定

   **自己判定: real。**

   未変更 production の瞬間値として 4 件は正しい。しかし承認済み combined wave の期待は 3 件だった [worklog.md:1013](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:1013)。さらに固定した 4 件は安定した契約ではなく、既知の design drift と dangling ancestry を golden 化したもの [test:516](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:516) である。

   壊れるもの: 将来の正当な [T-068] 実装や drift 修復が「回帰」として赤くなり、既知破損が期待値へ昇格する。

   推奨修正: [T-068] の再裁定が終わるまで、この 4 件を恒久契約として merge しない。current-state canary と hermetic refusal 契約を分離し、方式 B 採用なら 3 件、撤回なら 4 件という判断を明示する。

6. 対象: 親判断 3 — [T-066] を設計択一として返却

   **自己判定: real。**

   ユーザー承認済み文言は「外部固定の期待値へ置き換える」と既に方向を選んでいる。[worklog.md:1010](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:1010)。現 fixture は production hash の動的注入 [test_s1_measurement_freeze.py:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:98) と `build_document` echo [同:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:115) を行う。一方 production の measurement builder は known-axes 検証を統合契約として実行する。[s1_measurement_freeze.py:156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:156)、[同:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:249)

   親案 (b) の「measurement から切り離す」はこの統合契約を検査しなくなるため、承認内容と同値ではない。ユーザー裁定を要する二択ではなく、保守的な (a) が残る。

   壊れるもの: [T-066] が不要に差し戻され、既知の恒真 fixture が残存する。

   推奨修正: 外部 I/O・Git 値だけを固定し、実 extractor / reconstruction を動かして独立 golden と比較する方式で実装する。少なくとも [T-066] を消化扱いにしない。

7. 対象: 親判断 4 — M1/M2 の B-057 kill 判定

   **自己判定: real。**

   M1 は単一理由でない。余分な unique refusal を足すと helper の `len` と `set` の双方が独立に不一致になる。[test:62](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:62)。M2 は重複なので `set` は同じ、`len` だけが歯であり、この部分の帰属は成立する。

   ただし両変異とも `allowed` や fail-closed 挙動を変えないことを親自身が認めている。[handoff:122](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:122)。`dev-wave` の kill 基準は「受理集合または fail-closed 挙動」で、診断文字列だけの赤を kill に数えない。[dev-wave.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/.claude/commands/dev-wave.md:22)

   壊れるもの: M1/M2 を「2/2 KILLED」と記録すると、repository 自身の変異計上規律に違反する。

   推奨修正: 両者を **diagnostic sensitivity pin** として kill 集計外にする。M1で `set` の歯を独立検証するなら、件数を保ったまま既存理由を別理由へ置換する変異へ変更する。

8. 対象: worklog 記録

   **自己判定: real。**

   task-run の目的は依然 3 タスク全部である [task.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/task-runs/20260721-s1-oracle-hosyu-b-d07a2403/task.json:1) 一方、実装差分は [T-067] のテスト 1 ファイルだけ [handoff:103](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:103)。この射程変更を曖昧にすると工程記録が裁定文と食い違う。

   worklog には少なくとも次を明記すべきである。

   - [T-068] は「親が否認して完了」ではなく、後段 masking 等の新事実によるユーザー再裁定待ち。
   - [T-066] は未実装・未消化。
   - [T-067] は 9 個の `any` を変換しただけで、部分一致 11 個が残り未完。
   - node 名は golden 2 面と一致した。
   - production の最終差分はないが、M1/M2 のため一時的に production を変異して復元した。
   - M1/M2 は kill でなく診断保持 pin。
   - 実装子は対象 7 件、単一ファイル 55 passed/1 skipped、native 全走は sandbox の `index.lock` で失敗し、shim 全走が緑。[impl.md:60](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-s1b/impl.md:60)
   - 親の shim なし全走 2351 passed/19 skipped/0 failed を正式な変更後受入として記録する。[handoff:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:107)
   - task-run 台帳に記録されている full run は現状 1 回だけなので、変更前 baseline と変更後 run を「台帳上 2 回」とは書かない。[events.jsonl:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/task-runs/20260721-s1-oracle-hosyu-b-d07a2403/events.jsonl:1)
   - direct caller は `s1_report.py` / `s1_direct_comparison.py` ではないという段3訂正も吸収する。[handoff:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-oracle-hosyu-b.md:64)

**最終判定: NO-GO**

---

### 段5 実装子 完了報告 (修正ラウンド)

修正完了です。変更は [test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:66) のみで、commit・docs・production・output・node 名は変更していません。

変更内容:

- 実 repo 依存の 2 テストを `_assert_refusal_reasons` に変更し、揮発する hash/ancestry payload のみ prefix 化。
- 残存していた部分一致 7 件を実測。
  - 6 件を `_assert_exact_refusals` に変更。
  - `test_required_existing_claim_refuses...` は所有 PID が単独実走で `2`、xdist で `35` と変動したため、コメント付き prefix 検査に変更。
- tampered テストの docstring を「positive control ではなく既知破損の characterization」と明記。
- hermetic fixture の既存 exact 検査は維持。

実測した refusal 集合:

- real freeze:
  - `holdout-freeze-verify: ... design_source sha256 不一致: recorded=1829... actual=5fbd...`
  - `known-axes-freeze-verify: ... commit ancestor でない: 2066...`
  - `floor-null: freeze.floor が null`
  - `budget-null: freeze.budget が null`
- tampered freeze:
  - `holdout-freeze-verify: ... generator sha256 不一致: recorded=1910... actual=41c0...`
  - 上記と同じ ancestry、floor-null、budget-null
- 残り 7 件:
  - `v2-execution: reservation binding 検査失敗: 必須環境変数 IZANAGI_RESERVATION_JOB_ID がない`
  - `v2-execution: execution receipt の契約再検算に失敗`
  - `v2-execution: verified calibration sha256 が contract ref と不一致`
  - `v2-execution: verified calibration が別 contract に属する`
  - `v2-execution: G12 campaign claim root が durable out_root 下に事前 provisioning 済みでない: <tmp_path>/required-run-out/claims`
  - `v2-execution: candidate が approved root 配下でない`
  - `v2-execution: G12 campaign claim 取得失敗: campaign claim は既に <PID> が所有している`

検証結果:

- 対象 9 node: `9 passed in 0.50s`
- `python3 -m pytest -q orchestrator/tests/test_s8b_oracle_driver.py`
  - `55 passed, 1 skipped`
- `python3 -m pytest -q orchestrator/tests/test_real_repo_serialization.py`
  - `3 passed`
- `python3 tools/check_codex_agents.py`
  - OK
- `python3 tools/check_docs.py`
  - 違反なし
- `git diff --check`
  - 問題なし

`python3 tools/run_tests.py` の全走も試しましたが、この sandbox では real-repo テストが shared submodule を変更後、read-only の `.git/.../index.lock` のため `git checkout -- .` に失敗します。これにより後続の real-repo refusal が source hash 不一致へ変化しました。汚染は復元済みで、submodule は clean です。したがって全走について緑とは主張しません。本実走は親の全走を代替しません。