## 設計方針

新規 module 名は `orchestrator/campaign/p3_b4_certified_selection_connection.py` を提案する。

- `certified_selection_connection` は、既存分析経路が明示的に scope 外としている責務名そのもの。[p3_b4_analysis_path.py:11-16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_path.py:11)
- `consumer` よりも、material report を certified-selection 境界へ接続する限定責務が明確。
- `p3_b4_analysis_*` の名前にしないため、分析 source closure へ誤って追加する誘因も避けられる。

設計は「許可枝なし」とする。

- 正規入力は、`evaluated / protocol_violation / floor_domain_error` または `not_evaluated / assembly_rejected` の二形だけ。
- `established` は純分析契約上の enum 値ではあるが、material report の正規生成経路では到達不能。
- certified 昇格の権威は、caller-authored JSON ではなく、発行・再導出された `LaunchAdmissionRederivation.certifying`。[reflux_origin_binding.py:204-257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/reflux_origin_binding.py:204) [reflux_origin_binding.py:260-298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/reflux_origin_binding.py:260)
- その権威は material report の 3-file wire に存在せず、現 checkout には下流 consumer もない。[layer3_report.py:682-703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/layer3_report.py:682)
- よって dormant な許可枝を作らず、妥当な現行 report は必ず `admits_certified_selection=False`、不正入力は型付き例外とする。T-2140 が権威を発効した後は、その権威を入力に持つ別変更で許可枝を追加する。

`False` 自体は現行 domain 上の不変値だが、consumer 全体は定数関数ではない。3 file の実 bytes、schema、reachable domain、Markdown cross-binding を検査し、不正 pair は返り値を作らず拒否する。実 CLI が作った pair が正常 return path を実際に通る正例も置くため、「到達不能な許可条件を前件にした恒真保証」ではない。

## 変更面 (file:line)

変更するのは新規 2 file のみ。

- `orchestrator/campaign/p3_b4_certified_selection_connection.py`

  - 予定 `:1-34` — module docstring、wire/schema 定数、固定 file 名。
  - 予定 `:36-67` — public exception と frozen decision dataclass。
  - 予定 `:69-118` — symlink を追わない report-root / regular-file reader。
  - 予定 `:120-166` — duplicate-key・非有限値拒否を含む strict canonical JSON parser。
  - 予定 `:168-202` — `report.complete` schema と 2 digest の照合。
  - 予定 `:204-275` — report root key set、scope、floor、certification、analysis の正規値域検証。
  - 予定 `:277-310` — Markdown の JSON digest・status・verdict・non-certifying 表示の cross-check。
  - 予定 `:312-348` — public 全域入口と常に不許可の decision 構築。
  - 予定末尾 — `__all__`。

- `orchestrator/tests/test_p3_b4_certified_selection_connection.py`

  - 予定 `:1-45` — imports、canonical pair 再束縛 helper。
  - 予定 `:47-105` — production writer/CLI を使う実 report 作成 helper。
  - 予定 `:107-160` — `evaluated` と `not_evaluated` の valid-input 正例。
  - 予定 `:162-215` — 欠落・malformed・hash mismatch の発火試験。
  - 予定 `:217-290` — hash を再束縛して特定 domain guard まで到達させる負例。
  - 予定 `:292-325` — caller-authored `established` と Markdown cross-binding の負例。

触らない file と理由:

- [p3_b4_material_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:46) — producer wire、marker、402-row projectionを変更しない。
- `p3_b4_analysis_{contract,adapter,ledgers,path,prereg_consumer}.py` — 5-file closure を不変にする。新 module は `_SOURCE_CLOSURE_PATHS` と `_CLOSURE_PATHS` のどちらにも追加しない。[p3_b4_analysis_path.py:67-73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_path.py:67) [p3_b4_analysis_prereg_consumer.py:98-104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98)
- `p3_b4_{admission_record,closed_critic,launcher,wiring_probe}.py` と test — 別 wave 所有。import 依存も新設しない。
- [docs/phase3-b4-reflux-ablation-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/docs/phase3-b4-reflux-ablation-preregistration.md:154) — §5 / §5.1 / §5.1.1 を一切編集しない。
- [test_p3_b4_material_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_material_report.py:1)、[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_real_repo_serialization.py:247)、[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/conftest.py:258) — 既存期待値、golden、inventory を変更しない。
- `orchestrator/campaign/__init__.py` — 既存 module と同じく明示 import で使えるため登録不要。
- `layer3_report.py`、`reflux_origin_binding.py`、`p3_b4_prerun_issuer.py` — 権威・非保証の参照元に留める。

