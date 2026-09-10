# 親が実 repo で走らせた結果 (段 5 単位 A の統合直後)

実行日 2026-08-27。対象 repo は main checkout `/work/1/SFC/tanab/izanagi`。
実装は wave worktree の commit `c58f4acac`。

## D1. 親のテスト実走 (子は sandbox 制約で pytest を実走できなかった)

```
$ python3 tools/run_tests.py orchestrator/tests/test_check_branch_rescue.py
28 passed in 3.92s      (child rc=0、Pegasus job 950821.nqsv、Elapse 10S)
```

子が内容走査で特定したメタテスト 4 file も親が実走した。

```
$ python3 tools/run_tests.py orchestrator/tests/test_login_headroom.py \
    orchestrator/tests/test_pegasus_dispatch_compute.py \
    orchestrator/tests/test_p3_build_authority_cli.py \
    orchestrator/tests/test_pytest_collection_config.py
475 passed, 1 skipped in 66.21s
```

## D2. 実データ dogfood — **rc=2。実 repo で絵を描けない**

```
$ python3 tools/check_branch_rescue.py --repo /work/1/SFC/tanab/izanagi \
    --branch worktree-cleanup-branches-20260825
RC=2
```

出力 JSON:

```
issues = [ { code: "worktree-list-parse-error",
             phase: "assessment",
             scope: "repository",
             subject: null,
             message: "unknown worktree field: locked" } ]
root_snapshot.complete = false
root_snapshot.stable   = false
deletion_loss_closure.complete = false
deletion_loss_closure.commit_count = null
candidate_status = null
```

**この branch は親の独立実測では喪失閉包が 1 commit ある** (段 4 の N7)。
つまり本来 rc=0 で 1 commit を出せるはずの入力である。

### 原因と射程 (親の実測)

`git worktree list --porcelain` が `locked` field を出し、parser がそれを未知として拒否する。

```
$ git worktree list --porcelain | sed 's/ .*//' | grep -v '^$' | sort | uniq -c | sort -rn
     53 worktree
     53 HEAD
     37 locked
     27 branch
     26 detached
```

**53 worktree のうち 37 本が locked。** したがって現状の実装は、この repo に対して
**どんな入力でも rc=2 になる**。「常に止まる関門」であり、この wave が段 3 で
否認したのと同じ形である (段 4 の裁定 §2.1 / レンズ B 所見 3)。

`locked` は 2 つの行形が実在する。

```
locked
locked claude session dev-wave-b10-overthrottle-grid (pid 2811098 start 260073566)
```

`prunable` と `bare` はこの repo では 0 件だが、git の porcelain 語彙には存在する。
`prunable` は裁定 §2.3 で「期限付き root」に分類した対象そのものなので、
parser がその field に到達できないままでは分類が発火しない。

### 段 6 fix への要求

1. porcelain の既知 field を網羅し、**未知 field を見たときに fail-closed する範囲を
   「その worktree record」に限定するか、issue にしたうえで root としては安全側
   (= 恒久 root として残す) に倒すか**を裁定どおりに決めること。
   未知 field 1 個で repo 全体の絵を捨てる現在の形は、実環境で成立しない。
2. `locked` の 2 形、`prunable`、`bare`、`detached` の有無の全組合せをテストの母集合に入れること。
3. **修正後、親がもう一度実 repo で走らせて rc=0 と非空 closure を確認する。**
   これを通すまでこの道具は完成ではない。

## D3. 段 6 レビューで見るべき点 (親のメモ)

台帳 schema に `gc_headroom_at_loss` が残っている。裁定 §2.4 は
「総数由来の headroom を出さない」と定めた。これが標本由来か総数由来かを確認すること。
