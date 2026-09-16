# 段 6 裁定 追補 1 — 契約テストが B3 の不具合を期待値として固定している

**正本の関係:** `stage6-ruling.md` を追記で訂正する。衝突したら本書が優先する。

**発生:** fix 単位 F1 が編集前に fail-closed で停止した。**判断は正しい。**

`orchestrator/tests/test_pegasus_tools.py:487`
`test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench` は、**mocc を含む** job body に

```bash
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
```

が**ちょうど 1 回**あることを要求する。この期待値は段 5 の単位 B が「全 15 本を同じ 1 行にする」指示に
従って入れたものであり、**mocc についてはこの行こそが B3 の不具合** (自己 hydrate 前に、mocc が
一度も埋めない場所を見る) である。

## 決定

### (1) mocc の分岐に限り、期待値を「hydrate 出力の契約」へ置き換えることを許可する

これは**本 wave 自身が焼き込んだ誤った期待値の訂正**であり、「生き残る正しい挙動の期待値を緩める」
ことではない。ただし**同じ厳密さ**を保つこと。置き換え後の mocc の期待は少なくとも次をすべて exact に検査する。

1. 計算ノード上の hydrate (`fetch_third_party.py ... hydrate ... --staging-root ...`) が、
   gflags の source 存在検査・HEAD 照合より**前**にある。
2. gflags / glog の source path が、その hydrate 出力の `.source_root` から導かれる。
3. hydrate の既存検査 (cache root 必須、`.source_root` の絶対 path 検査、stderr の保存) が残る。
4. **mocc に、env / checkout 既定の staging を gflags / glog の解決元にする行が残っていない**
   (残すと B3 が再発する)。

### (2) mocc 以外の 14 本の期待値は変えない

とくに silo: B1 の直し方で silo の scratch に gflags / glog が入れば、silo の既存の 1 行は正しい解決になる。
**silo の期待値を変える必要が生じた場合だけ**、(1) と同じ条件 (同じ厳密さ・変更理由の報告) で許可する。

### (3) 報告

置き換えた assert の旧文と新文を並べて報告すること。検出力を落としていないことを、
「旧期待値が拒否していた入力を新期待値も拒否するか」で 1 行ずつ示すこと。

### (4) M11 の期待 node

(1) の置き換え後の node (または mocc の順序を検査する専用 node) を M11 の期待 node とする。
