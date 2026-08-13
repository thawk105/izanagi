# 親の実データ実走 (実測) — [T-1027] wave

完了条件 [T-1028] (rulings9 #16) 「親が実データで 1 回通す」の実施記録。
すべて 2026-08-13、worktree `dev-wave-t1027-acceptance-reds-checker`、commit `67a46f10`。

## 焦点走 (緑)

```text
python3 tools/run_tests.py --force-dispatch -p no:cacheprovider \
  orchestrator/tests/test_check_acceptance_reds.py
→ 67 passed in 2.67s (dispatch 経由、rc=0)
```

wave 前は同 file 36 test。67 へ増えた。

## 実走 1 — 空振り (log が緑だった)

対象 log `known-red-octopus/acceptance.log` は**後の走行で上書きされており赤 0 件**
(`10412 passed, 65 skipped`)。checker は `status=green` / rc=0 を返したが、
**赤が無いため collection 経路を一度も通っていない。**
これは完了条件の証拠にならないと判断し、実 log を全数走査して選び直した。

## 実走 2 — 真の再現条件で 5 つ目の実環境欠陥

対象 log `dev-wave-t139-a12-stress-check/acceptance3.log`。
赤 1 件、しかも**打ち切りを起こす当のファイル**にある。

```text
orchestrator/tests/test_codex_worker_launch.py::test_codex_argv_has_exact_trust_bypass_without_sandbox_bypass
```

(この file は 114 test / collect 出力 12,098 bytes で、relay 上限 4 KiB を超える。
 当該 nodeid が現 main の collection に実在することは dispatch receipt の
 全文 tail で確認済み。)

結果:

```text
status=invalid-input
reason=probe worktree is not clean, including ignored files
rc=2
```

## 実走 3 — 計測して原因を特定

repo 外に checker の計測用コピーを作り、指紋不一致時に `git status` 本文を出させた。

```text
PROBE-DIRTY-BEGIN
!! orchestrator/campaign/__pycache__/
!! orchestrator/codex_roles/__pycache__/
!! orchestrator/tests/__pycache__/
!! output/pegasus-dispatch/
!! tools/__pycache__/
!! tools/dev_waves/__pycache__/
PROBE-DIRTY-END
```

**残 blocker の構造:**

- `_assert_probe_identity` は指紋が空 tree の sha256 と一致することを要求する
  (= ignored file も含めて完全に空)。
- しかし checker 自身が collection のために probe worktree 内で pytest を dispatch する。
  計算ノードは同じ共有ファイルシステム上の probe worktree へ書くため、
  `PYTHONDONTWRITEBYTECODE=1` は PBS job へ伝播せず `__pycache__` が残る。
- `output/pegasus-dispatch/` も残っている (R4 の限定 cleanup が届いていない)。
- 結果、**checker が自分で作った残骸で自分を止めている。**

**この欠陥は本 wave の変更由来ではない。** `git show 67a46f10` の diff に
`_probe_fingerprint` と `_initialize_submodules_cache_only` の変更は無い。
前 wave では collection が先に失敗していたため、この先の障害が露出していなかった。

**新規 worktree が本当に空であることは実測済み** — 手で `git worktree add` した直後の
probe worktree で同じ指紋 command を走らせると 0 行 (clean)。
cache-only submodule init を行った後も 0 行のままだった。
つまり残骸は**すべて checker 自身の子が作ったもの**である。
