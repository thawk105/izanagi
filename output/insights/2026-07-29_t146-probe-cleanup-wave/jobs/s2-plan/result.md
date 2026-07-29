指定5ファイルを含む関連箇所を静的確認した。結論は GO。変更面は `orchestrator/tests/test_dev_waves_integration.py` だけで閉じられ、production `tools/dev_waves/` と isolation meta-test 本体は変更不要である。テストは一切実走しておらず、green とは判定していない。ファイル編集も行っていない。

## 最小実装案

対象は [_sandbox_permits_short_alias_bind():1093](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1093) のみ。

1. [docstring:1094](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1094)

   現行契約を次のように限定・明文化する。

   - capability 判定の本体は引き続き literal `.s` と `socket → bind → chmod → stat → listen`。production helper や `SOCKET_BASENAME` を輸入しない。
   - bind 前後の追加 `os.stat(".s", dir_fd=fd, follow_symlinks=False)` は所有判定専用であり、既存 capability 列の `stat` を置換しない。
   - helper が作った pathname だけを削除する。
   - cleanup の `FileNotFoundError` は「既に不存在」として受理するが、それ以外の unlink 異常は capability `False` に潰さない。
   - 引数 directory は当該 test node 専有で、並行 writer を契約外とする。

2. [所有判定と例外分類:1108](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1108)

   `probe` 作成後、bind 前に actual pathname を dirfd 基準・nofollow で調べる。

   - `FileNotFoundError`: absent、bind へ進む。
   - pathname が存在: helper は `False`、bind/unlink は行わず socket/dirfd を閉じる。
   - その他の pre-bind `OSError`: capability 不足として `False`。
   - `Path.exists()` は使わない。broken symlink を「不存在」と誤認するため。

3. [bind:1117](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1117)

   bind だけを内側の `try/except OSError` に分離する。

   - 正常 return: `owns_path = True`。
   - 例外: actual `.s` を同じ dirfd と `follow_symlinks=False` で再確認する。
     - 不存在なら所有なし。
     - 存在すれば、bind 前に不存在を確認済みなので当該 probe 所有とする。
     - 所有確認自体の `PermissionError` / `EIO` は `False` にせず送出する。
   - bind の元例外は既存 bool 契約どおり `False`。`finally` で、部分成功により現れた `.s` を回収する。

4. [cleanup:1125](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1125)

   socket close → owned pathname unlink → dirfd close の順を維持する。

   ```text
   close socket（既存どおり OSError を抑止）
   if owns_path:
       unlink(".s", dir_fd=fd)
       FileNotFoundError だけ抑止
   close dirfd（外側 finally）
   ```

   `PermissionError` と `EIO` は生の型・errno を保ったまま送出する。独自例外への正規化は不要。

## unlink エラーの裁定案

| unlink 結果 | helper の扱い | 理由 |
|---|---|---|
| `FileNotFoundError` | 抑止し、計算済み bool を維持 | pathname は既に不存在で cleanup postcondition を満たす |
| `PermissionError` | 送出 | 残留がほぼ確実で、本番の `.s` と衝突し得る |
| `OSError(EIO)` | 送出 | namespace 状態を証明できず、capability 不足として skip させてはいけない |

したがって、三者を同一扱いにはしない。`PermissionError` と `EIO` は同じ制御分類「cleanup invariant violation」だが、診断力を落とさないよう相互にも正規化せず、別 parameter で errno まで固定する。

## fault-injection test

追加位置は既存の [正負 capability gate:1155](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1155) の直後、[long-path node:1181](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1181) の前を推奨する。

全 node に `@pytest.mark.xdist_group("dev-waves-runtime")` を付ける。

1. `test_short_alias_bind_probe_recovers_partial_bind_and_closes_fds`

   - 実 socket FD を包む instance-local mock を `socket.socket` の戻り値にする。
   - `bind(alias)` の side effect は actual `directory / ".s"` を作ってから `OSError(EIO)` を投げる。
   - 期待:
     - helper は `False`。
     - `.s` は helper return 時に不存在。
     - raw socket は `fileno() == -1`。
     - 捕捉した directory fd は `os.fstat()` が `EBADF`。
   - test-level `finally` でも未閉鎖 FD と残留 pathname を回収し、変異時に worker を汚さない。

2. `test_short_alias_bind_probe_never_unlinks_preexisting_path`

   regular file と broken symlink の二ケースを parameterize する。

   - helper は `False`。
   - regular file は内容または inode が不変。
   - broken symlink は link 自体と link target 文字列が不変。
   - socket/dirfd は閉じる。
   - これにより、単なる `Path.exists()` を使う誤実装も検出できる。

3. `test_short_alias_bind_probe_cleanup_error_policy`

   capability 側の結論を `False` に固定するため、mock bind は actual `.s` を作り、listen が `EACCES` を投げる。その上で unlink を三ケース注入する。

   - `vanished`: real unlink を済ませてから `FileNotFoundError` を投げる。helper は元の `False`、`.s` は不存在。
   - `permission`: `PermissionError` を投げ、同じ例外・errno が外へ出て `.s` が残る。
   - `eio`: `OSError(EIO)` を投げ、同じ errno が外へ出て `.s` が残る。
   - 全ケースで socket/dirfd の閉鎖を確認する。

