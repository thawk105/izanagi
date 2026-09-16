## 前提の検算

指定された射影9ファイルはすべて読めた。以下の行番号は変更前の現物を指す。編集・pytest実行はしていない。

計画の基本方針はP1〜P6を採用する。ただし、現物から次の補正が必要である。

- `p3_b4_admission_record.py`の切り出し境界は、解析が617〜666行、1セル述語が668〜686行。687〜690行はexpectation行のraw／normalized二重grammar検査であり、1セル述語に含めない。
- `_SECTION5_LABELS`は77〜88行、module docstringの該当文は27〜30行。材料レポートの`_load_and_evaluate`定義は211行。
- floor issuerのfixtureは「floorだけの1行表」に加え、終端見出し`### 5.1`も欠けている。10行化と終端追加の両方が必要。
- 実文書154〜169行は完全表で、floorとexpectationを含む6セルが`未記入`。責任者行はD2079の追加受理形に一致する。
- P6の「2 module＋3 test file」だけでは完結しない。実repo読取テストの追加に伴い、既存の`conftest.py`と`test_real_repo_serialization.py`の分類・独立golden更新が必要。新しい台帳は作らない。
- P1の解析結果をそのまま使うだけでは、floorラベルの外周空白・NFKC互換文字も新たに受理する。これはP2の「値セルのstrip」以外の緩和になるため、**floorラベルの元表記を保持し、既存のexact label条件をfloor側で維持する**。

また、P1が必須とする固定表形状・全セルのdefault-ignorable拒否は、旧floor経路より受理を縮小する。「縮小は§5外・責任者欠落だけ」という文言を厳密な全差分と解するとP1自身と両立しない。本計画では、指定されたadmission解析への接続に伴う縮小として明記し、追加の意味検証は入れない。

## admission module の切り出し

対象は`orchestrator/campaign/p3_b4_admission_record.py:602`。

次の非公開helperを切り出す。

```python
def _parse_section5_fixed_table_source_cells(
    document_blob: bytes,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return normalized values, stripped raw values, and verbatim labels."""


def _assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel(
    label: str,
    value: str,
) -> None:
    """Apply the existing predicate to one already-normalized cell."""
```

戻り値の順序は`values, raw_values, verbatim_labels`とする。

- `values`：現在の663行と同じ、normalized label → normalized value。
- `raw_values`：現在の664行と同じ、normalized label → strip済み・NFKC前のvalue。
- `verbatim_labels`：normalized label → strip前のlabel。floor側の既存exact label条件を維持するためだけに使う。

解析helperへ617〜666行をそのまま移す。655行で得た`cells[0]`を`verbatim_labels[label]`へ保存する以外、条件・処理順を変更しない。raw labelの追加保存は受理判断に関与せず、既存admission関数では使わない。

1セルhelperへ668〜686行を移す。D2079の成功分岐にある`continue`だけを`return`へ置換する。通常の非sentinel値は従来どおり通す。責任者行へ識別子・制御文字・説明文などの意味検証を追加しない。

既存関数は次の構成にする。

```python
values, raw_values, _ = _parse_section5_fixed_table_source_cells(document_blob)

for label, value in values.items():
    _assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel(
        label, value
    )

_parse_closed_critic_expectation_row(raw_values[_EXPECTATION_ROW_LABEL])
expectation_row = _parse_closed_critic_expectation_row(
    values[_EXPECTATION_ROW_LABEL]
)
# 既存691〜701行のexpectation照合・returnをそのまま残す。
```

受理集合・例外契約の不変性は、次の対応で確認する。

| 変更前 | 変更後の対応 |
|---|---|
| 617〜666行のdecode・境界・形状・正規化・label集合検査 | 同じ順序で解析helper内へ移動 |
| `values.items()`の順序 | 同じdictの挿入順を維持 |
| D2079成功時の`continue` | helperから戻り、呼出元の次セルへ進む |
| 681〜686行の通常述語 | 条件式・例外生成をそのまま移動 |
| 687行のraw expectation検査 | normalized検査より先に維持 |
| 688〜701行のnormalized検査・期待値照合 | 変更なし |

