# 段 1 brief — [T-340] Pegasus third-party source の pin 検証つき取得経路

repo: /work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch (branch worktree-wave-t340-thirdparty-fetch, base 504ed6d)

## 確定済みユーザー裁定

択 (a) 採用 — `tools/pegasus/` に **pin 検証つきの取得経路**を置く。置き場の規約化だけに留めない。
対象は masstree / mimalloc / googletest。`gflags_source_path` / `glog_source_path` の絶対パス
直参照を scope に含めるかは実装 wave が判断する。

## 問題 (T-340 の実害)

`tools/pegasus/submit_silo_ladder_rung1.sh:152` は
`THIRD_PARTY_ROOT="$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"`
へ clone する。**worktree を畳むと実体が消える。** 前回の wave は policy.json の url+pin から
手で `~/github/{masstree,mimalloc,googletest}` を取り直した。取得の入口が repo 外に無い。

## scope

`tools/pegasus/` に新規ファイルだけで、(1) repo 外の永続 cache へ pinned clone を作る経路、
(2) その cache から worktree 内 job-staging へ pin 検証つきで hydrate する経路、(3) verify を置く。
テストを添える。docs は親が書く。

**成果物影響 (DW-G05):** 実装しない場合、新しい worktree で rung1 を投入するたびに GitHub からの
再 clone が要り (login node の network 依存)、worktree を畳めば実体が消えて手作業取得へ戻る。
attempt receipt の値 (`third_party_heads`) は pin と同一なので**数値・受理集合は変わらない**が、
pinned-clean source の**由来が人手依存**になり、再現手順が台帳から追えなくなる。

## 不変条件 (破ったら停止)

1. **凍結 4 本を 1 byte も変えない。**
   `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の `binding` が
   `tools/pegasus/policy.json` / `tools/pegasus/silo_ladder_rung1.sh` /
   `tools/pegasus/submit_silo_ladder_rung1.sh` / `orchestrator/campaign/silo_ladder_rung1.py` を
   sha256 で束縛し、`orchestrator/tests/test_silo_ladder_rung1_evidence.py` が照合する (現在一致、実測済み)
2. 既存の pin/clean 検証を弱めない・迂回しない。新経路も HEAD==pin と
   `git status --porcelain --untracked-files=all` 空を必ず検査する
3. 既存 clone に対して fetch/pull しない (submit script と同じ契約)
4. network を要求する操作と offline で完結する操作を分離する (計算ノードは network/DNS 無し)
5. 受理集合を変えない。`third_party_heads` の値は policy の pin と同一のまま
6. tracked tree を汚さない (hydrate 先 `output/env/pegasus/silo_ladder_rung1/job-staging/` は
   `.gitignore:24` で ignore 済み)
7. `tools/pegasus/policies/*.json` を新設するなら `registry_v1.json` へ登録する
   (`test_pegasus_policy_registry_is_complete_and_tracked`)

## 親の provisional 裁定 (攻撃対象)

- **(P1) cache root の既定値** = policy.json の `gflags_source_path` の親ディレクトリ。
  実測: `/home/SFC/tanab/github` に masstree/mimalloc/googletest/gflags/glog の 5 本が
  pin 一致・clean・origin url 一致で現存する。machine 固有 path を新規にコードや横断 docs へ
  書かずに済むのが理由。代案: 環境変数必須 / `tools/pegasus/policies/thirdparty_v1.json` 新設 /
  `--cache-root` 必須で既定なし
- **(P2) hydrate を scope に含める。** submit script の `if [[ ! -e "$destination" ]]` 分岐 (:173) を
  満たす形で job-staging を先に埋めれば、凍結ファイルを触らずに consumer 接続が成立する。
  submit の pin/clean 検証はそのまま走る
- **(P3) gflags/glog の絶対パス直参照の解消は scope 外。** policy.json が凍結されているため
  直参照そのものは動かせない。verify の対象に含めるだけに留める

## 成果物の形

- `tools/pegasus/fetch_third_party.py` (新規、Python)
- `orchestrator/tests/test_pegasus_thirdparty_fetch.py` (新規、local git fixture のみ、network 不要)
- docs 1 節 (親が書く)

## 並列分割方針

段 5 は 1 実装子 (tool + test は同一所有)。段 3 と段 6 は 2 レンズ並列。
