---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-hot-block-microbench
seq: 1
title: [T-2878] VHash の hot block 配置を 1 キー版選択の微小計測で比べた — LLC 外の最新版選択は連続配置 scalar が散在 linked の 0.55〜0.84 倍、hot 内の深い版は連続配置がほぼ一定、SIMD の利益は見えず。書き込みは ring が最安 (コード + test + insight、計算 1.82 node 時間、branch worktree-dev-wave-vhash-hot-block-microbench)
---

## 本文

- 依頼: VHash 論文の並行 wave md_5 (ユーザー依頼で親セッションが用意した `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_5.txt` と `common.txt`)。着手時は対象 item も `docs/paper-story-vhash/` も local main に未着地で、同じ中身の複製 (docs-snapshot) を読んだ。ユーザー就寝中につき判断は codex と自分で行うよう、並行セッションの監督役から連絡があった (ユーザーへの問い合わせは 0 件)。
- 成果物: 一次資料 `output/insights/2026-09-29/vhash-hot-block-microbench/README.md` (§0 が結論、§6 が限界、§7 が無効にした走の経緯)。置き場の判断は {{D:vhash-hot-block-microbench-standalone}}。
- 裁定で退けた所見: 段 3 相談 2 本がそろって must-fix に挙げた「依頼文と Cicada の PENDING の扱いが食い違う」は、出典メモ §7.3 が「対象 timestamp 以下に、より新しい PENDING」と書いており同じ意味なので不一致ではないと裁定し、照合ベクトルの明確化だけ採った。焦点再レビュー 1 の N1 (pilot の外挿が本走を代表しない) は shard ごとの `--max-wall-s` の硬い上限で運用して閉じ、N4 (既存出力先への再出力で新旧混在) は一次資料を常に新しい出力先へ出すので限界として記録した。
- 親が統合後に見つけた欠陥 (レビューが挙げなかったもの): 実装子の node が値の置き方に関係なく 320 B (5 cache line) だった、連続配置が hot で当たっても cold pointer を先に読んでいた、読み側のキー列が短周期だった ({{F:microbench-key-chain-short-period}})。3 件目で初回本走の読み側 (約 0.87 node 時間) を無効にし、取り直した。
- 計算ノードの異常: pilot1 は 35 分 QUE のまま dispatcher の全体時間上限で取り消された ({{F:dispatch-overall-timeout-includes-queue}}、runbook へ追記)。pilot2 は perf の smoke で、計算ノードの perf がこの CPU で汎用 event の L1-dcache-load-misses・dTLB-load-misses を数えられないと判明し、event を 5 つに絞った。pilot4 は ops 較正の打ち切りで失敗し、較正を直した。
- 書き込み側の keyset 区分は成立しなかった (履歴を回収しない追記のため 1 キーの確保量が数 MB になり、key 数が 64 と 84〜420、hot block は両方 cache 内)。書き込みの値は「cache 内の hot block」の費用として報告した。
- 変異: probe 1 走 (d0fe78c15、9 変異すべて赤を観測) → 本走 2 走 (b42cba01e) で 11 変異すべてが期待 node 集合と完全一致で KILLED (一次資料 §8)。M11 の走行で較正 test の補助 binary が計算ノードの repo 直下に core file を残し、次の harness 起動が untracked で止まった (消して再投入)。
- 焦点走 1 回目は赤 2 件: perf file 台帳 (`test_official_perf_closure.py`) が作図器を未審査と判定 (作図器は記録済みの perf 値を読むだけで perf を起動しないと審査し、先例 `plot_s1_9pair.py` と同じく台帳へ 1 entry を登録、fix 巡 9)、もう 1 件は未 commit の fragment による作業木の変更集合検査の赤 (commit で解消)。
- 受入 1 回目 (claimed main 3bf2d0a16) は `1 failed, 27965 passed, 74 skipped`。赤は自 wave 起因: 作図テストの Python 子起動が `env=dict(os.environ, …, PYTHONDONTWRITEBYTECODE="1")` の形で、bytecode guard の浅い検査器 (`tools/check_subprocess_bytecode_guard.py`) が guard と認識しない。argv に `-B` を足した (fix 巡 10)。新規 test を足すときの repo 全体の検査器 (この checker) を子も親も焦点走に入れていなかった。
- 工数: codex 子 = plan 1、consult 2、author 2、review 2、fix 11 (巡 1 が 2 本、巡 2〜10 が各 1 本)、focus 2。計測 job の合計 6,545 秒 (約 1.82 node 時間、無効にした初回分を含む)。変異・焦点走・受入の job は含まない。

## 次の一手差分

### 完了

- [T-2878] 3 方式 (連結リスト散在・局所、連続配置 scalar、連続配置 AVX2) を K (1〜16)・深さ (hot 内 / cold)・値の置き方と大きさ・キー数 (L2 内 / LLC 外) で比べ、書き込み 4 方式の費用と perf の cache miss・命令数を取り、図 3 種を生成器付きで置いた (一次資料 `output/insights/2026-09-29/vhash-hot-block-microbench/README.md`)。
  remaining: none
  base: d3516d3de69f680524edcc3a12bf8f69ee5ff225632dd97d333c601163d02f32

### 新規

- {{T:vhash-hot-block-followups}} **P2・新規 (VHash hot block 微小計測の延長)**: 一次資料 `output/insights/2026-09-29/vhash-hot-block-microbench/README.md` §6 の未測定を必要に応じて測る。(1) cache の外にある hot block への書き込み (履歴を回収して key 数を LLC 外まで増やす)、(2) 独立な複数キーを並べた throughput (本計測は依存連鎖の latency だけで、WAIT の cell はその理由で比較から外した)、(3) huge page と TLB の寄与 (pilot が 8×LLC まで飽和しない、dTLB event がこの perf で数えられない)、(4) AVX2 が K≥8 で scalar より遅い機序、(5) ring の読み側 (回転した順序) の費用。次の版 (`docs/paper-story-vhash/` 2 版目) の再導出で要るものだけ投げる。
