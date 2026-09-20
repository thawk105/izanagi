## 方針と P1〜P7 の判定

指定資料はすべて読取済み。以下の行番号は現 worktree の変更前の実物に対応する。新設関数の行番号は未確定なので、挿入先の既存行を示す。ファイル変更・pytest 実行は行っていない。

| 裁定 | 判定 | 実装への反映 |
|---|---|---|
| P1 | 支持 | sized・attempt-0002・D2172 項 2・2026-09-20 の定数 1 件だけを許す。source SHA は record から供給し、呼び手の SHA と照合する。 |
| P2 | 条件付き | schema・path・exact keys は支持。`_submission_intent_digest` の直接流用は不可。認可用 digest helper を別設する。 |
| P3 | 支持 | 認可 attempt の公開先を既存 leaf の兄弟 `<leaf>-attempt-0002` とする。 |
| P4 | 支持 | `authorize-rerun` を追加し、record だけを create-only で生成する。 |
| P5 | 支持 | record を走査前に検証し、既存の末尾 2 拒否だけを条件付きにする。 |
| P6 | 条件付き | **不在なら従来 leaf、不一致 record が存在すれば拒否**とする。「不一致でも従来 leaf」は P5 と依頼の不一致拒否に反するため採らない。 |
| P7 | 条件付き | 将来の観測にのみ適用する別版を支持。source commit による束縛と、専用の実行時 SHA 検査があることを混同しない。 |

変更する実装ファイルは driver と test の 2 本だけ。policy・契約・事前登録・既存追補・先行 attempt の証拠・公開物は変更しない。

## 1. 定数と record 形式

driver = `orchestrator/campaign/paper_story_a1_paired.py`。

既存の `V3_SIZED_STUDY_ID` は **100 行**であり、値は `paper-story-a1-20260901-balanced5-sized-v1`。schema 群は 108〜120 行、sized policy／事前登録の束縛定数は 202〜221 行にある。

120 行の schema 群直後に次を新設する。

```python
V3_RERUN_AUTHORIZATION_SCHEMA = (
    "paper-story-a1-paired-rerun-authorization/v1"
)
_V3_RERUN_AUTHORIZATION_KEYS = frozenset({
    "schema_version", "study_id", "attempt_root", "source_commit",
    "decision", "authorization_sha256",
})
```

221 行の sized 定数の直後、222 行の certificate 用コメントより前に新設する。

```python
V3_SIZED_RERUN_AUTHORIZATIONS = frozenset({
    (V3_SIZED_STUDY_ID, "attempt-0002", "D2172", 2, "2026-09-20"),
})
```

構造は `(study_id, attempt_name, decision_id, decision_item, decided_on)` の immutable な集合とする。record 自体に独立した `attempt_name` key は追加せず、`attempt_root` と filename から照合する。

record の形は次の 6 keys に固定する。

```json
{
  "schema_version": "paper-story-a1-paired-rerun-authorization/v1",
  "study_id": "paper-story-a1-20260901-balanced5-sized-v1",
  "attempt_root": "<durable base>/attempt-0002",
  "source_commit": "<lowercase 40-hex SHA>",
  "decision": {
    "id": "D2172",
    "item": 2,
    "decided_on": "2026-09-20"
  },
  "authorization_sha256": "<lowercase 64-hex digest>"
}
```

`source_commit` は先行 attempt の SHA ではなく、今回の fresh submit-tree の確定 SHA とする。実 base log にある attempt-0001 の `d2ebef7a…` を新 record に転記しない。

## 2. record の読取・照合 helper

2672 行の rear gate 直前に、新 helper を置く。

```python
def _has_exact_v3_rerun_authorization(
    base: Path, *, study_id: str,
    current_attempt: Path, source_commit: str,
) -> bool:
    ...
```

返値の契約は、**record 不在だけ `False`、完全一致だけ `True`、存在する不正 record は `PaperStoryError`**。

処理順を固定する。

