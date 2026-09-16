## 総括

**案 B を採用する。** 既存の受理条件を維持し、「実行責任者・開始時刻」行についてだけ、責任者が非空・非 sentinel で、開始時刻の値が正確に `未記入` である形を追加受理する。変更箇所は既存の値走査と追加テスト。本文の追補は親が行う。

指定された射影 8 ファイルはすべて読めた。以下はコード読解と `rg` による静的調査であり、**テストは実走していない**。ファイル変更・commit・Git 状態変更は行っていない。

なお、実文書 `docs/phase3-b4-reflux-ablation-preregistration.md:159,162-166` と射影の表には、対象行以外に **6 欄**の `未記入` がある。brief の「残り 5 欄」は数え違いと判断する。実文書が本変更後も拒否されるという結論は変わらない。

以降の行番号は調査時点。略記は次のファイルを指す。

|略記|ファイル|
|---|---|
|A|[p3_b4_admission_record.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time/orchestrator/campaign/p3_b4_admission_record.py:602)|
|T|[test_p3_b4_admission_record.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time/orchestrator/tests/test_p3_b4_admission_record.py:405)|
|D|[phase3-b4-reflux-ablation-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time/docs/phase3-b4-reflux-ablation-preregistration.md:339)|
|C|[p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301)|

## 1. 受理側の変更 plan

### 変更位置と述語

`A:667-673` の走査を `values.items()` に変更し、label の文字列一致で対象行だけ分岐する。新しい helper・gate は作らず、既存走査内に収める。

追加受理する構文は、既存の `strip()`・NFKC 正規化後の値に対する次の **fullmatch** とする。

```python
r"実行責任者 = (?P<owner>[^、=\r\n]+)、開始時刻 = 未記入"
```

さらに `owner = match.group("owner").strip()` に対し、既存の値検査と同じ三条件を適用する。

```python
bool(owner)
and _RESERVED_SENTINEL_RE.search(owner) is None
and owner.casefold() not in _RESERVED_SENTINEL_WHOLE_VALUES
```

具体的な置換案：

```python
for label, value in values.items():
    if label == "実行責任者・開始時刻":
        match = re.fullmatch(
            r"実行責任者 = (?P<owner>[^、=\r\n]+)、開始時刻 = 未記入",
            value,
        )
        if match is not None:
            owner = match.group("owner").strip()
            if (
                owner
                and _RESERVED_SENTINEL_RE.search(owner) is None
                and owner.casefold() not in _RESERVED_SENTINEL_WHOLE_VALUES
            ):
                continue

    if (
        not value
        or _RESERVED_SENTINEL_RE.search(value) is not None
        or value.casefold() in _RESERVED_SENTINEL_WHOLE_VALUES
    ):
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
```

`continue` は値走査の次の行へ進むだけであり、`A:674-688` の expectation 解析・model/prompt 束縛・projection の返却は必ず残る。

### 受理集合の境界

- 対象外の行は、同じ正規化済み値に同じ三条件を適用する。受理集合は変わらない。
- 対象行は「旧述語 OR 上記の追加述語」とする。既存の非 sentinel 値に新しい構文を強制しない。
- `_SECTION5_LABELS`（`A:77-88`）、sentinel 定義（`A:114-121`）、正規化（`A:538-544`）、表構造検査は変更しない。
- 責任者の実在性や識別子の意味は検証しない。非空・既存 sentinel 規則の確認に限定する。

この追加形は §0 の `名前 = 値` 表記に沿う。§0 の「placeholder が残れば閉じる」という部分については、D1871 が開始時刻だけを例外にする根拠となる。責任者指名義務は `D:339-340,349-350` に残るため、行全体を免除する案 A は採らない。

拒否し続ける形の例：

1. `未記入`
2. `実行責任者 = 未記入、開始時刻 = 未記入`
3. `実行責任者 = 、開始時刻 = 未記入`
4. `実行責任者 = TBD、開始時刻 = 未記入`
5. `実行責任者 = x、開始時刻 = 未記入`
6. `実行責任者 = thawk105、開始時刻 = TODO`
7. `実行責任者 = thawk105、開始時刻 = 未記入（後日記入）`
8. `開始時刻 = 未記入、実行責任者 = thawk105`
9. `実行責任者 = thawk105、代理 = other、開始時刻 = 未記入`

