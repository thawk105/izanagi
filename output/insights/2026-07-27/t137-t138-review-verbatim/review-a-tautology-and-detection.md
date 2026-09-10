静的レビュー結果です。テストは実行しておらず、緑・赤の記述は提供された JSON の記録との照合に限定します。

## 所見

### 1. M-C は過剰拒否の正例ではなく、恒真 skip を受理している

- (a) 主張: M-C は sandbox capability を落とさず probe 自身を壊しており、その `SKIPPED + rc=0` を成功扱いするのは T-138 と同型の恒真化を認証している。
- (b) file:line: [mutation_matrix.py](/tmp/claude-31609/-home-SFC-tanab-github-izanagi/96d62154-0f41-4a00-8132-05b75fe01ae1/scratchpad/wave-t137-t138/mutation_matrix.py:128)、[mutation_matrix.json](/tmp/claude-31609/-home-SFC-tanab-github-izanagi/96d62154-0f41-4a00-8132-05b75fe01ae1/scratchpad/wave-t137-t138/mutation_matrix.json:79)、[test_dev_waves_integration.py](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:929)
- (c) 失敗シナリオ: AF_UNIX capability が正常なホストで probe の alias が M-C のように `absent-dir/.p` へ退行し、同時に本番 alias が M-B のように実パスへ退行する → probe は `False`、テストは本番を一度も起動せず SKIP/rc=0 → T-138 が再び無検出になる。M-C 単独でも「正常環境を壊れた probe が skip する」過剰拒否を成功と誤判定している。
- (d) 成果物影響: mutation matrix と brief が「3/3 成立・過剰拒否なし」と誤記録され、長い repository path で supervisor が起動できず試行台帳が 0 件になる退行を certified な検出力として受理し得る。
- (e) 自己申告: **must-fix**

M-C は probe を変更せず、外側から raw `bind()` を `EPERM` にする正例へ差し替える必要があります。probe-defect と M-B の複合変異は別途「必ず fail」を期待すべきです。

### 2. probe は capability 判定として全域でなく、本番 bind の成功条件も代表していない

- (a) 主張: `socket.socket()` は例外捕捉の外にあり、逆に probe 成功後の本番 `chmod`・`stat`・`listen` は検査されないため、capability 不足を双方向に regression と誤認する。
- (b) file:line: [test_dev_waves_integration.py](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:905)、[protocol.py](/home/SFC/tanab/github/izanagi/tools/dev_waves/protocol.py:250)
- (c) 失敗シナリオ:
  - seccomp が `socket(AF_UNIX, SOCK_STREAM)` を `EPERM` にする → 905 行で未捕捉例外となり、本来の SKIP ではなく FAIL。
  - `socket()` と `bind()` は許すが `listen(2)` または socket inode への `chmod` を禁じる sandbox → probe は `True`、本番は 262–270 行で失敗し、環境 capability 不足を本番退行として FAIL。
- (d) 成果物影響: 同じ本番 bytes でも sandbox syscall policy により受入結果が SKIP ではなく FAIL となり、受入レポートと wave の landing 可否が環境依存で過剰拒否側へ変わる。
- (e) 自己申告: **must-fix**

なお、`O_NOFOLLOW` と uid の差はこの node では `Supervisor` 構築時の `RuntimeLayout.create()` が symlink・所有者を先に検査するため、主要なずれではありません。ただし本番は mode が厳密に `0700`、probe は raw bind の成否だけなので完全な同値条件ではありません。

### 3. `.p` と `.s` は長さ等価でも認可条件は等価ではない

- (a) 主張: basename の同バイト長が保証するのは `sun_path` 長だけであり、pathname を見る LSM・sandbox policy に対して `.p` は本番 `.s` の代表にならない。
- (b) file:line: [test_dev_waves_integration.py](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:902)、[protocol.py](/home/SFC/tanab/github/izanagi/tools/dev_waves/protocol.py:128)
- (c) 失敗シナリオ:
  - AppArmor 等が `/proc/self/fd/*/.p` を許可し `.s` を拒否 → probe は成功、本番は失敗して偽赤。
  - `.p` を拒否し `.s` を許可 → probe が失敗して SKIP、本番 alias の退行も検査されない。
- (d) 成果物影響: 同じ環境でも basename policy により受理集合が余分に縮小または拡大し、受入レポートが偽赤になるか、長 path の起動不能と台帳 0 件を rc=0 の SKIP で通す。
- (e) 自己申告: **must-fix**

server thread はまだ開始しておらず runtime は新規なので、raw control 自体を `.s` で bind・unlink する方が代表性は高いです。

## 攻撃しても問題を確認できなかった点

- M-A2 は、入力処理・run 完了より後の `shutdown()` でのみ差が発火し、静的には 962 行の thread 生存 assert が単一の機能的赤理由です。診断文字列だけの赤ではありません。
- M-B は独立 probe の後に本番 `socket_path_alias()` が長い実パスを拒否し、socket/roundtrip が成立しなくなる機能的な赤です。前段に同じ入力を拒否する経路は見当たりません。
- 旧2段目 skip の削除により、serve thread の bind 例外が再び SKIP へ逃げる経路は塞がれています。
- `bind_repo_socket` import と旧 probe の削除による有意な赤検出の喪失は確認できません。旧 probe の本番エラーは原則 SKIP され、その後の serve が同じ本番 bind を再実行していました。

## 親が次に測るべき実測

1. M-B と M-C の複合変異を同時適用して対象 node を実行する。

   ```bash
   python3 tools/run_tests.py orchestrator/tests/test_dev_waves_integration.py::test_socket_roundtrip_works_beyond_108_byte_repository_path -rf
   ```

   期待: probe defect は capability 不足扱いせず `failed/rc=1`。現状ロジックでは `skipped/rc=0` になるはず。

2. `socket()` 自体の拒否を確認する。

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
   import errno, tempfile
   from pathlib import Path
   from unittest import mock
   import orchestrator.tests.test_dev_waves_integration as t

   with tempfile.TemporaryDirectory() as raw:
       directory = Path(raw)
       directory.chmod(0o700)
       with mock.patch.object(
           t.socket, "socket",
           side_effect=PermissionError(errno.EPERM, "seccomp"),
       ):
           assert t._sandbox_permits_short_alias_bind(directory) is False
   PY
   ```

   期待: 修正後 rc=0。現状は `PermissionError` が漏れて rc≠0。

3. basename policy の非同値を固定化する。

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
   import errno, tempfile
   from pathlib import Path
   from unittest import mock
   import orchestrator.tests.test_dev_waves_integration as t

   class PolicySocket:
       def bind(self, path):
           if path.endswith("/.s"):
               raise PermissionError(errno.EACCES, "deny production basename")
       def close(self):
           pass

   with tempfile.TemporaryDirectory() as raw:
       directory = Path(raw)
       directory.chmod(0o700)
       with mock.patch.object(t.socket, "socket", return_value=PolicySocket()):
           assert t._sandbox_permits_short_alias_bind(directory) is False
   PY
   ```

   期待: 本番 basename を probe する修正後は rc=0。現状の `.p` probe は `True` となり assertion failure。