## public API

予定 API:

```python
CONNECTION_SCHEMA_VERSION = "p3-b4-certified-selection-connection/v1"

class B4CertifiedSelectionConnectionError(ValueError):
    reason: str
    detail: str

@dataclass(frozen=True, slots=True)
class B4CertifiedSelectionDecision:
    schema_version: str
    material_report_schema_version: str
    report_json_sha256: str
    report_markdown_sha256: str
    report_commit_sha256: str
    analysis_status: Literal["evaluated", "not_evaluated"]
    analysis_verdict: Literal["protocol_violation"] | None
    analysis_invalid_reasons: tuple[str, ...]
    admits_certified_selection: Literal[False]
    reason_code: Literal["material_report_has_no_certified_selection_authority"]

def evaluate_b4_certified_selection(
    *,
    report_root: str | Path,
) -> B4CertifiedSelectionDecision:
    ...
```

例外の `reason` は少なくとも次の閉じた文字列を使う。

- `report_root_invalid`
- `report_artifact_unavailable`
- `report_commit_invalid`
- `report_binding_mismatch`
- `report_json_invalid`
- `report_domain_mismatch`
- `report_markdown_mismatch`

全域性は「どの filesystem 入力も、不許可 decision または上記の型付き fail-closed rejection のどちらかになる」という境界で実現する。boolean の `True` を返す code path は置かない。

## 入力 field の実在と到達可能な値域

| file / field | producer 上の実在 | 正規値域と採用条件 |
|---|---|---|
| `report.complete.schema_version` | marker payload。[p3_b4_material_report.py:1171-1175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:1171) | exact `p3-b4-material-report-commit/v1` |
| `report.complete.report_json_sha256` | 同上 | 実際に読んだ `report.json` bytes の SHA-256 |
| `report.complete.report_markdown_sha256` | 同上 | 実際に読んだ `report.md` bytes の SHA-256 |
| `report.json.schema_version` | [p3_b4_material_report.py:717-719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:717) | exact `p3-b4-material-report/v1` |
| `report_scope.*` | [p3_b4_material_report.py:720-727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:720) | exact evidence-only / §5 not in effect / floor absent / expected PV+floor error / four-class false |
| `certification_scope.certifying` | [p3_b4_material_report.py:728-744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:728) | `False` のみ |
| `certification_scope.not_guaranteed` | 同上 | `certified_selection_connection` と `authoritative_floor_artifact` を含む固定 list。新 consumer が存在しても「report 自身が保証しない」は真なので変更しない |
| `floor.*` | [p3_b4_material_report.py:745-750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:745) | exact absent / `preregistration_section_5_unfilled` / source・value は null |
| `analysis.status` | [p3_b4_material_report.py:699-716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:699) | `evaluated` または `not_evaluated` |
| evaluated の `analysis.result.verdict` | material generator は `floor=None` を渡す。[p3_b4_material_report.py:214-230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:214) | floor domain check により `protocol_violation`。[p3_b4_analysis_path.py:349-353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_path.py:349) |
| evaluated の `analysis_invalid.reasons` | invalid result wire。[p3_b4_analysis_path.py:102-121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_path.py:102) | exact `["floor_domain_error"]` |
| not-evaluated の `analysis` | assembly rejection branch。[p3_b4_material_report.py:709-716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:709) | `reason="assembly_rejected"`、`result=null`、`floor_argument=null` |
| Markdown の JSON digest / status / verdict / certification | [p3_b4_material_report.py:849-870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:849) | JSON と一致する digest、`protocol_violation` または `not_evaluated`、non-certifying 固定文 |

`B4Verdict` 自体は 4 値を持つ。[p3_b4_analysis_contract.py:85-91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_contract.py:85) しかし既存の 4 値試験は renderer-only であり、正規経路到達性の証拠ではないと明記されている。[test_p3_b4_material_report.py:560-589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_material_report.py:560)

したがって `established` を要求する許可述語は採用しない。caller が JSON と marker を自己整合的に書き換えても `report_domain_mismatch` で拒否され、許可にはならない。

また `provenance.issuer_commitment_sha256` も certified 権威に使わない。issuer 自身が、この digest は identity・signature・external pin ではないと宣言している。[p3_b4_prerun_issuer.py:1-24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_prerun_issuer.py:1) [p3_b4_prerun_issuer.py:52-63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_prerun_issuer.py:52)

## 3 file 束縛の検証手順

