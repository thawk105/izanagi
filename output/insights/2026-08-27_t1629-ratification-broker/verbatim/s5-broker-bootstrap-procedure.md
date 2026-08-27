`_approval_stream()` の tty 非対応を修正しました。[tools/ratification_broker.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/tools/ratification_broker.py:510) だけを編集し、テストの期待値は変更していません。

実装は次の構成です。

- `os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)`
- `io.FileIO(fd, "w+")` による unbuffered I/O
- `io.TextIOWrapper` による UTF-8 text stream
- wrapper 構築失敗時も fd/raw stream を閉じる
- M15 の `/dev/tty` seam は `fd = os.open(...)` の 1 箇所を維持

`O_NOCTTY` は付けました。broker は既存の制御端末から承認を読むだけであり、新たな制御端末を取得する責務を持たないためです。

### 指定検証の逐語出力

子は `pty.fork()` で生成し、修正後の `_approval_stream()` を直接 import・呼び出しています。

```text
pty_prompt=True
pty_readline='y\n'
pty_child_exit=0
no_tty=BrokerError: cannot open /dev/tty; ratification is not approved
exit_code=0
```

したがって、PTY 上で prompt を書き、親から送った `y\n` を `readline()` が正確に返すこと、および制御端末なしでは fail-closed の `BrokerError` になることを確認済みです。

静的検査の逐語出力:

```text
AST tools/ratification_broker.py: ok
U+0300-U+036F tools/ratification_broker.py: 0
trailing-whitespace tools/ratification_broker.py: 0
AST orchestrator/tests/test_ratification_broker.py: ok
U+0300-U+036F orchestrator/tests/test_ratification_broker.py: 0
trailing-whitespace orchestrator/tests/test_ratification_broker.py: 0
static approval seam: one /dev/tty os.open; O_RDWR|O_NOCTTY; raw FileIO; TextIOWrapper
M15 replacement point: fd = os.open(...) remains one statement
test expectations changed: no
exit_code=0
```

pytest、`tools/run_tests.py`、Web 検索、git 操作は実行していません。実 repo の信頼根と v2 台帳も作成していません。

### 赤 4 node 対応表

共有 blocker は解消済みですが、node 固有の最終 assertion は親の pytest 実走待ちなので、保守的に `partial` とします。

| node | 判定 | 根拠 |
|---|---|---|
| `test_worktree_ledger_drift_is_rejected_inside_transaction` | partial | PTY 承認入力の通過を確認。transaction 内の drift 拒否までは未実走 |
| `test_private_key_bytes_are_not_present_in_remote_tree` | partial | PTY 承認入力の通過を確認。remote tree 全走査までは未実走 |
| `test_private_key_bytes_are_not_sent_to_children` | partial | PTY 承認入力の通過を確認。全 child payload の検査までは未実走 |
| `test_approved_receipt_is_signed_committed_and_records_provenance` | partial | PTY 承認入力の通過を確認。署名、commit、provenance の一連処理までは未実走 |

`closed` は 0 件、`regressed` は 0 件です。

### 人間が一度だけ行う bootstrap

AI が到達できない trusted host/account で、人間がレビュー済みの broker と verifier を operational path に配置します。

```bash
set -eu

RATIFY_REPO=/absolute/path/to/izanagi
RATIFY_INSTALL=/opt/izanagi-ratification
RATIFY_STATE=/var/lib/izanagi-ratification
RATIFY_KEY="$RATIFY_STATE/ratification-ed25519.key"
RATIFY_DER="$RATIFY_STATE/ratification-ed25519-public.der"

umask 077

install -d -m 0755 \
  "$RATIFY_INSTALL/tools" \
  "$RATIFY_INSTALL/orchestrator/campaign"

install -m 0755 \
  "$RATIFY_REPO/tools/ratification_broker.py" \
  "$RATIFY_INSTALL/tools/ratification_broker.py"

install -m 0644 \
  "$RATIFY_REPO/orchestrator/campaign/ed25519_verify.py" \
  "$RATIFY_INSTALL/orchestrator/campaign/ed25519_verify.py"

install -d -m 0700 "$RATIFY_STATE"

test ! -e "$RATIFY_KEY"
test ! -e "$RATIFY_DER"
test ! -e "$RATIFY_REPO/hooks/enforcement-source-ratification-trust-root.v1.json"
test ! -e "$RATIFY_REPO/hooks/enforcement-source-ratification-receipts.v2.jsonl"

openssl genpkey \
  -algorithm ED25519 \
  -out "$RATIFY_KEY"

chmod 0600 "$RATIFY_KEY"

openssl pkey \
  -in "$RATIFY_KEY" \
  -pubout \
  -outform DER \
  -out "$RATIFY_DER"
```