1. `path = base / f"{current_attempt.name}.authorization.json"`。
2. `os.path.lexists(path)` が偽なら `False`。dangling symlink を「不在」にしない。
3. `lstat()` を行い、symlink または非 regular file は拒否する。stat 失敗も拒否する。
4. `_read_json(path)` を使って読む。既存 helper は 489〜501 行で duplicate key・非 JSON 定数・非 object root を拒否する。読取エラーを捕捉し、認可 record の corrupt エラーへ包む。
5. top-level key 集合と `decision` の key 集合を exact に検証する。
6. 型・digest・対象 identity・定数を検証し、一致した場合だけ `True`。

型検査は次を明示する。

- `schema_version`, `study_id`, `attempt_root`, `source_commit`, `authorization_sha256` は `type(x) is str`。
- `decision` は `type(x) is dict`、keys は `{"id", "item", "decided_on"}`。
- `decision.id`, `decision.decided_on` は文字列。
- `type(decision["item"]) is int`。`True == 1` 等の Python の等値性に依存しない。
- source は `_FULL_OID.fullmatch(...)`、digest は `_FULL_SHA256.fullmatch(...)`。定義は **323〜324 行**。
- 日付は定数との完全一致で固定するため、別の日付パーサは追加しない。

照合する述語は以下。

```python
record["schema_version"] == V3_RERUN_AUTHORIZATION_SCHEMA
record["attempt_root"] == os.fspath(current_attempt)
record["study_id"] == study_id
record["source_commit"] == source_commit

(
    record["study_id"],
    current_attempt.name,
    record["decision"]["id"],
    record["decision"]["item"],
    record["decision"]["decided_on"],
) in V3_SIZED_RERUN_AUTHORIZATIONS
```

`attempt_root` は resolve してから比較せず、入力文字列を exact 比較する。caller 側の canonical／base 直下検証と組み合わせることで、filename stem・root basename・current attempt 名を一致させる。

エラーは用途別に分ける。

| 状況 | message 案 |
|---|---|
| symlink・非 regular・stat 失敗 | `rerun authorization record is unsafe: ...` |
| JSON・key 集合・型・正規表現・self digest 不正 | `rerun authorization record is corrupt: ...` |
| schema／attempt／study／source／定数との不一致 | `rerun authorization record differs: <field>` |

schema の型違いは corrupt、文字列として別 schema なら differs とする。検査エラーを `False` に変換しない。

**digest は別 helper が必要。** 2926〜2933 行の `_submission_intent_digest` は `intent_sha256` だけを除外するため、認可 record を渡すと `authorization_sha256` 自体を hash 対象に含めてしまう。

同関数の隣に `_rerun_authorization_digest(value)` を追加し、同型の短い実装にする。

```python
payload = dict(value)
supplied = payload.pop("authorization_sha256", None)
# supplied があれば str / _FULL_SHA256 を検査
return _sha256_bytes(_canonical_json_bytes(payload))
```

canonicalization は既存の **518〜528 行**、hash は **531〜532 行**を使う。汎用 digest framework や既存 intent helper の API 変更は不要。

## 3. rear gate と submit の変更

`_assert_no_prior_v3_bench_start` の **2672〜2674 行**に必須 keyword を追加する。

```python
base: Path, *, study_id: str, current_attempt: Path,
source_commit: str,
```

2676 行の `try: entries = tuple(base.iterdir())` より前で、認可 helper を呼ぶ。

```python
authorized = _has_exact_v3_rerun_authorization(
    base, study_id=study_id,
    current_attempt=current_attempt, source_commit=source_commit,
)
```

一致しても return しない。変更する拒否述語は次の 2 箇所だけ。

- **2901〜2908 行**：`if not authorized and (既存の3条件):`
- **2909〜2919 行**：`if not authorized and same_study_intent and (既存条件):`

候補ごとの `continue` も追加しない。後続候補の破損検査まで実行する。

保存する範囲は **2683〜2900 行**。具体的には intent の unsafe／corrupt（2688〜2717）、prior／barrier（2730〜2735）、ready（2739〜2805）、bench-go（2811〜2848）、bench-start（2852〜2898）の検査を変更しない。2676〜2681 行の base 列挙エラー処理も維持する。

