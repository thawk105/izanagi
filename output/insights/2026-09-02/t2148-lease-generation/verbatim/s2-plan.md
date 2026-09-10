## 候補の列挙

判定基準は次の 4 点とする。

- 1 回の lease 取得中は値が安定する。
- 同じ wave、同じ main でも、再取得時には別値になり得る。
- 署名主体と着地側が、呼び手の自己申告だけに頼らず同じ取得を照合できる。
- 値は signed-v6 の署名対象に入り、署名鍵と発行権限は AI が書ける領域外にある。これは `d906.md:3-5` の要求である。

現行制約の下で比較すべき候補は 17 件ある。

| ID | 値の場所、導出元、書き手 | D906 可否 | 機序 |
|---|---|---|---|
| C1 | lease payload の追加 field。取得ごとの乱数を `_create_lease` が書く | 現行では不可 | `_parse_lease` は field 集合を厳密一致するため、旧 reader が fresh lease を `unavailable` にする。`tools/wave_land_window.py:121-149,383-384` |
| C2 | payload の追加 field。取得時刻を `_create_lease` が書く | 不可 | C1 と同じ移行破壊に加え、時計後退、分解能、同時取得で一意性が成立しない。 |
| C3 | payload の追加 field。単調 counter を `_create_lease` が書く | 現行では不可 | C1 と同じ移行破壊。counter の永続状態も現行 lease にはない。 |
| C4 | 現行 payload bytes の SHA-256。追加保存なし、issuer が導出 | 不可、恒真 | bytes は実質 `holder/main_sha/ttl` だけで、renew は bytes を変えない。同じ wave と main の再取得で同値になるため取得世代を区別しない。 |
| C5 | `hash(holder, main_sha)`。追加保存なし | 不可、恒真 | signed receipt がすでに持つ `lease_holder` と `tested_main` の決定的な再符号化であり、同じ組の再取得を検出しない。 |
| C6 | 隣接 sidecar file。乱数を `_create_lease` と同じ主体が書く | 現行では不可 | 旧 reader との互換性はあるが、現行 release は sidecar を残す。次の lease と旧世代が誤って組になる。AI が繰返し値を選べる。 |
| C7 | 隣接 sidecar file。時刻または local counter を同じ主体が書く | 不可 | C6 の寿命不一致に加え、時刻は一意性不足、counter は crash をまたぐ状態と lease との原子性が未定義。 |
| C8 | 保護された sidecar file。外部署名主体が乱数または counter を書く | 条件付き可、現行は不可 | authority が固定 lease identity と結合して書き、AI が変更できなければ候補になる。現行 reference issuer は sidecar を読まず、呼び手の値を受け取るだけ。 |
| C9 | `acceptance.<generation>.lease` のように固定名を置換 | 不可 | 旧 reader は `acceptance.lease` が無いと読み、新しい固定名 lease と並行して自分の lease を取得する。排他が実際に開く。 |
| C10 | `acceptance.lease` を維持し、世代を別の file 名または hardlink 名へ符号化 | 条件付き可、現行は不可 | 旧 reader は固定名を尊重するが、release 後に別名 entry が残る。取得との対応と掃除主体が未定義。 |
| C11 | lease 自体を世代 directory の下へ移す | 不可 | C9 と同じく、旧 reader から固定 lease が消えて見える。 |
| C12 | 固定 lease を維持し、世代名の companion directory を置く | 条件付き可、現行は不可 | 旧 reader には無害だが、directory が release を越えて残り、現行 consumer は対応を検証しない。 |
| C13 | `acceptance.lease` の xattr。乱数または counter を current producer または外部主体が書く | 条件付き可、現行は不可 | 旧 reader は xattr を無視し、unlink で値も消える。filesystem 対応、書込み権限、issuer による同じ inode の観測が未実測。 |
| C14 | `st_dev/st_ino` と真の生成時刻 `btime` の組を hash。外部主体が stat から導出 | 条件付き可、現行は不可 | payload を変えない。候補になるのは安定した `btime` が取得でき、inode 再利用を区別できる場合だけ。`ctime` と `mtime` は renew の `os.utime` で変わるため代用できない。`tools/wave_land_window.py:152-160,386-413` |
| C15 | AI が書けない外部台帳。authority の単調 counter または乱数を lease identity に割り当てる | 条件付き可 | D906 に最も直接対応する候補だが、現行 consumer は台帳を読まない。本 wave では台帳新設を提案せず、比較候補として挙動を測るだけに留める。 |
| C16 | 現行どおり caller が `--lease-generation` で issuer へ渡す | 不可、恒真になり得る | reference issuer は値を live lease から導出せず、そのまま署名と期待値照合へ渡す。期待値も同じ caller 由来なら「渡した値と渡した値が等しい」だけになる。`tools/acceptance_issuer_reference.py:15,436-464,513-527,550-580` |
| C17 | 外部署名主体が受領証発行ごとに新しい乱数を生成し、lease 側には保存しない | 不可 | 外部発行と署名は成立するが、同じ lease から複数受領証を出すと世代が変わる。これは lease 世代ではなく receipt 世代である。 |

