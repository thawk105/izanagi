---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2632-b4-red-precursor-stock
seq: 1
title: [T-2632] B-4 の適格な赤 precursor は 0 件のままで、供給側と適格性側の双方に未充足条件があることを確定した (docs のみ、branch worktree-dev-wave-t2632-b4-red-precursor-stock、実装面の差分ゼロにより変異 matrix 免除)
---

## 本文

- ユーザー依頼は「B-4 の適格な赤 precursor の在庫を 0 件から増やす。供給源 (合成ループ campaign の
  whiteboard) と §5.1.1 の適格条件は変えない。母集合は B-4 の出力を見る前に freeze する。
  適格例が得られなかった場合も、不成立を結果として insight へ記録して返すこと (無理に数を作らない)。
  本題の在庫確保だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **調達できなかった。在庫は 0 件のままである。** 一次資料は
  `output/insights/2026-09-16/t2632-b4-red-precursor-stock/README.md`。
  **不成立の理由は「構造的に不可能」ではない。** 新しい正当な base 合成 campaign で自然な検疫赤が
  生じる可能性は否定していない。その live probe は実施していない。
- **決定的だったのは供給側ではなく適格性側である。** 仮に赤が 1 件出ても、適格性述語の
  `bootstrap_member` / `calibrated_workload_member` / `reference_is_unique` の 3 つが今日は
  いずれも正直に真にできない。事前登録 §6 が名指す publication root は不在、§5 の校正済み
  `PerfConfig` 欄と `env_tag` 欄は未記入である。3 条件の整備はいずれも別タスクで、依頼の scope 外。
- **依頼文の一節「成功例への置換と母集合を作る作業であり」は、台帳 T-2632 の原文
  「成功例への置換と母集合を作るための追加基盤は D1936 項 8 が不採用にしている」と逆の読みになる。**
  親は当初これを「切れた写し」と断定したが、段 3 luna が由来は記録されていないと指摘したので
  **断定は撤回した。** 由来がどうであれ、台帳原文・D1936 項 8・本 wave の明示禁止のいずれからも、
  どちらも採らないという結論は変わらない。
- **親の provisional 裁定 (P1-b) を段 2 と段 3 の両方が倒した。** 親は「§5 の母集合欄が空だから
  適格と言えない」と書いたが、母集合欄は適格判定と選択の**結果**を書く欄であり、この論法は循環である。
  結論は維持し、根拠を 3 条件の独立な照合へ差し替えた。**空欄を所属偽の証拠にしない。**
- **段 3 sol が親 brief の完了条件を倒した。** 親は「適格性述語の第 1 項を満たす行を 1 件以上得る」を
  完了条件の一つに置いていたが、これでは全条件適格数が 0 のまま T-2632 を完了にできてしまう。
  第 1 項該当は中間成果に降格し、到達範囲を「第 1 項該当数」「全条件適格数」「manifest 成立」の
  3 つに分けて記録した。
- **段 3 luna が T-2633 の裁定済みを見つけ、親が現物で裏取りした。** D1986 項 4 が
  「適格な行が必要数に満たない間は実施不可のまま走らせない。少数の赤 precursor に対して
  許されるのは記述としての報告まで」と決めている。**T-2633 を再裁定待ちへ戻さない。**
- **親は子の報告を鵜呑みにせず、決定的な 4 点を worktree の現物で裏取りした** — D1986 項 4 の本文、
  `default_perf()` が性能比較用較正でないこと、pegasus job body が AI worktree 配下の repo root を
  拒否すること、名指しの publication root が不在であること。
  `/work/SFC/tanab/izanagi` は別 checkout ではなく主 checkout への別名だった。
- **real だが scope 外**として 3 件を裁定パッケージ候補に残した。適格性の 3 真偽値に根拠を要求する
  経路が無いこと、`scheduled_attempt_registry` の全件性を単独で証明する経路が無いこと、
  通常合成 campaign 用の専用 checkout 調達手順が runbook に一本化されていないこと。