呼び手は **3234〜3236 行**だけを変更する。

```python
_assert_no_prior_v3_bench_start(
    attempt.parent, study_id=study_id, current_attempt=attempt,
    source_commit=expected_head,
)
```

**3225〜3233 行**の intent／attempt root／receipt namespace 再使用拒否は維持する。認可が存在してもここを通過できない。

record 不在で先行 bench 証拠も無い場合の初回投入は従来どおり受理する。「record 不在は拒否」は、先行証拠による rerun 禁止を解除できないという意味であり、全初回投入への認可必須化ではない。

## 4. 公開先 gate

**8264〜8267 行**を、既存位置引数を保ったまま拡張する。

```python
def _exact_materialization_destination(
    repo_root: Path, raw: Path,
    policy: Mapping[str, object] | None = None,
    *,
    attempt: Path | None = None,
    base: Path | None = None,
    source_commit: str | None = None,
) -> Path:
```

既存の relative 読取 **8270〜8279 行**の後、expected 計算 **8280 行**の前に処理を追加する。

- 追加引数がすべて `None`：従来動作。
- 一部だけ指定：不完全な context として拒否する。
- すべて指定：policy 必須。`base == _durable_measurement_base(policy)` を確認し、`_validate_attempt_root(attempt, base)` を使う。
- `_has_exact_v3_rerun_authorization(...)` を `_policy_study_id(policy)` と渡された source で呼ぶ。
- 一致時だけ `relative = relative.with_name(f"{relative.name}-{attempt.name}")`。

別 attempt 名を理由に reader を呼ばず return する分岐は作らない。その attempt の path に存在する不一致 record も拒否する。

認可済み attempt では兄弟 leaf **だけ**を expected とする。旧 leaf と兄弟 leaf の二者択一にはしない。

**8281〜8286 行**の exact 比較・`lexists` による既存宛先拒否・親 dir 実在検査は維持する。現行 policy の relative path は JSON **31 行**：

```text
output/insights/2026-09-13/paper-story-a1-balanced5-sized
```

従って新公開先は次になる。

```text
output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002
```

`_run_materialize_v3` の **8732〜8734 行**に追加する。

```python
attempt=attempt,
base=_durable_measurement_base(policy),
source_commit=args.expected_head,
```

attempt は **8695〜8696 行**の receipt roots から得る。source に receipt 内の任意の値や先行 attempt の SHA を代用しない。

非 v3 の **8875〜8877 行**は変更しない。既存の raw/source/WAL 検証と、**8757〜8762 行**の bundle publication 呼出しも変更しない。

## 5. producer `authorize-rerun`

`run_submit` の **3396 行**直前に `run_authorize_rerun(args) -> int` を新設する。argv は全項目必須。

```text
authorize-rerun
  --study-id paper-story-a1-20260901-balanced5-sized-v1
  --attempt-root <durable-base>/attempt-0002
  --expected-head <40-hex source commit>
  --decision D2172
  --decision-item 2
  --decided-on 2026-09-20
```

処理順：

1. `_load_policy_for_study(args.study_id)`（1780〜1782 行）。
2. `_durable_measurement_base(policy)`（2454〜2465 行）。
3. `_validate_attempt_root(Path(args.attempt_root), base)`（2468〜2486 行）。
4. source の型／`_FULL_OID` と、policy study・attempt 名・decision 3 field の定数 membership を検証する。CLI の study と policy study も一致させる。
5. `_attempt_intent_path(attempt)`（2922〜2923 行）、attempt root、authorization path のいずれかが `lexists` なら拒否する。
6. base の実在する directory を要求する。今回の実 base は既存なので、新規 base 作成を producer の役割に含めない。
7. record を組み立て、認可 digest helper で self digest を付ける。
8. `_exclusive_write(record_path, record)`、`_fsync_directory(base)`。
9. 成功時 `0`。

`_exclusive_write` は **842〜859 行**で `O_EXCL`／利用可能なら `O_NOFOLLOW`、file fsync を行う。directory fsync は **8290〜8298 行**。producer 固有のエラーは `PaperStoryError` とし、fsync の `OSError` も同例外へ包む。書込後失敗時に record を削除して再実行可能にはしない。

