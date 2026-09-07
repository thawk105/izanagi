# 実 repo `output/` snapshot の git 索引経由化 — 実測と変異検査

wave: `dev-wave-acceptance-speedup-20260905` / 2026-09-07

主題は受入全走の高速化。**律速を実測で特定し、正しさを緩めずに削る**ことを目的とした。
本書は測定値・変異検査・反証された仮説の記録である。設計判断の正本は decisions 台帳、
経緯の正本は worklog である。

## 1. 何が遅かったか

`orchestrator/tests/test_s8b_floor_campaign.py` の `_real_output_snapshot()` は、
実 repo の `output/` を歩き、**git 追跡下の 18,126 file (478.7 MB) をすべて開いて sha256** を取る。
呼ぶ test は 10 本 (parametrize 展開後 12 nodeid) で、各 test が前後比較のため 2 回呼ぶ。

ログインノード実測 (1 プロセス、本 worktree):

| 項目 | 値 |
|---|---:|
| 1 回 cold | 90.85 秒 |
| 1 回 warm | 10〜13 秒 |
| うち walk (scandir、stat なし) | 0.68 秒 |
| うち **stat 18,126 回** | 約 9 秒 |
| うち内容読取 + sha256 | 残り (実効 19 MB/s) |

**費用の主は内容のハッシュではなく Lustre へのメタデータ問い合わせ (stat) である。**
これは repo の成長に比例して伸びる作りで、`D335` が禁じる型の既存債務にあたる。

## 2. 何をしたか

git の索引を「内容の同一性」の出所にした。**返り値のタプルは 1 bit も変えない。**

1. `git ls-files -s -v -z` で index blob sha と index flag を取る (stat 不要)
2. `git status --porcelain=v1 -uall -z` で作業ツリーと index の差分集合を取る
3. clean な追跡 file は **`(index blob sha, repo 相対 path)`** をキーに sha256 をプロセス内キャッシュ
4. dirty / 未追跡は実体を読む。空 directory と symlink は walk から取る

索引と設定だけで判定する 5 つのフォールバック (fail-closed):
work tree 外 / `assume-unchanged`・`skip-worktree` flag / 部分木の `.gitattributes` /
`core.autocrlf` / 直下 `.gitattributes` の変換有効化。

### ログインノードでの検算 (pytest 非経由、実 `output/` 全体)

| 項目 | 値 |
|---|---|
| 高速路 vs 独立参照オラクル | **完全一致 True** (19,686 entry) |
| 高速路 初回 | 16.92 秒 |
| 高速路 定常 (4 回) | 3.90 / 5.23 / 7.55 / 5.65 → 平均 3.84 秒 |
| 参照オラクル | 12.25 秒 |
| `git ls-files -s` / `ls-files -v` / `status --porcelain` | 0.013 / 0.032 / 2.1 秒 |
| `git ls-files --eol` (**使わない**) | **27.8 秒** (working tree を読むため) |

## 3. 実機 (compute) の測定

**比較の定義。** 一次資料は `/work/1/SFC/tanab/.izanagi-acceptance-shards/*/junit.xml`。
wall は `testsuite@time` の最大 (D1620 の測定面)。改修前は固定窓
2026-09-04 03:07〜09-07 03:07 の **63 走**。改修後は本 wave の受入 1 走
(session `a1bc597644abc00ece658577ee3b9594`、3 shard)。

| 指標 | 改修前 63 走 | 改修後 1 走 |
|---|---|---|
| snapshot を呼ぶ 12 node の合計 | 中央値 **1,384.8 秒** (最小 1,017.8) | **990.3 秒** |
| 同 1 本平均 | 中央値 **115.4 秒** (最小 84.8) | **82.5 秒** |
| 最遅 shard の wall | 中央値 **324.3 秒** / p90 431.4 | **264.5 秒** |
| 300 秒超過 | 37/63 = 58.7% | 0/1 |
| 最長単体 node | 中央値 191.7 秒 | 188.2 秒 |
| 1 走の総作業 (testcase 合計) | 中央値 18,552 秒 | **21,467 秒 (+16%)** |

### 証拠の強さ (n=1 の後標本が改修前分布のどこに落ちるか)

| 指標 | 改修前 63 走中、後標本以下だった走行 |
|---|---|
| snapshot 12 node 合計 990.3 秒以下 | **0/63** (改修前の最小は 1,017.8 秒) |
| 同 1 本平均 82.5 秒以下 | **0/63** (最小 84.8 秒) |
| 最遅 shard wall 264.5 秒以下 | **16/63** (最小 231.3 秒) |

**読み方。**

- **狙った node は改修前 63 走の全範囲の外に出た。** しかも総作業が中央値より 16% 多い
  (= より混雑した) 条件での値である。効果は実在する。
- **wall の改善は 1 標本では言えない。** 264.5 秒以下だった走行は改修前にも 16/63 ある。
  wall は他の test の帯で決まっており、単独の後標本では分布の重なりを排除できない。
  中央値比では −59.8 秒だが、**これを本変更の寄与として主張しない。**
- 最長単体 node はほぼ不変 (191.7 → 188.2 秒)。本変更は床を動かしていない。

## 4. 反証された仮説 (親の誤り)

段 6 の敵対レビューが一次資料で反証し、親が受け入れたもの。**再提案しないこと。**

