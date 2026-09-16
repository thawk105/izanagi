# 段 4 裁定 — [T-2622]

親が段 2 の plan と段 3 の敵対 2 レンズ (a=sol 機序帰属 / b=luna 実験設計と安全) を
real / refuted へ裁定し、plan v2 と変異事前登録を確定する。

## 1. 親の provisional 裁定の帰結

| # | 親の裁定 | 判定 | 根拠 |
|---|---|---|---|
| P1-a | 機序は「stdout/stderr を掴んだ子孫が RUN に留める」 | **未同定へ格下げ** | レンズ a-1 / b-3。`exec` は shell の置換しか示さず、存在・所属・fd 保持が交絡している |
| P1-b | 上限なし `os.fsync` は refuted | **撤回する (real な指摘)** | レンズ a-2 / b。`_write_result_replace` は `os.replace` → `result-published` → **`_fsync_dir`** の順。**result.json 公開後に directory fsync が来る**ので、「pytest 完了・result 公開済み・job は終わらない」は fsync 仮説でも成立する |
| P1-c | 決め手は「存在」でなく「fd 保持」 | **未確定のまま維持** | 実験で分ける。これが本 wave の主命題 |
| P1-d | トレースでは正常終了と hang を分けられない | **限定して維持** | レンズ a-14。「`job-run-returned` まで到達した個体」に限る。fsync や supervisor 待機で止まれば最終事象は別になる。**トレースはむしろ 2 仮説を分ける** |
| P1-e | 再発 0 件なので痕跡経路は行き止まり | **強く限定する** | レンズ a-6/8/10。保存済み・終了済み標本に限る。**M5 の示すとおり受入全走級の exposure が 0 なので、その群への陰性証拠はゼロ** |

**親の誤りを 3 件認める。** (i) P1-b の refuted は誤り。(ii) P1-d が広すぎた。
(iii) handoff に書いた「F846 型 = interpreter 終了時の thread join 待ち」は親の推測で、
F846 自身は「根本原因: 未特定」「runner のどの段で futex を待っていたかまでは特定していない」
と明記している。**F901 を本症状の陽性例に数えるのもやめる** (レンズ a-17。F901 は
待ち手自身の長時間待機であって pytest 完了後の停止ではない)。

## 2. 所見の裁定

**棄却した所見は無い。レンズ a の 1〜28、レンズ b の 1〜13 はすべて real として採る。**
うち scope 内で本 wave が扱うものと、記録に留めるものを分ける。

### 採用して plan v2 へ反映する (scope 内)

| 出所 | 所見 | 反映 |
|---|---|---|
| a-5 / b-2 | 全条件 75 秒では「存在が原因」と断定できない | **統制条件 D (子孫を作らない) を新設**。J₀ を測る |
| b-11 | **安全 defect。** `total_deadline = submitted_at + walltime + overall_grace` は RUN 観測前から動く。plan の walltime 120 + grace 300 = 420 秒は `--queue-wait-timeout 900` より先に `overall-timeout` を起こし、取消経路に入る | **walltime 180 / queue-wait-timeout 600 / overall-grace 900** へ変更。期限の先後を整合させる |
| b-10 | 120 秒 walltime の余裕は静的に証明できない | **180 秒 = 起動予算 60 + 子寿命 75 + 終端余白 45** |
| b-1 / b-5 | 子孫の生存は保証されない。`/proc` が読めないことを不在と数えない | SID・PGID・starttime・state を条件ごとに記録。読取り拒否は「観測不可」 |
| b-4 | fd 差替えと全参照消滅は別 | 差替え前後で fd の device/inode/参照先を記録。複製を作らない |
| b-6 | 5 秒 / 15 秒の閾値の根拠不足 | realtime と monotonic を対で記録。**5〜15 秒は判別保留**とする |
| b-7 | 条件間で観測動作を揃える | 全条件が同じ通常 file 経路へ書く。job stderr への条件依存の追記を減らす。evidence path は条件ごとに一意 |
| a-13 | M8 は動的 import を覆わない (`tests` は pytest/xdist/packaging を dispatcher 自身へ import する) | **親が実測で埋めた。** 残余時間を task 別に割ると `tests` n=132 最大 0.0 秒 / `provenance` n=23 最大 -0.0 秒 / `generic` n=4 最大 -0.6 秒。**dispatcher の interpreter 終了処理の停止は、この 132 本では起きていない** |

### 採用するが本 wave では実験しない (記録に留める、scope 内)

a-19〜27 と b-1 の「未棄却の原因候補」を、**棄却できていない仮説集合**として insight に
そのまま残す。本 wave が実験で触るのは a-19〜27 のうち「子孫の存在 / 所属 / fd 保持」だけである。
残りは棄却も支持もしないと明記する。

### scope 外 (裁定パッケージ候補)

- **a-28**: `_group_member_count` が `Z` を除外するか ([T-2620])。既にユーザー裁定待ち。
  本 wave の実験結果から受理集合の変更を導かない。
- **b-13**: RUN 前にも overall deadline が適用される契約の意味と、
  `fresh-qstat-gate` 後の遷移を含む取消の保証範囲。**実装は変えない。**

## 3. plan v2 — 計算ノード実験

### 統制を足した 4 条件

`tools/probe_t2622_job_exit.py` を 1 本作り、`--condition` で分岐する。
全条件で親 probe は fork 後 5 秒で正常終了し、子を wait しない。

| 条件 | 子孫 | 子が job の stdout/stderr を手放す時刻 | 子の終了 |
|---|---|---|---|
| **D `no-child`** | **作らない (統制)** | — | 親が 5 秒で終了 |
| **A `close-now`** | 作る | fork 直後 | t0+75 秒 |
| **B `close-30`** | 作る | t0+30 秒 | t0+75 秒 |
| **C `hold-75`** | 作る | 手放さない | t0+75 秒 |