責任者の空・sentinel 拒否は、この**追加受理経路**について保証する。従来検査は任意の非 sentinel セルの内部構造を解析しておらず、今回そこへ新しい一般的な責任者検査は追加しない。

## 2. 正例・負例テストの plan

追加位置はすべて **`T:482`、既存 `test_section5_source_cell_examples_and_expectation_bindings` の後、次のテストの前**。既存テスト・fixture の内容は変更しない。

`T:81-112` の `_section5_document(value_overrides=...)` を使用する。呼出しには既存の `_MODEL`、`_PROMPT` を渡す。以下の `target` は `"実行責任者・開始時刻"` の略記。

負例の共通 assert は既存 `T:61-68` に合わせる。

```python
_raises(
    A.B4AdmissionRecordError,
    lambda: A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
        document,
        expected_claude_model_snapshot=_MODEL,
        expected_effective_critic_prompt_sha256=_PROMPT,
    ),
    exact=_SECTION5_ERROR,
)
```

|関数名案（すべて `T:482` に追加）|fixture の override／assert|
|---|---|
|`test_section5_accepts_unrecorded_start_time_with_named_owner`|`{target: "実行責任者 = thawk105、開始時刻 = 未記入"}`。返却値について `assert dict(result) == _PROJECTIONS`。|
|`test_section5_rejects_whole_unrecorded_owner_start_cell`|`{target: "未記入"}`。共通拒否 assert。|
|`test_section5_rejects_unrecorded_owner_with_unrecorded_start`|責任者も `未記入`。共通拒否 assert。|
|`test_section5_rejects_empty_owner_with_unrecorded_start`|責任者を空文字・空白のみとするケースをループ。共通拒否 assert。|
|`test_section5_rejects_reserved_owner_with_unrecorded_start`|責任者を `TBD`、`ＴＢＤ`、`N/A`、`要記入`、`x`、`---` とするケースをループ。共通拒否 assert。|
|`test_section5_rejects_other_start_sentinels`|責任者を `thawk105` に固定し、開始時刻を `TODO`、`要記入` にする。共通拒否 assert。|
|`test_section5_rejects_unrecorded_start_suffix`|開始時刻を `未記入（後日記入）` にする。共通拒否 assert。|
|`test_section5_rejects_reordered_unrecorded_start_fields`|`開始時刻 = 未記入、実行責任者 = thawk105`。共通拒否 assert。|
|`test_section5_rejects_extra_owner_start_field`|責任者と開始時刻の間に `、代理 = other` を挿入。共通拒否 assert。|
|`test_section5_rejects_unrecorded_other_rows_with_optional_start`|対象行は正例の値にし、対象外 9 label を一つずつ `未記入` にする。各ケースで共通拒否 assert。|

既存 fixture は対象行にも `fixture-value-10` を入れる（`T:88-90`）。これを引き続き受理することは既存正例 `T:405-414` が確認する。

実文書は対象外の未記入欄で拒否されるため、正例には使わない。これは表と検査順序の**読解による判断**であり、変更後の実走結果ではない。

## 3. 追補の文面案と挿入位置

**挿入位置：`D:357` の直後、既存の空行 `D:358` の前。** 現行の追記に続けて、同じ二字下げで追加する。`D:359` の §5.1.0 見出し以降には触れない。

親が追加する文面案：

> **追補 (2026-09-16、[T-2464]、D1871。開始時刻の受理条件への反映)。**  
> 上の追記で未裁定としていた開始時刻と sentinel 規則の関係は、D1871 により、開始時刻を発効条件から外すものと確定した。受理側をこの裁定に合わせ、「実行責任者・開始時刻」欄の `実行責任者 = <値>、開始時刻 = 未記入` という形について、実行責任者の値が非空かつ既存の予約 sentinel に該当しない場合に限り、開始時刻の `未記入` を受理する。行 label 集合と、他の 9 欄に適用する §0 の原子性・sentinel 規則は維持する。  
> 本追補は受理側への裁定反映を記録するものであり、§5 の値セルへの記入権限を与えず、値セルを変更せず、本書の発効または B-4 正式標本の実走を認可しない。