1. `report_root` は absolute/canonical directory として検査し、symlink component を拒否する。directory FD を `O_DIRECTORY | O_NOFOLLOW` で保持する。
2. その FD 相対で `report.complete`、`report.json`、`report.md` を `O_RDONLY | O_NOFOLLOW` で開き、regular file であることを `fstat` する。basename は固定し、caller path は受け取らない。
3. `report.complete` を duplicate-key・非有限値拒否で parse し、canonical bytes、exact 3-key set、commit schema、lowercase SHA-256 domain を検査する。
4. 読み取った JSON/Markdown bytes の SHA-256 をそれぞれ再計算し、marker の 2 field と exact compare する。
5. `report.json` も strict UTF-8、duplicate-key 拒否、producer と同じ compact/sorted/final-LF canonicalizationで再 encode し、raw bytes と一致させる。[p3_b4_material_report.py:150-180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:150)
6. report の exact top-level key setと、上節の certified-selection 関連 field、`block_count=201`、`arm_row_count=402`、`len(rows)=402` を検査する。402 row の全 leaf 再導出は producer の責務であり、この consumer へ複製しない。[p3_b4_material_report.py:498-663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:498)
7. Markdown を strict UTF-8/LF として読み、JSON SHA-256 行、schema、§5、floor、analysis status/verdict、non-certifying 行が JSON と一致し、各行が一意であることを検査する。全 402-row Markdown renderer は複製しない。
8. root path と保持中 directory FD の inode identity を再確認してから decision を返す。

publisher は JSON/Markdown を先に hard-linkし、directory を fsync してから marker を最後に linkし、再度 fsync する。[p3_b4_material_report.py:1176-1210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:1176) したがって marker は「この 2 byte string が一組として publication 済み」の commit point になる。

ただし marker は署名・発行者権威ではない。証明するのは 3 file の一貫性だけであり、certified 昇格は証明しない。この区別により caller 自己申告を権威化しない。

## test 計画 (正例・負例)

正例は「許可の正例」ではなく、「正規の実 artifact を読み、不許可 decision を返す正例」とする。

- `test_real_cli_material_reports_are_bound_non_certifying_decisions`

  - [test_p3_b4_raw_record_producer.py:881-917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_raw_record_producer.py:881) と [test_p3_b4_raw_record_producer.py:1523-1547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_raw_record_producer.py:1523) の production writer 経由 publication を実体として使う。
  - 既存 CLI 実行形 [test_p3_b4_material_report.py:903-940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_material_report.py:903) と同じく、clean subprocess で `report.json` / `report.md` / `report.complete` を実際に生成する。
  - material report writer、hash/parser、connection API を monkeypatch/stub しない。
  - evaluated pair について `protocol_violation`、`("floor_domain_error",)`、3 digest、`False` を確認する。
  - その後 planned artifact 1 件を除いた publication から別 output root へ report を生成し、`not_evaluated`、verdict null、reasons空、`False` を確認する。これで正規値域の二形を両方発火させる。

「発火自体が目的」の負例:

- `report.complete` 欠落。
- 3 file のいずれかが symlink / 非 regular。
- marker が malformed JSON、duplicate key、非 canonical。
- JSON/Markdown hash mismatch。

これらは最初の fail-closed 発火が目的なので、後続 guard まで到達させる必要はない。

「特定の時点で発火させたい」負例:

- report JSON を変更した後、marker の両 hash と Markdown 内 JSON digestを再計算して前段を通す。
- `schema_version` drift、`report_scope` drift、`certification_scope.certifying=True`、floor 出現、`analysis.result.verdict="established"` をそれぞれ `report_domain_mismatch` で拒否する。
- `established` ケースでは Markdown verdict も `established` に変更し、marker hashも更新する。これにより Markdown/hash 前段ではなく、正規値域 guard が発火したと一意に示す。
- Markdown cross-binding の試験では、Markdown の JSON digestだけを壊し、marker の Markdown hashは更新する。marker bindingを通過した後の cross-checkを狙う。
- すべて `exc.value.reason` を exact compareし、message substringだけに依存しない。

## golden / inventory への登録判定

登録不要にできる。

- 新 test file に `pytest.mark.xdist_group` を付けない。したがって `_XDIST_GROUP_NAMES_GOLDEN` と `_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN` は変更不要。[test_real_repo_serialization.py:247-315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_real_repo_serialization.py:247)
- long-lived module/session fixtureを作らず、実 artifact 正例も function-scoped `tmp_path` 内で完結させる。
- production API は repository root や `verify_repository_preregistration_contract()` を読まない。test も実 working tree の可変 artifact、Git state、`output/`、共有 submodule を読まない。
- よって `_REAL_REPO_NODE_INVENTORY` への追加も不要。[conftest.py:258-260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/conftest.py:258)
- `conftest` が inventory 登録 node に自動で付ける `real-repo` group の対象にもならない。[conftest.py:1991-2000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/conftest.py:1991)

