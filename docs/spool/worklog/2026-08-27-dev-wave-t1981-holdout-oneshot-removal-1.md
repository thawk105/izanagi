---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1981-holdout-oneshot-removal
seq: 1
title: [T-1981] 性能測定の一回性を予約経路から撤去し測定世代へ置き換えた — 実機投入で撤去は効いたが、床値を止めるものが別の欠陥へ移った (コード + docs、branch worktree-dev-wave-t1981-holdout-oneshot-removal、変異 matrix = baseline PASSED・KILLED 5・SURVIVED 0・MISMATCH 0)
---

## 本文

- **D1124 の「実害」節の前提が実測で誤りだった。** 同 D は「2026-08-24 に途中死した床値 run が
  12 cell 全部の key を焼き」「成果物の不在だけを見て未実行と判定していた」と書くが、一次資料に
  当たると当該 run (request `945229.nqsv`、campaign run id `20260824T205358Z-2c8cf9be`) は
  **driver_rc=0 で完走**しており、12 セル x 8 session = 96 attempt がすべて `valid=True`、
  床値の実測値 (`rr20` scalar_alt 3.555e+04、`rr80` 4.551e+04) も出ていた。成果物は repo 外の
  evidence bundle へ意図的に退避されていた。**決定そのものは覆らない** — 中核の論拠
  「性能測定は繰り返しても何も無効化しない」は run が死んだか完走したかに依存しない。
  ただし**成果物影響は「床値が 1 つも出ない」ではなく「同じ cell を測り直せない」が正しい。**
- **実機投入で撤去は効いた。撤去の終端条件は満たしていない。** 撤去後の tip から承認引数なしで
  床値 pilot を実 qsub した (request `952615.nqsv`)。`qsub -v` に承認 env は載らず、
  `already consumed` も出なかった。投入元の `git rev-parse --git-common-dir` が
  `/work/1/SFC/tanab/izanagi/.git` であることを実測で記録し、台帳の 12 claim と 96 marker を
  残したまま投入したので恒真な受入ではない。**しかし job は 67 秒で、cell 予約より手前の
  ビルド段で落ちた** (`binary admission receipt を発行できない: compiler input manifest の
  完全検証に失敗: external compiler input is unavailable`)。予約に到達していないため、
  **消費済み 12 cell が再測定を妨げないことの実機証明はまだ無い。**
- **その赤は本 wave の回帰ではない。** main (`98f61815c`) だけの独立 worktree を作り、
  main 側の手順どおり承認引数つきで同じ投入を行ったところ (request `952631.nqsv`)、
  **62 秒で完全に同一のエラー本文・同一の失敗段**で落ちた。署名の一致ではなく本文と段の
  両方が一致している。本 wave の差分は `buildcache.py` も `s8b_compiler_input.py` も触っていない。
  当日 11:17 の `b215f1a27` も原因ではない (本 wave の base はそれを含まないのに同一の赤になった)。
  この症状は `docs/` にも `output/insights/` にも前例がない新種である。
- **床値実測を止めているものが、一回性から別の欠陥へ移った。** 2026-08-27 05:54 の投入は
  このビルド段を通過して 350 秒地点の予約段まで到達していた。一回性を外した今、
  同じ主経路をビルド段の別の欠陥が止めている。
- 親の brief の暫定裁定は 2 件とも実測で棄却された。(a)「拒否する 1 行だけ外す」は finalize 側と
  旧 claim identity 照合でも止まる。(b)「attempt ticket は残す」は台帳に **96 件の marker**
  (floor の 12 claim digest 配下、1 cell あたり 8 件) が現存するため成立しない。
- **attempt ticket の帰属も誤っていた。** 親と段 2 はどちらも D893 の reward hack 防壁だと
  見なしたが、段 3 レンズ A が D434 由来であることを指摘し、親が台帳で裏取りした。D893 が
  要求した機構 (launch reservation / run nonce / terminal tombstone) は [T-469] として未実装の
  まま carry 中である。**したがって「同じ試行を複数実行先で走らせて良い値を選ぶ」経路には、
  現在いかなる実装防壁も無い。**
- 段 3 レンズ A が「反復可能化だけを先に入れると best-of-N の再凍結経路が開く」を real で挙げた。
  親は **real だが現時点で到達不能**と裁定した。official は `_assert_official_permitted()` が
  production で無条件拒否し (§8 未裁定)、再凍結側は `eligible_for_refreeze is True` を要求するが
  pilot は false である。二重に塞がっている。**恒真な保証を新設せず、条件を記録して次項へ渡した。**
- 段 3 レンズ B が親の実測を 2 件否認し、親が一次資料で訂正した。(a) 上記の「途中死」。
  (b)「投入元は main repo の worktree だった」は推論として不成立 — 同じ親 directory 下の
  独立 clone でも証拠 root は同じ値になる。**レンズ B は台帳の実物を read-only で再導出し、
  旧 36 行すべてが現行 key を通り、旧 floor marker 96 件すべてが exact に claim・ledger・
  filename へ戻ることを確認した。**
- **段 5 の実装子は main に存在するテストを 11 本削除していた。** うち 3 本は承認機構そのものを
  固定するもので撤去範囲内だが、resume の意味論 4 本と
  `test_inspection_positive_legacy_v1_remains_readable_and_conservative` (旧 v1 bytes の
  可読性の正例) を含んでいた。親が差分を読んで検出し、5 本の復元を裁定した。復元後、main 版から
  落とした assert はゼロで、2 本はむしろ assert が増えた。