要求された軸との対応は、payload=C1-C3、別 file=C6-C8、file 名=C9-C10、directory=C11-C12、metadata=C13-C14、外部台帳=C15、追加保存なし=C4-C5/C16-C17 で網羅する。乱数、時刻、holder-main hash、単調 counter、inode と生成時刻、既存 field 導出、および current producer と external issuer の両 writer も含む。

## 候補ごとの測定計画

**読んで推論した結果**

- `_lease_payload` は 3 field だけを生成し、`_parse_lease` は同じ 3 field の厳密一致を要求する。`tools/wave_land_window.py:121-149`
- fresh な parse 不可 lease は claim で `unavailable`、release でも `unavailable`、status でも `unavailable` になる。`tools/wave_land_window.py:383-384,521-522,576-579`
- fixed lease を維持した sidecar、extra filename、companion directory、xattr、外部台帳は現行 reader の入力にならない。claim は固定名を直接 open し、status だけが directory listing で固定名の有無を見る。`tools/wave_land_window.py:367-381,555-579`
- `dev_wave_wait` は `unavailable` を既知 state として parse するが、accepted にも nonblocking にも分類せず `claim-state` で停止する。`tools/dev_wave_wait.py:370-375,2768-2800,2895-2900`
- 実際の malformed lease 出力は `holder_self=false` なので lifecycle は `NONE` になる。cleanup は release を呼ばない。`tools/dev_wave_wait.py:2781-2799,3183-3214`
- signed-v6 schema は `lease_generation` を 64 桁 SHA-256 形式として署名対象に含め、異なる expected generation を拒否する。`tools/acceptance_receipt_signature.py:82-90,168-217,326-375`
- reference issuer は production waiter/lander から呼ばれず、世代は caller-supplied である。`tools/acceptance_issuer_reference.py:4-16,436-464,513-527`
- production lander は v5 の 27 field を厳密受理し、署名 verifier を呼ばない。signed-v6 または v5 への `lease_generation` 追加は受領証段階で拒否される。`tools/dev_wave_land.py:94-130,775-785,934-965`
- lander の lease renew 結果は land 実行を止めず、release 失敗も core の land result を上書きしない。`tools/dev_wave_land.py:5628-5650,5661-5722`

**親がすでに実走した結果**

`premeasure.md:12-62` が観測済みなのは次だけである。

- baseline claim は `acquired`、別 wave は `held`。
- fresh payload に `generation` を追加すると claim、owner release、status はすべて `unavailable`。
- stale 後の claim は旧 entry を剥がして `acquired`。
- sidecar は claim/release に影響せず、release 後に残る。

私はテストや probe を実走していない。以下はすべて親が実行する計画であり、現時点で緑とは扱わない。

**7 consumer 面の測定 matrix**