`--expected-head` は record へ束縛する source SHA として検査・保存する。producer に submit の hydration／CCBench／qsub 前提を持ち込まない。実 HEAD との一致は既存 `run_submit` **3403〜3404 行**で再確認される。

`_parser` **8912 行**の submit 登録の隣に subcommand を追加し、`--decision-item` は `type=int`。`main` **8945〜8952 行**に明示分岐を追加する。既存の例外時 stderr／返値 `2`（8953〜8955 行）を使う。

## 6. test の構成と DW-C01

test file = `orchestrator/tests/test_paper_story_a1_paired.py`。

fixture の現物は以下。

- `_v3_pilot_policy`：**255〜256 行**。
- sized policy を返す既存 fixture：**`sized_certificate_copy`、1113〜1125 行**。返値は `(policy, certificate, certificate_path)` であり、単純な `_v3_sized_policy` helper は存在しない。
- sized policy の直接ロード先例：**1137〜1138 行**。
- bench-go／ready-triple fixture：**4208〜4258 行**。
- 公開先 test：`test_materialization_is_exact_leaf_and_noreplace_publish`、**2485 行**。

新 test の policy は `copy.deepcopy(paired.load_policy(paired.V3_SIZED_STUDY_ID)[0])` を使い、必要な test 内コピーの base だけ tmp に置換する。certificate 改変をしない test で `sized_certificate_copy` の副作用まで利用する必要はない。

**4275 行の後**に `_rerun_prior_barrier_fixture` を新設し、4208〜4258 行の形を移植する。prior 名を `attempt-0001`、study を sized にし、bench-go／ready-triple を選択可能にする。元の pilot test の意味は変えない。

record fixture は production producer を使わず、test 側で JSON を構成する。digest も test 側の `json.dumps(ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"` と `hashlib.sha256` で独立算出する。identity 変更負例では digest を再計算し、digest 不正で偶然落ちることを避ける。

以下は新設 **26 test 関数**の名前と docstring 内容。各行の「受理」「拒否」をそのまま **2 文**の docstring にする。parameterization の各 case は独立した tmp namespace を使う。

