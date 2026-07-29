結論は **NO-GO**。現実装の cleanup 本体は概ね正しいものの、段6 blocker が2件あります。編集・テスト実走はしていません。

## real findings

### R1 — 重大 / blocker: pathname 不在でも ownership syscall を要求している

[integration.py:1128](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1128)〜1132 は、すべての bind failure で無条件に `getsockname()` を呼びます。

静的再現:

1. fresh directory で `.s` は不在。
2. `bind()` が pathname を作らず `EPERM`。
3. 未bind socket の `getsockname()` も `EPERM`。
4. helper は `False` を返さず例外送出。
5. [同:1385](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1385) の既存 exact-reason SKIPへ到達せず FAIL。

[同:1237](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1237)〜1240 が `getsockname=""` を注入しているため、この実環境断面を隠しています。

成果物影響: production artifact の値・参照は不変ですが、対応 sandbox の test acceptance が「既存 exact-reason SKIP」から「EPERM FAIL」へ承認なく縮小します。

最小 fix:

- bind failure 後、literal `.s` を dirfd + `follow_symlinks=False` で観測する。
- 不在なら ownership 観測なしで `False`。
- present の場合だけ `getsockname()` を呼び、alias 一致時だけ `owned=True`。
- 既存 bind-failure test の `getsockname` を `EPERM` side effect にし、呼ばれず `False` になることを固定する。

### R2 — 重大 / blocker: fault matrix が例外種別×pathname状態を閉じておらず、M‑T146‑B は等価変異

cleanup は [同:1147](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1147)〜1165、fault 注入は [同:1272](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1272)〜1285です。

| unlink 結果 | pathname | 契約 | 現 test |
|---|---|---|---|
| FNF | absent | 元 verdict を維持 | `True` のみあり |
| FNF | present | 元 FNF を再送出 | なし |
| EPERM/EIO | present | 元例外を送出 | あり |
| EPERM/EIO | absent | 元例外を送出 | なし |
| success | present | `FileExistsError` | あり |

静的再現は2通りあります。

- FNF handler を単純抑止へ退行させても、`fnf-after-real-unlink` は既に absent、`no-op-unlink` は例外 branch を通らないため、現8 nodeでは検出できません。
- [plan v2:56](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s4-adjudication-plan-v2.md:56) の M‑T146‑Bどおり外側を `except OSError` に広げても、現 EPERM/EIO は unlink 前に投げて pathname が残ります。その後 `stat()` が成功し、[integration.py:1154](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1154) の bare `raise` が同じ例外を再送出するため、type・errno・present の期待はすべて維持されます。従って期待した kill にはなりません。

成果物影響: test acceptance が、FNFなのに pathnameを残して成功扱いする実装や、side effect 後のEPERM/EIOを catch-all で抑止する実装を受理できます。M‑T146‑Bを kill として記録できず、段6 mutation proof が成立しません。

最小 fix:

- `fnf-with-path-present` を追加し、元FNFとpathname残留を確認する。
- `eperm/eio-after-real-unlink` を少なくとも1件追加し、pathname不在でも元例外を要求する。
- FNF-after-real-unlink は pending verdict `True/False` の双方を固定する。
- その後に M‑T146‑Bを再照準し、非等価になったことを静的確認してから実走する。

### R3 — 低 / nit: close→unlink の時間順序は test が固定していない

実装順は [同:1141](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1141)〜1147で正しく、socket close試行後にunlinkしています。一方、testは [同:1307](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1307) で最終的な `closed` しか観測しません。両ブロックを交換しても現assertは静的には通ります。

成果物影響は将来の検出力だけで、single-writer callerの現 verdict・product値は変わりません。段6 blockerにはしません。必要なら fake socket と injected unlink に event log を持たせ、`close < unlink` を固定するのが最小です。

## refuted

- **preexisting entry の `FileExistsError` 化:** 承認可能です。[同:1110](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1110)〜1117 は nofollow で regular file / broken symlink を検出し、socket生成前に停止します。所有外 caller はなく、唯一の実callerはfresh runtimeを使うlong-path nodeです。正常受理集合は変わらず、汚染時だけSKIPから明示FAILへ硬化します。
- **path-present bind failure の識別:** single-writer前提では、alias-boundなら部分成功、非aliasならforeignとして非所有にできます。ただしR1のpost-bind pathname観測を先に置く必要があります。
- **cleanup実装:** 現コード自体は、FNF+absentでpending verdictを維持し、no-opを`FileExistsError`、EPERM/EIOを元オブジェクトのまま送出します。問題はR2の検出集合です。
- **patch / dirfd / symlink:** `socket.socket` と `os.unlink` はhelperが参照する実体に当たり、patch復元後に保存済み`real_unlink`を使っています。pathname観測はdirfd + nofollow、broken symlinkは`readlink(dir_fd=...)`で忠実です。
- **通常 product artifact:** tracked差分はintegration test 1枚だけで、`tools/dev_waves/protocol.py` とisolation meta-testは不変です。

## scope外候補

- **cleanup例外を外側 `os.close(fd)` が上書き:** [integration.py:1166](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1166)〜1167には実在する二重fault経路があります。test finalizerもreal unlinkが非FNFを投げるとdirfd closeへ到達しません。ただし任意close fault族はplan v2で明示的にscope外であり、独立再現もないため今回のblockerにはしません。将来はprimary例外を保持したままclose例外をchain/noteし、finalizerを二重finallyにするのが最小です。
- **hostile concurrent writer / production partial-bind:** stat→getsocknameは原子的ではありません。またproduction側も [protocol.py:260](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/dev_waves/protocol.py:260)〜279でbind後例外族を一般化していません。どちらも今回のsingle-writer test-helper scope外です。

テスト実走は0件です。「8 passed」「isolation 1 passed」「long-path 1 failed」はauthor提供データであり、本レビューによるgreen確認ではありません。

## 総括

**NO-GO。** 段6 fix必須事項は次の2点です。

1. path-absent bind failureでは`getsockname()`を省き、安全に`False`へ戻す。既知のbind EPERM + getsockname EPERM断面を決定的testにする。
2. FNF-present、non-FNF-absent、FNFの元`False` verdictをfault matrixへ追加し、等価なM‑T146‑Bを再照準する。

この2点を閉じるまで、既知赤もmutation proofも受理できません。