| 等価類 | 候補 | claim / release / status の読解予測 | acceptance の予測 | signature / issuer | dev_wave_land |
|---|---|---|---|---|---|
| P: payload 追加 | C1-C3 | fresh はすべて `unavailable`。stale 後は claim=`acquired`、status=`stale`、release=`unavailable` | acceptance 本走前に `claim-state` | 任意の 64 hex 値なら署名単体は通るが live lease 由来ではない | renew は `unavailable` でも v5 land は進む。signed-v6 receipt は拒否 |
| H: 既存値または metadata から導出 | C4-C5,C14 | baseline と同じ | baseline と同じ | exact expected は通る。再取得後も同値なら replay 区別不能 | v5 receipt からは値を照合できない |
| S: fixed lease に companion を追加 | C6-C8,C10,C12-C13,C15 | baseline と同じ。release 後の残置または xattr 消滅を別途観測 | baseline と同じ | 値を手動供給すれば通るが、現行 issuer は companion を読まない | lease companion は無視。signed-v6 receipt は拒否 |
| R: fixed lease を置換 | C9,C11 | claim は固定名が free と見えて新規取得、release/status は旧 generation lease を見ない | 別 lease を取得して本走へ進み得る | 署名結果とは独立に排他が破れる | 固定名側だけを renew/release |
| O: receipt 内だけ | C16-C17 | baseline と同じ | baseline と同じ | exact 値は通るが lease 取得との関係を証明しない | signed-v6 自体を受理しない |

各候補について、claim、release、status、acceptance、signature/issuer、lander、既存 test の 7 面を埋める。17 候補で 119 coverage cell になるが、現行 consumer から見て等価な候補は同じ probe で測る。

**Command 1: placement matrix。14 scenario × 3 subcommand を repo 外で測る**

```bash
T2148_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-probe \
T2148_JOB=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-probe \
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

repo = Path(os.environ["T2148_REPO"])
job = Path(os.environ["T2148_JOB"])
helper = repo / "tools" / "wave_land_window.py"
generation = "0" * 64
sha_a = "a" * 40
sha_b = "b" * 40

def invoke(args):
    completed = subprocess.run(
        [sys.executable, str(helper), *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    value = json.loads(completed.stdout)
    return completed.returncode, value

def payload(value, stale=False):
    def mutate(directory):
        path = directory / "acceptance.lease"
        data = json.loads(path.read_text(encoding="ascii"))
        data["lease_generation"] = value
        path.write_text(json.dumps(data) + "\n", encoding="ascii")
        if stale:
            stamp = time.time() - 2401
            os.utime(path, (stamp, stamp))
    return mutate

def sidecar(name, value):
    return lambda directory: (directory / name).write_text(
        str(value) + "\n", encoding="ascii"
    )

def replace_name(directory):
    (directory / "acceptance.lease").rename(
        directory / f"acceptance.{generation}.lease"
    )

def companion_hardlink(directory):
    os.link(
        directory / "acceptance.lease",
        directory / f"acceptance.{generation}.lease",
    )

def replace_directory(directory):
    target = directory / f"generation.{generation}"
    target.mkdir()
    (directory / "acceptance.lease").rename(target / "acceptance.lease")

def companion_directory(directory):
    (directory / f"generation.{generation}").mkdir()

def xattr(directory):
    os.setxattr(
        directory / "acceptance.lease",
        b"user.izanagi_lease_generation",
        generation.encode("ascii"),
    )

def external_ledger(directory):
    directory.with_name(directory.name + ".ledger").write_text(
        generation + "\n", encoding="ascii"
    )

scenarios = {
    "baseline": lambda directory: None,
    "payload-random": payload(generation),
    "payload-time": payload(time.time_ns()),
    "payload-counter": payload(1),
    "payload-stale-2401": payload(generation, stale=True),
    "sidecar-random": sidecar("acceptance.generation", generation),
    "sidecar-counter": sidecar("acceptance.counter", 1),
    "external-sidecar-placement": sidecar("authority.generation", generation),
    "filename-replacement": replace_name,
    "filename-hardlink-companion": companion_hardlink,
    "directory-replacement": replace_directory,
    "directory-companion": companion_directory,
    "xattr": xattr,
    "external-ledger-placement": external_ledger,
}

for label, mutate in scenarios.items():
    for action in ("claim", "release", "status"):
        directory = Path(tempfile.mkdtemp(
            prefix=f"probe-{label}-{action}-", dir=job
        ))
        invoke([
            "claim", "--lease-dir", str(directory),
            "--wave", "probe-wave-A", "--main-sha", sha_a,
        ])
        try:
            mutate(directory)
        except OSError as exc:
            print(json.dumps({
                "scenario": label,
                "action": action,
                "unsupported": type(exc).__name__,
            }, sort_keys=True))
            continue
        if action == "claim":
            rc, result = invoke([
                "claim", "--lease-dir", str(directory),
                "--wave", "probe-wave-B", "--main-sha", sha_b,
            ])
        elif action == "release":
            rc, result = invoke([
                "release", "--lease-dir", str(directory),
                "--wave", "probe-wave-A",
            ])
        else:
            rc, result = invoke([
                "status", "--lease-dir", str(directory),
                "--wave", "probe-wave-A", "--json",
            ])
        print(json.dumps({
            "scenario": label,
            "action": action,
            "rc": rc,
            "state": result.get("state"),
            "reason": result.get("source", {}).get("reason"),
            "entries_after": sorted(
                str(path.relative_to(directory))
                for path in directory.rglob("*")
            ),
        }, sort_keys=True))
PY
```

