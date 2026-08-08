#!/bin/bash
set -Eeuo pipefail

readonly REPO_ROOT="/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation"
readonly TARGET="output/s8b-freeze/floor_protocol.json"
readonly RECEIPT="output/t080-migration/legacy-freeze-repin.receipt.json"
readonly ACTIVATION_RECORD="orchestrator/campaign/env_contract_activations/00000002.json"
readonly ACTIVATION_SOURCE="orchestrator/campaign/env_contract.py"
readonly BACKUP="/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/floor_protocol.pre-g2.json"
readonly OLD_SHA256="261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac"
readonly NEW_SHA256="c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d"
readonly G1_SHA256="e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01"
readonly G2_SHA256="1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c"

TMP_DIR=""
RESTORE_REQUIRED=0

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

cleanup_and_restore() {
    trap - EXIT
    trap '' HUP INT TERM

    local rc="$1"
    local direct_restore_failed=0
    local restore_failed=0
    local backup_actual_sha256=""
    local fallback_target_sha256=""
    local head_blob=""
    local index_blob=""
    local restore_tmp=""
    local restore_tmp_sha256=""
    local worktree_blob=""

    if [[ "$RESTORE_REQUIRED" -eq 1 ]]; then
        set +e
        printf '失敗または中断を検出: %s を HEAD へ復元します。\n' "$TARGET" >&2
        git restore --source=HEAD --staged -- "$TARGET" || direct_restore_failed=1
        git restore --source=HEAD -- "$TARGET" || direct_restore_failed=1

        if [[ "$direct_restore_failed" -ne 0 ]]; then
            printf 'HEAD からの直接復元に失敗: 検証済み backup から原子的復元を試みます。\n' >&2
            if [[ ! -f "$BACKUP" || -L "$BACKUP" ]]; then
                restore_failed=1
            elif ! backup_actual_sha256="$(sha256sum -- "$BACKUP")"; then
                restore_failed=1
            else
                backup_actual_sha256="${backup_actual_sha256%% *}"
                if [[ "$backup_actual_sha256" != "$OLD_SHA256" ]]; then
                    restore_failed=1
                elif ! restore_tmp="$(mktemp "$REPO_ROOT/${TARGET}.restore.XXXXXX")"; then
                    restore_failed=1
                elif ! cp --preserve=mode,timestamps -- "$BACKUP" "$restore_tmp"; then
                    restore_failed=1
                elif ! restore_tmp_sha256="$(sha256sum -- "$restore_tmp")"; then
                    restore_failed=1
                else
                    restore_tmp_sha256="${restore_tmp_sha256%% *}"
                    if [[ "$restore_tmp_sha256" != "$OLD_SHA256" ]]; then
                        restore_failed=1
                    elif ! mv -f -- "$restore_tmp" "$TARGET"; then
                        restore_failed=1
                    else
                        restore_tmp=""
                        if ! fallback_target_sha256="$(sha256sum -- "$TARGET")"; then
                            restore_failed=1
                        else
                            fallback_target_sha256="${fallback_target_sha256%% *}"
                            [[ "$fallback_target_sha256" == "$OLD_SHA256" ]] || restore_failed=1
                        fi
                    fi
                fi
            fi

            # staged restore が一時的に失敗した場合も、fallback 後に HEAD へ再同期する。
            git restore --source=HEAD --staged -- "$TARGET" || restore_failed=1
        fi

        if [[ -n "$restore_tmp" && -e "$restore_tmp" ]]; then
            rm -f -- "$restore_tmp" || restore_failed=1
        fi
        head_blob="$(git rev-parse "HEAD:$TARGET" 2>/dev/null)" || restore_failed=1
        index_blob="$(git rev-parse ":$TARGET" 2>/dev/null)" || restore_failed=1
        worktree_blob="$(git hash-object -- "$TARGET" 2>/dev/null)" || restore_failed=1
        if [[ -z "$head_blob" || "$index_blob" != "$head_blob" || "$worktree_blob" != "$head_blob" ]]; then
            restore_failed=1
        fi
        if [[ "$restore_failed" -ne 0 ]]; then
            printf 'CRITICAL: %s の HEAD 復元または blob 一致検査に失敗しました。\n' "$TARGET" >&2
            printf '手動復旧用 backup: %s\n期待 SHA-256: %s\n' "$BACKUP" "$OLD_SHA256" >&2
            rc=97
        else
            printf '復元完了: HEAD/index/worktree blob が一致しました (%s)。\n' "$head_blob" >&2
        fi
    fi
    if [[ -n "$TMP_DIR" ]]; then
        if [[ "$TMP_DIR" == /tmp/izanagi-reissue-floor.* && -d "$TMP_DIR" ]]; then
            rm -rf -- "$TMP_DIR" || rc=98
        else
            printf 'WARNING: 一時 directory の安全な除去条件を満たしません: %s\n' "$TMP_DIR" >&2
            rc=98
        fi
    fi
    exit "$rc"
}

