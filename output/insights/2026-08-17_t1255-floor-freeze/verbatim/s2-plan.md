結論は、親案 P1 を採用し、D460 を部分改訂するのが最小かつ安全です。D460 を維持したまま解決するには別の current pointer が必要になり、追加 artifact と新しい trust root が増えるため本 wave の不変条件に収まりません。

## 1. resolver の曖昧性解消

### 実装

`orchestrator/campaign/s8b_floor_campaign.py:882-901` の `resolve_current_floor_protocol` を次の順に変更します。

1. `root = Path(root)` の直後に `_head_commit_oid(root)` を厳密に 1 回だけ呼ぶ。
2. その OID を以下の双方へ渡す。

   - `_scan_floor_protocol_index_at_commit(root=root, commit_oid=head_commit)` (`:782-870`)
   - `_ccbench_gitlink(root, head_commit)` (`:904-922`)

3. index 全体から、各 record の `env_tag` に対する現行 env contract と `record.contract_sha256` が一致する候補集合 `C` を先に作る。
4. `C` の中だけから `record.ccbench_pin == HEAD gitlink` の集合 `E` を作る。index 全体から直接 `E` を作ってはならない。
5. 選択規則を以下に固定する。

   - `len(E) == 1`: その record を返す。
   - `len(E) == 0 and len(C) == 1`: 唯一の現行 contract record へ fallback する。
   - それ以外: `FloorCampaignError`。`current_count` と `head_exact_count` を message に含める。

この規則なら、現状の発行前 repository は fallback で legacy を返し、発行後は HEAD pin exact の versioned record を返します。stale contract が HEAD pin と一致しても `E` に入らず、辞書順、mtime、最大 pin、namespace 優先などは使いません。

公開 API は引き続き keyword-only の `root` だけです。`scan_floor_protocol_index` 自体の API や index の全件返却契約は変えません。

### テスト

`orchestrator/tests/test_s8b_protocol_builder.py:1001-1084` を次のケースへ組み替えます。

- `_head_commit_oid` が 1 回だけ呼ばれ、その同じ OID が private scan と `_ccbench_gitlink` に渡る。
- 現行 contract 2 件のうち HEAD pin exact が 1 件ならそれを返す。
- HEAD pin exact が無く、現行 contract が 1 件なら fallback する。
- 現行 contract が 2 件で HEAD pin exact が無ければ fail-closed。
- stale contract だけが HEAD pin exact でも、唯一の現行 contract recordへ fallbackする。
- stale exact があり、現行 contract が複数かつ exact なしなら、stale を選ばず fail-closed。
- 現行 contract 0 件は従来どおり拒否。
- resolver の引数が `root` だけである検査は維持。

既存テストは public `scan_floor_protocol_index` を mock していますが、実装後は private `_scan_floor_protocol_index_at_commit` と `_ccbench_gitlink` を mock する必要があります。

### D460 の改訂

新規 fragment は `docs/spool/decisions/2026-08-17-dev-wave-t1255-floor-freeze-1.md` とし、例えば `{{D:floor-protocol-head-pin-disambiguation}}` を使います。

撤回する内容:

- D460 の「選択条件に ccbench pin を入れてはならない」という絶対禁止。
- 同一 contract の複数 record は production で到達不能、という却下理由。

残す内容:

- 現行 env contract 一致が第一の必須条件。
- caller は path、contract、pin、env tag を渡せない。
- resolver は root だけから authority record を返す。
- consumer は再読 bytes を indexed SHAまたはraw bytesと照合する。
- zero match、曖昧な複数 match は fail-closed。
- caller 選択、辞書順、mtime、最大 pin、namespace 優先は禁止。

新しい決定は「HEAD pin は現行 contract 候補内だけの曖昧性解消に使い、exact が無い場合は現行 contract exact 1 件にだけ fallback」とします。D460 が記録した「legacy pin は今日の HEAD と違う」という実測事実は、fallback の必要理由として残します。