観測点は、P 類の `unavailable`、R 類の `free/acquired`、S 類の baseline 同値、release 後の残置、xattr の利用可否である。stale scenario では claim だけが回収可能になり、release はなお `unavailable` であることを確認する。

**Command 2: C4、C5、C14 の安定性を renew と再取得の両方で測る**

```bash
T2148_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-probe \
T2148_JOB=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-probe \
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

repo = Path(os.environ["T2148_REPO"])
job = Path(os.environ["T2148_JOB"])
helper = repo / "tools" / "wave_land_window.py"
directory = Path(tempfile.mkdtemp(prefix="probe-identity-", dir=job))
path = directory / "acceptance.lease"
wave = "probe-wave-A"
sha = "a" * 40

def run(action):
    argv = [
        sys.executable, str(helper), action,
        "--lease-dir", str(directory), "--wave", wave,
    ]
    if action == "claim":
        argv += ["--main-sha", sha]
    return subprocess.run(
        argv, cwd=repo, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout

def snapshot(label):
    raw = path.read_bytes()
    data = json.loads(raw)
    st = path.stat()
    print(json.dumps({
        "label": label,
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
        "holder_main_sha256": hashlib.sha256(
            (data["holder"] + "\0" + data["main_sha"]).encode("ascii")
        ).hexdigest(),
        "dev": st.st_dev,
        "ino": st.st_ino,
        "mtime_ns": st.st_mtime_ns,
        "ctime_ns": st.st_ctime_ns,
        "birthtime": getattr(st, "st_birthtime", None),
    }, sort_keys=True))

run("claim")
snapshot("acquired-1")
time.sleep(0.01)
run("claim")
snapshot("renewed-same-acquisition")
run("release")
time.sleep(0.01)
run("claim")
snapshot("acquired-2")
PY
```

比較は 6 件と数える。payload hash と holder-main hashについて「renew 前後」「再取得前後」、metadata tuple について同じ 2 比較を行う。inode が異なることを期待値にせず、実測値をそのまま残す。

**Command 3: 実 helper を通る acceptance propagation**

