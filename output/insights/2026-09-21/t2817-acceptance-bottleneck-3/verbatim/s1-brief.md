# 段 1 brief — [T-2817] + [T-2273]/[T-2444]/[T-2495]/[T-2560] 受入律速の再同定 (第 3 回) と collection 差の分解診断

wave `dev-wave-t2817-acceptance-bottleneck-3`、起点 local main `285477c00` (fresh worktree、HEAD == main、開始 gate rc 0)。依頼の逐語は `T-2817-origin.md`。

## 研究前進 (1 行)
受入全走 (Phase 3 の全 wave が毎回払う土台) の最遅 shard を 5 分以内へ入れる作業 (T-2273、D1936 項 35 = 実測で律速を選んでから実装する) の、pairing 既定 on (entry 1756) 後の律速の再同定と、collection 差の同条件分解。完了判定 = 律速の成分と機構を一次資料で特定し、削減策の効果量の見込み (実装しない) を書くこと。

## scope
- (1) pairing 後の実受入で最遅 shard の wall の内訳を取り直し律速を再同定する。(2) 受入 `pre` 61 秒と温 collection 18.4 秒の差 約 43 秒を、同 job・同 checkout で「独立 48 process → xdist -n 48 (hold 検査を壊さない全 deselect の形) → shard plugin 有り → duration ledger 有り」と段階的に載せて分解する。
- 診断のみ・実装 0 行 (conftest / gate / ledger の改変で代用しない)。probe (runner / plugin / 集計) は Codex author が job dir に書き、repo には逐語 `.txt` だけ置く。削減可能量は分解が閉じるまで書かず、効果量の見込みだけ記録する。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

## 確定済みユーザー裁定
D2148 項 6 (受入時間は組み合わせの実測と共有準備の内訳調査を進める、受理集合維持、5 分超過を受容しない)、D1936 項 35 (実測の最遅 worker を対象、効果を先に測る)、D2107 (ledger refresh mode の運用)、D2185 (早期 memo prewarm は現行維持)、D532 (worker 数・配布順の変更は提案しない)、D2068 の却下 3 案は再提示しない。

## brief 前の前提実測が出した新事実 (段 4 で再裁定する対象)
一次資料は本 job dir の `shards-recent-v1.json` / `shard0-pairing-v2.json` (読み取り script `read_shards_v1.py` / `read_shards_v2.py`、受入成果物 `/work/1/SFC/tanab/.izanagi-acceptance-shards/` の直近 60 session を read-only で整形。pairing property の有無で群分け、pairing 群 21 session / 63 shard、観測 2026-09-21 00:5x JST)。
- N1. 最遅 shard は 21/21 で shard-0。W 中央値 398.6 秒 (349.6〜648.2)。最長 node L は 21/21 で `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[...]` (中央値 233.7 秒)。
- N2. **L の worker の相方は 21/21 で 0.0 秒 (pairing は L の worker に効いている) が、最大占有 worker は 21/21 で L の worker と別**で、rank 423〜429 (2 session は 376〜377) の `test_s8b_oracle_driver.py` の node (`test_t080_active_v2_delegation_accepts_full_receipt` 180〜335 秒、`test_v1_gate_does_not_delegate_with_active_v2` 189〜336 秒、`test_t080_active_v2_preserves_nonlayer2_receipt_refusal` 144〜153 秒、`test_t080_failed_launch_preserves_receipt_refusal` 45〜279 秒) を 2〜3 個直列に抱える。O_max 中央値 327.3 = L + 62.7 秒 (55.0〜170.0)。
- N3. これらの node は ledger (`orchestrator/tests/acceptance_duration_ledger.json`、最終再生成 2026-09-17 `363e79b10` [T-2236]) に**未収載** (T-2724 で 2026-09-18 に追加)。conftest の並び替えは未収載 unit に「既知 cost の 96 番目」を既定 cost として与える (`_ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS = 96`)。shard-0 の選択集合と ledger で offline 再現 (`rank_replay_v1.py`) すると 4116 unit 中 334 unit が未収載、既定 cost = 13.0 秒、当該 node は rank 373〜382 (実走の 423〜429 は collection 順の近似差)。**律速の機構 (仮説、同 job 対照は未実施): 実所要 150〜335 秒の unit が 13 秒扱いで後方に置かれ、動的配布で別 worker へ直列に載る。**
- N4. 固定費 F = W − O_max は shard-0 中央値 77.3 秒 = 開始前 `pre` 67.0 秒 (59.9〜123.9) + 終了後 10.0 秒 (21/21 で 10.0〜10.1、shard-1/2 は約 3〜4 秒)。`pre` のうち controller の早期 receipt memo prewarm (`IZANAGI_MEMO_PREWARM_V1` の `receipt_memo_s`) は中央値 58.2 秒 (45.5〜89.5) で、worker は `pytest_collection_finish` でこれを待ってから `collection_finished_epoch_s` を記録する (conftest `_wait_early_memo_job` → shard plugin trylast)。`pre − receipt_memo_s` の中央値は 5.0 秒。**T-2700 / D2185 は同じ機構を「E 経路は memo 解決が collection と並走して配布開始 60 秒」と定量化済み**で、T-2243 §5 (d) の「約 43 秒」はこれと接続されていなかった。
- N5. `--collect-only` は xdist を無効化する (`xdist/plugin.py` L269) ので、xdist 段の「collection だけ」は別設計が要る。controller の hold 完全性検査は `pytest_xdist_node_collection_finished` で worker 報告 (deselect 後) の ids を見るため `-k` 全 deselect は必ず壊れる (T-2243 X 腕)。