D460 を改訂しない代案は explicit current pointer の新設ですが、第二 artifact、更新手順、chain record、障害復旧、履歴検査が必要です。「新規 artifact 1 fileだけ」という今回の発行形にも反するため、採用しません。

## 2. T-419 (3) の配線分類

| 定数 | 分類と根拠 | 実装 |
|---|---|---|
| `s8b_ratified_freeze._SELECTOR_PROTOCOL_PATH` (`:76`, `:2677-2701`) | proof-chain の歴史錨定。`pre_oracle_head` の 100644 blob を hash 化し、selector journal の `expected_header.protocol_sha256` と照合する。 | 変更しない。resolver へ動かすと既存 journal の `selector-declaration-invalid` 受理 bit が変わる。 |
| `s8b_prediction_runner._PROTOCOL_PATH` (`:79`, `:1542-1548`) | proof-chain の歴史錨定。`pre_oracle_head:path` の bytes を承認定数からの再導出 bytes と比較し、その hash を journal binding (`:1469-1475`) に入れる。 | 変更しない。動かすと seal gate と journal header が変わり、ratified 側も動かさなければ新旧いずれかの chain が拒否される。 |
| `s8b_holdout_admission._PROTOCOL_REL` (`:64`, `:463-490`) | live 選択面。予約時に HEAD blobを読み、caller supplied protocol と比較し、hash を manifest、ledger、attemptへ束縛する (`:784-795`)。 | resolver 経由へ変更する。 |
| `s8b_holdout_freeze.FLOOR_PROTOCOL_REL` (`:46`) | 混合だが live 選択面ではない。`:1293-1341` は過去の official result の protocol hashとproto8を検証、`:1545` は closure 除外、`:1648-1651` は生成する v2 g1 証拠へ path/hashを記録する。 | 全使用箇所を legacy のまま残す。動かすと `result.protocol_sha256`、proto8、manifest検証の受理集合と candidate bytes、closure集合が変わる。 |
| `floor_campaign.sh:954` の `PROTOCOL_PATH` | live 選択面。`:971` の driver 引数、`:986-1037` の結果検証用再読、`:1107-1135` の job-result記録へ同じ値を流す。 | resolverを1回だけ呼び、その返値を3箇所で共有する。 |

### live 面の具体的変更

`orchestrator/campaign/s8b_holdout_admission.py:463-490`:

- 循環 import を避けるため `_authority` 内で `s8b_floor_campaign` を local importする。同 module は逆向きに holdout admission を import済みです。
- `resolve_current_floor_protocol(root=root)` を呼ぶ。
- `_head_blob(root, protocol_record.path)` で committed blobを読む。
- blob bytesと`protocol_record.raw_bytes`、SHA-256と`protocol_record.sha256`を照合する。
- その後に、現在の `protocol_document == dict(protocol)`、freeze path/hash、freeze documentの照合を維持する。
- resolver失敗、record型不正、indexed bytes不一致は、cell claim作成前に `HoldoutAdmissionError` として拒否する。

`orchestrator/campaign/s8b_floor_campaign.py:6566-6577,6689-6723`:

- caller引数を一切持たない `resolve-current-protocol` CLIを追加する。
- 成功時は resolver が返した sanctioned relative pathを1行だけ出力する。
- `--path`、`--contract-sha256`、`--ccbench-pin`、`--root` は argparseで拒否する。
- 失敗時は非0で、driverを起動しない。

`tools/pegasus/floor_campaign.sh:954-971`:

- literal代入を上記CLIの1回の呼出しへ置換する。
- resolver失敗は `floor_protocol_resolution` として記録し、`:967` の `floor-driver.launch-attempted` より前に終了する。
- 解決した relative pathを既存のdriver引数、metrics検証、job-resultへそのまま流す。

`orchestrator/campaign/s8b_floor_campaign.py:171` の `_FLOOR_PROTOCOL_REL` は変更しません。これは index anchor (`:788-817`)、reseal lineage (`:941-944`)、旧 human freeze destination (`:1284-1285`)、official proof-chainの歴史錨定です。pilot CLI自体は supplied pathを読み込むため (`:6749-6765`)、versioned pathを拒否しません。