trap 'cleanup_and_restore "$?"' EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

[[ -z "${PYTHONOPTIMIZE+x}" ]] || die "PYTHONOPTIMIZE が設定されています。検査を最適化で無効化しないでください。"
[[ -t 0 ]] || die "stdin が tty ではありません。人間の対話 shell から実行してください。"
[[ "$(pwd -P)" == "$REPO_ROOT" ]] || die "cwd が対象 worktree ではありません: $(pwd -P)"
if ! actual_root="$(git rev-parse --show-toplevel)"; then
    die "Git worktree root を取得できません。"
fi
[[ "$actual_root" == "$REPO_ROOT" ]] || die "Git worktree root が対象と一致しません: $actual_root"
if ! tree_status="$(git status --porcelain=v1 --untracked-files=all)"; then
    die "作業木状態を取得できません。"
fi
[[ -z "$tree_status" ]] || die "作業木が clean ではありません。"

[[ -f "$TARGET" && ! -L "$TARGET" ]] || die "floor protocol が通常ファイルとして存在しません: $TARGET"
if ! git ls-files --error-unmatch -- "$TARGET" >/dev/null 2>&1; then
    die "floor protocol が tracked file ではありません: $TARGET"
fi
if ! target_sha256="$(sha256sum -- "$TARGET")"; then
    die "floor protocol の sha256 を計算できません。"
fi
target_sha256="${target_sha256%% *}"
if ! head_target_sha256="$(git cat-file blob "HEAD:$TARGET" | sha256sum)"; then
    die "HEAD の floor protocol blob sha256 を計算できません。"
fi
head_target_sha256="${head_target_sha256%% *}"
[[ "$target_sha256" == "$head_target_sha256" ]] || die "floor protocol が HEAD blob と一致しません。"

# activation record と head 定数は working tree でなく HEAD の bytes を検査する。
if ! python3 - "$ACTIVATION_RECORD" "$ACTIVATION_SOURCE" "$G2_SHA256" <<'PY'
import sys

if sys.flags.optimize != 0:
    raise SystemExit(f"Python optimize flag must be 0, got {sys.flags.optimize}")

import ast
import json
import subprocess

record_path, source_path, g2_sha256 = sys.argv[1:]