```bash
T2148_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-probe \
T2148_JOB=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-probe \
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path(os.environ["T2148_REPO"])
job = Path(os.environ["T2148_JOB"])
directory = Path(tempfile.mkdtemp(prefix="probe-acceptance-", dir=job))
lease = directory / "acceptance.lease"
receipt = directory / "receipt.json"
log = directory / "acceptance.log"
wave = "dev-wave-t2148-lease-generation-probe"
main_sha = subprocess.run(
    ["git", "rev-parse", "main"], cwd=repo, check=True,
    text=True, stdout=subprocess.PIPE,
).stdout.strip()

subprocess.run([
    sys.executable, str(repo / "tools/wave_land_window.py"), "claim",
    "--lease-dir", str(directory), "--wave", wave, "--main-sha", main_sha,
], cwd=repo, check=True, stdout=subprocess.PIPE)

value = json.loads(lease.read_text(encoding="ascii"))
value["lease_generation"] = "0" * 64
lease.write_text(json.dumps(value) + "\n", encoding="ascii")
before = (lease.read_bytes(), lease.stat().st_mtime_ns)

environment = dict(os.environ)
for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH", "PYTHONHOME"):
    environment.pop(name, None)
environment["PYTHONDONTWRITEBYTECODE"] = "1"

completed = subprocess.run([
    sys.executable, str(repo / "tools/dev_wave_wait.py"), "acceptance",
    "--wave", wave,
    "--lease-dir", str(directory),
    "--receipt-file", str(receipt),
    "--log-file", str(log),
    "--max-wait-seconds", "600",
    "--", sys.executable, "tools/run_tests.py",
], cwd=repo, env=environment, text=True,
   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

after = (lease.read_bytes(), lease.stat().st_mtime_ns)
print(json.dumps({
    "rc": completed.returncode,
    "stderr": completed.stderr,
    "receipt_exists": receipt.exists(),
    "log_exists": log.exists(),
    "lease_unchanged": before == after,
}, sort_keys=True))
PY
```

必須観測は 6 点である。`rc=70`、最終 stage=`claim-state`、受入 child 未起動、receipt 無し、log 無し、lease bytes/mtime 不変。別 stage なら前処理で止まっただけなので、この測定は未成立とする。

**Command 4: signature と reference issuer の世代受け渡し**

```bash
T2148_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-probe \
python3 - <<'PY'
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tools import acceptance_issuer_reference as issuer
from tools import acceptance_receipt_signature as signing

repo = Path(os.environ["T2148_REPO"])
fixture = repo / "orchestrator/tests/fixtures/production-acceptance-receipt-v5.json"
v5 = json.loads(fixture.read_text(encoding="utf-8"))
generation = "0" * 64
other = "1" * 64
checker = "2" * 64
key = Ed25519PrivateKey.generate()
configured = signing.ConfiguredPublicKey(
    signing.public_key_id(key.public_key()), key.public_key()
)

issuer._verify_commit = lambda *args, **kwargs: None
issuer._blob = lambda *args, **kwargs: ("a" * 40, b"launcher")
issuer._validate_launcher_request = lambda *args, **kwargs: None
issuer._execute_tested_main_launcher = lambda *args, **kwargs: dict(v5)
issuer._compare_issuer_derived_expectations = lambda *args, **kwargs: checker
issuer._read_private_key = lambda: key
issuer.load_configured_public_key = lambda: configured

raw = issuer.issue_signed_receipt(
    repo_root=repo,
    acceptance_wave=v5["acceptance_wave"],
    tested_main=v5["tested_main"],
    tested_tip=v5["tested_tip"],
    lease_generation=generation,
    log_file=repo / "unused-probe-log",
    launcher_argv=(),
)
receipt = json.loads(raw)
assert receipt["lease_generation"] == generation
signing.verify_signed_receipt_signature(
    receipt, configured,
    expected_acceptance_wave=v5["acceptance_wave"],
    expected_tested_main=v5["tested_main"],
    expected_tested_tip=v5["tested_tip"],
    expected_lease_generation=generation,
)
try:
    signing.verify_signed_receipt_signature(
        receipt, configured,
        expected_acceptance_wave=v5["acceptance_wave"],
        expected_tested_main=v5["tested_main"],
        expected_tested_tip=v5["tested_tip"],
        expected_lease_generation=other,
    )
except signing.ReceiptSignatureError as exc:
    print(json.dumps({
        "issuer_passed_generation": receipt["lease_generation"],
        "exact_context": "accepted",
        "different_generation": str(exc),
    }, sort_keys=True))
else:
    raise SystemExit("different generation unexpectedly accepted")
PY
```