### 配線テスト

- `orchestrator/tests/test_s8b_holdout_admission.py:87-103,520-530`

  - 簡略 fixture用には canonical resolverをmockし、HEAD blob由来の`IndexedFloorProtocol`を返す。
  - 専用ケースではversioned fileをcommitし、legacy working bytesを汚してもversioned recordで予約できることを検査。
  - record SHA不一致、supplied protocol不一致、resolver拒否がclaim作成前に止まることを検査。

- `orchestrator/tests/test_pegasus_floor_tools.py:810-816,1033-1083,1094-1120,2162-2228`

  - fake driverに `resolve-current-protocol` と実driver呼出しを区別させる。
  - resolver呼出し exact 1回、driver呼出し exact 1回を検査。
  - versioned pathが `--protocol`、metrics reader、job-resultの3箇所で同じであることを検査。
  - resolver非0時はlaunch marker、driver、job-resultを生成しないケースを追加。
  - `_driver_tail` と `_dependency_build_fragment` の開始・終了anchorを、削除されるliteralではなく新resolver blockへ更新。

- `orchestrator/tests/test_s8b_protocol_builder.py:1087-1116`

  現在の「全literalがresolver結果と一致する」テストは削除または改名し、次の分類契約へ置換します。

  - ratified freeze、prediction runner、holdout freeze、floor campaign lineage anchorはlegacyのまま。
  - holdout admissionとshellにはlive legacy literalが無い。
  - live面はresolver呼出しを持つ。

## 3. 発行、検証、commit手順

実装・テスト変更を先にstageし、発行前のunstaged/untracked集合を空にしておくと、issuerが変更したrepository面が新規1 fileだけだと機械確認できます。

```bash
set -euo pipefail

ROOT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1255-floor-freeze
JOB_DIR=/work/1/SFC/tanab/dev-wave-jobs/wave-t1255-floor-freeze
LEGACY=output/s8b-freeze/floor_protocol.json
CONTRACT=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
PIN=511c9538e4e8efa54b45cda62e72389ed3b706ec
ARTIFACT="output/s8b-freeze/floor-protocols/${CONTRACT}--${PIN}.json"
ARTIFACT_SHA=2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a
ISSUE_LOG="$JOB_DIR/reseal-protocol-output.json"

cd "$ROOT"
test ! -e "$ARTIFACT"
test ! -e "$ISSUE_LOG"

git add -- \
  orchestrator/campaign/s8b_floor_campaign.py \
  orchestrator/campaign/s8b_holdout_admission.py \
  tools/pegasus/floor_campaign.sh \
  orchestrator/tests/test_s8b_protocol_builder.py \
  orchestrator/tests/test_s8b_holdout_admission.py \
  orchestrator/tests/test_pegasus_floor_tools.py

git diff --quiet
mapfile -t PRE_UNTRACKED < <(git ls-files --others --exclude-standard)
test "${#PRE_UNTRACKED[@]}" -eq 0

python3 -I -B orchestrator/campaign/s8b_floor_campaign.py \
  reseal-protocol >"$ISSUE_LOG"

mapfile -t POST_UNTRACKED < <(git ls-files --others --exclude-standard)
test "${#POST_UNTRACKED[@]}" -eq 1
test "${POST_UNTRACKED[0]}" = "$ARTIFACT"
git diff --quiet
git diff --quiet -- "$LEGACY"
cmp "$LEGACY" <(git show "HEAD:$LEGACY")
```

field単位とbyte単位の双方を確認します。