### 判定表 (結果を見る前に固定する)

`J` = `job-run-returned` の時刻、`E` = NQSV の `Ended Request Time`。
`E - J` を条件ごとに比べる。差 5 秒以内を「対応」、15 秒以上を「分離」、
5〜15 秒を **判別保留**とする。

| 観測 | 判定 |
|---|---|
| D≈J、A≈J、B≈+30、C≈+75 | **fd 保持が決め手** (P1-c real、存在だけでは留めない) |
| D≈J、A≈+75、B≈+75、C≈+75 | **子孫の存在が決め手** (P1-c refuted、P1-a は存在版で real) |
| D≈J、A≈J、B≈J、C≈J | **どちらも refuted。** NQSV は子孫を待たない → 原因は job 内部 (fsync・stdio・interpreter・scheduler 側) |
| 条件間で子が早期消滅 / 記録不足 / 時刻対応なし | **判別不能** (打切り観測。scheduler の kill と断定しない) |

**この実験が示すのは今回の単純な process 構造での機序までである。**
F853 の歴史的原因、受入全走への外挿、`tests` 固有の import・終了処理へは一般化しない
(レンズ a-3 / b-3、M11 の `env_mode=clean` 限定)。

### 投入 argv (1 条件 1 job、直列、detached)

```
python3
tools/pegasus/dispatch_compute.py
--task
generic
--walltime
00:03:00
--queue-wait-timeout
600
--overall-grace
900
--accounting-grace
120
--poll-interval
2
--
python3
-B
tools/probe_t2622_job_exit.py
--condition
<no-child|close-now|close-30|hold-75>
--evidence
output/insights/2026-09-16/t2622-compute-job-exit-hang/evidence/probe-<condition>.jsonl
```

`--walltime` は `HH:MM:SS` 形式が必須 (M14)。先例 = request `997000.nqsv`。
**期限の整合:** `total_deadline = submitted + 180 + 900 = submitted + 1080` >
`queue-wait-timeout 600`。よって queue が詰まった場合は **`queue-wait-timeout` が先に発火する**
(QUE 状態の取消は許される安全な側)。

### 親が満たす安全水準 (b-12 を採用して明文化する)

「orphan hold が絶対に発生しない」の証明は**求めない** — それは通常の dispatch にも無い。
本 wave が満たすのは次である。

1. 無期限の FIFO / pipe 待ち、hang 変異、walltime kill に依存する終了を**含めない**。
2. 子の待機は monotonic deadline に揃え、記録失敗で寿命を延ばさない。
3. detached かつ**同一 worktree から直列**に投入する (`DW-O26`)。
4. 1 条件ごとに正常終了・会計・receipt・`orphan-holds/` の件数を確認してから次へ進む。
5. 異常時は追加投入を止め、`qdel` を使わず終端を待つ。

## 4. 変異事前登録 (DW-M01) — 追補 (2026-09-16 12:20、段 5 の 1 回目の停止後)

**当初は probe と test を repo へ commit する前提で変異 matrix M1〜M5 を登録した。
これを取り消す。**

理由は先例の運用が違うためである。`output/insights/2026-09-14/t1643-has-include-real-pair/README.md`
§8 は、計算ノード probe について
「`t1643_has_include_pair_probe.py` — probe 本体 (475 行、Codex `role=author` が作成、
**repo へは残さない**)」と書き、raw JSON ともども job dir
(`/work/1/SFC/tanab/dev-wave-jobs/...`) に保全している。実際 repo の `tools/` に probe file は
1 件も無く、同 path の git 履歴も 0 件である (親が実測)。

したがって本 wave も同じ運用を採る。

- probe は Codex `role=author` が書き (D95 / [T-317] は未裁定なので author 必須)、
  実験に使い、**commit しない**。job dir へ保全し、insight から SHA-256 と byte 数で同定する。
- 新規 test file も作らない。よって受入所要台帳 (F902) への追記も不要になる。
- **commit される実装面の差分は 0 になるので、`DW-S04` により変異 matrix を免除する。**
  受入全走は免除しない。
- probe の fail-closed 挙動 (旧 M1〜M5 の対象) は、**probe 自身の `--selftest` として
  probe 内に置き、親が login node で実走して結果を記録する。** commit されないので
  gate ではなく、実験器具の自己検査である。

| # | 検査する fail-closed 挙動 | 確認方法 |
|---|---|---|
| S1 | 未知の `--condition` は rc≠0、fork も evidence 生成もしない | `--selftest` |
| S2 | `--child-seconds` > 120 と `--release-seconds` > `--child-seconds` は rc≠0 | `--selftest` |
| S3 | 解放後の fd 1 / 2 が `/dev/null` を指し、元の参照の複製が残らない | `--selftest` |
| S4 | 記録に失敗しても子の寿命が延びない | `--selftest` |
| S5 | 親が子を `wait` せず、子より先に終わる | `--selftest` |

## 5. 成果物の形

`output/insights/2026-09-16/t2622-compute-job-exit-hang/` に
(i) 段 1 実測 M1〜M15、(ii) 段 2 plan と段 3 レンズ 2 本の逐語、(iii) 本裁定、
(iv) 実験の生データと判定、(v) **棄却できていない仮説集合**。
worklog / decisions / failures は `docs/spool/` の fragment とする。

## 6. 現時点の結論 (実験前)

**症状は実在する。fd 機序は未確定。fsync (とくに directory fsync) は未棄却。**
既存の痕跡からは原因を同定できない — 保存された corpus に陽性例が 1 件も無く、
唯一の一次記録 F853 の原因欄は分離実験の裏づけを欠く推論である。