| 親の主張 | 実際 |
|---|---|
| 呼び出しは 40 回 (484 秒) | **22 回 (約 253 秒)**。20 は call site 数で test 数ではない |
| キャッシュは 1 プロセスに載る | **最低 4 プロセスへ分散**。11 node の testcase 合計 1,261.267 秒 に対し shard wall 411.888 秒 |
| これが最長単体 node の犯人 | **63 走中 4 走 (6.3%) でしか最長でない。全消ししても最長中央値 191.690 秒は不変** |
| wall 中央値 338 秒 / 78% 超過 | **324.3 秒 / 58.7%** (前者は junit mtime と receipt からの近似。撤回) |
| collection の resolve キャッシュは 1 shard 87.6 秒 | **wall では約 1.8 秒** (87.6 秒は CPU 合計。48 worker は並列) |
| 実 repo 全体の等価性テストは wall を 98 秒食う | **約 2.3 秒** (node 時間と wall 増分の取り違え) |
| 対象 test は `xdist_group("real-repo")` で直列固定 | **1 本も登録されていない** (同 file からの登録は ccbench build canary 3 本のみ) |

## 5. 却下した高速化案 (いずれも実測に基づく)

- **チェック回数の削減 (per-test → per-module)** — 最も効くが「test A が汚し test B が戻す」を
  検出できなくなる。**受理集合の拡大であり採らない。**
- **mtime / size だけの弱い検出器** — 同上。
- **digest を `(path, size, mtime, ino, dev)` でキャッシュ** — 15% しか減らない。stat が残るため。
- **blob sha 単独のキャッシュキー** — `.gitattributes` の変換で同じ blob が異なる working bytes へ
  展開されうるので衝突する。path を含めると初回だけ約 6.7 秒増える (相異なる blob は
  12,074 / 18,126 file) が、**この費用を払う。**
- **実 repo 全体を参照オラクルと比較する常設テスト** — repo 成長比例 node を受入へ常設し、
  本 wave が返済している債務を作り直す。代わりに大きさに依存しない性能モデルのテストを置いた。

## 6. 変異検査

spec: `mutation/mutation-spec.json` (sha256 `83a056a9faaabc6e78b48e5091a7fa05a7b16dbfb9fe4cd2ca787fb6e85ba02d`)
台帳: `mutation/mutation-ledger.json`。実装前に事前登録し、固定 HEAD `45aad0e7b` へ本走 (dispatch)。
baseline rc=0。

| 判定 | 件数 |
|---|---|
| KILLED (期待 node と完全一致) | **8** |
| KILLED (期待より多くの node が発火) | **4** |
| SURVIVED (対照、事前登録どおり) | **1** |

### 単一理由が確認できた 8 件

`M1` dirty 集合の無視 / `M4` キャッシュキーから path を落とす /
`M6` `core.autocrlf` 検査の除去 / `M9` `assume-unchanged`・`skip-worktree` 検査の除去 /
`M10` 末尾 NUL 検査の除去 / `M11` 部分木 `.gitattributes` 検査の除去 /
`M12` 直下 `.gitattributes` 検査の除去 / `M7` collection キャッシュが全 item へ同一値を返す。

**5 つのフォールバック条件それぞれに独立した歯があることが、これで確かめられた。**

### erratum — 期待 node が不完全だった 4 件 (`DW-M08`)

`M2` (未追跡 file 落とし) / `M3` (空 directory 落とし) / `M5` (blob sha を返す) /
`M8` (collection キャッシュが絶対 path を保持) は、**いずれも赤になり、事前登録した期待 node も
観測集合に含まれていた**が、予測しなかった node も同時に落ちた。
`M2`・`M3` は git 管理外の合成木で `tracked` が空になるためフォールバック側の既存 test まで
巻き込む、という構造による。

`DW-M03` に従い、**この 4 件は冗長 gate として記録し、単独変異の証拠から外す。**
期待を実測に合わせて書き換えて再走すれば台帳は 13/13 になるが、それは新しい事実を何も
証明しないため行わない。初回結果は消さずここに残す。

### 対照 (`C1`)

comment 1 行の書き換え。**SURVIVED**、rc=0。事前登録どおり。
これが赤になっていた場合、他 12 件の赤は「何をしても赤になる」ことの現れにすぎなかった。

## 7. この変更が動かさなかったもの

- **最長単体 node の床** (191.7 → 188.2 秒)。次の床は
  `test_t080_stub_free_e2e_single_defects...[ccbench-current...]` (63 走中 44 走で最長残存) と
  `test_p3_autonomous_workload_trial::test_role_sink_bytes_vary_only_at_declared_declassifications`。
- **`test_s8b_oracle_driver.py` の `_t080_output_snapshot`** (metadata 比較)。
  size/mtime/ctime を見る作りで、内容不変の `touch` まで捉える。索引は内容の同一性しか
  言えないため index 経由化すると受理集合が変わる。**意図的に高速化の対象外とした。**
  共有 module へ移した (`git_visible_output_metadata_snapshot`) が、本文は逐語のまま移動しただけである。
  この移動により、`test_real_repo_serialization.py:719` が持つ元実装との間に
  **独立オラクルの関係が生じる** (それ以前は両者逐語一致)。以後どちらも削除しないこと。

## 8. 既知の限界

`D1184` のとおり、**受入 gate 自身の実装を編集する wave の受入 green は、
弱体化が不可能だったことの独立証明にならない。** 本 wave は `orchestrator/tests/` を編集した。
主張はせず、記録に残す。