次に raw 32-byte public key を検査し、repo の 2 file を exclusive-create します。

```bash
python3 - \
  "$RATIFY_DER" \
  "$RATIFY_REPO/hooks/enforcement-source-ratification-trust-root.v1.json" \
  "$RATIFY_REPO/hooks/enforcement-source-ratification-receipts.v2.jsonl" <<'PY'
import base64
import json
import os
from pathlib import Path
import sys

der_path = Path(sys.argv[1])
trust_path = Path(sys.argv[2])
ledger_path = Path(sys.argv[3])

prefix = bytes.fromhex("302a300506032b6570032100")
der = der_path.read_bytes()
if len(der) != len(prefix) + 32 or not der.startswith(prefix):
    raise SystemExit("not an Ed25519 SubjectPublicKeyInfo")

public_key = der[len(prefix):]
trust_raw = json.dumps(
    {
        "public_key_ed25519_base64": base64.b64encode(public_key).decode("ascii"),
        "schema_version": "enforcement-source-ratification-trust-root/v1",
    },
    ensure_ascii=True,
    sort_keys=True,
    separators=(",", ":"),
).encode("ascii") + b"\n"

for path, raw in ((trust_path, trust_raw), (ledger_path, b"")):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o644)
    with os.fdopen(fd, "wb") as stream:
        os.fchmod(stream.fileno(), 0o644)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
PY

git -C "$RATIFY_REPO" add -- \
  hooks/enforcement-source-ratification-trust-root.v1.json \
  hooks/enforcement-source-ratification-receipts.v2.jsonl

git -C "$RATIFY_REPO" commit \
  -m "Bootstrap enforcement-source ratification trust root"
```

2 file の exact content は次です。

`hooks/enforcement-source-ratification-trust-root.v1.json`:

```text
{"public_key_ed25519_base64":"<生成した raw 32-byte public key の canonical base64>","schema_version":"enforcement-source-ratification-trust-root/v1"}\n
```

空白なし、表示順の field、末尾 LF は exact 1 個です。上の Python が placeholder を実値へ置換した bytes を生成します。

`hooks/enforcement-source-ratification-receipts.v2.jsonl`:

```text
0 byte
```

bootstrap 後、AI 側は以下を検査します。

- worktree ではなく committed HEAD の trust root、ledger、closure blob を読む
- trust root の schema、exact field set、canonical JSON/base64、raw key 32 bytes、末尾 LF を検査
- private key から得た public key と committed trust root の一致を検査
- ledger 全行の canonical JSON、serial、previous hash、trust fingerprint、closure paths、署名を検査
- committed closure digest を計算
- approval 後に HEAD と ledger blob ID を再確認
- worktree/index drift を拒否し、CAS、stage、commit、provenance を検査

主張上限は次のとおりです。

> 現在の committed 信頼根の鍵で検証できる署名 receipt の集合と、要求された closure digest を比較する。信頼根の秘密鍵は repo の外にあり、AI はそれを持たない。

これは「人間が批准したことの機械的証明」や、D905/D906 の充足を意味しません。

## 総括

非 seekable な `/dev/tty` を buffered `r+` で開いていた共有真因を、`O_NOCTTY` 付き raw `FileIO` と `TextIOWrapper` へ修正しました。PTY prompt、`y\n` の読み取り、制御端末なしの `BrokerError` を実機確認済みです。4 node の共有 blocker は解消していますが、node 全体の確定は親の pytest 実走待ちです。