- **fix は 4 巡を要した。** 焦点走の赤は 16 → 6 → 3 → 0 (実質)。第 1 巡は親の制約
  (既存テストの期待値を変更するな) が広すぎたため正しく停止した — 段 5 が新設したテストが
  裁定と衝突していた。制約を「main に存在するテスト」と「この wave が新設したテスト」へ分けて
  出し直した。第 3 巡で世代 ID を決定的導出へ変えたところ resume・成果物の決定性・`O_EXCL` の
  恒真性が同時に解けたが、**その際に独立した run identity 照合まで削っていた**ので第 4 巡で
  復活させた。
- 段 5 の実装子は親の識別子命名の裁定 (無修飾 `generation` を新 field 名に使うな、D197) を
  **既に pin されている既存 field 名にも適用**し、R33 role contract の `generation_id` を改名した。
  `tools/check_docs.py` が exact 1 件で機械検査しており rc=1 になった。名前の pin は grep では
  見つからず、機械検査を走らせて初めて出る。
- 待ち手が本体より先に落ちる事象を 1 件踏んだ。完了通知ではなく `.done` の実在で判定する規律で
  検出し、張り直して回復した。
- 実測: 焦点走 (17 file) = 1529 passed / 12 skipped。残る 1 件は file 選択走の import path 未確立に
  よる非帰属の偽赤。`tools/check_docs.py` rc=0、`tools/check_ai_provenance.py` rc=0。
  変異 matrix = baseline PASSED (rc=0・赤 0 件)、KILLED 5・SURVIVED 0・MISMATCH 0・TIMEOUT 0。
  期待 node は probe 走 (全件 SURVIVED 期待) の観測から完全集合で登録した (172 / 91 / 1 / 1 / 6 node)。
- 設計判断は {{D:measurement-generation-replaces-cell-oneshot}} と
  {{D:oracle-npilot-identifier-removal-deferred}} に記録した。

## 次の一手差分

### 更新

- [T-1981] **P1・実装完了、実機確認が残件**: 予約の可否を決める経路から一回性 key の照合を外し、
  測定世代へ置き換えた。承認 flag と env 伝播も floor 経路から撤去した。実機投入で
  「承認なしで投入できる」「`already consumed` が出ない」までは確認済み。
  **残件は「消費済み 12 cell が再測定を妨げない」ことの実機証明だけである。**
  現在それを塞いでいるのは一回性ではなく {{T:floor-compiler-input-unavailable}} の
  ビルド段の欠陥であり、そちらが解けたら床値を再投入して本項を閉じる。
  実装面の証明は旧 claim 12 件・旧 marker 96 件を配置した統合テストと、それを壊す変異 2 件
  (91 node / 6 node) が担っている。
  base: 678fde9d8d572d8ea2ebf6ebd43c9d43099eb497b6f81b9fdcf0044babdd7795

### 新規

- {{T:floor-compiler-input-unavailable}} **P1・新規**: 床値 job が binary admission receipt の
  発行段で落ちる新種の赤を直す。本文は
  `compiler input manifest の完全検証に失敗: external compiler input is unavailable`
  (`orchestrator/campaign/s8b_compiler_input.py:438` の `_external_entry()` が絶対 path の
  external input を `resolve(strict=True)` で解決できない)。
  **main 単独で再現する** (job `952631` = 62 秒 / 撤去後 tip の job `952615` = 67 秒、本文は同一)。
  2026-08-27 05:54 の job `951456` はこの段を通過していたので、当日中に環境か main が変わった。
  当日 11:17 の `b215f1a27` は原因ではない。**床値実測の主経路を現に止めており、
  T-1981 の終端もこれに塞がれている。**
- {{T:selection-side-barrier-inventory}} **P1・新規**: 一回性を撤去した後、
  「holdout の値を見てから選択・凍結・主張を変えない」がどこで守られているかを棚卸しする。
  本 wave の実測では、現在の防壁は
  `s8b_floor_campaign.py:453-462` の `_assert_official_permitted()` (production で official を
  無条件拒否) と `s8b_holdout_freeze.py:1617-1618` の `eligible_for_refreeze is True` 要求の
  2 つだけで、いずれも **official が解禁されたら消える**。`--floor-result` は
  `s8b_holdout_freeze.py:1884` で呼び手指定の必須引数であり、複数の完走測定から選べる。
  D893 が要求した機構は [T-469] として未実装のままである。
  **無ければ「守られていない」と正直に記録し、恒真な保証を作らない。**
- {{T:oracle-npilot-approval-identifier-removal}} **P2・新規**: oracle / n-pilot 側に残る
  `--confirm-irreversible-pilot-holdout` の identifier を撤去するか残すかを裁定する。
  R33 事前登録 protocol が driver と job script の bytes を pin しており現に一致、かつ R33 は
  未実行のため、撤去には successor 事前登録の発行が要る。**事前登録の再発行はユーザー手番**
  であり AI が勝手に発行しない ({{D:oracle-npilot-identifier-removal-deferred}})。
- {{T:oracle-driver-g12-oneshot-scope}} **P2・新規**: `s8b_oracle_driver.py` の holdout 予約より
  **上流**に残る恒久 G12 one-shot claim を、D1124 の撤去対象と見るか独立した正しさ gate と
  見るかを裁定する。予約 API の反復は通るが、同一 campaign identity の oracle driver 完全再実行は
  ここで拒否される。
- {{T:attempt-registry-generation-support}} **P2・新規**: `s8b_attempt_registry.py` は旧
  `consumed/` と旧 marker schema だけを読む。現在 production から接続されていないため床値経路を
  止めないが、role adapter を再接続する前に測定世代へ対応させる必要がある。
- {{T:floor-reservation-budget-doc-drift}} **P3・新規**: floor 予約予算の drift を解消する。
  コードは `_floor_reservation_budget()` が 30000 を返す一方、`floor_campaign.sh` と
  `tools/pegasus/README.md` は 28200 / 28800 のままである。