## (P) 親の provisional 裁定・攻撃対象
- (P1) **最長 node L の内訳 (base 構築 / verify / copy) の計算ノードでの取り直し (T-2786 型 wrapper probe の 5 要素 key への適合 + replica) は本 wave では行わない。** 理由: N2 で wall を決める worker は L の worker ではなく、内訳を取り直しても律速の同定に効かない。代わりに (1) は shard 層 (W / O_max / L / 相方 / F / pre / memo / 終了後) を実受入 21 session + 本 wave 同 tip の実受入 1 走で取り直し、L の内訳は T-2786 (`7975385b5` の命題) の値を「取り直していない」と明記して引く。依頼文の「共有 base 構築・verify・copy」を取り直さない読み替えなので、段 3 が反証すれば T-2786 probe の適合 + replica 1 job を足す (別 node へ並行投入)。
- (P2) **段階載せの設計:** 同 job・同 node・同 checkout (wave 木、Lustre、pyc 温) で S0 = 独立 48 process `--collect-only` (T-2243 L 腕の再現)、S1 = `-n 48 --dist loadgroup --maxfail=1` + probe scheduler (shard plugin 無し)、S2 = S1 + `-p tools.acceptance_shards` + spec env (shard 0/3、session_root は job dir)、S3 = S2 から `--maxfail=1` を外す (ledger 読込 + 並び替え + pairing 有り = 実受入の argv 形)。各 2 走、順序反転。
  - 「collection だけで test を実行しない形」= probe plugin が `pytest_xdist_make_scheduler` (firstresult、xdist 側は trylast) で `LoadGroupScheduling` の派生 (`schedule()` は何も送らず、`tests_finished` は collection 完了で真) を返す。deselect しないので hold 検査は完全 collection のまま通り、DSession は collection 完了直後に shutdown へ進む。conftest の `_xdist_flaky_collection_is_complete` が読む `sched.numnodes` は継承で保たれる。
  - `--maxfail=1` は conftest `_acceptance_options_allow_reordering` が「通常の実行順でない」と判定する parsed option で、ledger 読込 (`_acceptance_controller_should_load_duration_ledger`) と並び替え (pairing を含む) を conftest 改変なしに切る lever。test を実行しないので他の効果は無い (攻撃対象)。
  - 計時: probe plugin の hookwrapper (`wrapper=True, tryfirst=True`) が worker ごとに (a) `pytest_collection_modifyitems` 前後、(b) `pytest_collection_finish` の入口 (= 自分の collection 完了、conftest の memo 待ちの前) と出口 (= 待ち後) の epoch を `workeroutput` へ書き、controller が `pytest_testnodedown` で回収。controller 側は `pytest_sessionstart` epoch (junit timestamp と同じ起点)、`pytest_xdist_node_collection_finished` の到着時刻、`IZANAGI_MEMO_PREWARM_V1` 行、総 wall を記録。`pre` 相当 = max(worker の出口 epoch) − sessionstart。
  - 分解の読み方 (結果を見る前に固定): S1 − S0 = xdist 起動 + 48 worker collection の同時性 + controller 照合; S2 − S1 = shard plugin (records / allocate / deselect) + 早期 memo 待ち (worker の出口 − 入口で直接分離); S3 − S2 = ledger 読込・配送 + 並び替え。段の差は同 job の対比較で、`pre` 61 秒の「成分配分」は S3 の値と本 wave 同 tip の実受入 `pre` が整合したときだけ書く (整合しなければ差を条件差として記録)。