`B4AdmissionRecordError`と`_SECTION5_SOURCE_CELL_CONTRACT_FAILED`の文字列は変更しない。UTF-8 decode失敗の`from exc`も維持する。スタックフレームは変わるが、例外型・`str(exc).encode("utf-8")`・期待値不一致のmessageは不変になる。

helperは`_`付きでfloor issuerから明示importする。用途がB-4内部の固定§5契約であり、汎用validatorや広い公開APIとして扱わないためである。docstringにはfloor側が共有する範囲を明記する。

module docstring27〜30行は、「完全なadmission検査」の説明であることを明確化する。続けて、floor読取は固定表解析と責任者行述語を共有するが、他セルのsentinelやexpectation宣言を検証しない旨を書く。HTML comment処理の既知の過剰拒否説明31〜36行は残す。

## floor issuer 側の接続

対象は`orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1470`と1484行。

`_floor_cell`はbytesを受け、共有解析で特定したfloorセルだけを返す。返す2値は「strip済みraw」「normalized」の順とする。

```python
def _floor_cell(raw: bytes) -> tuple[str, str]:
    try:
        values, raw_values, verbatim_labels = (
            _parse_section5_fixed_table_source_cells(raw)
        )
    except B4AdmissionRecordError as exc:
        if isinstance(exc.__cause__, UnicodeError):
            raise B4FloorArtifactError(
                "preregistration_encoding_error",
                "preregistration は UTF-8 でない",
            ) from exc
        raise B4FloorArtifactError(
            "preregistration_floor_row_error",
            f"§5 fixed table: {exc}",
        ) from exc

    if verbatim_labels[PREREGISTRATION_FLOOR_LABEL] != PREREGISTRATION_FLOOR_LABEL:
        _fail(
            "preregistration_floor_row_error",
            "§5 floor row label は既存の exact 表記でなければならない",
        )

    owner_label = "実行責任者・開始時刻"
    try:
        _assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel(
            owner_label, values[owner_label]
        )
    except B4AdmissionRecordError as exc:
        raise B4FloorArtifactError(
            "preregistration_floor_row_error",
            f"§5 実行責任者・開始時刻: {exc}",
        ) from exc

    return (
        raw_values[PREREGISTRATION_FLOOR_LABEL],
        values[PREREGISTRATION_FLOOR_LABEL],
    )
```

resolverは1491〜1495行のfilesystem処理を保持し、1496〜1505行を置き換える。

```python
raw = _read_regular(root, prereg_relpath, label="preregistration")
raw_cell, normalized_cell = _floor_cell(raw)

if normalized_cell == PREREGISTRATION_ABSENT_SENTINEL:
    return None

match = _FLOOR_PIN_RE.fullmatch(raw_cell)
if match is None:
    _fail(
        "preregistration_floor_grammar_error",
        "floor cell は 'artifact_path=<repo relative>; sha256=<lowercase hex64>' でない",
    )

artifact_path = _relative_path(match.group("path"), label="floor artifact_path")
expected_sha256 = match.group("sha256")
return load_authoritative_floor(
    repo_root=root,
    artifact_path=artifact_path,
    expected_sha256=expected_sha256,
)
```

責任者検査はsentinelによる`None`返却より先に実行する。責任者行欠落は解析段階、値が`実行責任者 = 未記入、開始時刻 = 未記入`なら述語段階で、それぞれ拒否される。

エラーcodeは次の扱いとする。

| code | 方針 |
|---|---|
| `preregistration_floor_row_error` | 維持。固定表解析失敗・floorラベル不一致・責任者述語失敗へ適用。従来の`exact 1`というdetailは置換 |
| `preregistration_floor_grammar_error` | 維持。表と責任者が通った後、非sentinel floorが既存pin grammarに一致しない場合 |
| `preregistration_encoding_error` | 維持。解析helperが保持するUnicodeError causeを識別して写像。二重decodeはしない |
| 新設・廃止 | なし |

P5に従いdecodeはadmission側の`utf-8-sig`へ統一する。固定表のfloor行は文書先頭には置けないため、先頭BOM除去だけで旧経路が拒否したfloor値を新たに許すことはない。