## 変異候補

以下はすべて、新 test が前段 hashを必要に応じて再束縛するため、無効化時に赤くなる理由を一つに絞れる。

| ID | 予定位置 | 変異 | killer / 一意性 |
|---|---|---|---|
| C01 | connection `evaluate_b4_certified_selection` 最終 decision、予定 `:330` | `False` を `True` | 実 CLI 正例の exact bool assertionだけが赤。可 |
| C02 | marker validator、予定 `:178` | commit schema 比較を削除 | hashes が正しい wrong-schema marker。ほかは valid。可 |
| C03 | marker binding、予定 `:190` | JSON digest compare を削除 | marker の JSON digest fieldだけ誤値。JSON/MD は相互整合。可 |
| C04 | marker binding、予定 `:194` | Markdown digest compare を削除 | marker の Markdown digest fieldだけ誤値。可 |
| C05 | strict JSON、予定 `:152` | canonical-byte equalityを削除 | hashesを更新した trailing-space JSON。duplicate-key guard等には当たらない。可 |
| C06 | report scope validator、予定 `:222` | exact `report_scope` 比較を削除 | `expected_analysis_verdict="established"` に変更し全 hash再束縛。可 |
| C07 | certification validator、予定 `:238` | `certifying is False` を削除 | `certifying=True`、他 field/hashは valid。可 |
| C08 | floor validator、予定 `:246` | exact absent floor 比較を削除 | floor value/sourceを出現させ、全 hash再束縛。可 |
| C09 | evaluated branch、予定 `:260` | verdict/reason exact compare を削除 | JSON/Markdownとも `established` にし全 hash再束縛。可 |
| C10 | Markdown validator、予定 `:292` | JSON digest line cross-check を削除 | Markdown digest行だけ誤値、marker の Markdown hashは更新。可 |

候補から外すもの:

- file欠落・symlink guard の単独削除 — 後段 `os.open`、regular-file check、JSON parserも同じ入力を拒否しうるため、一意な mutation killer にしにくい。
- duplicate-key hook 単独削除 — canonical-byte equalityも同じ入力を拒否するため除外。
- stale markerのまま semantic fieldを変更する変異 — marker hash比較が先に拒否するため、domain guardの変異候補にならない。必ず marker/Markdown を再束縛した負例を使う。

## 親 provisional 裁定への異議

- P1: 結論には賛成。ただし「常に False を返すだけ」にはしない。valid pair のみ digest付き decisionを返し、不正 pairは型付き拒否とする。許可枝は置かない。
- P2: 賛成。analysis path の docstring は「この module の scope 外」であり、新 moduleへ責務を置いても真のまま。material report の `not_guaranteed` も「report単独では保証しない」ため真のまま。
- P3: 異議あり。`verify_repository_preregistration_contract()` は §5.1.1 と5-file source closureを検証する。[p3_b4_analysis_prereg_consumer.py:1027-1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1027) §5 table の未発効状態は検証しない。実際、現 §5 は多数の `未記入` を含む。[phase3-b4-reflux-ablation-preregistration.md:154-167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/docs/phase3-b4-reflux-ablation-preregistration.md:154) したがって、この受領証を「§5未発効の権威」として使ってはならない。許可枝がない本設計では prereg consumer を呼ぶ必要自体がない。
- P4: 条件付きで賛成。CLI が生成した tmp report pair は接続の正常発火正例になる。一方、real B-4 output が未着地である以上、「live certified-selection path が運用済み」とは主張しない。証明するのは consumer の発火可能性と現行 report の機械的不許可まで。

## 未解決の疑問

なし。T-2140 後に許可を追加する場合は、material report の `verdict` ではなく発行・再導出済み `certifying` 権威を新 API 入力へ持ち込む設計変更が必要であり、本 wave に先置きしない。

## 総括

実装面は新規 production module 1本と test file 1本だけに限定する。consumer は output root の `report.complete` が束縛する JSON/Markdown bytesを再検証し、正規に到達可能な二形を machine-readable な不許可 decisionへ写す。`established` 自己申告、壊れた束縛、将来値はすべて型付きで拒否し、許可枝は存在させない。

pytest は指示どおり実走しておらず、上記は静的読解に基づく実装プランである。