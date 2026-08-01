# [T-229] conftest の /dev/shm 誘導撤去 — 一次資料 (2026-08-01)

worklog 2026-08-01 (80) の一次資料。計測値・裁定・変異・敵対所見の逐語を置く。

## 1. 前提の裏どり (ユーザー依頼「16GiB を裏どりしてください」)

- ログインノード **pegasus01 / pegasus02 / pegasus03 すべて**で cgroup v2
  `user.slice/user-<uid>.slice` の `memory.max` = `memory.high` = **17179869184 バイト = 16 GiB**
  (`systemctl show user-<uid>.slice` の `MemoryMax` / `MemoryHigh` とも一致)
- **課金の因果を実測**: `/dev/shm` へ 512 MiB 書込 → `memory.current`
  4417654784 → 4958449664 (**+540794880 バイト ≈ +515.7 MiB**)、削除で 4417585152 へ**全額復帰**
- 計算ノード bnode033: job cgroup は `/system.slice/nqs-jsv.service` で
  `memory.max` = **123480309760 (115 GiB)**。tmpfs 256 MiB 書込で `memory.current` +268574720。
  `/scr` は XFS で 5.87 TB 空き、`/dev/shm` は 62.2 GiB
- **`/scr` はログインノードに存在しない** (`ls -d /scr` が ENOENT)

## 2. 実害の規模 (専用計測ジョブ、200ms サンプリング)

job `874750`、bnode033、loadavg 0.04 (単独)、全走 `4197 passed / 19 skipped / 206.59s / rc=0`。

| 指標 | 値 |
|---|---|
| before | 0 バイト |
| **peak** | **7,934,971,904 B = 7.39 GiB** |
| mean | 5.28 GiB (1026 サンプル中 942 = 92% が 1 GiB 超) |
| **after (残留)** | **6,221,352,960 B = 5.79 GiB** |
| 残留エントリ | **174** |

**計算ノードの /dev/shm はジョブ間で掃除される** — job `874753` が同じ bnode033 へ着地し
`shm_used_before=0` / 自他エントリ 0 を実測。親が段 1 で書いた「共有計算ノードにゴミを置く」は撤回した。
ログインノードには掃除主体が無く、[T-118] の 40,280 個はその累積である。

## 3. 代替置き場の実測 (300 回 write+fsync、payload 4 KiB、単一プロセス)

| 置き場 | 計算ノード bnode021 (loadavg 0.29、3 走同値) | ログインノード pegasus02 (loadavg 17、3 走) |
|---|---|---|
| `/dev/shm` | 0.001s | 0.002s |
| `/tmp` | **0.026s** | **8.7〜9.4s** |
| `/scr` | 0.021s | 存在しない |
| `/home` (Lustre) | 0.42〜0.49s | 0.435〜0.447s |

fstype は `stat -f` 実測: 計算ノード bnode041/043 の `/` `/tmp` `/scr` はいずれも **xfs**
(magic 58465342)、`/dev/shm` は tmpfs (0x1021994)、`/home` `/work` は lustre。
`/proc/self/mountinfo` に `/tmp` の独立 mount 行は**無い** (親 mount の `/` へ最長一致する)。

**ログインノードでは `/tmp` が最も遅く `/home` が 20 倍速い** (8.7/0.435)。
「局所ディスクなら速い」は成り立たない。

段 6 レビューの独立実測: `test_campaign.py` (168 node) が `TMPDIR=/dev/shm` で **2.21 秒**、
`TMPDIR=/tmp` で **12.33 秒** (5.6 倍)。**fsync 回数は両方とも 620 回で完全一致**
(規律 2 = 検査は弱めていない)。

## 4. 段 4 裁定 — プランの 80 行設計を不採用にした理由

段 2 プラン (codex 相当の read-only 子が起草) は tmpfs 判定 + `/scr` 選択 +
`dispatch_compute` 変更 + 新規テストファイルを提案したが、段 3 敵対レンズが次を実証したため
**採用しなかった**。

- **A1**: tmpfs 判定と空き容量ガードは login (`/scr` 不在)・受入全走 (job script が先に export)・
  qlogin (`/scr` は XFS) の全経路で評価されず、**実機で検出力ゼロの装飾**になる