| test 名 | 受理の文 | 拒否の文 |
|---|---|---|
| `test_rerun_authorization_accepts_exact_record` | 受理: 正常な先行 barrier と一致 record を持つ attempt-0002 は通過する。 | 拒否: 認可のない同一 study の反復は通過しない。 |
| `test_rerun_authorization_rejects_absent_record` | 受理: 一致 record は先行 bench の禁止だけを解除する。 | 拒否: record 不在では group rerun を拒否する。 |
| `test_rerun_authorization_rejects_other_attempt` | 受理: filename と root と定数の attempt-0002 が一致する。 | 拒否: 別 attempt または filename と root の不一致を拒否する。 |
| `test_rerun_authorization_rejects_other_study` | 受理: sized の record と呼出し study が一致する。 | 拒否: 別 study または呼出しとの不一致を拒否する。 |
| `test_rerun_authorization_rejects_other_source` | 受理: record の source が渡された SHA と一致する。 | 拒否: 別の有効な source SHA を拒否する。 |
| `test_rerun_authorization_rejects_other_decision` | 受理: D2172 項 2 と裁定日が完全一致する。 | 拒否: decision の各 field の単独変更を拒否する。 |
| `test_rerun_authorization_rejects_bad_digest` | 受理: canonical payload の digest が一致する。 | 拒否: 形が正しい別 digest を拒否する。 |
| `test_rerun_authorization_rejects_unsafe_file` | 受理: regular file の record を読める。 | 拒否: symlink と非 regular file を拒否する。 |
| `test_rerun_authorization_rejects_extra_keys` | 受理: 登録された key 集合だけを持つ。 | 拒否: top-level または decision の余分な key を拒否する。 |
| `test_rerun_authorization_rejects_corrupt_json` | 受理: 一意な keys の JSON object を読める。 | 拒否: 壊れた JSON と重複 key を拒否する。 |
| `test_rerun_authorization_rejects_bad_shape` | 受理: schema と各 field の型および hash 形式が正しい。 | 拒否: schema 違いと欠落および型と hash 形式の不正を拒否する。 |
| `test_rerun_authorization_preserves_prior_integrity` | 受理: 認可済みでも正常な先行証拠を検査する。 | 拒否: 一致 record があっても corrupt な先行 ready を拒否する。 |
| `test_rerun_materialization_accepts_authorized_sibling` | 受理: 一致 record の attempt は未存在の兄弟公開先を使う。 | 拒否: 認可済み attempt の旧 leaf 指定は拒否する。 |
| `test_rerun_materialization_rejects_sibling_without_record` | 受理: record 不在なら従来の未存在 leaf を使う。 | 拒否: record 不在の兄弟公開先を拒否する。 |
| `test_rerun_materialization_rejects_existing_exact_leaf` | 受理: 従来 leaf は未存在なら受理する。 | 拒否: record 不在でも既存の exact leaf は拒否する。 |
| `test_rerun_materialization_rejects_existing_sibling` | 受理: 認可された兄弟公開先は未存在なら受理する。 | 拒否: 一致 record があっても既存の兄弟公開先を拒否する。 |
| `test_rerun_materialization_rejects_mismatched_record` | 受理: 公開時にも record の全 identity が一致する。 | 拒否: 不一致 record を旧 leaf への fallback に使わない。 |
| `test_rerun_materialization_requires_parent` | 受理: 公開先の親 directory が実在する。 | 拒否: 認可済みでも親 directory 不在を拒否する。 |
| `test_rerun_materialization_preserves_legacy_call` | 受理: 追加引数のない呼出しは従来の exact leaf を受理する。 | 拒否: 従来呼出しで別 leaf を拒否する。 |
| `test_authorize_rerun_is_create_only` | 受理: 初回生成は正しい record と返値 0 を得る。 | 拒否: 2 回目は既存 bytes を保持して拒否する。 |
| `test_authorize_rerun_rejects_constant_mismatch` | 受理: 定数の study と attempt と裁定だけを生成する。 | 拒否: attempt-0003 と別 study および別裁定を拒否する。 |
| `test_authorize_rerun_rejects_existing_intent` | 受理: intent のない namespace に生成する。 | 拒否: 既存 intent があれば record を作らない。 |
| `test_authorize_rerun_rejects_existing_attempt` | 受理: attempt root のない namespace に生成する。 | 拒否: 既存 attempt root があれば record を作らない。 |
| `test_authorize_rerun_rejects_invalid_source` | 受理: lowercase 40-hex の source を保存する。 | 拒否: 不正な source では record を作らない。 |
| `test_submit_v3_passes_authorization_context` | 受理: submit の policy と attempt と expected head が実 gate へ届く。 | 拒否: source 不一致は intent 生成前に拒否する。 |
| `test_materialize_v3_passes_authorization_context` | 受理: receipt の attempt と policy と expected head が実公開先 gate へ届く。 | 拒否: source 不一致は bundle 公開前に拒否する。 |

配置は公開先 7 本を既存公開先 test の隣、その他 19 本を 4275 行後の新 fixture 群とともに置く。既存関数を途中で分断しない。

追加の case 設計：

- 正例は bench-go と ready-triple の両方を parameterize する。
- 別 attempt は、current／record とも attempt-0003 の case と、filename が attempt-0002 で record root が attempt-0003 の case を持つ。
- 別 study は、record だけ別 study と、caller／record とも別 study の両 case を持つ。後者の先行証拠も同 study にし、実際に禁止対象にする。
- unsafe は通常 symlink、dangling symlink、directory。
- integrity は正常な ready fixture の `recorded_epoch` だけを `0` に変更し、`prior ready evidence is corrupt` を要求する。
- materialize 不一致は attempt／study／source／decision／digest を parameterize する。
- producer 正例は `main(argv)` 経由で parser と dispatch も検証し、record 全体と独立算出 digest を確認する。失敗例では record 非作成を確認する。

