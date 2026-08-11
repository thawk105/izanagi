# [T-816] FN-2 trace v2 の C++ 半分 — 実装・実測・変異台帳 (2026-08-11)

**status: 手順 1・2 完了。手順 3 (人間の push と承認定数更新) 待ち。**
一次資料: 本文書 + `verbatim/` + 変異台帳 2 組 + TRACE=0 同一性 JSON 3 本 + `emitter-probe-digest.txt`。

wave = `dev-wave-t756-fn2-trace-v2` / branch `worktree-dev-wave-t756-fn2-trace-v2`。
裁定は [T-816] Q1〜Q3 全問 (a)。**担ったのは 4 段手順のうち 1・2 だけ。**

## 1. 成果物

| もの | 値 |
|---|---|
| 新 commit (submodule、local のみ) | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| submodule branch | `izanagi-trace-t816-fn2` (親 = 現行 pin `d706650`) |
| bundle (repo 外、完全な履歴) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/izanagi-trace-t816-511c953.bundle` |
| bundle sha256 | `3a36b53094243234fe119d746396fc9bf56259a07b25c968a225774297dbb82b` |
| 親 repo の gitlink | `d706650cdb31e442bef45b9b4216951d4fb40969` (**不変**) |
| 承認定数 | `CCBENCH_FULL_SHA` / `CURRENT_PIN` とも**不変** |
| checker | `tools/check_trace0_preprocess_identity.py` |

**bundle からの復元は実証済み** — 新規 clone を作り、HEAD が新 SHA に一致すること、
ファイル内容が v2 であること、さらにその clone に対して checker を走らせて同じ判定が出ることを確認した。

## 2. 形式 (v2)

```
C <txid> <thid> <epoch> <tid> <read_count> <write_count>   7 token (v1 は 5 token)
R <txid> <key_hex> <ver_epoch> <ver_tid>                   v1 のまま
W <txid> <key_hex> <op> <epoch> <tid>                      v1 のまま
X <txid> <key_hex> <reason>                                v1 のまま
E <txid>                                                   新規。txn 記録の終端
```

v1/v2 は C 行の token 数で判別できる (版行を置かない)。SI は v1 helper のまま。

## 3. 実測

### 3.1 規律 1 (TRACE=0 側の等価性)

旧 `d706650` 対新 `511c953`。**16 context (8 genome × 2 overlay) 全件一致、3 本すべて `result: pass`。**

| run | compiler | repo | 結果 |
|---|---|---|---|
| `trace0-identity-g++-11.json` | g++-11 (11.4.0) | wave の submodule | pass |
| `trace0-identity-g++-12.json` | g++-12 (12.3.0) | wave の submodule | pass |
| `trace0-identity-restored-clone.json` | g++-12 | **bundle 復元 clone** | pass |

差分 path は `--expect-paths cc/silo/transaction.cc` で固定した。
`g++-13` はこの環境に存在しない (段 2 プランは実走条件に据えていたが、runbook §7 の記述どおり不在)。

### 3.2 emitter の実測 (計算ノード、request 903846)

bundle 復元木を TRACE=1 でビルドして YCSB を 1 本走らせ、raw trace を verifier を通さず照合した
(現行 parser は v2 を読めないため)。逐語は `emitter-probe-digest.txt`。

- trace 4 ファイル、**committed txn 244,971 件**
- **framing 違反 0 件、v1 (5 token) C 行 0 件**
- C が宣言した read/write 件数と実 R/W 行数が全件一致、各 txn の末尾に E がちょうど 1 本

1 回目の probe は依存 (gflags) 不足で configure が落ちた。計算ノードに gflags/glog は無いので、
pinned ソースから prefix へ static install する形に直して取り直した。

### 3.3 変異 (2 巡、通算 KILLED 6/6・SURVIVED は drift control 1 件のみ)

| # | 変異 | 1 巡目 (spec A) | 2 巡目 (spec B) |
|---|---|---|---|
| M1 | `--expect-paths` の厳密一致を無効化 | KILLED (2 node) | — |
| M2 | TRACE=0 正規化出力の比較を無効化 | **MISMATCH** (4 node) | **KILLED** (4 node) |
| M3 | include 活性の比較を無効化 | KILLED (1 node) | — |
| M4 | header 拒否を無効化 | KILLED (5 node) | — |
| M5 | context 件数 gate を無効化 | **SURVIVED** | **KILLED** (1 node) |
| M6 | compiler 不在を素通しに | KILLED (1 node) | — |
| M7 | drift control (コメントのみ) | SURVIVED (期待どおり) | — |

**erratum:** 1 巡目の M2 / M5 の結果は `mutation-ledger-a.json` に残す。

- **M2 は検出自体はされていた。** 親の期待 node が 1 件ずれていた — 実測では
  `test_non_cpp_changed_path_is_rejected` ではなく
  `test_every_modified_cpp_source_is_checked_without_expected_paths` が落ちる。
  非 C++ path は suffix gate が先に拒否するようになったためで、これは fix で明記した
  「冗長な gate は単独変異の kill 証拠に使えない」の実例である。
- **M5 の SURVIVED は変異が本来の仕事をした結果である。** 既存テストが到達していたのは
  「context 列挙が空」を拒否する gate で、「実際に積んだ件数が期待数と一致しない」gate には
  テストが 1 件も無かった。production は正しかったのでテストだけを足し、2 巡目で KILLED になった。

**変異 harness の制約 (実測):** 失敗 node が多い変異は失敗 digest が予算で切り詰められる。
`git diff-tree` から `-r` を落とす変異は **26 件失敗**するが digest は 12 件しか出さない
(`omitted_failures=14`)。期待 node の完全集合を記録できないので KILLED 勘定から外し、
実測値だけを証拠として残した。narrow な gate へ再照準するのが正しい扱いである。

### 3.4 焦点走

fix 後 **38 passed / 0 failed** (新 checker のテスト + plain-runner meta-test)。
fix 前は meta-test が 1 件赤だった (新テストの自走 harness が検出器の literal に当たらない形)。

## 4. 敵対検証が捕らえたもの (全件 real と裁定)

段 3 (プラン攻撃) と段 6 (実装攻撃) で計 9 件の blocker。主なもの:

1. **承認済み・未 push の pin `c9c1a9c` ([T-167]) の存在** — 新 commit の系譜が兄弟分岐になる。
   裁定パッケージへ (`verbatim/ruling-package.md`)。
2. **`git diff-tree --raw` に `-r` が要る** — 無いと tree 単位。親が 028f34d→d706650 で実測。
3. **`g++-13` 不在** — 実走条件を g++-11 / g++-12 へ変更。
4. **context 集合が空でも pass** (fail-open) — 列挙元から期待数を導出して塞いだ。
5. **header 変更の死角** — `-E -P` は `#define` を出力に残さない。header 差分を拒否する形に。
6. **JSON の old/new digest が旧側の複製** — 独立計算へ。
7. **新テストの自走 harness が実際に赤** — 子は「harness あり」と報告していた。存在と効力は別物。
8. **helper 残置による C 行の二重出力** — `emit_commit` は残さず置換する契約にした。
9. **v1 拒否を protocol 無差別に適用すると SI が壊れる** — 手順 4 の hard block 条件として返す。

## 5. 閉じた範囲と閉じていない範囲

**閉じるのは「C が宣言した件数に対する R/W framing の欠落」だけ。** 次は閉じない。

- **同時欠落**: write set から要素が消えれば件数も W 行も同時に減る → write-intent shadow の領分。
- **X 行の中間欠落**: C は X の件数を宣言しない。
- **内容の置換**: 件数が合ったまま R/W の中身が別物になる形。
- **実行の完了**: W 行は実データ更新より前に出るので、E は write loop 終端到達を示すだけ。

checker の保証も「翻訳単位の同一性」ではなく「選定した macro context における TRACE=0 正規化
preprocess 出力の同一性、および include 活性の同一性」に限定して名乗る。

## 6. 次

手順 3 は**人間手番** — bundle から取り込んで `origin/izanagi-trace` へ push し、新 pin を承認する。
手順 4 (gitlink 前進・承認定数更新・verifier の v2 配線・v1 拒否・characterization 反転) は
承認後の別 wave。その前に `verbatim/ruling-package.md` の 2 問を裁定する必要がある。