- **B-4**: `_job_script` は f-string で、プランの bash 挿入は `{`/`}` 二重化と `\\n` を欠き
  **`dispatch_compute.py` が import 不能**になる (dispatch 全滅)
- **B-3**: 新設 7 node は helper 直叩きのみで、tmpfs 復活・結線削除・`tempfile.tempdir=None` 削除の
  いずれも殺せない
- **A3 (決め手)**: `patchharness.py:101-105` の apply 排他 lock は TMPDIR 由来。
  compute で TMPDIR を **job 単位**へ向けると共有 `external/ccbench` の排他が消え
  `buildcache` の `src_token`/`binary_hash` が実 source と乖離しうる = proof chain 汚染。
  **親は proof chain のリスクを新規に導入しない**と裁定した

採った最小 load-bearing 変更 = **conftest から `/dev/shm` 選択を削除するだけ**。
TMPDIR 未設定 → 環境既定 `/tmp` は計算ノードでも **node 単位**なので lock scope は現行のまま。
段 6 レビュー 2 がこれを独立に検算し、**むしろ pytest 経路と非 pytest 経路が同じ lock file へ
収束して排他は強くなる**と結論した (A3 は refuted)。

## 5. 親の主張のうち敵対検証で撤回したもの

- **「`_assert_free_disk` は恒真ゲート」→ 撤回**。呼び出しは `s1_verify_extime_calibration.py:385` /
  `s2_verify_calibration.py:292` の `main()` 内のみでテスト非到達。親が挙げた導線
  (README:13 の助言) も誤りで、README:12-14 は「GB 級の実 trace / 実ビルドでは tmpfs は RAM を食う —
  ディスク側 TMPDIR のまま」と当の経路を明示的に遠ざけていた。計算ノードでは tmpfs サイズ
  (62.2 GiB) 側が拘束なので 20 GiB 閾値は有意
- **「login でも同機序で最大 7.39 GiB」→ 撤回** (F46 型)。7.39 GiB は `-n 48` の値で、
  repo に `addopts` は無く login 直叩きは既定で直列
- **「共有計算ノードにゴミを残す」→ 撤回** (job 874753 の実測)

## 6. 段 6 で潰したガード自身の穴 (すべて変異で実証)

| # | 穴 | 是正 |
|---|---|---|
| MX2 | `_fs_type` の実 mountinfo 経路に対照が無く、壊すと node1 が SKIP 化して 5 node 全緑 | `/` と `/dev/shm` の両方向対照を追加 |
| MX3 | node5 の load-bearing 検査が文字列 `in` 判定で、token を残したまま `offenders.append` を殺すと全緑 | 述語を実行する positive control (`mock.patch.object`) へ |
| W2 | `/tmp` が tmpfs な環境で**無過失の赤** (受理集合の縮小) | 明示 tmpfs = 赤 / 環境既定 tmpfs = skip (理由に path・realpath・fstype) |
| N1 | `skiputil.skip()` が pytest 下で投げる `Skipped` は `BaseException` 派生で control を貫通し、**node5 自身が受入全走で必ず SKIP** になっていた (fix 1 巡が入れた退行。4202/19 → 4201/20 が一次証拠) | `pytest.skip.Exception` も分類し、貫通自体を赤にする control を追加 |
| N2 | `tempfile.tempdir = "/dev/shm"` 型の結線が 5 node 全緑で通る (fix 1 巡が開けた穴。段 5 時点では赤だった) | AST scanner が `<...>.tempdir = <tmpfs リテラル>` も検出 |
| N3 | `_fs_type` の**部分**劣化は skip でなく**偽緑**になる (親 mount の xfs へ落ちるため) | 実経路の tmpfs 正例対照を追加 |

事前登録変異 M1 (`setdefault("TMPDIR","/dev/shm")`) / M2 (assert 恒真化) / M3 (ガード node 削除) は
段 5 時点で全て KILLED。段 6 レビューが独立設計した変異 (job script からの tmpfs 注入、
`_fs_type` 全損、`_effective_tmpdir_candidates` から env 候補を落とす、tmpfs リテラル集合の削減) も
すべて KILLED。**生き残った変異**: `assert not offenders` を残したまま恒真フィルタを足す形
(DW-M03 の構造 pin の既知限界) と、node5 自身を消す形 (`test_plain_runner_coverage.py` の
自己適用と同型の限界。docstring に「diff レビューが最終防壁」と明記済み)。