P2は採用する。sentinel比較はnormalized値、pin grammarはstrip済みraw値に掛ける。例えば`artifact_path=artifacts/Ａ.json; sha256=...`をNFKC後に処理すると、実際の参照先が`artifacts/A.json`に変わる。NFKC済み文字列をloaderへ渡してはいけない。全角hash・全角構文文字もraw grammarで拒否を維持する。

resolverの1489行docstringから「verbatim sentinel」を除き、共有する§5契約、strip後のsentinel、raw pin grammarを記す。

issuerの`main():1520`は発行専用でresolverを呼ばない。従って現在のCLI経路に直接の変更はない。1552〜1556行のJSONエラー形式も変更しない。材料レポートでは`p3_b4_material_report.py:221`が従来どおり`authoritative_floor_rejected`へ包み、CLIの1610〜1611行が同理由を出力する。

## 既存 test の期待値変更

以下のパスはいずれも`orchestrator/tests/`配下。

| file:line | 変更と期待 |
|---|---|
| `test_p3_b4_floor_artifact_issuer.py:188` `_preregistration` | 10行の完全表＋`### 5.1`へ変更。責任者はD2079形、floor以外の一般欄は`未記入`でもよい |
| 同`:681` `test_resolver_exact_sentinel_is_the_only_absence` | `未記入`に加え、694行の` 未記入`・`未記入 `を`None`期待へ移す。`TBD`・`artifact_path=x`はgrammar errorのまま |
| 同`:703` `test_resolver_returns_exact_fraction_from_valid_pin` | fixture変更のみ。Fraction型、path、hashの期待は維持 |
| 同`:733` `test_m05_m06_resolver_fails_closed_without_absence_fallback` | fixture変更のみ。missing/hash/schemaの対象検査まで到達させ、拒否を維持 |
| 同`:772` `test_resolver_rejects_duplicate_floor_rows` | 完全表の別行labelをfloor labelへ置換し、行数を12行のままにして重複を作る。`match="exact 1"`をやめ、row error codeと新detailを検証 |
| 同`:1312` `test_aggregate_public_issue_load_and_preregistration_pin` | 1324行のfixture経由で完全表化。resolvedとloadedの一致、最大Fraction、v2 schema期待を維持 |
| `test_p3_b4_material_report.py:77` `_write_floor_preregistration` | 137〜142行の単一行書込みを完全表bytesへ変更。present/absent双方の戻り値は維持 |
| 同`:959` aggregate正例 | 1004〜1008行を完全表へ変更。resolverのpath/hash/Fraction、evaluatorへの最大floor引渡しを維持 |
| 同`:1103` m7 | 1113〜1119行を完全表へ変更。missing artifactへの到達を保ち、1138〜1142行のreason・cause=`path_error`・evaluator未呼出しを維持 |
| 同`:1516` CLI test | 期待値変更なし。実文書を読むclean subprocess経路として再走 |
| `test_p3_b4_admission_record.py:405`以降 | 既存期待値は変更しない。文字列完全一致の拒否、raw expectation grammar、D2079の受理集合を回帰確認 |

fixtureは`test_p3_b4_admission_record._section5_document:81`のcross-test importを採用する。これは独立したliteral label集合を持ち、production定数をそのまま期待値へ流用しない利点もある。

既存の先例は`test_p3_b4_material_report.py:964`の`_aggregate_public_sources` import。各fileに小さなfixtureを複製する案はimport依存が少ない一方、10ラベル・境界・責任者形の保守が重複する。今回は既存builderを再利用し、各fileの小さなwrapperでfloorと責任者、他欄の`未記入`を上書きする。

importは既存慣行に合わせた関数内importとし、builder import時に実repoの内容を読んだり、テストを実行したりしないことを確認する。builderのデフォルト責任者値は`fixture-value-10`なので、D2079形への明示overrideを忘れない。

## 新規 test 案

主な追加位置は`test_p3_b4_floor_artifact_issuer.py:681`付近とする。以下は予定node名。