§0、§5 表、§5.1.0、§5.1.1 の既存 bytes は保持する。

## 4. 波及の静的列挙

### 検索根拠と参照関係

repo 全体を対象に `rg` で公開関数、module 名、private symbol を検索した。Python 検索に加え、private symbol は拡張子を限定しない検索も行った。検索では Git 管理領域・`.claude`・成果物領域を除外している。

|参照元|関係|
|---|---|
|`A:788`|変更する検査関数の production 直接呼出し。`verify_b4_admission_record` 内。|
|`orchestrator/campaign/p3_b4_closed_critic.py:61,1268,1931`|verifier を import し、production pair 作成と certified pair 検査から呼ぶ。|
|`orchestrator/campaign/p3_b4_launcher.py:28,381`|verifier を import し、launcher から呼ぶ。|
|`orchestrator/campaign/p3_b4_closed_critic.py:104,646-647`|変更ファイルを `ADMISSION_VALIDATOR_FILE` として projection closure に含める。|
|`orchestrator/campaign/p3_b4_raw_record_producer.py:987,995`|`_projection_paths` が同じ admission validator ファイルを列挙する。|
|`T:408` ほか|変更関数を直接検査する。|
|`orchestrator/tests/test_p3_b4_closed_critic.py:796`、`test_p3_b4_launcher.py:108,698`|verifier の呼出し。|

private symbol の検索結果：

- `_RESERVED_SENTINEL_RE`、`_RESERVED_SENTINEL_WHOLE_VALUES`：production では `A` の定義と値走査だけ。
- `_normalized_source_cell`：production では `A:538` の定義、`A:659-660` の呼出しだけ。
- `_SECTION5_LABELS`：production では `A` の定義・表行数・label 集合検査だけ。テスト内の同名 tuple は独立定義。
- 今回、これらの private symbol 自体は変更しない。

**ファイル bytes の変更は projection closure のハッシュ入力も変える。** 根拠は上記のファイル列挙である。既存の束縛を緩めたり、§5 の値を更新したりする plan は含めない。

### 影響しうるテストと焦点走

まず次の 5 ファイルを焦点走の対象とする。

```text
orchestrator/tests/test_p3_b4_admission_record.py
orchestrator/tests/test_p3_b4_closed_critic.py
orchestrator/tests/test_p3_b4_launcher.py
orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py
orchestrator/tests/test_p3_b4_analysis_path.py
```

前半 3 件は検査経路、後半 2 件は文書追補と解析契約・receipt の不変確認に対応する。

参照検索で確認した間接影響候補も列挙する。

|test file（`orchestrator/tests/` 以下）|根拠行・関係|
|---|---|
|`test_p3_b4_raw_record_producer.py`|`:29,32,57` — critic、producer、critic fixture を参照。|
|`test_p3_b4_producer_auth_experiment.py`|`:27,326,365-374` — producer とそのテスト補助を参照。|
|`test_p3_b4_material_report.py`|`:24,27,30-31` — critic、producer、producer fixture を参照。|
|`test_p3_s4_loop.py`|`:44-45,912` — critic、launcher、critic fixture を参照。|
|`test_p3_s4_loop_sort.py`|`:31-32,47` — 同上。|
|`test_p3_s4_loop_trigger_gating.py`|`:34-35,156` — 同上。|
|`test_p3_b4_proposal_binding.py`|`:16` — launcher を参照。|
|`test_ccbench_spawn_sites.py`|`:173` — admission module の `_git_call` を列挙。|
|`test_t671_source_binding.py`、`test_artifact_admission.py`|`:83`、`:116` — launcher のソースパスを列挙。直接の変更関数参照ではない。|

projection closure を扱う後続確認には、上表の producer・material・3 driver loop テストを含める。実装後の実行は親の通常手順で `tools/run_tests.py` を通す。本段では実走していない。

## 5. §5.1.1 の SHA 不変の確認方法

読解上、指定位置への追補では raw/semantic SHA は変わらない。

