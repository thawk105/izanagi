---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-acceptance-5min-floor
seq: 1
title: 受入全走の律速を実測で特定し、fixture 入力の肥大を共有 base で塞いだが wall 短縮は観測できなかった (コード、branch worktree-dev-wave-acceptance-5min-floor)
---

## 本文

- **ユーザーの依頼**は「受入全走が壊滅的に死んでて研究開発が死んだ。受入全走は 5 分と決めているが
  数十分動いているやつがいる。すぐに 5 分に収めろ」。途中で「そいつらは CC 自動合成研究の実現に
  必要なのか。価値が小さいものに毎度高いコストを払うのはバカみたいでしょ」「codex と相談しながら
  検討して」と追加され、最終的に「あなたの仕事は受入全走の劇的改善」と scope が確定した。

- **救出 (本 wave の最初の行動)。** 計算ノード job 996124.nqsv と 996191.nqsv が pytest 完了後に
  CPU を一切使わないまま walltime まで居座っていた。Accumulated CPU Time を 3 回サンプルして
  増加ゼロを確認 (996124 は 6093.72 秒で固定のまま Elapse が 2679 → 2777 秒) し、ユーザーの
  指示で `qdel` した。所有 session 2 者へ連絡し、両者から独立の裏取りを得た。
  **qdel した走行は赤ではなく infra (`rc=70` / `normalized_child_rc=16` /
  `dispatch-attestation-missing`) で戻り、再走が必要になる。**

- **価値の問いへの答え (段 2・3 の codex 相談 2 本、lane=sol / luna、reasoning=high)。**
  sol の判定は「100 秒以上の 37 node のうち、走ごとに答えが変わらないので毎走でなくてよいと
  証明できたものは **0 件・0 秒**。32 件は certified 選択・proof chain・材料レポート・試行台帳の
  いずれかを直接守る。残り 5 件は別研究 (認証層比較、計 643.7 秒) が 4 件と開発運用が 1 件」。
  **同じ案は F485 で実行済みで事故になっている** (T-080 の 11 node をコスト理由で opt-in 化し、
  11 日後に赤 2 件が発覚、凍結検証の追随漏れを隠していた)。D532 は削除・skip・selection 縮小を
  規律 2 違反として検討対象外にし、D700 は T-080 の別 gate 定期実行も却下している。
  **したがって削減は採らない。** 高コストの原因は価値ではなく欠陥であった
  ({{F:fixture-input-drift-26x}})。

- **並行 wave との噛み合わせ。** repo 肥大の掃除 wave に照会したところ、
  `output/insights` と `output/env` は **tracked の削除確定 0 件**、pin 閉包が閉じていて削れず、
  wave ごとに増える、との回答を得た。件数も独立集計でほぼ一致した
  (先方 22,994 件 / 639,961,594 bytes、こちら 22,988 件 / 639,898,207 bytes)。
  同 wave から「`test_s8b_oracle_driver.py` の 1302 行・1328 行がコピーの全件性そのものを
  検査しているので、絞ると正しく赤になる」という警告を受け、**コピー範囲を絞る方向は採らず、
  同じ中身のコピーを安くする方向へ倒した。**

- **D1918 の前提が失効していた。** 同決定は 2026-09-09 の 9 走を根拠に「最遅 shard は shard-2」と
  記録するが、09-10〜09-14 の **112 走では shard-0 が 103 走 (92%) で最遅** (shard-2 は 7 走、
  shard-1 は 2 走)。最遅 shard の wall が 300 秒超なのは 106/112 走 = 94.6%、中央値 345.2 秒。
  掃除 wave からの指摘を受けて集計し、独立に確認した。

- **親の誤記 2 件を訂正した。** (1) 当初「shard-0 は 57 走すべて 300 秒超」と書いたが、同じ表の
  最小値 268.9 秒と矛盾する。正しくは中央値 345.2 秒。(2) 当初「最後のテスト終了から wall 終端まで
  約 76 秒」と書いたが誤り。正しい分解は開始側 55.74 秒 / dispatch 49.17 秒 / 実行 313.61 秒 /
  終了側 20.01 秒 (段 3 の luna が report.json と junit から再計算)。

- **主要な打ち手は効かなかった。** {{F:single-run-perf-claim}} のとおり、同時刻の旧コード 44 走を
  対照に取ると新コード 2 走はどちらも分布の内側であり、wall 短縮は検出できない。
  構造としては lustre からの全件読み出しが 11 回 → 1 回になっており、機構は動いている
  (`test_t080_shared_base_builds_real_builder_once_across_processes` が実 builder の呼び出し回数を
  数えて緑)。しかし build は 1 回 20〜24 秒で node 全体は約 260 秒であり、効果は約 8% で
  ばらつきに埋もれる。

- **ハング修正は撤去した。** {{F:subreaper-zombie-window}}。実走で孫 6 本の取り残しを実際に
  回収できたが、44 走緑だった正しさテストを赤にしたため規律 2 に従って撤去した。
  診断の `IZANAGI_DISPATCH_JOB_TRACE` だけ残した。**pytest 完了後に job が終わらない事象そのものは
  未解決である。**

