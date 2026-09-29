## 2026-09-29 (1911) — VHash と timestamp forwarding の論文ストーリー系列を新設し、並行 wave の投げ文を用意する (docs のみ、branch worktree-paper-story-vhash-setup)

- ユーザー指示 (2026-09-29): 外部の対話 AI との議論をまとめた研究メモ (VHash・選択的 timestamp forwarding・GC の協調) を
  貼り、「これで論文を一本書こうかと考えている」「docs/ に新しい paper-story のディレクトリを専用に設けてくれ」
  「図やグラフを多用してわかりやすく」「dev-wave を並列で投げまくって調査・試行錯誤・実装・実験を進めたい」
  「投げ文は /work/1/SFC/tanabe/tmp に md_1.txt のように外出しして」と依頼した。`/work/1/SFC/tanabe` は実在せず、
  実在する `/work/1/SFC/tanab/tmp` の下に置いた。
- 新設の判断は D2280。初版 `2026-09-29.md` は Mermaid 24 枚・文字の図 1 枚・画像 0 枚。
- 確かめた事実: CCBench の `cc/silo/transaction.cc` には `#if TRACE` があり、`cc/cicada/` の全ファイルには `TRACE` の
  文字列が無い。`orchestrator/verifier/` にも `cicada` の文字列が無い。Cicada の variant は現状、正しさ検査器を通せない。
- 並行 wave の投げ文 6 本 (文献・実測・正しさ検査・小さいモデル・配置の微小計測・forwarding 試作) を repo の外に置いた。
  各 wave は下の新規 item に対応する。投げ文は T 番号を持たず、item を本文の文言で探す形にした (ユーザー指摘「T番号に依存する必要ある？」)。
  本エントリの land より先に、同じ投げ文 (md_1) の文献調査 wave が docs の repo 外複製を読んで着手・着地し、
  文献調査の残件を [T-2873] として自分で登録した。重複を避けるため、本エントリは文献調査の新規 item を登録しない。
- 本エントリの land は、Pegasus の gen_S が 80〜90 本待ちの混雑で受入の shard が queue 待ち 900 秒で 8 回打ち切られ
  (テストは 0 件実行)、06:31 JST に門番経由の 9 回目で child-green になった。その後 main へ md_1 wave が着地したので
  取り込み直し、断片を直して受入をやり直した。
- 受入の赤の帰属 (DW-O18): 07:07 JST の受入 (tip 5104356aa、main f6772df03) で
  `orchestrator/tests/test_env_contract_activation.py` の 3 件
  (`test_historical_calibration_is_verified_only_when_resolved_in_source_stage[missing]`・同 `[modified]`・
  `test_import_performs_no_open_or_stat_io_in_worktree_or_archive_source_stage`) が、テスト内の
  `git archive ... HEAD` の 30 秒 timeout (`subprocess.TimeoutExpired`) で落ちた。本 branch の差分は docs と spool fragment だけで
  この経路に触れない。同じ tip で 3 件だけを計算ノードへ投げた単独再走 (request 33958.nqsv) は `3 passed in 11.11s`。
  混雑時の共有 FS による一過性で、本 branch に帰属しないと判定した。
- 同じく 07:31 JST の受入 (tip 58c6906aa、main da4068e0e) で `orchestrator/tests/test_t810_coordinator.py` の 3 件
  (`test_prepare_group_accepts_external_root_with_anchor_union`・`test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir`・
  `test_prepare_group_rejects_forged_git_identity_before_any_mkdir`) が `cannot read worktree registration: file is absent` で落ちた。
  本 branch は worktree 登録の経路に触れない。3 件だけの計算ノード単独再走は `3 passed in 5.27s`。受入中の並行 session による
  worktree 登録の変化と読み、本 branch に帰属しないと判定した。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (1910)