これは外部 key path や live launcher を測る production control ではない。issuer の pass-through、exact generation 受理、different generation 拒否の 3 点だけを測る。

**Command 5: malformed lease と追加 receipt field の lander 実経路**

```bash
T2148_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-probe \
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys
from orchestrator.tests import test_dev_wave_land as support

repo_root = Path(os.environ["T2148_REPO"])

def run_case(label, *, extra_lease=False, extra_receipt=False):
    with support._repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", label + "\n")
        request = repo.request(wave, tip=tip)
        lease_dir = repo.root / "lease"
        lease_dir.mkdir()
        subprocess.run([
            sys.executable,
            str(repo_root / "tools/wave_land_window.py"),
            "claim", "--lease-dir", str(lease_dir),
            "--wave", request.acceptance_wave,
            "--main-sha", request.tested_main_sha,
        ], cwd=repo_root, check=True, stdout=subprocess.PIPE)
        lease = lease_dir / "acceptance.lease"
        if extra_lease:
            value = json.loads(lease.read_text(encoding="ascii"))
            value["lease_generation"] = "0" * 64
            lease.write_text(json.dumps(value) + "\n", encoding="ascii")
        if extra_receipt:
            value = support._receipt_payload(request.acceptance_receipt)
            value["lease_generation"] = "0" * 64
            support._write_receipt(request.acceptance_receipt, value)
        before = support._git(repo.main, "rev-parse", "HEAD")
        rc, result, _raw, errors = support._invoke_land_main(request, lease_dir)
        after = support._git(repo.main, "rev-parse", "HEAD")
        print(json.dumps({
            "case": label,
            "rc": rc,
            "status": result["status"],
            "reason": result["reason"],
            "main_changed": before != after,
            "lease_exists": lease.exists(),
            "stderr": errors.splitlines(),
        }, sort_keys=True))

run_case("baseline")
run_case("extra-lease-field", extra_lease=True)
run_case("extra-receipt-field", extra_receipt=True)
PY
```

期待する 3 ケースは、baseline の正常 land/release、extra lease field でも land 本体は進むが renew/release が `unavailable`、extra receipt field は `RC_AUDIT` と `acceptance-receipt-rejected` で main 不変、である。`dev_wave_land` 自体には `--lease-dir` が無いため、lease 作成は明示的な `--lease-dir`、lander への受渡しだけは production と同じ `IZANAGI_WAVE_LEASE_DIR` を test helper が使う。

**Command 6: 現行テスト 22 target**

```bash
python3 tools/run_tests.py \
  orchestrator/tests/test_wave_land_window.py::test_claim_empty_directory_acquires_and_creates_lease \
  orchestrator/tests/test_wave_land_window.py::test_second_wave_is_held_by_first_holder \
  orchestrator/tests/test_wave_land_window.py::test_renew_invalid_fresh_lease_is_unavailable \
  orchestrator/tests/test_wave_land_window.py::test_release_then_other_wave_can_acquire \
  orchestrator/tests/test_wave_land_window.py::test_status_distinguishes_free_and_held \
  orchestrator/tests/test_wave_land_window.py::test_claim_ttl_boundary_uses_literal_2400 \
  orchestrator/tests/test_wave_land_window.py::test_status_reports_stale_at_2401_seconds \
  orchestrator/tests/test_wave_land_window.py::test_stale_invalid_lease_is_reclaimed_by_mtime \
  orchestrator/tests/test_wave_land_window.py::test_fresh_invalid_lease_remains_fail_closed \
  'orchestrator/tests/test_dev_wave_wait.py::test_acceptance_claim_is_single_nonblocking[held-default]' \
  'orchestrator/tests/test_dev_wave_wait.py::test_acceptance_rejects_non_nonblocking_claim_state[unavailable]' \
  orchestrator/tests/test_dev_wave_wait.py::test_release_failure_overrides_primary_result \
  orchestrator/tests/test_dev_wave_wait.py::test_default_wiring_with_real_git_and_lease_helper \
  orchestrator/tests/test_external_acceptance_signing.py::test_recorded_production_v5_receipt_passes_canonical_projection \
  orchestrator/tests/test_external_acceptance_signing.py::test_signed_v6_signature_covers_every_root_field_except_itself \
  orchestrator/tests/test_external_acceptance_signing.py::test_valid_test_signature_and_exact_context_pass \
  orchestrator/tests/test_external_acceptance_signing.py::test_signed_receipt_replay_into_other_context_is_rejected \
  orchestrator/tests/test_dev_wave_land.py::test_land_accepts_receipt_bound_to_wave_tip_and_emits_digest \
  'orchestrator/tests/test_dev_wave_land.py::test_land_rejects_tampered_acceptance_receipt[unknown-field]' \
  orchestrator/tests/test_dev_wave_land.py::test_main_releases_owned_lease_after_success_and_preserves_core_result \
  orchestrator/tests/test_dev_wave_land.py::test_main_renew_exception_does_not_change_land_result \
  orchestrator/tests/test_dev_wave_land.py::test_release_failure_never_overwrites_land_result
```