def head_bytes(path: str) -> bytes:
    return subprocess.run(
        ["git", "cat-file", "blob", f"HEAD:{path}"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout

record = json.loads(head_bytes(record_path))
if type(record) is not dict:
    raise SystemExit(f"activation record must be an object, got {type(record).__name__}")
if record.get("activation_serial") != 2:
    raise SystemExit(f"activation_serial mismatch: {record.get('activation_serial')!r} != 2")
expected_state = "398b192013e0e3996ca225454049a14cb2866ef256b581fc3dfbfda02476bed8"
if record.get("activation_state_sha256") != expected_state:
    raise SystemExit(
        "activation_state_sha256 mismatch: "
        f"{record.get('activation_state_sha256')!r} != {expected_state}"
    )
rows = record.get("active_contracts")
if type(rows) is not list:
    raise SystemExit(f"active_contracts must be an array, got {type(rows).__name__}")
if not any(
    type(row) is dict
    and row.get("env_tag") == "pegasus"
    and row.get("generation") == 2
    and row.get("contract_sha256") == g2_sha256
    for row in rows
):
    raise SystemExit("active_contracts has no Pegasus generation=2 row bound to expected g2 sha256")

tree = ast.parse(head_bytes(source_path).decode("utf-8"), filename=source_path)
serial_values = []
state_values = []
for node in tree.body:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.target.id == "_ACTIVATION_HEAD_SERIAL":
            serial_values.append(ast.literal_eval(node.value))
        elif node.target.id == "_ACTIVATION_HEAD_STATE_SHA256":
            state_values.append(ast.literal_eval(node.value))
if serial_values != [2]:
    raise SystemExit(f"_ACTIVATION_HEAD_SERIAL definitions mismatch: {serial_values!r} != [2]")
expected_state_values = [record["activation_state_sha256"]]
if state_values != expected_state_values:
    raise SystemExit(
        f"_ACTIVATION_HEAD_STATE_SHA256 definitions mismatch: {state_values!r} != {expected_state_values!r}"
    )
PY
then
    die "HEAD の activation record serial=2 / head 定数 / Pegasus g2 束縛が一致しません。"
fi

if [[ "$target_sha256" == "$NEW_SHA256" ]]; then
    printf '実施済み: %s は期待する再発行後 SHA-256 と一致します。変更しません。\n' "$TARGET"
    exit 0
fi
[[ "$target_sha256" == "$OLD_SHA256" ]] || die "floor protocol が旧 SHA-256 とも新 SHA-256 とも一致しません。"

# 旧 bytes の独立 golden を、backup や target 除去より前に固定する。
if ! python3 - "$TARGET" "$OLD_SHA256" "$G1_SHA256" <<'PY'
import sys

if sys.flags.optimize != 0:
    raise SystemExit(f"Python optimize flag must be 0, got {sys.flags.optimize}")

import hashlib
import json
import pathlib

path = pathlib.Path(sys.argv[1])
expected_sha256 = sys.argv[2]
g1_sha256 = sys.argv[3].encode("ascii")
raw = path.read_bytes()

def reject_constant(token: str):
    raise ValueError(f"non-JSON constant: {token}")

def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key: {key}")
        out[key] = value
    return out

document = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
if len(raw) != 774:
    raise SystemExit(f"old floor byte length mismatch: {len(raw)} != 774")
actual_sha256 = hashlib.sha256(raw).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit(f"old floor sha256 mismatch: {actual_sha256} != {expected_sha256}")
g1_count = raw.count(g1_sha256)
if g1_count != 1:
    raise SystemExit(f"old floor g1 sha256 occurrence mismatch: {g1_count} != 1")
if type(document) is not dict:
    raise SystemExit(f"old floor document must be an object, got {type(document).__name__}")
if len(document) != 18:
    raise SystemExit(f"old floor key count mismatch: {len(document)} != 18")
expected_contract = g1_sha256.decode("ascii")
if document.get("contract_sha256") != expected_contract:
    raise SystemExit(
        f"old floor contract_sha256 mismatch: {document.get('contract_sha256')!r} != {expected_contract}"
    )
PY
then
    die "旧 floor protocol が独立 golden を満たしません。"
fi

if ! TMP_DIR="$(mktemp -d /tmp/izanagi-reissue-floor.XXXXXX)"; then
    die "一時 directory を作成できません。"
fi
[[ "$TMP_DIR" == /tmp/izanagi-reissue-floor.* && -d "$TMP_DIR" ]] || die "一時 directory が安全条件を満たしません。"
readonly T080_OUTPUT="$TMP_DIR/t080-verify.json"
readonly MESSAGE_FILE="$TMP_DIR/commit-message.txt"

# argparse の verify --path 形で rc と JSON payload の両方を検査する。
t080_rc=0
if python3 -m orchestrator.campaign.t080_freeze_migration verify --path "$RECEIPT" >"$T080_OUTPUT"; then
    t080_rc=0
else
    t080_rc=$?
fi
[[ "$t080_rc" -eq 0 ]] || die "T-080 receipt verify が rc=$t080_rc で失敗しました。"
if ! python3 - "$T080_OUTPUT" <<'PY'
import sys

if sys.flags.optimize != 0:
    raise SystemExit(f"Python optimize flag must be 0, got {sys.flags.optimize}")

import json
import pathlib

def reject_constant(token: str):
    raise ValueError(f"non-JSON constant: {token}")

def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key: {key}")
        out[key] = value
    return out

payload = json.loads(
    pathlib.Path(sys.argv[1]).read_bytes(),
    object_pairs_hook=unique_object,
    parse_constant=reject_constant,
)
if type(payload) is not dict:
    raise SystemExit(f"T-080 payload must be an object, got {type(payload).__name__}")
if payload.get("state") != "active-valid":
    raise SystemExit(f"T-080 state mismatch: {payload.get('state')!r} != 'active-valid'")
if payload.get("refusals") != []:
    raise SystemExit(f"T-080 refusals mismatch: {payload.get('refusals')!r} != []")
observation = payload.get("t080_freeze_migration_observation")
if type(observation) is not dict:
    raise SystemExit(
        "T-080 migration observation must be an object, "
        f"got {type(observation).__name__}"
    )
PY
then
    die "T-080 receipt の state/refusals/observation が発行前条件を満たしません。"
fi

readonly backup_parent="${BACKUP%/*}"
[[ "$BACKUP" != "$REPO_ROOT/"* ]] || die "backup が repo 内を指しています。"
[[ -d "$backup_parent" && -w "$backup_parent" ]] || die "backup directory が存在しないか書込み不能です: $backup_parent"
[[ ! -e "$BACKUP" && ! -L "$BACKUP" ]] || die "backup が既に存在します。上書きしません: $BACKUP"
if ! cp --no-clobber --preserve=mode,timestamps -- "$TARGET" "$BACKUP"; then
    die "旧 floor protocol の非破壊 copy に失敗しました。"
fi
[[ -f "$BACKUP" && ! -L "$BACKUP" ]] || die "backup が通常ファイルとして作成されませんでした。"
if ! cmp -s -- "$TARGET" "$BACKUP"; then
    die "backup bytes が旧 floor protocol と一致しません。"
fi
if ! backup_sha256="$(sha256sum -- "$BACKUP")"; then
    die "backup の sha256 を計算できません。"
fi
backup_sha256="${backup_sha256%% *}"
[[ "$backup_sha256" == "$OLD_SHA256" ]] || die "backup SHA-256 が旧 golden と一致しません。"

# ここから成功 commit までは、全ての失敗・signal で HEAD 復元を行う。
RESTORE_REQUIRED=1
if ! rm -- "$TARGET"; then
    die "create-only writer のための target 除去に失敗しました。"
fi
[[ ! -e "$TARGET" && ! -L "$TARGET" ]] || die "target が除去されていません。"

# stdin は一切 redirect せず、呼出元の tty を freeze-protocol へそのまま渡す。
if ! python3 -m orchestrator.campaign.s8b_floor_campaign freeze-protocol --confirm-user-freeze; then
    die "freeze-protocol が失敗しました。commit せず HEAD へ復元します。"
fi
[[ -f "$TARGET" && ! -L "$TARGET" ]] || die "再発行後 target が通常ファイルとして存在しません。"

# 新 bytes は独立 golden の全条件と、旧 JSON との差分 key 集合を満たさなければならない。
if ! python3 - "$BACKUP" "$TARGET" "$OLD_SHA256" "$NEW_SHA256" "$G1_SHA256" "$G2_SHA256" <<'PY'
import sys

if sys.flags.optimize != 0:
    raise SystemExit(f"Python optimize flag must be 0, got {sys.flags.optimize}")

import hashlib
import json
import pathlib

old_path, new_path = map(pathlib.Path, sys.argv[1:3])
old_expected_sha, new_expected_sha, g1_text, g2_text = sys.argv[3:]
g1 = g1_text.encode("ascii")
g2 = g2_text.encode("ascii")

def reject_constant(token: str):
    raise ValueError(f"non-JSON constant: {token}")

def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key: {key}")
        out[key] = value
    return out

def load(raw: bytes):
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)

old_raw = old_path.read_bytes()
new_raw = new_path.read_bytes()
old = load(old_raw)
new = load(new_raw)

if len(old_raw) != 774 or len(new_raw) != 774:
    raise SystemExit(f"floor byte length mismatch: old={len(old_raw)}, new={len(new_raw)}, expected=774")
old_actual_sha = hashlib.sha256(old_raw).hexdigest()
if old_actual_sha != old_expected_sha:
    raise SystemExit(f"old floor sha256 mismatch: {old_actual_sha} != {old_expected_sha}")
old_g1_count = old_raw.count(g1)
if old_g1_count != 1:
    raise SystemExit(f"old floor g1 sha256 occurrence mismatch: {old_g1_count} != 1")
expected_new_raw = old_raw.replace(g1, g2, 1)
if new_raw != expected_new_raw:
    raise SystemExit("new floor bytes are not the exact single g1-to-g2 replacement")
new_actual_sha = hashlib.sha256(new_raw).hexdigest()
if new_actual_sha != new_expected_sha:
    raise SystemExit(f"new floor sha256 mismatch: {new_actual_sha} != {new_expected_sha}")
if type(old) is not dict or type(new) is not dict:
    raise SystemExit(
        f"floor documents must be objects, got old={type(old).__name__}, new={type(new).__name__}"
    )
if len(old) != 18 or len(new) != 18:
    raise SystemExit(f"floor key count mismatch: old={len(old)}, new={len(new)}, expected=18")
if set(old) != set(new):
    raise SystemExit(f"floor key sets differ: old={sorted(old)!r}, new={sorted(new)!r}")
changed_keys = {key for key in old if old[key] != new[key]}
if changed_keys != {"contract_sha256"}:
    raise SystemExit(f"floor changed key set mismatch: {sorted(changed_keys)!r} != ['contract_sha256']")
if old["contract_sha256"] != g1_text:
    raise SystemExit(f"old contract_sha256 mismatch: {old['contract_sha256']!r} != {g1_text}")
if new["contract_sha256"] != g2_text:
    raise SystemExit(f"new contract_sha256 mismatch: {new['contract_sha256']!r} != {g2_text}")
PY
then
    die "再発行後 floor protocol が独立 golden を満たしません。commit しません。"
fi

if ! git diff --check -- "$TARGET"; then
    die "再発行差分が git diff --check を通りません。"
fi
if ! unstaged_paths="$(git diff --name-only --)"; then
    die "unstaged path 集合を取得できません。"
fi
[[ "$unstaged_paths" == "$TARGET" ]] || die "unstaged path が target 1 件だけではありません: $unstaged_paths"
if ! staged_before="$(git diff --cached --name-only --)"; then
    die "staged path 集合を取得できません。"
fi
[[ -z "$staged_before" ]] || die "発行前から staged path が存在します: $staged_before"
if ! untracked_paths="$(git ls-files --others --exclude-standard)"; then
    die "untracked path 集合を取得できません。"
fi
[[ -z "$untracked_paths" ]] || die "発行中に想定外の untracked path が現れました: $untracked_paths"

if ! git add -- "$TARGET"; then
    die "target の staging に失敗しました。"
fi
if ! staged_paths="$(git diff --cached --name-only --)"; then
    die "staged path 集合を取得できません。"
fi
[[ "$staged_paths" == "$TARGET" ]] || die "staged path が target 1 件だけではありません: $staged_paths"
if ! unstaged_after="$(git diff --name-only --)"; then
    die "staging 後の unstaged path 集合を取得できません。"
fi
[[ -z "$unstaged_after" ]] || die "staging 後に unstaged path が残っています: $unstaged_after"

if ! printf '%s\n\n%s\n' \
    '[T-657] reissue floor protocol for pegasus g2' \
    'AI-Agent: none' >"$MESSAGE_FILE"; then
    die "commit message file を作成できません。"
fi
if ! python3 - "$MESSAGE_FILE" <<'PY'
import sys

if sys.flags.optimize != 0:
    raise SystemExit(f"Python optimize flag must be 0, got {sys.flags.optimize}")

import pathlib

text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
paragraphs = text.rstrip("\n").split("\n\n")
if paragraphs[-1] != "AI-Agent: none":
    raise SystemExit(f"final commit-message paragraph mismatch: {paragraphs[-1]!r} != 'AI-Agent: none'")
trailer_count = sum(line.startswith("AI-Agent:") for line in text.splitlines())
if trailer_count != 1:
    raise SystemExit(f"AI-Agent trailer count mismatch: {trailer_count} != 1")
PY
then
    die "commit message の trailer が AI-Agent: none 1 行のみではありません。"
fi

if ! python3 tools/check_ai_provenance.py --message-file "$MESSAGE_FILE"; then
    die "commit message の provenance preflight が失敗しました。"
fi
if ! git commit --only -F "$MESSAGE_FILE" -- "$TARGET"; then
    die "floor protocol の単独 commit に失敗しました。"
fi

# commit 成功後にだけ復元 trap を解除し、直後に full-history provenance を監査する。
RESTORE_REQUIRED=0
trap - EXIT HUP INT TERM
full_audit_rc=0
if python3 tools/check_ai_provenance.py; then
    full_audit_rc=0
else
    full_audit_rc=$?
fi
if ! rm -rf -- "$TMP_DIR"; then
    die "commit 後の一時 directory cleanup に失敗しました: $TMP_DIR"
fi
TMP_DIR=""
[[ "$full_audit_rc" -eq 0 ]] || die "commit 直後の full-history provenance 監査が rc=$full_audit_rc で失敗しました。"

cat <<'EOF'
floor protocol の再発行と単独 commit が完了しました。
次は wave の別工程で、以下の pin を更新してから post-C 受入・変異を実施してください。
  - orchestrator/tests/test_frozen_artifacts.py: FROZEN_MANIFEST の floor protocol SHA-256
  - orchestrator/tests/test_s8b_protocol_builder.py: approved protocol bytes / freeze success の SHA-256
  - orchestrator/tests/test_s8b_floor_campaign.py: real seal E2E の protocol SHA-256、Pegasus g2 calibration SHA-256、contract SHA-256
更新値: protocol=c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d
        calibration=94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9
        contract=1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c
この script 自身は pin を更新していません。
EOF
