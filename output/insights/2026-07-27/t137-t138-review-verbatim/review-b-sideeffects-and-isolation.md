静的検査のみ実施し、pytest は実行していません。所見はゼロではありません。

## 所見

### 1. 非 daemon 化により、停止処理の退行が「赤」ではなく pytest worker の無期限停止になる経路がある

- **主張:** `daemon=False` は不要な可用性リスクであり、lease 検査へ戻らない退行では `assert not thread.is_alive()` が赤を記録しても interpreter が終了できない。
- **file:line:** [test_dev_waves_integration.py:941](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:941)、[daemon.py:1613](/home/SFC/tanab/github/izanagi/tools/dev_waves/daemon.py:1613)、[daemon.py:1643](/home/SFC/tanab/github/izanagi/tools/dev_waves/daemon.py:1643)
- **失敗シナリオ:** `select.select(..., 0.25)` が退行して timeout なしになった場合、要求処理後の serve thread は `select` 内で永久待機する。主スレッドが `shutdown()` で event を set しても select は起床せず、`join(5)` → assertion failure となる。TemporaryDirectory が `.s` や lease pathname を削除しても、select は開いた listening FD を待ち続けて `lease.assert_valid()` へ戻らないため、非 daemon thread が pytest/xdist worker の終了を永久に阻止する。同様に、`dispatch()`、blocking `accept()`、deadline なしの `send_frame()` 内で停止した場合も lease 失効は観測されない。
- **成果物影響:** 受入全走が完了せず当該 wave を受理集合へ入れられないため、その commit を参照する certified 選択・材料レポート・試行台帳はいずれも生成・更新不能になる。
- **判定:** **must-fix**

提供された `preflight_nondaemon.json` が示すのは、`_shutdown.set()` 単独落としで thread が 0.25 秒周期の loop に戻り、tempdir 削除後に lease 失効を観測できる経路だけです。「必ず終わる」ことの一般的な根拠にはなりません。

`daemon=True` のままでも、新設された `join(5)` と `assert not thread.is_alive()` が shutdown 退行を赤にします。以前偽緑だった原因は daemon 属性だけでなく、生存 assertion がなかったことです。

### 2. 新設された 5 秒の停止 assertion は、共有ノードの scheduler starvation を機能退行として誤判定し得る

- **主張:** 正常な shutdown でも serve thread が 5 秒以上 deschedule されれば新しい assertion が偽赤になる。
- **file:line:** [test_dev_waves_integration.py:960](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:960)、[daemon.py:1615](/home/SFC/tanab/github/izanagi/tools/dev_waves/daemon.py:1615)
- **失敗シナリオ:** `shutdown()` は正しく event を set するが、xdist 全体や同一ノードの高負荷で serve thread が 5 秒以上実行されないと `join(5)` が timeout し、停止契約の退行として赤になる。`xdist_group` は対象 group 内を直列化するだけで、別 worker の CPU・I/O 負荷から隔離しない。
- **成果物影響:** 正しい test-only wave が受理集合から誤排除され、certified 選択・レポート・試行台帳は旧 commit の参照に留まる。
- **判定:** **nit（高負荷実測で再現すれば must-fix に昇格）**

socket 起動の deadline 5 秒と 10 ms polling は差分前から存在するため、この wave が新たに増やした弱点ではありません。一方、join timeout を失敗条件にした点は新規で、既知の [T-136] と同型です。

### 3. probe の cleanup は通常経路では閉じるが、例外安全性と所有権が完全ではない

- **主張:** `probe.close()` の例外時は `.p` の unlink が実行されず、逆に bind 失敗時は helper が作っていない既存 `.p` まで削除する。
- **file:line:** [test_dev_waves_integration.py:900](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:900)
- **失敗シナリオ:** bind 成功後に `probe.close()` が `OSError` を投げると、直後の unlink へ進まず `.p` が残る。また事前に `.p` が存在すれば bind は `EADDRINUSE` になるが、finally が無条件にその `.p` を unlink する。unlink が `PermissionError`/`EIO` を返す場合も socket と dirfd は閉じる一方、`.p` は残って helper 自体が例外終了する。
- **成果物影響:** 現行唯一の caller は node 固有 TemporaryDirectory 内なので、certified 選択・レポート・試行台帳の値や参照は変わらない。影響は当該 test の cleanup error に限定される。
- **判定:** **nit**

