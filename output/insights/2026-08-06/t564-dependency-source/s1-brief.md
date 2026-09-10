# [T-564] 段 1 brief — 依存 source の所在を home の外へ移す

wave: `dev-wave-t564-dependency-source` / branch: `worktree-dev-wave-t564-dependency-source`
base: local main `616ef5db` (ff-only 取り込み済み、submodule 初期化済み、起動 gate rc=0)

## scope

1. `tools/pegasus/policy.json` の `gflags_source_path` / `glog_source_path` を home 配下から
   `/work/1/SFC/tanab/github/{gflags,glog}` へ移す。
2. `orchestrator/tests/test_pegasus_tools.py` の同 path literal 2 箇所を追随させる。
3. `orchestrator/tests/test_silo_ladder_rung1_evidence.py` の `binding["policy"]` 検査を、
   同 test が `driver` に対して既に使っている **歴史定数 pin + 現行 bytes との不一致 assert** の型へ移す。
4. `orchestrator/tests/test_t126_pegasus_tools.py` の binding 等値検査を同型へ移し、
   **現行 policy bytes の明示 sha256 定数**を新設して共有 policy の無断 drift 検知力を維持する。
5. D96 の手続義務に従い、新しい設計判断を spool fragment として起こす。
6. certify job を再投入し、`gflags` / `glog` 段を通過することを実測する (復旧実証)。

## 確定済みの前提と裁定

- **source は準備済み**。親が実測: `/work/SFC/tanab/github/gflags` HEAD
  `e171aa2d15ed9eb17054558e0b3a6a413bb01067`、`.../glog` HEAD
  `8f9ccfe770add9e4c64e9b25c102658e3c763b73`。いずれも policy の expected_head と一致し、
  `git status --porcelain --untracked-files=all` は空。
- worklog (250) が挙げた択一のうち **(b) source の所在を policy ごと home の外へ移す**を採る。
  (a) home 配下への再作成は「Pegasus では home に不要物を置かない」運用方針と衝突する。
  (c) 依存 source の cache hydrate 化は `tools/pegasus/fetch_third_party.py` の対象拡張を伴い、本 wave の scope 外。
- 凍結証拠の byte pin について、ユーザーは「そこが変わっても実害はない」と述べた
  (2026-08-06 の対話)。親はこれを**この点を blocking 裁定として上げない**根拠としてのみ扱い、
  検知力を落とす根拠には使わない。

## 前提実測 (段 1、`DW-O19` の復元規律に従い一時変異 → 復元)

policy.json の 2 行を変異した状態で**受入全走**を 1 回実施 (request `892356.nqsv`、1101.60s、
計算ノード 48 worker)。**4 failed / 6728 passed / 20 skipped。**

| # | 落ちた test | 落ちる理由 |
|---|---|---|
| 1 | `test_pegasus_tools.py::test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench` | home path の literal 等値 |
| 2 | `test_pegasus_tools.py::test_certify_glog_stage_is_pinned_fail_closed_and_precedes_ccbench` | 同上 (glog) |
| 3 | `test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` | 凍結証拠の `binding.policy.sha256` == 現行 bytes を要求 |
| 4 | `test_t126_pegasus_tools.py::test_shared_pegasus_policy_owns_no_t126_qualification_keys` | 同じ binding 等値 |

現行 sha256 = `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac`。
変異後 = `e2c39d573973e17c1dd820afd577882b19f5de19923407b5424e8bc179c89daa` (実測値であり land 予定値ではない。
(P1) の決着次第で変わる)。**全 6752 件を走らせて赤はこの 4 件だけ**であり、これが pin 閉包の実測である。

## 不変条件 (破ってはならない)

- **過去 campaign の記録 `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の bytes を変えない。**
  当時の走行が使った値の記録であり、書き換えは歴史の改竄になる。
- **共有 policy の無断 drift を検知する力を落とさない。** 現行 bytes を明示定数として pin し直し、
  将来のどの byte 変更も赤にする (「凍結証拠と一致」から「明示定数と一致」へ根拠を移すだけとする)。
- **現行の受理集合を狭めない。** 上記 4 件以外の test の期待値に触れない。
- 依存 source を home 配下へ戻さない。
- `tools/pegasus/certify_calibration.sh` 本体の検査 (path 不在・HEAD 不一致・dirty の fail-closed) を緩めない。

## 成果物影響 (`DW-G05`)

- scope 1〜2 を入れない場合: certify job は `gflags source path missing` で 11 秒停止し続け、
  **新しい較正の取得が不能のまま**である (U-2 の blocker が 1 本残る)。certified 選択・レポート・
  台帳の既存値は変わらない。
- scope 3〜4 を入れない場合: 受入が 4 件赤のままで land できない。放置して赤を消す方向 (検査削除) を採ると、
  共有 policy の無断書換えが検知されなくなり、他 campaign の binding が黙って drift する。
- scope 5 を入れない場合: 受理集合を変える改修の記録義務 (D96) 違反となり、
  なぜ path が動いたかの一次資料が台帳に残らない。
- scope 6 を入れない場合: 「復旧した」が机上の主張のままになる。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** policy に書く文字列は realpath 形 `/work/1/SFC/tanab/github/{gflags,glog}` とする。
  `/work/SFC` は `/work/1/SFC` への symlink であり、repo 自身も `/work/1/SFC/tanab/izanagi` の形で
  記録されている。symlink 形を書くと `realpath` 系の witness と表記が割れる。
- **(P2)** 凍結証拠側は不変とし、test を歴史定数の型へ移す。`driver` key に前例がある。
- **(P3)** 検知力維持のため、現行 policy bytes の sha256 を test 側の明示定数として置く。
  これは新しい gate ではなく、既存 assert の根拠の付け替えである。
- **(P4)** 復旧実証は「certify job が `gflags` / `glog` 段を通過すること」までを名乗る範囲とする。
  完走 (約 110 分見込み) と較正の登録は [T-529] 活性化権限などが別途 blocker であり、本 wave では名乗らない。
- **(P5)** `/work/1/SFC/tanab/github` という機体固有の絶対 path を repo へ書くのは、home path が
  既にそうだったのと同じ結合であり、結合の**種類**は増えない。cache hydrate 化 (択一 (c)) による
  結合の除去は別タスクへ送る。

## 分割方針

実装子 1 本 (Codex `role=author`)。所有は `tools/pegasus/policy.json` と上記 test 3 file のみ。
docs・spool fragment・commit・certify 投入は親が行う。段 2・3 と段 6 のレビュー 2 本は省かない
(`DW-C00`: 正しさ防壁に触れ、受理集合が変わるため)。