```bash
python3 - "$LEGACY" "$ARTIFACT" "$PIN" "$CONTRACT" "$ARTIFACT_SHA" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

legacy_path, artifact_path, pin, contract, expected_sha = sys.argv[1:]

def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result

def reject_constant(token):
    raise ValueError(f"non-finite constant: {token}")

def load(path):
    raw = Path(path).read_bytes()
    document = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=no_duplicates,
        parse_constant=reject_constant,
    )
    return raw, document

legacy_raw, legacy = load(legacy_path)
artifact_raw, artifact = load(artifact_path)

if len(legacy) != 18 or set(legacy) != set(artifact):
    raise SystemExit("field集合が18 fieldで一致しない")

changed = sorted(
    key for key in legacy
    if legacy[key] != artifact[key]
)
if changed != ["ccbench_pin"]:
    raise SystemExit(f"ccbench_pin以外も変化した: {changed}")

if artifact["contract_sha256"] != contract:
    raise SystemExit("contract_sha256が期待値と不一致")
if artifact["ccbench_pin"] != pin:
    raise SystemExit("ccbench_pinがHEAD gitlinkと不一致")

expected = dict(legacy)
expected["ccbench_pin"] = pin
canonical = json.dumps(
    expected,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
if artifact_raw != canonical:
    raise SystemExit("legacy + ccbench_pin置換のcanonical bytesでない")

old_pin = legacy["ccbench_pin"].encode("ascii")
new_pin = pin.encode("ascii")
if legacy_raw.count(old_pin) != 1:
    raise SystemExit("legacy pinのbyte出現がexact 1でない")
if artifact_raw != legacy_raw.replace(old_pin, new_pin, 1):
    raise SystemExit("byte差がccbench_pinの40 bytes置換だけでない")

if len(artifact_raw) != 774:
    raise SystemExit(f"artifact size不一致: {len(artifact_raw)}")
if hashlib.sha256(artifact_raw).hexdigest() != expected_sha:
    raise SystemExit("artifact sha256不一致")
PY
```

indexとresolverを検証します。

```bash
INDEX_JSON="$(
  python3 -I -B orchestrator/campaign/s8b_floor_campaign.py \
    check-protocol-index
)"

python3 - "$INDEX_JSON" "$LEGACY" "$ARTIFACT" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
expected_paths = {sys.argv[2], sys.argv[3]}
actual_paths = {row["path"] for row in payload["protocols"]}

if payload.get("status") != "ok":
    raise SystemExit("index status不一致")
if payload.get("count") != 2:
    raise SystemExit(f"index count不一致: {payload.get('count')}")
if actual_paths != expected_paths:
    raise SystemExit(f"index path集合不一致: {actual_paths}")
PY

RESOLVED="$(
  python3 -I -B orchestrator/campaign/s8b_floor_campaign.py \
    resolve-current-protocol
)"
test "$RESOLVED" = "$ARTIFACT"

! grep -F -- "$ARTIFACT" orchestrator/tests/test_frozen_artifacts.py

git add -- "$ARTIFACT"
test "$(git diff --cached --name-only -- output/s8b-freeze)" = "$ARTIFACT"
git diff --cached --quiet -- "$LEGACY"
git diff --cached --quiet -- orchestrator/tests/test_frozen_artifacts.py
git diff --quiet
mapfile -t REMAINING_UNTRACKED < <(git ls-files --others --exclude-standard)
test "${#REMAINING_UNTRACKED[@]}" -eq 0
git diff --cached --check
```

親の関連走は直接pytestではなくrunner経由にします。

```bash
bash -n tools/pegasus/floor_campaign.sh

python3 tools/run_tests.py \
  orchestrator/tests/test_s8b_protocol_builder.py \
  orchestrator/tests/test_s8b_holdout_admission.py \
  orchestrator/tests/test_pegasus_floor_tools.py

python3 tools/run_tests.py \
  orchestrator/tests/test_campaign.py \
  -k floor_admission

python3 tools/run_tests.py \
  orchestrator/tests/test_real_repo_serialization.py \
  orchestrator/tests/test_hold_inventory.py \
  orchestrator/tests/test_growth_test_holds_contract.py

python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

その後、decision/worklog fragmentとinsightを明示的にstageし、provenance trailer入りのmessage fileでcommitします。

```bash
COMMIT_MESSAGE_FILE="$JOB_DIR/commit-message.txt"
test -s "$COMMIT_MESSAGE_FILE"

