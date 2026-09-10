# [T-2383] role sink 非干渉 node の所要 — 何が遅かったのか、依頼の前提はまだ正しいのか

**日付:** 2026-09-09
**branch:** worktree-dev-wave-t2383-role-sink-duration
**対象:** `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications`

## 要約

この node は「32 通りの秘密入力 (5 bit wire) を同じ公開入力で流したとき、各 role へ渡る bytes が
宣言済みの開示点でしか変わらない」ことを検査する。遅い理由はテスト本体ではなく、
**32 回の反復が repo 全体規模の受理検査を毎回やり直していること**だった。

被覆を 1 つも消さずに短くした。実測は次のとおり。

| 場面 | 変更前 | 変更後 |
|---|---|---|
| 計算ノード単独走 | 17.44 / 16.75 秒 | 3.92 / 6.50 / 3.95 秒 |
| 受入全走 (1 node × 48 worker) | 50〜226 秒 (直近 12 走、中央値 約 80) | **18.281 秒** (本 wave の受入走) |

**ただし受入 wall の短縮は主張しない。** この node は現在の受入の床ではない (§2)。

## 1. 何に時間が使われていたか

login node で `cProfile` を掛けた 1 走 (D1795 適用後の main、`2143a49c0`)。

```
1 passed in 172.06s (0:02:52)
real 2m52.912s / user 0m7.480s / sys 0m7.246s
```

`time` は待ち合わせた子孫の資源も集計するので、`user + sys` には git subprocess の CPU も入る。
したがって **wall の約 91.5% は CPU を使っていない待ち**である。
(親は初出時に `sys` を落として「96%」と書いた。段 3 レンズ B が訂正した。)

cumulative の主要行:

| 呼び出し | 回数 | cumtime (秒) |
|---|---:|---:|
| 対象 node 全体 | 1 | 164.81 |
| `run_trial` | 32 | 164.13 |
| `require_admitted_campaign` | 64 | 114.84 |
| `capture_contract_loader_binding` | 64 | 89.52 |
| `_read_regular_file_no_follow` | 4032 | 68.37 |
| `_run_git` | 640 | 59.99 |
| `verify_committed_contract_loader_binding` | 64 | 24.42 |

internal time では `select.poll` 71.14 秒 (26,227 回)、`posix.open` 42.33 秒 (23,585 回)、
`posix.close` 21.38 秒、`fsync` 20.15 秒 (832 回)。**sha256 の総計は 0.239 秒しかない。**
計算ではなく、file を開いて読むことと git を起動して待つことが費用である。

`_read_regular_file_no_follow` の 4032 回は「閉包 63 path × 64 回の binding 検査」である。
1 反復あたり 2 回の admission が、そのたびに閉包全部を no-follow で開き直していた。

## 2. 依頼の前提は既に古くなっていた

依頼は「受入 63 走で最長残存 node (268〜312 秒)」を前提にしていた。
これは **D1795 (2026-09-08、閉包 blob 取得を 62 process から 2 process へ) より前**の窓の値である。

親が `/work/1/SFC/tanab/.izanagi-acceptance-shards/` の junit を直接読んだ実測:

- 直近 12 走のこの node: 171.905 / 103.504 / 60.747 / 49.972 / 68.870 / 75.850 /
  59.234 / 88.618 / 130.621 / 225.640 / 77.351 / 85.035 秒。中央値 約 80 秒
- 最新走 (`ca3fc62c...`、22,147 node) の最長は `test_t080_*` 群の 280〜298 秒。
  この node は同じ走で 171.9 秒であり、上位 10 件に入らない
- 3 走で確かめると、この node を持つ shard 2 の wall (267.55 / 260.16 / 250.19) より
  shard 0 の wall (319.30 / 325.97 / 440.97) の方が長い
- 本 wave の受入走 (`0a6a4374...`、22,170 node) でも最長は `test_t080_*` の 186.8 秒だった

**この node をゼロにしても受入 wall は縮まない。** D1714 の「床は単独 node でなく帯である」
という既裁定がそのまま当てはまる。本 wave の成果は「この node の所要が下がった」までである。

## 3. 採らなかった道と、その理由

- **32 個への parametrize 分割** — F829 が明示的に否定済み。ループ末尾の横断比較が
  どの node からも消える。速さのために検査を消す形であり絶対規律 2 に触れる。