特に、`test_external_acceptance_signing.py:214-340` は test key と literal generation の機能試験に限られる。同ファイル冒頭 `:1-5` も production signed-v6 positive control が未充足だと明記する。また、現行テストから `issue_signed_receipt` の full path を呼ぶ箇所は見つからない。

## 移行窓の測定計画

新 writer が payload field を追加し、旧 reader が動く窓は次の順で測る。

1. baseline として旧 writer/旧 reader の claim、release、status を保存する。
2. exact schema 名である `lease_generation` を追加し、fresh 状態で旧 claim、owner release、status、renew を測る。親実測は `generation` という別名だったが、厳密 field 集合の拒否確認としては等価である。追試では exact 名を使う。
3. Command 3 で旧 `dev_wave_wait acceptance` を実走する。予測される停止点は `_claim_once` の JSON parse 後、`_try_claim_once_without_wait` の `claim-state` で、preflight や child command の失敗とは区別する。`tools/dev_wave_wait.py:2736-2880,2883-2911`
4. acceptance cleanup が release を試さないことを、最終 stage が `release-state` ではなく `claim-state` のままであることと、receipt/log が作られないことで確認する。
5. Command 5 で旧 lander を独立に測る。旧 waiter が止まることから、旧 lander も止まるとは一般化しない。lander は renew=`unavailable` でも `land(request)` を呼ぶ。`tools/dev_wave_land.py:5628-5650`
6. v5 receipt と extra-field lease の組では land 本体が進み得る一方、signed-v6 receipt は v5 field 集合で拒否されることを分離して記録する。これは lease schema と receipt schema の 2 つの独立した移行不整合である。
7. stale 前後を分ける。age 2400 以下では fresh、2401 以上では claim が回収可能になる。status は `stale` になるが、release は stale 判定より先に payload validity を要求するため、invalid lease の owner release は 2401 秒後も `unavailable` のままである。`tools/wave_land_window.py:152-160,383-425,521-522,576-579`

親の前提実測が production 経路を測れている範囲は `wave_land_window.py` の CLI dispatch と、そこから呼ばれる claim/release/status 本体までである。`tools/wave_land_window.py:637-690`

測れていない範囲は次のとおり。

- `renew`。これは `dev_wave_land` が実際に使う subcommand 相当の API である。
- `dev_wave_wait` の preflight、state classification、cleanup、最終 rc/stage。
- `dev_wave_land` の direct import による renew/release と land result の関係。
- signed-v6 verifier と reference issuer の pass-through。
- production lander が signed-v6 を受け取る経路。現状はその経路自体が未接続。
- sidecar の release 後残置と次の取得との組合せ。
- C13 の xattr 対応、C14 の真の birth time、C8/C15 の保護された外部 writer。

したがって、親実測は「旧 reader が extra-field payload を free と読む」という D1400 の機序を覆すには十分だが、「acceptance 全体がどう終わるか」「land も停止するか」「TTL 後に自動回復するか」までは証明していない。

## brief の前提の点検

**P1: `wave_land_window` の結果を acceptance 全体へ一般化してよい**