## 7. 効果と受入 (すべて計算ノード実測)

| | before job `874750` (bnode033) | after job `874773` (bnode043) |
|---|---|---|
| `/dev/shm` peak | 7,934,971,904 B (7.39 GiB) | **20,480 B (20 KiB)** |
| 終了後の残留 | 6,221,352,960 B (5.79 GiB) | **0** |
| 残留エントリ | 174 | **0** |
| 単独性 | loadavg 0.04 | loadavg 0.41 |

計算ノード上で conftest を import した直後の実測: 変更前 `TMPDIR=/dev/shm` /
`gettempdir=/dev/shm` → 変更後 `TMPDIR=<unset>` / `gettempdir=/tmp`。

**リークは消えていない — 行き先が移っただけである。** job `874781` (bnode042) の実測:
走行前 `/tmp` 自己所有 0 バイト / 0 entry → 走行後 **5,274,105,353 バイト (4.91 GiB) / 174 entry**、
`/dev/shm` は 0。prefix histogram は **`s8b-selector-*` が支配的** = [T-118] の
`s8b_prediction_runner.py:1070` 後始末漏れ。`/tmp` の掃除は
`D /tmp 1777 root root 10d` + `systemd-tmpfiles-clean.timer` = active で **10 日保持**
(bnode042 / pegasus02 の両方で実測) であり、**tmpfs のとき (ジョブ間で掃除) より残る期間は長い**。

## 8. 受入全走とフレークの帰属 (DW-O18)

main 取り込み (`3ca5cfe` → `18d7fc3` の fast-forward) 後の実測。

| commit | 走 | 結果 | wall |
|---|---|---|---|
| HEAD `318b6ed` | `875793` | 2 failed / 4290 passed | 200.36s |
| HEAD | `875805` | 1 failed / 4291 passed | 190.51s |
| HEAD | 3 走目 | **0 failed / 4292 passed / 19 skipped / rc=0** | 212.82s |
| 親 `18d7fc3` | 1 走目 | 0 failed / 4287 passed | 203.75s |
| 親 | 2 走目 | 0 failed / 4287 passed | 211.16s |

- 落ちた node は走ごとに**移動**した — 走 1 は `test_s8b_oracle_driver.py` の
  `test_real_freeze_gate_lists_floor_and_budget_null@real-repo` と
  `test_v3_cli_subprocess_returns_rc_3_on_protocol_violation` (rc 3 期待に対し 2)、
  走 2 は `test_codex_worker_launch.py::test_token_cap_uses_cli_reported_definition` (**F57 の族**)
- 走 1 の 2 件を**単独再走したら 2 passed / 72.59s** で再現しなかった
- 総 node 数は 4292 で一貫 (親 4287 + 新設ガード 5) しており、node の増減はない
- wall は HEAD 190〜213s、親 204〜211s で**差は無い** (「遅くなったから落ちる」では説明できない)

`DW-O18` に従い**実装差分へ帰属させない**が、**親 2/2 緑に対し HEAD 2/3 で赤**という
非対称は残る。1 走ずつの比較では交絡しうるため [T-230] として起票し、
再発時は本エントリを一次資料にする。

## 9. AI provenance

Codex はレートリミット逼迫のため使用不能で、**2026-08-01 のユーザー裁定**により実装子・
レビュー子を Claude で構成した。D105 決定 1 の waiver 経路を用い、
`AI-Agent-Waiver: reason=codex-rate-limit; ratified=2026-08-01` を最終 trailer block へ
`role=author` と併記した。履歴監査 (計算ノード job `875792`、10 秒) は
**633 件、違反なし**、免除の実発火は **2 件** (`fee55899` = 別 wave の 2026-07-31 分、
`cf2779e` = 本 wave の amend 前 commit)。amend 後の実発火件数は段 7 の記録後監査で再取得する。