- (P3) **効果量の見込みの書き方:** N3 の ledger 未収載 (D2107 の refresh 対象) について、当該 8 node に実測中央値を与えた並びを offline 再現し「O_max がどう変わるか」の算術見込みを書く (実 wall の予測値は書かない、D357)。N4 の memo prewarm 58 秒は D2185 で現行維持が裁定済みなので、短縮策は提示せず「`pre` の成分として同 job で確認した値」だけ書く。終了後 10.0 秒は成分名を当てず観測として記録 (shard-0 固有、原因未同定)。
- (P4) **単独性・並行投入:** Job A (段階載せ、1 node、30〜40 分、`dispatch_compute.py --task generic`) は wave 木を cwd に読むだけ (`PYTHONDONTWRITEBYTECODE=1`、`-p no:cacheprovider`、出力は node-local → job dir、memo cache は TMPDIR)。実受入 1 走 (3 shard、`dev_wave_wait.py acceptance`) は Job A 終了後に投入 (runbook §7.5 「受入全走の隣」)。pyc は投入前に login で `python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider` (書込み許可) を 1 回走らせ wave 木の `__pycache__` を温める (実受入の 2 回目以降と同じ条件)。

## 不変条件
規律 2 (受理集合・hold・verifier に触れない)、規律 7 (過去測定を現行差で無効化しない)、D1936 項 35 (実装しない)、DW-O19 (tracked file の一時変異なし — 本 wave は 0 件)、probe は job dir (repo へ入れない、逐語 `.txt` のみ)。

## 成果物
`output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md` (結論・前提実測 (1)・段階載せ (2)・弁別・効果量の見込み・既存被覆・所見と裁定・限界・再現手順)、`aggregate.*`、`raw/`、`verbatim/` (依頼・brief・相談・裁定・author・レビュー・probe 逐語)、worklog fragment、T-2817 / T-2273 / T-2444 / T-2495 / T-2560 の次の一手更新。decisions fragment は新しい設計判断が出た場合だけ。

## 分割方針 (軽量版 + 診断 wave の型)
段 1 → 段 3 相談 1 本 (read-only、2 レンズを 1 本: (a) 設計・帰属の攻撃、(b) 依頼との整合と既存被覆) → 段 4 → 段 5 Codex author 1 本 (probe runner / plugin / 集計、job dir) → 親の login 生死確認 (probe plugin を `-n 2` で通す) → 計算ノード Job A → 親の README → 実受入 1 走 → 段 6 read-only review 1 本 + 焦点再レビュー (上限 3 巡) → 7 → 8 → 9。段 2 は省く (設計択一は (P2) に集約し段 3 に攻撃させる)。