この前提は未成立である。`brief.md:89-91` 自身も `dev_wave_wait` は未実走だと認めている。code reading では `unavailable` が `claim-state` になることは強く予測できるが、production waiter の preflight、最終出力、cleanup まで観測したことにはならない。

また、brief の「TTL の 2400 秒間 lease dir 全体が unavailable に固まる」`brief.md:59-64` は一般化しすぎている。

- 2401 秒後に可能になるのは、別 claimant による stale entry の unlink と再取得である。
- status は `stale` になる。
- invalid payload に対する owner release は stale 後も `unavailable` であり、自動的に free にはならない。
- old `dev_wave_land` は renew の `unavailable` を land 前提条件にせず、v5 receipt が有効なら land 本体を続ける。

従って正確な表現は、「fresh 中は旧 waiter の acceptance が claim-state で停止する。TTL 超過後は次の claim による回収が可能になるが、release 自体が回復するわけではない」である。

**P1: 候補集合が尽くせているか**

`brief.md:92-93` の列挙は不足している。少なくとも次が欠ける。

- fixed lease を維持する別名 marker/hardlink と、fixed lease 自体を置換する file 名案の区別。
- replacement directory と companion directory の区別。
- xattr。
- inode と真の birth time。単なる mtime は renew で変わる。
- 現行 payload bytes の hash と holder-main hashという、payload を 1 byte も変えない恒真候補。
- caller-supplied generation という現行 reference issuer の実態。
- external issuer が receipt ごとに生成する値と、lease 取得ごとの値の区別。
- sidecar または外部 authority が値を書く場合の writer の違い。

**file:line の食い違い**

- `premeasure.md:29-30` は `state=free` の fixed-file absence 分岐を `tools/wave_land_window.py:565-566` とするが、現実体は `:567-568`。
- `premeasure.md:57-59` は claim が `os.listdir` で固定名を見ると説明するが、claim は `:367-381` で固定名を直接 open/create する。`os.listdir` は renew の `:440-446` と status の `:562-568` である。
- sidecar が旧実装に無視されるという結論自体は正しいが、上記の機序と引用行は訂正が必要。
- `brief.md:16-26` の `_parse_lease`、`_open_lease`、claim、署名 slot、claim state の行番号は現実体と一致している。

**既存テストから言える範囲**

- invalid fresh lease と stale 回収は `orchestrator/tests/test_wave_land_window.py:1132-1216` が pin するが、extra `lease_generation` field の exact fixtureではない。
- `unavailable` の acceptance 拒否は `orchestrator/tests/test_dev_wave_wait.py:5510-5528` にあるが、fake claim result であり実 helper との結合試験ではない。
- generation mismatch の署名拒否は `orchestrator/tests/test_external_acceptance_signing.py:284-326` にあるが、expected generation の独立した生成源を証明しない。
- lander の unknown receipt field 拒否は `orchestrator/tests/test_dev_wave_land.py:1283-1348` が pin する。これは現行 lander が signed-v6 positive consumer でないことと整合する。

## 総括

- 候補: 17 件。
- consumer coverage: 17 候補 × 7 面 = 119 cell。
- 独立して実行・記録する測定: 82 件。内訳は placement 42 行、世代安定性 6 比較、acceptance 6 観測点、issuer/signature 3 ケース、lander 3 ケース、既存 test 22 target。
- 親が実行すべき command: 上記 6 command block。
- この段では実装、schema 変更、受理集合変更、外部台帳新設を行わない。
- この計画を実走すれば、移行互換性を壊す候補、恒真候補、現行 consumer から不可視な候補を裁定する材料は揃う。
- C8、C13、C14、C15 のいずれかを積極採用する裁定には、なお「AI が変更できない writer/storage が実在するか」「issuer と lander が同じ lease inode と世代を観測できるか」という外部 authority 側の証拠が不足する。現行 production lander が signed-v6 を受理しない点も未閉鎖である。従って本計画だけで可能なのは棄却と shortlist の裁定までで、最終採用にはその operational evidence が別途必要である。