1. `test_resolver_real_preregistration_is_absent`
   `Path(__file__).resolve().parents[2]`をrepo rootにし、実文書を公開resolverへ渡して`None`を確認する。新しい実repo読取テストはこれ1件だけ。

   登録先は既存の次の4集合。

   - `conftest.py:260` `_REAL_REPO_NODE_INVENTORY`
   - `conftest.py:452` `_REAL_REPO_PARENT_ONLY_NODES`
   - `test_real_repo_serialization.py:52` `_REAL_REPO_CLASSIFIED_NODES_GOLDEN`
   - 同`:212` `_REAL_REPO_PARENT_ONLY_NODES_GOLDEN`

   アクセスは`RealRepoAccess("read", None)`。独自marker・fixture・lockは作らず、既存hookに任せる。

2. `test_resolver_ignores_pin_outside_section5`
   §5のfloorはsentinel、`### 5.1`以降にgrammar上有効なpin行を置く。`None`かつloader未呼出し。§5外のpin先を作らず、誤参照でもテストが落ちる構成にする。

3. `test_resolver_rejects_missing_floor_despite_outside_pin`
   §5のfloor行を削除して9行表にし、外側には有効pin行を残す。row error、loader未呼出し。

4. `test_resolver_rejects_unrecorded_owner_before_loading_pin`
   完全表・有効pinで、責任者を`実行責任者 = 未記入、開始時刻 = 未記入`に変更。row errorと責任者detail、loader未呼出し。

5. `test_resolver_rejects_missing_owner_row`
   有効pinを残し責任者行を削除。row error、loader未呼出し。

6. `test_resolver_ignores_blocked_section5_decoys`
   1つのテスト内でfence／HTML commentの2入力を検証する。blocked領域へ偽の§5完全表・pinを置き、外の真正§5はsentinelにする。両方`None`。境界探索から除外することを確認する。

7. `test_preregistration_floor_label_matches_admission_label`
   `issuer.PREREGISTRATION_FLOOR_LABEL == admission._SECTION5_LABELS[4]`をpinする。

8. `test_resolver_preserves_raw_floor_pin`
   padded pinのstripを確認し、`artifacts/Ａ.json`がloaderへ同じ文字列で渡ることを確認する。全角hashやNFKCでのみ成立する構文はgrammar errorにする。

9. `test_resolver_keeps_exact_floor_label`
   floor labelへの外周空白追加・`floor`の全角化を各々拒否する。admission自身のlabel正規化は変更しない。

10. `test_resolver_rejects_unknown_label_at_fixed_row_count`
    無関係な1ラベルを未知labelへ置換し、行数・floor・責任者は維持。label集合検査単独の欠落を検出する。

11. `test_resolver_preserves_encoding_error`
    不正UTF-8は既存encoding code、先頭BOM付き完全表は通常の結果になることを確認する。

admission test側にはhelperの`raw_values`と`values`を区別する小さな確認を追加する。特に既存`:667`のNFKCでのみASCII grammarに一致するexpectation拒否を維持する。

新規テスト本体はbytes操作、小さなtmp file、loaderの呼出し観測で構成し、subprocess・artifact発行・新しい大規模publication fixtureは追加しない。実repo読取1件もresolver自身はsubprocessを使わない。ただし既存real-repo lock基盤のGit照会は別であり、「スイート全体でsubprocessゼロ」とは報告しない。5分上限への追加負荷は小さい設計だが、達成は後段の受入実測で確認する。

## 変異 matrix の事前登録候補

行番号は変更前の対応箇所。Aは`orchestrator/campaign/p3_b4_admission_record.py`、Fは`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`を指す。各変異は単独適用する。