既存 3 本への変更は以下だけ。

| 既存 test | 呼出し行 | 追加 |
|---|---:|---|
| `test_mf2_prior_same_study_bench_start_blocks_new_attempt_M4` | 4202〜4205 | `source_commit="a" * 40` |
| `test_f1_prior_bench_barrier_blocks_with_empty_or_missing_start_M8` | 4262〜4265 | 同上 |
| `test_f1_first_submit_has_no_prior_attempt_and_is_accepted_M8` | 4271〜4275 | 同上 |

これらにも不足する DW-C01 の 2 文 docstring を付ける。

## 7. 変異候補と kill の帰属

全負例で、狙った field 以外は正常にする。identity の変更後は digest を再計算し、例外 message も照合する。

| 変異 | 1 理由で kill する test |
|---|---|
| (a) record 不在でも解除 | `test_rerun_authorization_rejects_absent_record` |
| (b) attempt 名の照合を除去 | `test_rerun_authorization_rejects_other_attempt` の current／record とも attempt-0003 case |
| (c) study_id の照合を除去 | `test_rerun_authorization_rejects_other_study` の caller／record とも別 study case |
| (d) source_commit の照合を除去 | `test_rerun_authorization_rejects_other_source` |
| (e) decision の定数照合を除去 | `test_rerun_authorization_rejects_other_decision` の ID 単独変更 case |
| (f) record 一致時に完全性検査を skip | `test_rerun_authorization_preserves_prior_integrity` |
| (g) 公開先 create-only を除去 | `test_rerun_materialization_rejects_existing_sibling` |
| (h) record 無しで兄弟公開先を受理 | `test_rerun_materialization_rejects_sibling_without_record` |
| (i) producer create-only を除去 | `test_authorize_rerun_is_create_only` |
| (j) self digest 照合を除去 | `test_rerun_authorization_rejects_bad_digest` |

(b) の filename／field 不一致と (c) の caller／record 不一致も、それぞれ別 case で対応する。これにより「定数 membership だけ残っていた」「caller 比較だけ残っていた」という取り違えを分離できる。

(i) は変異の具体化に注意が必要。producer の事前 `lexists` と `_exclusive_write` の `O_EXCL` は二重の拒否である。片方だけを消しても既存 record は拒否されるため、それを「producer create-only を解除した変異」と報告しない。再作成を可能にする関数内の意味的変異として登録するか、片側除去が等価であることを記録する。共有 `_exclusive_write` 自体の変更は不要。

**両層 stub について：** reader と gate の両方を stub した test だけでは、無条件受理の実装でも緑になりうる。本 plan の gate／公開先 test は双方を実関数で実行し、record も実 tmp file とする。

配線 test では以下に限定する。

- submit：実 `_run_submit_v3` → 実 rear gate → 実 reader を通す。通過後の `_v3_group_intent`（3237 行）に sentinel を置き、qsub へ進めない。source 不一致では sentinel 未到達を確認する。
- materialize：既存の前段検証を通過させるための seam は使用可能だが、実公開先 gate と reader は stub しない。`_publish_materialization_bundle`（8757 行）を捕捉し、正例の兄弟宛先と負例の未到達を確認する。

この 2 本は配線の焦点 test であり、stub した前段を含む end-to-end 証明とは報告しない。実 base 複製による親の実走を別の証拠として残す。

## 8. 親が書く docs

実装子は次の docs を編集しない。

`output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md`：

- 冒頭に `authority: preregistration-amendment`、`default_effect: no-state-change`、study、D2172 項 2／裁定日、将来の attempt-0002 に限る適用範囲。
- 元の事前登録・policy・source 契約 v2・既存 source 追補を参照し、凍結 bytes と attempt-0001 の判定を保存する。
- §6.1 追補：同じ durable base、認可 record の場所、兄弟公開先の exact 規則、create-only、先行 leaf に追記しないこと。
- §6.4 追補：同 seed・同物理順の独立観測 1 attempt。従来の bench 前失敗理由の閉じた列挙を編集せず、性能出力による再走正当化・anomaly 後の再試行を許さない。
- intent／attempt namespace の再使用拒否、先行証拠完全性、非認証 lane、既存限定を保存する。
- 本追補を含む確定 source commit を record に記載し、submit／materialize の expected head と一致させる。
- record と self digest は電子署名でも性能値を見た後の選択を防ぐ装置でもないことを限界として記す。
- 投入・結果・図は別 wave であり、追補の成立を測定完了と表現しない。