- [T-265] (1910)
- [T-129] (1910)
- [T-238] (1910)
- [T-570] (1910)
- [T-580] (1910)
- [T-793] (1910)
- [T-823] (1910)
- [T-841] (1910)
- [T-1069] (1910)
- [T-1071] (1910)
- [T-1234] (1910)
- [T-1295] (1910)
- [T-1524] (1910)
- [T-1660] (1910)
- [T-1702] (1910)
- [T-1703] (1910)
- [T-1708] (1910)
- [T-1784] (1910)
- [T-1794] (1910)
- [T-1832] (1910)
- [T-1834] (1910)
- [T-1882] (1910)
- [T-1883] (1910)
- [T-1944] (1910)
- [T-1950] (1910)
- [T-2000] (1910)
- [T-2005] (1910)
- [T-2052] (1910)
- [T-2084] (1910)
- [T-2092] (1910)
- [T-2100] (1910)
- [T-2172] (1910)
- [T-2205] (1910)
- [T-2218] (1910)
- [T-2221] (1910)
- [T-2222] (1910)
- [T-2244] (1910)
- [T-2245] (1910)
- [T-2250] (1910)
- [T-2273] (1910)
- [T-2277] (1910)
- [T-2288] (1910)
- [T-2300] (1910)
- [T-2318] (1910)
- [T-2322] (1910)
- [T-2323] (1910)
- [T-2351] (1910)
- [T-2378] (1910)
- [T-2387] (1910)
- [T-2404] (1910)
- [T-2415] (1910)
- [T-2422] (1910)
- [T-2425] (1910)
- [T-2451] (1910)
- [T-2453] (1910)
- [T-2459] (1910)
- [T-2461] (1910)
- [T-2463] (1910)
- [T-2511] (1910)
- [T-2522] (1910)
- [T-2538] (1910)
- [T-2541] (1910)
- [T-2559] (1910)
- [T-2560] (1910)
- [T-2561] (1910)
- [T-2575] (1910)
- [T-2604] (1910)
- [T-2606] (1910)
- [T-2648] (1910)
- [T-2685] (1910)
- [T-2699] (1910)
- [T-2725] (1910)
- [T-2739] (1910)
- [T-2740] (1910)
- [T-2741] (1910)
- [T-2754] (1910)
- [T-2755] (1910)
- [T-2759] (1910)
- [T-2767] (1910)
- [T-2787] (1910)
- [T-2806] (1910)
- [T-2808] (1910)
- [T-2818] (1910)
- [T-2820] (1910)
- [T-2827] (1910)
- [T-2829] (1910)
- [T-2838] (1910)
- [T-2840] (1910)
- [T-2846] (1910)
- [T-2848] (1910)
- [T-2850] (1910)
- [T-2851] (1910)
- [T-2852] (1910)
- [T-2853] (1910)
- [T-2854] (1910)
- [T-2855] (1910)
- [T-2859] (1910)
- [T-2864] (1910)
- [T-2865] (1910)
- [T-2867] (1910)
- [T-2870] (1910)
- [T-2871] (1910)
- [T-2872] (1910)
- [T-2873] (1910)
- [T-2874] (1910)
- [T-2875] **P1・新規**: Cicada の版探索長・hot 相当の当たり率 (K 別の反実仮想)・forwarding の機会・GC 境界の遅れ・生存版数を診断計器 patch で実測する (メモ §29 段階 1)。
- [T-2876] **P1・新規**: Cicada に検査用トレースを足し、izanagi の正しさ検査器で多版の履歴を検査できるようにする。壊した Cicada の positive control も用意する (forwarding 試作の正しさゲートの前提)。
- [T-2877] **P1・新規**: 選択的 forwarding のプロトコルを小さいモデルで書き、reader・writer・forwarding・GC の割り込みを全探索して serializability を検査する (メモ §29 段階 2)。
- [T-2878] **P1・新規**: 版選択の配置を微小計測で比べる (連結リスト・連続配置 + scalar・連続配置 + SIMD、K・版の深さ・値の大きさ)。
- [T-2879] **P1・新規**: Cicada に cold 境界 (論理的な K 版) で発火する選択的 forwarding を inert variant patch として試作し、abort して再実行する対照と比べる (GC 保護は変えない、メモ §29 段階 3)。
- [T-2880] **P2・新規**: 上の 5 件と [T-2873] (文献調査) の一次資料が揃ったら、`docs/paper-story-vhash/` の 2 版目を全面再導出する (図を先に)。