- **`contract_loader_binding` への process 内 cache / memo** — D1795 が
  「process 内 cache・memo は導入しない」を明示裁定済み。object store の prune や root 差し替え後に
  古い bytes を返して fail-closed を壊しうるという理由も現に正しい。
- 親は段 1 brief で「`contract_loader_binding.py` は自身が閉包 63 path の member だから変更不能」
  と書いたが、これは**過大だった**。member である事実は正しいが、変更できないのではなく
  **pin 追従の費用がある**だけである (D1795 自身が同 file を変更している)。段 3 レンズ B の訂正。

## 4. 実際に入れた変更 (test file 1 本のみ)

1. **fixture の lock 用 binding を前計算** — `campaign_lock_test_support.build_v2_campaign_lock` は
   既に `binding` の注入を受け付ける。テスト側 helper が 32 回作り直していたものを 1 回にした。
   `_run_git` は 640 回から 516 回へ減る。
   **production の受理集合は変えず、64 回の admission も 64 回の live closure capture も減らしていない。**
   既存の引数省略 caller 2 箇所は既定値 `None` で現行どおり。
2. **32 反復の並行実行** — `ThreadPoolExecutor` と順序保存の `executor.map`。
   worker は局所値を返し、集約は main thread だけが行う。`as_completed` は使わない。
3. **件数 32 の明示検査** — 逐次 loop が構造から与えていた保証を明示検査で置き換えた (§5)。
4. **失敗時の wire 診断** — per-iteration assert に wire を message として付けた (条件式は不変)。
5. **docstring** — 被覆する命題と、§6 の裁定と損失を書いた。

## 5. 段 3 レンズ A が見つけた穴 — 集約を分けると件数が守られない

`len(set(sink_bytes["planner"])) == 1` は**要素が 1 個でも真になる**。
`_critic_relation_equivalent` も 1 個で真になる。`auditor` だけが `== 32` なので件数が守られていた。

逐次 loop では「32 回まわして毎回 append する」という構造が件数を保証していた。
並行化で検査と append が分離されると、collector が一部を落としても緑で通る。
そこで 4 role と `trusted_variants` / `secret_records` に件数 32 の明示検査を足した。

**これは新設 gate ではない。** 逐次 loop が構造から得ていた強さの保存である。
変異 M8 (collector が critic を先頭 1 件だけ append する) がこの検査の正例対照であり、KILLED した。

## 6. 受け入れた損失 — 実行スケジュールの被覆

全 assert の意味は実行順に依存しない (横断 7 種はすべて集合の要素数、per-iteration 6 種は
その反復に閉じた値だけを見る)。したがって失われるのは性質の被覆ではなく**実行スケジュールの被覆**である。

**それでも損失はある。** 「逐次のときだけ wire を混ぜる」形の欠陥は、変更後の node では
決定的には捕まらない。この wave はこれを明示的に受け入れた。docstring にも書いた。**等価とは主張しない。**

## 7. 並行度をどう決めたか

段 3 レンズ B は「固定 4 に事前の根拠がない」と指摘した。正しい。答えは断念ではなく実測である。
段 4 で**結果を見る前に**「最良値の 10% 以内に収まる最小の並行度を採る」と決め、
計算ノード単独走で振った (`DW-O19` の 1 行一時変異、走行のたびに `git checkout --` で復元)。

| max_workers | 実測 (秒) |
|---:|---|
| 変更前 (逐次・前計算なし) | 17.44 / 16.75 |
| 1 | 26.68 / 14.83 |
| 2 | 6.91 |
| 4 | 3.92 / 6.50 / 3.95 |
| 8 | 3.51 / 4.99 |

**この計算ノードの走行ごとの変動は大きい** (同じ構成で 26.68 と 14.83、3.92 と 6.50)。
4 と 8 はこの変動の中で区別できない。**同じ利得なら並行度は小さい方を採る**という
事前規則に従って 4 を選んだ。

`max_workers=1` の 2 標本が変更前を挟んでいるため、**前計算だけの寄与はこの変動幅の中で
分離できなかった。** 分離できたのは静的な事実 (`_run_git` 640 → 516) だけである。

## 8. 変異 matrix — 短縮前と同じものを殺せるか

これが本 wave の証明義務である。**同じ変異を変更前 HEAD 版と変更後版の双方へ当てた** (DW-M08)。