- **land が 1 時間 26 分止まっていた。** {{F:land-lock-provenance-starvation}}。別 session からの
  報告を自分の ref で裏取りし、機序をコードで確認した。**本 wave では直していない** —
  8 session が同時に使う生命線であり、窓の時計の定義は D254 / `DW-O25` の設計そのものなので
  ユーザー裁定へ返す。

- **残る床の構造 (受入 1 走の分解、最遅 shard)。** collection 約 93 秒 + 収集終了から開始まで
  25.6 秒 + テスト実行窓 243.4 秒。**テスト以外が約 1/3 を占める。** 同時走行数と最遅 wall の
  相関係数は 0.381 (n=46) で、混雑の寄与はあるが支配的ではない。同時走行が最少のときでも
  最遅 wall の中央値は 385.3 秒である。**300 秒に入るには約 62 秒削る必要があり、
  残る打ち手はすべて裁定が要る。**

- **エージェント工数。** codex 子 8 本 (consult 2 = reasoning high、author 2 / fix 4 = medium、
  すべて gpt-6-astra)。受入全走 3 回、焦点走 5 回、単独 node 測定 1 回。

## 次の一手差分

### 新規

- {{T:acceptance-collection-cost}} **P1・新規**: 受入 1 走の collection 約 93 秒と、収集終了から
  最初のテスト開始までの 25.6 秒の内訳を確定し、短縮の可否を判定する。D1830 は「残余の動く分は
  主に collection に出る」とし、D1728 は自 shard 絞り込みを D711 の禁止ごと維持している。
  **絞り込み以外の手があるかを先に調べ、無ければ裁定へ返す。**

- {{T:t080-fixture-copy-scope}} **P1・新規・ユーザー裁定待ち**: `_copy_git_visible_output` が
  複製する `output/` 全件を、builder が実際に必要とする閉包 (`migration.KNOWN_AXES_REL` から
  `collect()` した `source_paths`、`operational` の 6 件、発行済み receipt の
  `migration_basis_commit` から復元する source closure) へ絞れるか。
  **絞ると `test_s8b_oracle_driver.py` の 1302 行・1328 行 (全件性の検査) が正しく赤になる。**
  受理集合が変わるため裁定が要る。全件性の理由は同 file 1000 行のコメント
  (「subprocess が import closure を host から補えないようにする」)。

- {{T:acceptance-shard-count-gt3}} **P2・新規・ユーザー裁定待ち**: 受入の分割数 K を 3 から
  増やすか。`tools/acceptance_shards.py` の `allocate` / `create_session` は `{2, 3}` を、
  `tools/acceptance_launcher.py` は `{1, 2, 3}` を受理する。D1620 が canonical を K=3 と明記し、
  D1103 は「K=3 で既に単体テストの床に達している」とする。**測定面の定義に触れる。**

- {{T:group-member-count-zombie}} **P2・新規・ユーザー裁定待ち**: `tools/codex_worker_launch.py` の
  残存数の計数が `/proc/<pid>/stat` の state `Z` を除外すべきか。除外しないため、reparenting を
  変える変更 ({{F:subreaper-zombie-window}}) がゾンビを残存として拾う。受理集合が変わる。

- {{T:land-lock-window-starvation}} **P1・新規・ユーザー裁定待ち**: land の共通 lock 待ち窓を
  lock 外の provenance 監査が食い潰す構造 ({{F:land-lock-provenance-starvation}})。候補は
  (a) 窓の起点を lock 待ち開始へ移す、(b) 同一 tip・同一 checker blob の監査結果を disk の
  受領証として再利用する。**D254 / `DW-O25` の設計に触れる。**

- {{T:dispatch-job-exit-hang}} **P1・新規**: 計算ノード job が pytest 完了後に終わらない事象の
  再調査。本 wave で残した `IZANAGI_DISPATCH_JOB_TRACE` が、次の再発時にどの段で止まったかを
  与える。**subreaper は採らない** ({{F:subreaper-zombie-window}})。
  容疑者は `_write_result_replace` 後の上限なし `os.fsync` と、孤児化した孫 process。

- {{T:acceptance-flaky-timeout-family}} **P2・新規**: 実 repo への subprocess / syscall へ
  壁時計の短い上限 (5 秒 / 30 秒 / 60 秒) を掛け、その上限が守られることを検査するテスト群が、
  負荷で走行ごとに入れ替わりながら赤になる。`test_pegasus_floor_tools` /
  `test_t1259_qsub_env_delivery_probe` / `test_env_contract_activation` /
  `test_run_tests_preflight` / `test_s8c_preregistration_predicates` が該当
  (`test_repository_candidate_uses_real_s8c_budget_module` は 44 走中 7 走で赤 = 16%)。
  **上限を伸ばすと検査対象そのものが恒真化する**ため、設計判断が要る。

- {{T:acceptance-auth-layer-4nodes}} **P3・新規・ユーザー裁定待ち**: 認証層比較の 4 node
  (計 643.7 秒、`test_p3_b4_producer_auth_experiment`) を毎走走らせる価値。段 2 の sol は
  「現行 production の認証機構ではなく別研究の比較報告を守る。直接 consumer の不在は確認できたが、
  退役可能性・代替検出力までは証明していない」とした。**親は裁定しない。**