形式は読取済みの `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md` に倣うが、その bytes・適用範囲を変更しない。

`output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` には、brief／plan／相談／裁定／レビュー／変異台帳／親の test と実 base 複製実走を記録する。実 base への書込や投入を行ったかのように記述しない。

## 9. DW-O13：入力の実在と配線

| field | submit 時の実在箇所 | materialize 時の実在箇所 | 新照合への経路 |
|---|---|---|---|
| study_id | `args.study_id` 3399 行、policy load 3400 行、`_run_submit_v3` の `study_id` 3213 行 | result から policy load 8775 行、`study_id` 8776 行、v3 へ policy を渡す 8780〜8781 行 | 両 gate で policy 由来 study と record、および定数を照合 |
| attempt 名 | `args.attempt_root` を検証した `attempt` 3409 行、v3 へ渡す 3421 行 | receipt roots 8695 行、`attempt = Path(...)` 8696 行 | `attempt.name` と record root exact 比較、定数 membership |
| source_commit | `args.expected_head` の HEAD 比較 3403 行、v3 へ渡す 3421 行、仮引数 `expected_head` 3209 行 | `args.expected_head` を acquisition 検証 8711 行、completion 検証 8718 行、source 検証 8729 行で使用 | submit 3234 行と materialize 8732 行の呼出しへ明示追加 |
| decision | **既存 submit 入力には無い** | **既存 materialize 入力には無い** | 新 reader の record 内 3 fields と新定数を照合。consumer CLI に追加しない |
| durable base | policy から 3408 行、rear gate へ `attempt.parent` 3235 行 | policy は v3 仮引数 8687 行に実在 | 公開先 call に `_durable_measurement_base(policy)` を追加 |

decision は producer の新 argv から record に保存され、その後は両 consumer が同じ record を読む。既存 receipt に decision が保存されているという前提は置かない。

## 総括

変更面は次のとおり。行はすべて変更前の実物アンカー。

| file | 関数／変更面 | 行 |
|---|---|---:|
| driver | schema・認可定数 | 120 後、221 後 |
| driver | 新 record reader | 2672 前 |
| driver | `_assert_no_prior_v3_bench_start` | 2672〜2676、2901〜2919 |
| driver | 新認可 digest helper | 2926〜2933 の隣 |
| driver | `_run_submit_v3` | 3234〜3236 |
| driver | 新 `run_authorize_rerun` | 3396 前 |
| driver | `_exact_materialization_destination` | 8264〜8280 |
| driver | `_run_materialize_v3` | 8732〜8734 |
| driver | `_parser`／`main` | 8912 付近、8945〜8952 |
| test | 公開先 7 test | 2485 の既存 test の隣 |
| test | 既存 gate 3 test の引数・docstring | 4182〜4275 |
| test | fixture・gate 12／producer 5／配線 2 test | 4275 後 |
| 親 docs | 追補 README・認可実装記録 README | 新規、行番号未確定 |

**追加 test は 26 関数、既存修正は 3 関数。** parameterize 後の実行件数は author が確定する。静的読解のみで、test の合否は未確認。

open questions は親の段 4 で次を確定する。

- **Q1：P6 の不一致処理。** 推奨は「不在のみ従来 leaf、存在する不一致 record は拒否」。P5 と依頼の不一致拒否に整合する。
- **Q2：P7 の束縛の表現。** 推奨は追補を含む source commit の一致を指す表現。専用の追補 file digest 検査を追加したとは称さない。
- **Q3：変異 (i) の単位。** 推奨は producer の再作成を実際に可能にする意味的変異。二重拒否の片側削除だけなら、等価性を記録して kill 成功と数えない。