mock が表すのは「pathname 作成後に wrapper が例外を足す」境界だけとする。pathname、socket FD、dirfd は実物を観測し、mock の `created` / `closed` 属性を成果物の代理にしない。実 AF_UNIX roundtrip は既存 long-path node が担当するため、fault test 自体は sandbox capability に依存させない。

## 受理集合

| 状況 | helper | `.s` | pytest 上の扱い |
|---|---|---|---|
| socket/bind/chmod/stat/listen の capability 不足 | `False` | 不存在 | long-path node だけ exact reason で SKIP 可 |
| capability 十分 | `True` | helper return 時は不存在 | long-path test を完走 |
| bind 部分成功後の例外 | `False` | 不存在 | fault node は PASS 必須、SKIP 不可 |
| cleanup `FileNotFoundError` | 元の bool | 不存在 | fault node は PASS 必須 |
| cleanup `PermissionError` / `EIO` | bool を返さず送出 | 残留または不明 | 実 caller では FAIL/ERROR。fault node は期待例外を観測して PASS |
| helper の恒真・恒偽変異 | 不正 | 任意 | 既存正負 gate が FAIL。SKIP は kill と数えない |

`pytest.skip` の唯一の consumer は [1191–1192](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1191)。新規 fault node と既存正負 gateには skip を認めない。全走では絶対 skip 数だけでなく node ID と理由を記録し、新規 node の skip や long-path node の想定外 skip 増加を拒否する。

## race・symlink・xdist・docstring

- race: absent-before/present-after は test-private directory では十分な所有根拠。ただし hostile writer がその間に同名 entry を置く TOCTOU は原理的に残る。dirfd anchoring と nofollow はパス逸脱を防ぐが、最後の stat と unlink 間の name replacement まで原子的には防げない。
- symlink: preexisting broken symlink も `os.stat(..., follow_symlinks=False)` で存在扱いにし、削除しない。unlink が symlink target を辿ることもない。
- mock fidelity: FNF は「unlink せず FNF」ではなく、先に real unlink してから投げる。Permission/EIO は実際に pathname を残す。process-wide patch は各 `with` 内に限定する。
- xdist: isolation meta-test の [語彙:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:35) と [推移導出:70](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:70) は、新規 test から helper への到達を既に検出する。各新規 test に marker を付ければ [actual == expected:102](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:102) を満たす設計なので、meta-test 本体は no-change。
- docstring: 「全 OSError を False」ではなく「capability-bearing OSError を False、所有・cleanup invariant は別」と境界を明記する。既存の basename、syscall 列、恒真 gate の説明は削らない。

## 変異 positive control

production は変異対象にも含めない。

- M-T146-A（必須）: bind 例外後の actual pathname 再確認、または `owns_path = True` を削除して旧 `created=False` 挙動へ戻す。
  - 既存 T-138 正負 gateは PASS 予想。
  - 新規 partial-bind node が `.s` 残留で FAIL、rc 非0になること。
  - SKIP または rc=0 は SURVIVED。

- M-T146-B（推奨）: cleanup の `except FileNotFoundError` を `except OSError` に拡大する。
  - Permission/EIO parameter が「例外が出なかった」で FAIL。
  - FNF parameter は PASS。
  - これで「全 unlink 異常を同一抑止」に戻せないことを示す。

fix 前 positive control は、partial-bind node の `.s` 残留と、vanished/FNF case の例外送出を期待する。段5/6では変異前後の rc、failed node、skip nodeを記録し、変異復元後に対象ファイルの bytes を照合する。

## 関連受入案

以下は親が実装後に実走する案であり、今回は未実走。

1. 新規3 test、既存正負 gate、long-path node、isolation exactness test。
2. integration と isolation の両ファイル全体。
3. M-T146-A/B の targeted matrixと復元後再走。
4. `python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、`git diff --check`。
5. `python3 tools/run_tests.py` 全走。
6. production no-touch を wave base との差分で確認。
7. commit 後に `python3 tools/check_ai_provenance.py`。

既存被覆は socket factory/bind/listen 拒否の `False`、permissive mock の `True`、正常 cleanup の空 directory、恒偽・恒真変異、実 long-path roundtrip、marker exactness。純増する検出力は、部分成功 bind の回収、preexisting regular/broken-symlink の保存、FNF と Permission/EIO の分離、および対象異常経路での実 socket/dirfd 閉鎖である。

## 総括

GO。

推奨 plan は、integration helper だけを実 pathname の absent→present で所有判定するよう直し、cleanup は FNF のみ冪等成功、Permission/EIO は invariant violation として送出すること。新規 fault test は skip 不可とし、production と isolation meta-test は no-touch とする。

残る裁定点は、test-private directory に concurrent writer がいないという既存隔離契約を ownership の前提として受容するかだけである。hostile writer との原子的な競合まで保証する要求なら、この局所 test-helper scopeでは NO-GOとなり、より広い pathname ownership protocol の別設計が必要になる。