- 実装面の差分はゼロ。段 5・6 を飛ばし `4→7→8→9`。変異 matrix は DW-S04 により免除。
- 検査: `check_docs` rc=0 (違反なし)、`spool_fold --dry-run` rc=0、`git diff --check` rc=0、
  凍結語の機械走査 `s8b_holdout_freeze search` rc=0 (新規 file の hit 0 件)、
  provenance 全史監査 rc=0 (10466 件・新規違反なし)。
  受入全走 attempt 1 は `child-green`、raw / normalized child rc=0、red 0 件・flake 0 件、
  tested main `d97c423bdd14e0b416cb4f585d350e6c2b251287`、effective scheduler `loadgroup`。
  lease は未取得のため release 対象なし。
- **親の手順誤りを 1 件記録する。** 受入全走を段 7 の記録 commit の**後**に走らせた。
  DW-S04 は記録前の実走と worklog への結果記載を求めている。fragment へ実測値を入れて
  commit を amend し、受入を取り直した。attempt 1 の結果は上のとおりで、緑であることは変わらない。
- 工数: codex 子 3 本、いずれも accepted (plan 1 = 334 秒 / 12 call、consult 2 = 256 秒 / 12 call と
  288 秒 / 9 call)。計算ノード job は 0 本。campaign・build・benchmark は 1 本も起動していない。
- **受入 attempt 2 は非帰属の赤だった。** rc=70 / child rc=1、内訳は `45 error, 24031 passed,
  68 skipped`。45 件はいずれも **failure ではなく setup の error** で、本文は 3 件とも
  `subprocess.TimeoutExpired`、対象は `git ls-files --others` / `git status --porcelain=v1` /
  `git archive` が 30 秒で切れたものである (shard の `junit.xml` から読んだ。子 log には
  FAILED 行しか出ない)。投入時の `/proc/loadavg` は `94.80 79.24 76.90` で上昇局面、
  同時走行中の受入待ち手は 5 本だった。**本 wave の差分は docs のみで、落ちた 2 file
  (`test_s8c_preregistration_predicates.py` / `test_t1259_qsub_env_delivery_probe.py`) の
  どの assertion にも到達しない。** 署名一致ではなく error 本文と差分実体で非帰属と判定した。
  同じ tip の attempt 1 相当は緑だった。
- セッション異常は無かった。`tools/dev_wave_wait.py producer` が pid-only へ縮退して rc=0 を
  返した場面があったが、`.done` の時刻を見ると producer は待ち手を張る前に正常終了しており、
  **待ち手の判定は正しかった。** `DW-O01` の「完了は `.done` と exit code だけで判定し、
  待ち手 rc を判定にしない」がそのまま効いた。
- 環境の所要: `git worktree add` は共有 FS 上で 11 分超かかった。submodule 初期化は 1 度目が
  `runtime-io-failure: update-no-fetch` で落ち、DW-O08 に従い同じ引数で 1 度だけ再実行して通した。

## 次の一手差分

### 更新

- [T-2632] **P2・更新**: B-4 の適格な赤 precursor の在庫を 0 件から増やす。供給源 (合成ループ
  campaign の whiteboard) と §5.1.1 の適格条件は変えない。成功例への置換と母集合を作るための
  追加基盤は D1936 項 8 が不採用にしている。2026-09-16 の照合で、供給側だけでなく**適格性側の
  3 条件が独立に未充足**であることが判明した — 事前登録 §6 が名指す publication root
  `output/b4-prerun-publication` の不在、§5 の校正済み `PerfConfig` 欄と `env_tag` 欄の未記入。
  順序は (1) publication の封印発行、(2) §5 の 2 欄の記入、(3) 専用 checkout からの通常 base
  campaign 起動と自然発生赤の回収。得られた少数は D1986 項 4 により記述報告までに留める。
  照合の一次資料は `output/insights/2026-09-16/t2632-b4-red-precursor-stock/README.md`。
  base: 8563e8a7fd7503ff2d4de2d1aa5b4fc3de75bfca933ffcb7dc158d84f1721def