1. `C:236-284` の `_headings` は文書を走査し、見出しの **byte offset** を求める。
2. `C:301-316` の `_locate_section` は、H4 で `5.1.1`・`分析契約`・`一括凍結` に一致する見出しを一意に選ぶ。
3. `C:317-321` は、その後に現れる最初の level ≤ 4 の見出しを終端にする。
4. `C:342` が切り出すのは `document_bytes[h4.start:end]`。現物では **`D:407` の見出しから `D:692` の §6 見出し直前まで**。
5. 追補位置 `D:358` は抽出開始より前である。追補によって開始・終了 offset は同じ byte 数だけ移動するが、切り出した bytes は同一となる。
6. raw SHA はその bytes、semantic SHA は同じ bytes から作った `_semantic_section_bytes` に基づく（`C:348-361,399-407`）。したがって双方とも不変。

親による追補後の確認方法は、変更前後の bytes をメモリ上で読み、次を比較する。新しい恒久テスト・gate は不要。

```python
before_section = _locate_section(before).raw_bytes
after_section = _locate_section(after).raw_bytes

assert before_section == after_section
assert sha256(after_section).hexdigest() == PREREGISTRATION_SECTION_5_1_1_SHA256
assert (
    sha256(_semantic_section_bytes(after_section)).hexdigest()
    == PREREGISTRATION_SECTION_5_1_1_SEMANTIC_SHA256
)
```

不変の前提が崩れる条件は、抽出範囲内の改行を含む bytes の変更、同じ fingerprint の H4 追加、または前方で未閉鎖の HTML comment／コード fence を作って見出し認識を変える場合である。提示した通常段落の追補はこれらを含まない。

**この前後 SHA 比較は本段では実行していない。** また、節 SHA と文書全体 SHA は別であり、追補で文書全体 SHA は変わる。`A:775-783` の文書束縛はそのまま維持する。

## 6. 変異事前登録の候補

下表の新規 test node はすべて `orchestrator/tests/test_p3_b4_admission_record.py::` に続く名前。変異箇所は §1 の `A:667-673` 置換部分である。

|変異：どこを何に書き換えるか|赤になるべき test node|
|---|---|
|追加受理分岐を削除して一律 sentinel 検査に戻す。|`test_section5_accepts_unrecorded_start_time_with_named_owner`|
|対象 label 分岐を無条件 `continue` にする。|`test_section5_rejects_whole_unrecorded_owner_start_cell`|
|例外適用から label 一致条件を外す。|`test_section5_rejects_unrecorded_other_rows_with_optional_start` だけでは殺せないため、この変異は下記補足の fixture を同 node に追加して殺す。|
|責任者の `bool(owner)` 条件を削除する。|`test_section5_rejects_empty_owner_with_unrecorded_start`|
|責任者の `_RESERVED_SENTINEL_RE.search(owner)` 条件を削除する。|`test_section5_rejects_reserved_owner_with_unrecorded_start`|
|責任者の whole-value sentinel 条件を削除する。|`test_section5_rejects_reserved_owner_with_unrecorded_start` の `x`／`---` ケース。|
|正規表現の開始時刻を `(?:未記入\|TODO)` に広げる。|`test_section5_rejects_other_start_sentinels`|
|`re.fullmatch` を `re.match` に替える。|`test_section5_rejects_unrecorded_start_suffix`|
|責任者 capture を `[^、=\r\n]+` から `.+` に替える。|`test_section5_rejects_extra_owner_start_field`|
|`_RESERVED_SENTINEL_RE` の既存定義から `未記入` を削除して全行へ緩和を波及させる。|`test_section5_rejects_unrecorded_other_rows_with_optional_start`|

**label 条件削除を殺す補足 fixture：** §2 の `test_section5_rejects_unrecorded_other_rows_with_optional_start` に、対象外の通常行、例えば `env_tag (実測環境)` へ正例と同じ文字列 `実行責任者 = thawk105、開始時刻 = 未記入` を置くケースも追加する。対象行も正例の値とし、共通拒否 assert を使う。これにより「構文だけで例外を全行に適用する」変異を捕捉する。

上記は変異と観測点の事前登録案であり、変異実走による kill は未確認である。