| ID | 対象 | 変異内容 | 期待結果／KILLED node |
|---|---|---|---|
| M0 | A:27 | comment／docstringのみ変更 | 等価対照としてSURVIVED期待。floor・§5機能焦点では成功。closure hash自体は変わる |
| M1 | F:1470 | 共有解析によるfloor選択を旧全文prefix走査へ戻す | `test_resolver_ignores_pin_outside_section5` |
| M2 | F:1470の新責任者述語呼出し | 述語呼出しを削除 | `test_resolver_rejects_unrecorded_owner_before_loading_pin` |
| M3 | A:665 | label集合比較だけ削除 | `test_resolver_rejects_unknown_label_at_fixed_row_count` |
| M4 | A:658・664 | raw valueをstripせず保存し、F:1503相当でそれをsentinel比較する単一変異patch | `test_resolver_exact_sentinel_is_the_only_absence`のpaddedケース |
| M5 | A:664 | `raw_values[label]`へnormalized valueを格納 | `test_section5_expectation_row_rejects_nfkc_only_ascii_grammar_matches` |
| M6 | A:625〜644 | 境界探索と区間検査からfence除外を削除 | `test_resolver_ignores_blocked_section5_decoys`のfence入力 |
| M7 | A:625〜644 | 同じ箇所のHTML comment除外を削除 | 同nodeのHTML comment入力 |
| M8 | F:1505 | pin fullmatchへrawではなくnormalized値を渡す | `test_resolver_preserves_raw_floor_pin` |
| M9 | F:1470の新exact label比較 | 元floorラベルの比較を削除 | `test_resolver_keeps_exact_floor_label` |

M4では、単にnormalizedからrawへ比較対象を変えるだけではrawもstrip済みなので等価になりうる。strip前比較を再現するpatchとして登録する。

M0は「機能上の等価」であり、closureのbytes同一性まで等価とは扱わない。各KILLED判定は指定nodeのassertion失敗を根拠とし、import失敗・環境エラー・時間切れを代用しない。ここでは未実施である。

## 焦点テスト集合と影響範囲

`grep -rn --include='*.py'`で`orchestrator/`全体の直接参照を確認した。

| 起点 | 直接consumer・参照 |
|---|---|
| admission | `campaign/p3_b4_closed_critic.py:56,104,646` |
| admission | `campaign/p3_b4_launcher.py:28` |
| admission bytes | `campaign/p3_b4_raw_record_producer.py:995` |
| floor issuer | `campaign/p3_b4_material_report.py:33` |
| admission tests | `test_p3_b4_admission_record.py:21`、`test_p3_b4_closed_critic.py:32,629,2008`、`test_p3_b4_launcher.py:18` |
| admissionのsource inventory | `test_ccbench_spawn_sites.py:173` |
| floor issuer tests | `test_p3_b4_floor_artifact_issuer.py:17`、`test_p3_b4_material_report.py:25,964` |

間接2段では次を確認した。

- closed critic → launcher`:32`、raw record producer`:33`。後者は`:987`以降でclosure入力を再構成する。
- closed critic → `p3_s4_loop.py:2102`のreceipt検証。
- launcher → raw record producer`:34`、`wal.py:521`以降、base/sort/trigger loopのcontext検証。
- material report → raw producer test`:30`、producer auth experimentのsource参照・subprocess検証。
- material reportのCLIは`test_p3_b4_material_report.py:1516`。実文書を使うためfixture変更だけの確認では足りない。
- `campaign_lock.py`などにはlauncherのpath literalもあるが、本変更はpathやspawn siteを増やさない。

再走集合は次の順にする。すべて後段で`tools/run_tests.py`経由とし、この段では実行しない。

1. 必須焦点：
   `test_p3_b4_admission_record.py`、`test_p3_b4_floor_artifact_issuer.py`、`test_p3_b4_material_report.py`、`test_p3_b4_closed_critic.py`、`test_p3_b4_raw_record_producer.py`、**`test_p3_b4_launcher.py`**。
2. 実repo分類変更：
   `test_real_repo_serialization.py`、`test_acceptance_schedule_order.py`。
3. 間接consumer：
   `test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`、`test_p3_b4_proposal_binding.py`、`test_p3_b4_producer_auth_experiment.py`、`test_ccbench_spawn_sites.py`。
4. 受入全走：
   brief指定の`tools/dev_wave_wait.py acceptance --lease-optional -- python3 tools/run_tests.py`。

briefの焦点5fileにはlauncherと分類回帰が不足している。既存の関連consumerは受入全走でも確認する。docs・Codex agents・commit後provenance検査は親の完了手順に従う。