| 変異 | 変更前 (2143a49c0) | 変更後 (1fb217c23) |
|---|---|---|
| M1 planner の記録 payload へ wire 混入 | KILLED | KILLED |
| M2 coder の記録 payload へ wire 混入 | KILLED | KILLED |
| M3 auditor の未宣言な変動 (`correctness_digest`) | KILLED | KILLED |
| M4 `diffq_variant_id` を定数化 | KILLED | KILLED |
| M5 candidate label を raw variant に戻す | KILLED | KILLED |
| M7 `payload_bytes` の二重記録 | KILLED | KILLED |
| M8 collector が critic を先頭 1 件だけ append | (構造なし) | KILLED |
| M9 worker が wire 17 で例外を送出 | (構造なし) | KILLED |

共通 6 件の KILLED 集合が一致した。M8 / M9 は並行化で新しく生じた壊れ方に対する検査で、
変更後版だけが持つ。

### erratum と限界 (隠さない)

- **M5 の初回は MISMATCH だった。** 段 4 の裁定表には期待赤 node として
  対象 node と `test_final_generation_critic_rebuilds_projected_digest` の 2 件を書いていたが、
  **親が spec JSON へ写すときに後者を落とした。** 観測は裁定表と一致していた。
  spec を直して再走し KILLED を確認した (`mutation-new2-out.json`)。
  原因は転記漏れであって機構の欠陥ではない。
- **変更前版の matrix は 2 回とも wrapper が rc=125 で終了した。**
  理由は `mutation_worktree.py` の「共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した」で、
  12 分の走行中に他 session が共有 checkout を触ったためである。約 50 本の wave が同時に動く環境では
  避けにくい。**変異結果そのものは固定 commit の隔離 scratch worktree で得たもので、2 回とも同一 (6/6 KILLED) だった。**
  ただし wrapper の保証は成立していない。この限界ごと記録する。
- **M6 (production の呼び出しへ `do_build=True` を渡す) は登録から外した。**
  1 箇所を変えると build 経路が trial を走らせる全 test へ波及し、赤理由が単一に絞れない
  (DW-M01 / F28 の「実効 gate へ再照準」)。期待赤 node 集合を事前に確定できないため、
  推測の集合を登録せず取り下げた。

## 9. 段 6 の敵対レビューが挙げた must-fix と裁定

- **レンズ A: must-fix ゼロ。** should-fix は失敗時の wire 診断 1 件で、fix 子が解消した。
- **レンズ B: must-fix 2 件。**
  1. 4 並行の自己負荷で contract-loader git の 10 秒 timeout をまたぎうる (確率は未実測) —
     **コードでなく受入全走で判定する**と裁定した。段 4 で結果を見る前に登録した採否条件そのものである。
     本 wave の受入は緑で、receipt の `flake_nodeids` も `red_nodeids` も空だった。
  2. `executor` に hard timeout が無く、timeout 無しの git 待ちに入った worker があると
     `shutdown(wait=True)` が待ち続ける — **real だが、この変更が入れたものではない。**
     逐次版にも同じ性質があり、結果も同じ「node が終わらない」である。
     hard timeout の新設は依頼が scope 外とした gate 追加にあたるため、別項として起票した。

## 10. 残した既知の性質 (本 wave では直さない。別項として起票)

- `run_trial` 経路に hard timeout が無い (上記 B-2)。
- 対象 node は `report["status"] == "complete"` を検査せず partial report を見逃しうる (既存)。
- `artifact_admission` の説明文字列が「exact 62 path」のままで現物は 63 path (既存)。
- `_AUDITOR_D_POINTERS` の exact 集合を pin する assert が無い (既存)。
- 対象 node は実 checkout の HEAD と閉包を読むが `REAL_REPO_RESOURCE_NODES` に未登録 (既存)。
- free-threaded runtime では replay capability の `issued` dict に lock が無い
  (現行 CPython 3.10 では GIL 下で衝突しない)。

## 11. 一次資料

| 内容 | path |
|---|---|
| profile (cProfile 出力) | `/home/SFC/tanab/.claude/jobs/cb160f57/tmp/prof1.out` (session 一時領域) |
| 段 2 plan / 段 3 レンズ 2 本 / 段 6 レビュー 2 本 / 実装子・fix 子の報告 | `verbatim/` |
| 変異 matrix (変更後・M5 再走・変更前 2 回) | `mutation/` |
| 受入 receipt | `acceptance-receipt-1.json` |
