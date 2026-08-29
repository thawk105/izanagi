---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t1981-floor-rescue
seq: 1
title: T-1981 holdout と floor campaign の救出材料 11 file を全件破棄と裁定する (docs のみ、branch worktree-dev-wave-t1981-floor-rescue)
---

## 本文

- ユーザー依頼で、救出置き場 `/work/1/SFC/tanab/dev-wave-jobs/rescue-20260829/` の 4 対象
  (impl-a、impl-b、flaky-holds-a、acceptance-fastest-author) 計 11 file を file 単位で裁定した。
  判定基準はユーザー指定で「研究が前へ進むか」「破棄が既定」「着地させるなら、これが無いと
  何の測定・主張が立たないかを 1 行で書けること」。**結論は 11 file すべて破棄。**
- 対象 3 branch (`impl-dev-wave-t1981-a`、`impl-dev-wave-t1981-b`、
  `impl-dev-wave-acceptance-fastest-author`) はいずれも main の祖先で、commit 済み内容は
  着地済みだった。救出対象は worktree の未 commit 差分のみである。

### 既着地の測り方 (この wave で使った判定)

branch が main の祖先なので `git diff main...branch` は空になり、三点 diff では既着地量を測れない。
def 名の grep も、main 側に同じ面を覆う別名の後継が居ると誤判定する。実際に効いたのは
**救出 file の追加行のうち、main の当該 file に 1 行も存在しないものだけを残余とする行単位照合**
だった。これで 11 file 中 9 file の残余が 0〜数行に落ち、読む対象が 4100 行から数十行になった。

### file ごとの処遇と理由

| 対象 | file | 処遇 | 理由 |
| --- | --- | --- | --- |
| impl-a | `orchestrator/campaign/s8b_holdout_admission.py` | 破棄 | T-1981 の中核 (測定世代) は main へ着地済み (同 file に `measurement_generation` が 265 箇所)。救出版は main より約 200 行小さい。真の差は 2 点だけで、いずれも main の巻き戻しである — (1) `generation_id` を旧名 `n_pilot_design_generation_id` へ戻す改名、(2) resume を「測定開始後は拒否」へ戻す実装。main は resume 時に既存 claim を突合して再開を支援する側へ進んでいる。 |
| impl-a | `orchestrator/tests/test_s8b_holdout_admission.py` | 破棄 | 追加 15 試験のうち 13 は main に同名で存在。残る 2 も後継がある。`test_resume_reservation_uses_new_measurement_generation` は main の `test_resume_reservation_reuses_measurement_generation` と**逆の意味**を主張するため着地させると main の現行意味と矛盾する。`test_legacy_claim_bytes_remain_inspectable` は main の `test_inspection_positive_legacy_v1_remains_readable_and_conservative` が同じ面を覆う。 |
| impl-a | `orchestrator/tests/test_s8b_oracle_driver.py` | 破棄 | 追加 2 試験とも main に同名で着地済み。残余は行の並び替え由来のみ。 |
| impl-b | `orchestrator/tests/test_pegasus_floor_tools.py` | 破棄 | 残余 0 行。main が同 file で 79 行分先行。confirmation 撤去の試験は着地済み。 |
| impl-b | `orchestrator/tests/test_s8b_floor_campaign.py` | 破棄 | 残余 0 行。main が 13 行分先行。 |
| impl-b | `tools/pegasus/floor_campaign.sh` | 破棄 | 残余 0 行。main が 7 行分先行。 |
| flaky-holds-a | `orchestrator/tests/test_real_repo_serialization.py` | 破棄 | 残余 0 行。main が 802 行分先行。 |
| flaky-holds-a | `orchestrator/tests/test_s8b_floor_campaign.py` | 破棄 | 残余 0 行。main が 310 行分先行。 |
| flaky-holds-a | `orchestrator/tests/test_s8b_oracle_driver.py` | 破棄 | 残余 0 行。main が 135 行分先行。 |
| acceptance-fastest-author | `orchestrator/tests/conftest.py` | 破棄 | 既裁定に反するため。下記参照。 |
| acceptance-fastest-author | `orchestrator/tests/test_real_repo_serialization.py` | 破棄 | 同上 (conftest 側の登録に対応する独立 golden)。 |

### acceptance-fastest-author だけは main 未変更だったので個別に見た

4 対象 11 file のうち、main が触っていない (そのまま当たる) のはこの 2 file だけだった。
内容は T-080 stub-free E2E の 3 node を real-repo access 台帳
(`_REAL_REPO_NODE_INVENTORY` / `_REAL_REPO_BOTH_READER_NODES` /
`REAL_REPO_PROCESS_MEMO_NODES`) へ登録するもの。技術的には成立している —
3 node は `_build_t080_stub_free_e2e_repo` 経由で実 repo (`ROOT/orchestrator`、`ROOT/output`、
freeze 成果物) を読むので「読み手」の宣言自体は事実であり、main の conftest にこの 3 node は
まだ 1 件も入っていない。

それでも破棄と裁定した理由は 3 つある。

1. **既裁定に反する。** D700 は T-080 stub-free E2E の nodeid を単一 worker 直列化の集合へ
   登録する案を、その worker が critical path になり受入予算と両立しないという理由で明示的に
   却下している。D1260 は同型の process-memo grouping を実測し、fixed tip 3 走ずつで
   244.810 秒 → 245.707 秒 (+0.37%) にとどまるとして不採用にしている。本 file はこの
   既裁定済みの機構をもう一度当てるものであり、新しい実測を伴っていない。
2. **立たなくなる測定・主張が無い。** floor campaign の測定にも論文主張にも効かない。
   効くのは受入全走の worker 配置だけである。
3. **正しさは買っていない。** access 台帳では親 working tree は全 node が `read` で、書き手が
   1 件も存在しない。したがって読み手同士の競合は起きず、この登録が生むのは scheduling の
   変化だけである。正しさ防壁の台帳を scheduling の手段として使う形になっている。

なお受入全走の直近実測は約 4 分 (D1260 の 244.810 秒) で、D678 / D900 が定める 5 分予算の
内側にある。速度が律速になっていない以上、効果が測られていない配線を conftest へ入れる理由は
無いと判断した。

### 撤去

破棄と裁定した 4 対象について、`tools/check_branch_rescue.py --ledger-check` に 3 branch と
4 worktree を 1 回の cleanup としてまとめて渡し、**最終根を失う commit は 0 件・閉包は complete**
を確認した。同 tool は rc=2 を返したが、原因は `root-snapshot-moved` (走行 138 秒の間に並行
session が ref を動かした) であって損失ではない。snapshot の揺れに依存しない裏取りとして、
4 worktree の HEAD (`343b8f5a5` ×2、`45b693d6b`、`e29084e02`) がいずれも main の祖先であることを
個別に確認した。これは並行 session が何をしても変わらない。

## 次の一手差分

### carry

- [T-1981]