git add -- \
  docs/spool/decisions/2026-08-17-dev-wave-t1255-floor-freeze-1.md \
  docs/spool/worklog/2026-08-17-dev-wave-t1255-floor-freeze-1.md \
  output/insights/2026-08-17_t1255-floor-freeze

git diff --cached --check
git commit -F "$COMMIT_MESSAGE_FILE"

test -z "$(git status --porcelain=v1 --untracked-files=all)"
test "$(
  python3 -I -B orchestrator/campaign/s8b_floor_campaign.py \
    resolve-current-protocol
)" = "$ARTIFACT"

python3 tools/check_ai_provenance.py
```

issuer後の検査が失敗した場合は、artifactを自動削除せず、commitせずに停止します。`FROZEN_MANIFEST`への登録は行いません。

## 4. 発行で赤になる既存テストの完全一覧

省略なしの検索は、`orchestrator/campaign`、`orchestrator/tests`、`tools` に対する4語の横断grepで40 hitでした。実repo indexを読むnodeだけを分離すると、発行単独で赤になるのは次の2件です。

1. `orchestrator/tests/test_s8b_protocol_builder.py::test_current_floor_protocol_resolver_selects_exact_index_record`

   `:1015-1024` が現行 contract候補exact 1件、legacy path、HEAD pin不一致を固定しています。旧resolverでは発行直後に`count=2`で例外、新resolverではversionedを返した後にこの3 assertが破れます。

2. `orchestrator/tests/test_s8b_protocol_builder.py::test_floor_protocol_path_literals_match_current_resolver`

   `:1088` で実resolverを呼び、`:1116` で歴史錨定を含む6 literalすべてをresolver結果と同値にしています。発行後は旧resolverの`count=2`で落ち、新resolver後も歴史錨定をlegacyに残すためassertが落ちます。単純な期待値更新ではなく、前述の分類テストへ置換します。

親が候補にしていた次の2 parameter nodeは赤になりません。

- `...::test_build_and_write_leave_repo_tree_unchanged[top-level]`
- `...::test_build_and_write_leave_repo_tree_unchanged[nested]`

現HEADの`:1508-1529`には`len(index)==1`がありません。legacy pairの存在を検査し、追加recordは`floor-protocols/` prefixなら受理します。したがってindex 2件でも通ります。ここへ`len(index)==2`を新設するのも、将来のpin前進で壊れるため避けます。

逐語台帳もnode名を維持すれば変更不要です。

- `orchestrator/tests/conftest.py:170-175`
- `orchestrator/tests/growth_test_holds.py:468-475`
- `orchestrator/tests/test_hold_inventory.py:187-195,309-314`
- `orchestrator/tests/test_real_repo_serialization.py:38-42,1045-1098`
- 追加で見つかった独立oracle: `orchestrator/tests/test_growth_test_holds_contract.py:177-182`

`test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root`も上記関数を直接呼びますが、index件数を固定していないため赤になりません。`test_codex_worker_launch.py:1831`の`len(index)==1`はfailure archiveのJSONL indexであり、floor protocolとは無関係です。他のscan/resolver hitはtmp repositoryまたはmock indexを使うため、実artifact追加だけでは赤になりません。

なおテストnodeは実走していません。runnerのhelp確認も書込可能tmp不在でcollection前に停止しており、緑とは数えていません。作業ツリーへの変更はなく、最終`git status`はcleanです。

## 総括

- resolverは固定HEADを1回だけ解決し、現行contract候補内のHEAD pin exactを優先します。
- exactが無い場合は現行contract exact 1件だけへfallbackし、それ以外はfail-closedです。
- D460はpin絶対禁止と複数候補到達不能の部分だけを撤回し、caller非選択と現行contract優先を残します。
- resolverへ配線するlive面はholdout admissionとshell driverの2箇所だけです。
- ratified freeze、prediction runner、holdout freezeの歴史錨定と除外集合は動かしません。
- 発行artifactはlegacyからccbench_pinの40 bytesだけを置換した774 bytesとして機械検証します。
- 発行だけで赤になる既存nodeは2件で、`test_build_and_write_leave_repo_tree_unchanged`は赤になりません。