## P4 の検算

P4の主要部分は現物で裏付けられた。

- `p3_b4_closed_critic.py:646`がadmission moduleをclosureへ含め、668〜670行で`path.read_bytes()`のSHA-256を取る。
- `projection_sha256:681`はmanifest全体をhash化する。この共通entryはbase/sort/triggerすべてに入るので、admission bytes変更で3種類とも変わる。
- `assert_b4_document_projection_closures_are_live:687`は3種類すべてを比較する。呼出元は同file`:918`のinvoke、`:1283`のproduction pair作成、`:1936`のcertified pair検証、`p3_b4_launcher.py:386`。
- raw producerも`:995`で同moduleを含み、`:1019`以降でclosureを計算する。新旧receipt混用は検出される。
- `git ls-files 'docs/phase3-b4-reflux-ablation-admission-record-*.json'`は0件。working treeの同patternも0件。
- 実文書`:166`のexpectation行は`未記入`。現在有効な3driver closure宣言はない。
- 現在のadmission／floor issuer／material report各moduleのSHA-256を計算し、tracked fileを`git grep -F`で検索したところ、いずれも一致0件だった。

従って、**今回確認した現行の登録文書・admission recordについて、失効処理や再発行が必要な対象はない**。事前登録文書を編集しないので、そのbytesおよび§5.1.1の文書内pinは変わらない。

既存の歴史的receiptを新しいlive closureへ書き換える計画は入れない。外部・未追跡の実走成果物全体が存在しないことまでは、この検算から断言しない。将来の正式発行では変更後closureを使う。

## リスクと未確定点

- **現行文書の正例保持**
  解析後に述語を適用するのは責任者行だけ。他欄の`未記入`、expectation grammarはfloor経路では検査しない。従って現文書は静的には`None`へ到達する。実行による確認は後段に残る。

- **受理集合の意図しない拡大**
  floorラベルの元表記比較を残し、値セルのstrip以外の緩和を防ぐ。pinのNFKC適用も禁止する。§5外の重複行を無視して真正§5を読めるようになる変更は、要求された境界修正そのものとして扱う。

- **正規化による縮小**
  P1に従い、他セルもdefault-ignorable拒否の対象になる。ただし非空・sentinel述語は適用しない。この区別をdocstringと試験で固定する。

- **将来のadmission変更との結合**
  境界・形状・label・正規化・責任者述語の変更がfloorへ波及することは、今回の接続の意図した性質である。共有範囲をdocstringに明示し、将来もfloorの実文書正例とpin grammar回帰を同時に走らせる。

- **symlinkに関するbriefの表現補正**
  issuerの`_repo_root:341`自体はrootのsymlinkを拒否せず、`resolve(strict=True)`で解決する。解決後root配下のpreregistration／artifactのsymlink componentを`_read_regular:384`→`_assert_no_symlink:368`が拒否する。この処理は保持する。

- **admissionとの読取元の違い**
  共有するのはbytes解析だけ。admission verifierはrecordのfilesystem検査に加え、`:465`のGit tree blobとcommit bindingを使う。floor resolverへGit commitment検証を持ち込まず、逆にadmissionをworking-tree読取へ変更しない。

- **エラー写像の結合**
  encoding code維持はhelperのUnicodeError cause保存に依存する。これは実装上の明示契約とし、encoding回帰で固定する。

- **変更file数**
  実装2module、主要test3fileに加え、real-repo分類2fileとbrief指定のinsight README／worklog・decisions fragmentが必要。authorはP6どおり1本でよい。事前登録文書は編集しない。

## 総括

共有するのは既存§5固定表解析と1セル述語で、floor経路は責任者行だけを述語検査する。raw／normalizedを保持し、sentinelはnormalized、pinはstrip済みrawで処理する。

briefへの重要な補正は、**floorラベルのexact条件維持、expectation検査の切り出し対象からの除外、real-repo分類2fileの追加、launcher回帰の追加**である。P4は現行登録対象について成立する。

静的検算のみ完了。ファイル変更・テスト・変異実行は行っていない。