通常経路の追跡結果は以下です。

- `os.open()` 失敗: dirfd は取得されておらずリークなし。
- `/proc/self/fd` 不在または alias 長超過の早期 return: 外側 finally が dirfd を閉じる。
- `socket.socket()` 失敗: 外側 finally が dirfd を閉じる。
- bind 成功・通常失敗: socket close → `.p` unlink → dirfd close。
- capability 不足による `pytest.skip`: helper の全 finally が完了した後であり、fd/socket は残らない。
- `probe.close()` または unlink の異常: 上記 nit の不完全経路。
- 後続 node 汚染: 各 node の TemporaryDirectory が異なるため、通常はなし。

### 4. 現在の xdist marker 照合は壊れないが、`socket.socket` 不在は将来の隔離穴である

- **主張:** 現差分では group は維持されるが、meta-test の runtime 語彙は raw AF_UNIX helper を本質的には認識していない。
- **file:line:** [test_dev_waves_isolation_contract.py:33](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_isolation_contract.py:33)、[test_dev_waves_integration.py:891](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:891)、[test_dev_waves_integration.py:945](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:945)
- **失敗シナリオ:** 現 node は `threading.Thread` で直接 taint され、helper も docstring 内の文字列 `bind_repo_socket` に偶然マッチするため expected/marker は一致する。将来、Thread を使わない raw-socket nodeを追加する、または helper の docstring から旧 API 名を消すと、`socket.socket` が語彙にないため必要な group を導出できない。
- **成果物影響:** 現差分では受理集合・certified 選択・レポート・試行台帳への影響なし。将来は非直列 node の残留 socket/FD により受入結果が不安定になり得る。
- **判定:** **nit・本 wave の scope 外候補**

静的 AST 導出では expected と marked は同じ 8 node でした。これはテスト実行結果ではありません。

## 波及確認

- `import socket` の実行時利用は新 helper の 1 箇所だけで、同名ローカルとの衝突はありません。
- 削除した `bind_repo_socket` import に他の実行時 caller はありません。残る出現は helper の説明文だけです。
- 新 helper は当該 node からのみ呼ばれ、名前が `test_` で始まらないため pytest node として収集されません。同名 helper もありません。
- `.p` を名前で拾う残留検査・freeze scan・directory exact-set assertion は見つかりませんでした。同ファイルの runtime 内容検査は別 TemporaryDirectory の node であり、競合しません。
- 提示された patch に本番ファイルの差分はありません。

## 親が次に測るべき実測

1. **無期限 select 変異による worker hang の positive control**

   `daemon.py:1615` の timeout だけを一時的に `None` にしたうえで、復元規律付きで実行:

   ```bash
   timeout --signal=TERM --kill-after=5s 20s \
     python3 -m pytest -q \
     orchestrator/tests/test_dev_waves_integration.py::test_socket_roundtrip_works_beyond_108_byte_repository_path
   ```

   現構成の予想は pytest の通常の `rc=1` ではなく外部 timeout の `rc=124`。これが出れば所見 1 を直接実証します。

2. **高負荷下の join(5) 偽赤確認**

   ```bash
   for i in $(seq 1 20); do
     python3 -m pytest -q -n 32 --dist=loadgroup \
       orchestrator/tests/test_dev_waves_integration.py \
       orchestrator/tests/test_dev_waves_isolation_contract.py || break
   done
   ```

   期待は 20/20 完走し、`shutdown() が serve ループを止めていない` が一度も出ないこと。発火すれば所見 2 を must-fix へ昇格。

3. **probe cleanup の fault injection**

   `probe.close()` が実 socket を閉じた直後に `OSError` を投げる wrapper を一時注入して helper を単独実行し、例外後の `Path(directory, ".p").exists()` を確認する。現コードの期待値は `True`。これにより unlink が close 例外に耐えないことを確定できます。