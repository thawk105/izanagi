# [T-1858] / [T-1571] 受入の排他鎖 2 本を共有化で短縮し、鎖はもう律速でないことを実測した

- wave: `dev-wave-t1858-chain-shared-setup`
- branch: `worktree-dev-wave-t1858-chain-shared-setup`
- base main: `b253e0b79609f74ce757a7fc11c609f21643a7b7`
- 実装 commit: `190f3c42`、fix commit: `b9953324`

## 依頼と、依頼の前提のうち訂正した 2 点

依頼は「`s8c-preregistration-candidate` (台帳 97.1 秒) と `s8c-predicate-snapshot` (同 99.7 秒) の
2 鎖に同じ手を当てる。ほどければ『鎖以外の最遅 worker 149.4 秒』の項が下がる」だった。

**訂正 1: 97.1 / 99.7 秒は file 合計であって鎖の長さではない。** 台帳を xdist group 所属 node
だけで集計した鎖の長さは **candidate 83.500 秒 (5 node)・predicate-snapshot 52.001 秒 (3 node)** である
(段 3 レンズ B が独立に再集計して一致)。file 全体は candidate 20 node で 97.090 秒、
predicate 192 node で 99.673 秒。

**訂正 2: この 2 鎖はいずれも現在の makespan 下界を支配していない。**
台帳 15909 entry の直接合計は **7874.186 秒**であり、`W/48 = 164.046 秒`。
最長単体 node は 140.0 秒
(`test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications`)。
したがって理想 48-way の下界は `max(164.046, 83.500, 140.0) = 164.046 秒 = W/48` であり、
鎖ではなく総 work が支配している。**「本 wave 後の次の律速はここになる」は現台帳では成り立たない。**

D747 が使った 5316.9 秒は当時の値であり、現台帳では再現しない。より保守的に
「source 内容走査で現存を確認できる非 param の top-level node 9367 件」だけに絞っても
5390.202 秒 / 48 = 112.296 秒で、やはり鎖 83.5 秒を上回る。

**それでも短縮の値打ちは残る。** 総 work が下界を支配している regime では、
work を減らすことが下界を下げる唯一の手である。

## 内訳の実測 ([T-1571])

同一 command (`-q -p no:randomly -n 0 --durations=0 -k <鎖の node>`) の対比較。

### candidate 鎖 (login node)

| | 変更前 | 変更後 |
|---|---:|---:|
| 鎖の合計 | **76.76 秒** | **44.44 秒** |

変更前の内訳:

```
22.72s setup  test_candidate_freeze_matches_contract_and_generation_chain
17.21s call   test_candidate_is_not_effective_and_has_zero_satisfied_predicates
16.83s call   test_repository_tip_binds_current_decider_version_without_activation
15.96s call   test_wave_files_do_not_contaminate_production_holdout_scan
 1.40s call   test_candidate_freeze_matches_contract_and_generation_chain
 1.07s call   test_candidate_freeze_batch_is_bounded_by_frozen_touch_points
```

変更後の内訳:

```
15.92s setup  test_repository_tip_binds_current_decider_version_without_activation
14.96s setup  test_candidate_freeze_matches_contract_and_generation_chain
11.21s call   test_wave_files_do_not_contaminate_production_holdout_scan
 1.07s call   test_candidate_freeze_matches_contract_and_generation_chain
 0.92s call   test_candidate_freeze_batch_is_bounded_by_frozen_touch_points
 0.04s call   test_repository_tip_binds_current_decider_version_without_activation
```

**重複していたのは 2 系統だった。**

1. `prereg.activation_report_at(ROOT, candidate)` を 2 node が独立に呼んでいた (17.21 秒 + 16.83 秒)。
   共有後は fixture setup 15.92 秒の 1 回だけになり、2 つの consumer の call は
   0.04 秒と計測閾値未満へ落ちた。
2. `_commit_paths(candidate)` を 2 node が独立に呼んでいた。
   holdout scan の node は 15.96 秒から 11.21 秒へ下がった。

**setup 22.72 秒は重複ではない。** `_candidate_commit` の `read-tree` / `add -A` /
`write-tree` / `commit-tree` であり、session fixture で既に 1 回だけである。

### predicate-snapshot 鎖 (計算ノード 950292/950429.nqsv)

| | 変更前 | 変更後 |
|---|---:|---:|
| 鎖の合計 | **44.37 秒** | **28.56 秒** |

変更前は `evaluate_all("HEAD", repo_root=_ROOT)` を 2 回払っていた。
1 回目は module fixture の `_snapshot_current_commit` が archive すべき evidence path を集めるため、
2 回目は `test_current_repository_snapshot_exactly_matches_head` の比較の右辺として。
共有後は 1 回になり、15.29 秒の call が消えた。

**A は login node、B は計算ノードで測っている。** 前後は同一の実行場所どうしで比較しているが、
2 鎖の絶対秒を互いに比較する用途には使えない。

## 段 2 の据え置き裁定を段 3 が覆した

段 2 のプランは predicate 鎖を「2 回目の HEAD 評価は独立再導出そのものが検出力だから共有できない」
として据え置いた ([T-1619] の裁定項目 3 を根拠にした)。

**段 3 の 2 レンズは独立に、これを refuted と判定した。**

- 共有するのは fixture 内の 1 回目の HEAD 評価だけであり、比較の左辺
  (一時 repository での `evaluate_all(head, repo_root=root)`) は独立に再導出されたままである。
  したがって恒真化しない。[T-1619] が禁じたのは「両側を共有値にすること」である。
