---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2515-rr5-accepted-calibration
seq: 2
---

## 再発

### F348

- **再発: 2026-09-16** — 向きが逆の同型。段 2 plan 子と段 3 レンズ B が、`attempts/*/calibration.md` を
  固定集合と完全一致で比較する `test_env_attestation.py::test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies`
  の本文だけを読み、「新しい attempt を 1 件足すと赤になるので実装子が要る」と独立に判定した。
  実際には同 node は `orchestrator/tests/growth_test_holds.py:300` に
  `hold_axis=output_artifacts` で登録済みで、実走は `1 skipped` になる。親が実走して反証し、
  不要な実装子と変異 matrix を立てずに済んだ。F348 は「保留 node を期待赤に選ぶ」= 赤になると
  思った node が走らない型で、本件は「走らない node を根拠に作業を増やす」型である。
  **どちらも根は同じ — テストの実在と実行は別問題で、子は `_HOLD_ROWS` を見ない。**
  親の brief も「赤の予測は hold 台帳を見てから書け」と指示していなかった。
  ただし hold による skip は整合性の確認ではない。本 wave は投入前から 6 件あったコーパス乖離と
  増分 1 件を `output/insights/2026-09-16/t2515-rr5-calibration/README.md` §7 に記録した。

### F859

- **再発: 2026-09-16** — 3 回目。背景 job の dev-wave で submodule 初期化を
  `cd <主 checkout> && python3 tools/dev_wave_submodule_init.py --worktree <wave>` の形で打ち、
  永続 shell の cwd が共有 checkout へ移って以後 3 回の Bash が全拒否された。
  `EnterWorktree({path: <wave worktree>})` で復旧し、実害は時間のみ。
  **本 wave の本題は、その先で起きた重複検討である。** 段 8 でこの作法を**新規候補**として扱い、
  `DW-C01` (追記で 1223 > 1000 bytes、exact 契約 pin) と `DW-O20` (1111 > 1000 bytes) への収容を
  試し、D730 / D782 の手順で「実施しない」へ落とすところまでをやり直した。
  **F859 の恒久対応節は同じ結論 (「`DW-O20` へ復旧経路を足す案は byte 予算が満杯のため採らない。
  安全義務を削って捻出しない」) を 2026-09-07 に既に書いている。**
  原因は段 8 の routing 前に failures を主題で引かなかったこと。
  `grep -n "EnterWorktree" docs/failures.md` は 16 hit あり F859 は 23328 行にあるが、
  `head -10` で切って上位だけを読み、F100 (4719 行) を見て「同型なし」と判断した。
  CLAUDE.md の「既存被覆を性質で decisions / failures / archive まで検索し、純増だけ書く」
  (`DW-S01`) に反している。
- 追加の再発検知: 段 8 の候補を routing する前に、候補の**主題語**で `docs/failures.md` を引き、
  **hit 件数を数えてから全 hit の F 見出しを確認する**。先頭だけを読んで同型なしと判断しない。
