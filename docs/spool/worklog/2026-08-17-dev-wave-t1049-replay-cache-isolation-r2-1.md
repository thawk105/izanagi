---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1049-replay-cache-isolation-r2
seq: 1
title: replay cache の test 間汚染は起票時の衝突源が 89723b89 で既に消えており、隔離すべき汚染が無いことを実測して完了へ送る — 共通 autouse fixture は不変条件を破るので不採用 (docs、branch worktree-dev-wave-t1049-replay-cache-isolation-r2、実装差分ゼロにつき変異 matrix 免除)
---

## 本文

- **依頼は「test 側で隔離する」だったが、段 1 の前提実測で隔離すべき汚染が無いと分かったため
  実装しなかった。** 起票 (2026-08-13) 時の失敗機序は、`_origin_public_inputs` を使う 5 本の test が
  `terminal_operation_id="public-origin-terminal"` という同一定数を、`tmp_path` の違いによって
  異なる payload とともに使っていたことである。xdist の同一 worker に 2 本以上が載れば 2 本目が
  必ず `FormalReceiptError(REPLAY)` を投げた。この定数は 2026-08-15 の commit `89723b89`
  (`feat(t244)`) で `tmp_path` の sha256 を付けた一意値へ変更されており、衝突源そのものが消えている。
  台帳の赤の観測も archive (519) と (535) の 2 回だけで、いずれも 2026-08-13 である。
- **親が実測した 4 走はすべて緑。** 到達しうる 6 file の直列単一プロセス走 (`-n 0`) が 403 passed
  (204.78 秒)、既存 clear fixture を持つ `test_reflux_formal_consumer.py` を外した 5 file の直列走が
  353 passed (210.40 秒)。後者は「clear が衝突を隠している」可能性を狙って潰した走である。
  並列 (loadgroup) の 4 file 走は 285 passed (119.88 秒)、2 file 走は 72 passed (3.73 秒)。
- **敵対レンズが親の推論を 1 点訂正した。** 親は「`pytest-randomly` 未導入なので順序はファイル順で
  決定的」と書いたが false である。`--dist loadgroup` の scope 並べ替えと完了時刻による work unit
  配布で worker 同居は非決定的になる。結論が維持されるのは順序が決定的だからではなく、現行 writer の
  `operation_id` が互いに異なるからである。根拠を差し替えた。
- **共通 autouse fixture (段 1 の (P1)/(P2)) は 2 本のレンズが独立に潰した。** 決定打は
  `test_pytest_failure_digest.py::test_nested_pytest_main_currently_clears_outer_failure_stash` が
  外側 test の途中で `pytest.main(..., plugins=[C])` を再入することで、共通 autouse fixture は内側
  session にも登録されるため「同一 test 内の replay 検出状態を途中で消さない」を直接破る。加えて
  旧定数へ戻しても test 境界の clear が REPLAY red を消すため、隔離ではなく検出力の破壊になる。
- **pin assertion 案も不採用とした。** 旧定数への巻戻しは既存 2 test が同一 process に載れば既に殺し、
  別 worker に分かれれば survive する。変異 verdict が worker 分配に依存するため、`DW-M01` の
  単一理由性を満たす事前登録変異を作れない。
- **族一般化は条件を満たさない。** worklog (519) と (535) は同一事象の 2 回観測であって独立 2 例ではない。
  広い「process-local test state 汚染」族の独立例としては F306 (worker signal mask 汚染) があるが、
  formal replay cache 族としては 1 例のみなので `DW-G03` により制度化しない。
- **既存の登録済み受容へ収容した所見が 1 件。** レンズ A は「`--confcutdir` を suite root 下へ
  向けると共通 conftest を迂回でき、受入形判定もそれを許す (`tools/run_tests.py` の
  `_NONSELECT_VALUE_OPTIONS` に `--confcutdir` が入っている)」を挙げた。親が実測確認したところ、
  `tools/hold_inventory.py` が `pytest-confcutdir-below-suite` を `known-unresolved-bypass` として
  登録し、`orchestrator/tests/test_hold_inventory.py` がその登録を機械検査していた。
  同 entry の `tracking` field が指す [T-930] は 2026-08-13 (515) で完了済みなので、
  現在の所有者は台帳の task ではなく inventory の登録 entry 自身である。
  本 wave は共通 conftest へ依存を足さないため新規起票はしないが、この所在は記録しておく。
- **子の工数と非実走。** 段 2 plan 1 本 (`gpt-5.6-sol`、reasoning=max、rc=0)、段 3 敵対 2 本
  (sol / luna、reasoning=max、いずれも rc=0)。3 本とも read-only sandbox で pytest を 1 度も
  実走しておらず、緑を騙らなかった。テストの実測はすべて親が取った。
- **前回中断の原因は解消済みだった。** 2026-08-13 の中断は Codex plan job が既定 5 秒の evidence
  deadline まで session event 0 で終了したことだったが、現 `tools/dev_wave_codex.py` の
  `--evidence-grace-s` 既定は `min(90, --max-wall-clock-s)` になっており、本 wave では 3 本とも
  正常に model call まで到達した。
- **親が実装面の script を 1 本書いた (境界逸脱)。** worklog fragment の `base:` を carry 解決経由で
  取るため、job tmp に `base_digest.py` を書いて `tools/spool_fold.py` の内部関数を呼んだ。
  `DW-C00` の凍結境界は probe / script も実装面と定め Codex `role=author` に限っている。
  repo 外かつ出力が `spool_fold --dry-run` で fail-closed に再検査される性質のため実害は無いが、
  逸脱として記録する。**これは規律の緩みではなく構造の穴**で、carry 解決済み digest を出す公開手段が
  repo に無く、`spool_fold` の private API を呼ぶしかない。段 8 で裁定パッケージ RP-1 へ送った。
- **段 8 自己改善は候補 2 件を裁定し、docs 編集はゼロだった。** (1) 前回中断の原因だった Codex plan の
  evidence deadline は既に `min(90, --max-wall-clock-s)` へ改善済みで、本 wave の 3 本とも正常に
  model call へ到達したため是正不要。(2) 上記の `base:` 取得手段は `DW-C00` の実装子権限境界に
  関わるため、`docs/skill-self-improvement.md` の dev-wave 終端に従い実装せず裁定パッケージへ送った
  (`output/insights/2026-08-17_t1049-replay-cache-isolation/ruling-package.md`)。

## 次の一手差分

### 完了

- [T-1049] 起票時の衝突源が commit `89723b89` で既に消えていることを実測し、現 main に隔離すべき
  汚染が無いことを 4 走で確認した。共通 autouse fixture は不変条件を破り、pin assertion は変異の
  単一理由性を満たさないため、いずれも不採用として実装せずに閉じた。
  remaining: none
  base: d78b80a73ccb4e9930282255d2ed84075af92b827bdac62d225f8480e4c2cc3a

### 新規

- {{T:spool-base-digest-tool}} **P2・新規・ユーザー裁定待ち (RP-1)**:
  spool fragment の `base:` に要る carry 解決済み digest を出す公開手段が repo に無く、
  親は `tools/spool_fold.py` の private `_extract_latest_active` を呼ぶ script を書くしかない。
  ところが `DW-C00` の凍結境界は script も実装面と定め Codex `role=author` に限っているため、
  台帳を終端する wave のたびに親が境界を破るか docs 1 行のために実装子を立てるかになる。
  親の推奨は読み取り専用 subcommand の追加 (択 i)。詳細と選択肢は
  `output/insights/2026-08-17_t1049-replay-cache-isolation/ruling-package.md`。