- 2 回目だけが殺す production 実装の具体的な 1 行変異は書けない。評価器は HEAD を呼出し冒頭で
  一度解決し、raw / AST / binding / graph の cache をすべて呼出しローカルに作る。
  時刻・乱数・並行読取の非決定源も見当たらない。
- 唯一失われるのは「走行中に実 HEAD が動いた」場合の検出である。

**親はこれを採用し、失われる分を安い形で補った。** fixture が評価対象の OID を記録し、
比較の直前に現在の HEAD OID と一致することを純関数 `_require_unchanged_head` で確かめる。
gate が恒真にならないよう、正例と負例を helper 経由で 1 件ずつ足した。

**受理集合は前後で同一ではない。新実装の拒否集合の方が広い。** 旧実装が比較したのは評価結果の
tuple だけなので、HEAD が動いても結果が同じなら通っていた。新 gate は結果が同じ OID 変化も拒否する。

## 段 6 が見つけた must-fix

レビュー A が real な欠陥を 1 件見つけた。fixture は `git rev-parse HEAD` で OID を記録した後、
`evaluate_all` / `git ls-tree` / `git archive` へはいずれも文字列 `"HEAD"` を渡して**それぞれ独立に**
再解決していた。記録 OID・評価結果・snapshot が別 commit 由来になりうる状態であり、
gate はその不整合を検出できず、逆に一貫した走行を誤って拒否しうる。

fix は解決済み OID を 3 か所すべてへ渡すことである (`b9953324`)。
「`rev-parse` を評価の後ろへ動かす」だけでは原子的にならない、というレビューの指摘も採った。

## 台帳 (`acceptance_duration_ledger.json`) を更新しなかった理由

段 3 レンズ B は同 wave での更新を推した。親は不採用にした。

1. どの検査も赤にならない。台帳は scheduling hint として読まれるだけで実所要との照合はなく、
   node 集合も件数も変わらないので coverage 90% 検査・schema 検査・group golden は維持される。
2. 更新するなら全 15909 entry の再生成になる。8 node だけの手編集は `--check` の byte 一致で落ちる。
   無関係な差分をこの wave のレビュー対象へ持ち込むのは変更面の所有としても不適切で、
   他 wave の受入とも競合する。
3. 台帳はすでに多数の node で stale であり、本 wave が原因ではない。

## 効果の言い方

- 確定して書けるもの: 焦点鎖の前後所要 (同一実行場所の対比較)、重い評価の呼び出し回数
  (2 系統 + 1 系統がそれぞれ 2 回から 1 回)、削減した直列 work。
- 書いてはならないもの: 受入全走 wall の短縮保証。
  **「削減 work / 48」は実 wall 短縮の上限ではない。** 均衡した work 律速時の下界改善量であって、
  実 wall は tail が別 worker なら 0、短縮した worker が tail ならそれ以上にもなりうる
  (段 3 の 2 レンズが独立に同じ訂正を出した)。
- xdist 3.8.0 には完了 worker が次 unit を引く再配分機構が実在する
  (`mark_test_complete()` → `_reschedule()`、残 pending が 2 以下で global queue から割当) ので、
  鎖短縮の wall 効果はゼロ固定ではない。ただし global queue が尽きた後に既割当 unit を移す機構はない。

## 変異 matrix — 検出力が保存されていることの実証

本 wave は production 差分ゼロのテスト等価変換なので、証明すべき命題は
「8 node の kill 集合が変更前後で同一である」ことである。同一 spec を新旧両版へ当てた
(先行事例 [T-1619] と同じ方法)。

### 新旧比較 (probe、`sha256=24ed7434...`)

runner は両版とも同一 argv。baseline は両版とも PASSED
(旧版 `b253e0b7` 212 passed / 新版 `b9953324` 214 passed)。

| 変異 | 旧版が殺した node | 新版が殺した node |
|---|---|---|
| `effective` を無条件 `True` | 3 件 | **同一の 3 件** |
| `freeze_generation` を `None` へ | 1 件 | **同一の 1 件** |
| `max_generation` を `1` へ固定 | 3 件 | **同一の 3 件** |
| evidence ref を記録しない | 2 件 | **同一の 2 件** |

**4 変異すべてで kill 集合が完全一致した。** とくに 4 番目は
`test_current_repository_snapshot_exactly_matches_head` が殺しており、
「共有すると検出力を失う」という段 2 の懸念が実測で否定された。

### 本走 (`sha256=99a62c9c...`、commit `b9953324`)

baseline PASSED、**6/6 一致・KILLED 5・SURVIVED 1 (登録どおり)・MISMATCH 0**。
本走は `-n 0` の直列で走らせた。並列走行では conftest が `@<group>` 接尾辞を合成するが、
harness の期待 node 実在検査は素の collection を見るため一致しない。

SURVIVED 1 件は `MUT-T1858-HEAD-GATE-CALLSITE-REMOVED` で、事前登録どおりである。
新設した HEAD 不変 gate の**呼び出し行そのものを消す変異は、安定した checkout ではどのテストも
赤にしない**。gate 本体の恒真化 (`if recorded != current:` を `if False:` へ) は
`test_require_unchanged_head_rejects_mismatched_oids` が殺すので、helper は恒真ではない。
呼び出し配線を検査する形が要るかは次の一手へ送った。

- spec: `output/insights/2026-08-26_t1858-mutation-spec-final.json`
- 台帳: `output/insights/2026-08-26_t1858-mutation-ledger.json`
