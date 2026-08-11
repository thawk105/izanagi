---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t827-slow-tests
seq: 2
title: 受入全走を約 568 秒から 187.98 秒へ縮めた — T-080 receipt 履歴検査の per-commit git 起動 4500 本を batch 2 本へ畳み、重い E2E 11 nodeid を opt-in 化 (コード + docs、branch worktree-dev-wave-t827-slow-tests)
---

## 本文

- **依頼と結果。** ユーザー依頼「受入全走が遅すぎる。時間のかかっているテストを高速化して 5 分で
  終わらせたい」。受入形の全走で **187.98 秒 / 9122 passed / 31 skipped** を実測した
  (計算ノード bnode059、request 905029)。1 走目は bnode032 (905028)。
- **基線と留保。** 同日 [T-810] が実測した受入全走 **560.00 秒 / 576.29 秒** (平均約 568 秒) を基線とする。
  約 3.0 倍。**留保 3 点を明記する。**
  (i) **同一 allocation の paired 比較ではない** — 別 request・別ノード・別時刻。ノード間性能差は
  未測定で、その測定こそが [T-810] の目的でありまだ 1 度も走っていない。ただし 3.0 倍は登録済み
  calibration の差 (1.774%) や下記の観測幅 (2.9%) より 2 桁大きく、ノード差では説明できない。
  (ii) **workload は同一でない** — 「同じ集合を速くした」ではなく「集合の縮小を含む」。
  同じ merge base (`427da17c`) の main を [T-860] が測った **9123 passed / 20 skipped** に対し
  本 wave は 9122 / 31 で、内訳は `9123 − 11 (opt-in へ移動) + 10 (新設 positive control) = 9122`
  と検算が閉じる。余計な増減はゼロ。
  (iii) **(a) batch 化と (b) opt-in 化の寄与は分解していない。** `IZANAGI_T080_E2E=1` を立てれば
  同一 workload を作れるが本 wave では未実施。**未測定を推測で分けない。**
- **[T-810] が渡した観測幅。** 同一 workload・同一結果の 2 走で 560.00 秒と 576.29 秒 (差 16.3 秒、2.9%)。
  **n=2 のため変動の推定量ではなく観測範囲**である。別 request で実行され、**割当てノードは
  dispatch receipt に記録されているが `output/pegasus-dispatch/` は gitignore された worktree 内に
  あり、wave teardown で失われた**ため、ノード間差・キュー負荷と分離できていない。
  本 wave はこの指摘を受け、受入 2 走分の receipt を repo 外 job dir へ退避してからホスト名を確定した。
- **遅さの原因は 1 箇所に収束した。** T-080 移行 receipt の履歴検査が、発行後の descendant を
  **1 commit につき git subprocess 2 本** (`ls-tree` + `diff-tree`) で問い合わせていた。
  descendant は 2026-07-23 の発行から **2255 commit** (日に約 120 増)、1 解決あたり約 4500 プロセス・
  182 秒、受入 1 走で 2 回発生。さらに同じコードが T-080 E2E fixture 構築 (cProfile 実測
  **1 回 213.40 秒**、うち 198.7 秒が subprocess 待ち) の約 9 割を占めていた。
  `real-repo` group 290.18 秒のうち 181.91 秒も同一起因。設計判断は {{D:t080-history-scan-batched}}。
- **親が立てて実測で棄却した仮説 2 件。** (1) 「`_copy_t080_basis_file` の per-file `git show` が
  数千プロセス」→ 誤り。source path は 32 件で起動は 36 回程度。(2) 「E2E fixture 87 秒級の主犯は
  `git clone`」→ 誤り。**並行セッション (module fixture 最適化) の cProfile が
  `_find_rollout` 74.62 秒 / 67%、`json.loads` 3,030,525 回で 51.04 秒、`select.poll` は 33.84 秒**
  と実測し、私の帰属を訂正した。cProfile の subprocess 待ち総量から中身を推測したのが誤りだった。
- **敵対レビュー 2 本が must-fix 4 件を検出し、全件 closed。** 最重要は **両レンズが独立に指摘した
  非 UTF-8 path の過剰拒否** — `diff-tree -z` は pathname の quoting を無効化して raw bytes を出すため、
  path を UTF-8 strict decode すると receipt と無関係な非 UTF-8 filename が 1 つあるだけで
  正当な active receipt を `receipt.git_error` で拒否していた。**受入テストでは踏まない** (repo に
  該当ファイルが無い) ため、静的レビューでしか見つからない型である。
  他 3 件は opt-in env 名の自己参照 pin、呼び出し本数テストが退行を検出できない欠陥、
  opt-in 対象集合の非固定。
- **親の指示自体の穴を 1 件、レビューが突いた。** 呼び出し本数テストについて親は
  「種別ごとの件数を descendant 3 対 7 で比較せよ」と指示したが、**旧 scalar 実装へ戻すと
  呼び出しの分類が `diff-tree` へ変わり `diff-batch` は両側 0 == 0 で通る**。約 4500 subprocess の
  退行をテスト緑のまま戻せる状態だった。全 argv の multiset と総数の exact 比較へ改め、
  scalar `diff-tree` と per-commit `cat-file` の 0 回を明示 assert する形にした。
- **変異 matrix: 6/6 KILLED、MISMATCH 0、SURVIVED 0** (`mutation-final.json`、rc=0、674 秒)。
  **初回 probe では 3 件が生存した (erratum として残す)。** V1 (mode 検査無効化)・V4 (S1 検査無効化) は
  単独では S3 検査 (`_batched_history_touches_path`) に mask されて生存し、V3 は照準ミスだった。
  DW-M02 に従い両層同時変異へ再照準した結果、V1b は 5 node、V4b は 4 node を落とし、
  **専用の positive control が両方に存在することが確認できた** (検出力の穴ではなく層の重複)。
  再照準後の V3b は**等価変異**と裁定 — 落とした `raise` は配列境界の番人で、消すと直後の索引が
  `IndexError` を出す。**どちらも拒否し受理集合は不変**で、差は構造化拒否か未捕捉例外かという
  診断の質だけである (DW-M03 により kill に数えない)。
- **退行防止が機能することを実測。** V7 (per-commit 起動へ戻す変異) が 2 node で KILLED。
  fix 3 巡目で「魔法の定数でなく規模を変えた 2 回計測で pin せよ」と指示したテストが、
  本 wave の高速化を将来の変更から守る。
- **既定 suite から外れた 11 nodeid (検出力の低下範囲)。** すべて
  `orchestrator/tests/test_s8b_oracle_driver.py`。`IZANAGI_T080_E2E=1` で走る。
  段 6 の敵対レビュー B は **11 件すべてに「同じ受理集合を通す完全代替は無い」**と判定した。
  `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` /
  `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5` の 4 parameter
  (`known-artifact` / `ccbench-current` / `holdout-artifact` / `unknownness-layer2`) /
  `test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5` /
  `test_t080_full_valid_history_defects_have_one_baseline_reason_f28` の 3 parameter
  (`modify-revert` / `bad-trailer` / `extra-r-path`) /
  `test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28` /
  `test_never_issued_generator_tamper_reaches_public_driver_gate_g7`。
  解除側は実測済み (1 passed / 261.21 秒 — 走ったこと自体が 213 秒級 fixture 構築の証拠)。
- **opt-in の落とし穴を 2 つ実測した。** (1) **最遅 node だけを外すと節約が消える** — fixture は
  同一 key の初回消費者が構築費を払うため、`known-artifact` (223.11 秒) を外すと
  `holdout-artifact` (0.96 秒) が 223 秒を払う。helper の消費者を全数まとめて外す必要がある。
  (2) **env allowlist へ登録しないと解除できない** — 詳細は {{D:optin-needs-dispatch-env-allowlist}}。
- **main 由来の赤 2 件を構造ごと直した。** `test_t793_report.py` の 2 node が
  `decision_ids ['D292','D305'] != ['D292']` で赤。本 wave の変更とは無関係で
  (`git diff --stat main -- orchestrator/publication/ docs/decisions.md` が空 = 当該テストが読む入力が
  main と byte 同一)、main が D305 を入れた (`427da17c`) ためだった。production は正しく、
  `_scan_d291_supersession` は意図どおり保守的に拾っている。ユーザー裁定「壊れ方を直す」に従い、
  期待値の完全一致を外して `status` exact + `"D292"` membership + 数値昇順・重複なしの構造検査へ改めた。
  **次に D291 を参照する決定が入っても再発しない。**
- **並行セッションとの調整で 4 件の誤りが是正された。** 上記の帰属誤り 2 件に加え、
  (3) [T-810] の基線を「3 走とも同一 576 秒」と受け取った → 実際は 560.00〜576.29 秒で 1 走目は結果も違う
  (T-810 が自ら訂正)、(4) 走間変動 2.9% を「全 wave の下限精度」へ全称化しようとした → n=2 は
  観測範囲でありノード未分離、と指摘され撤回。**逆に本 wave が是正した側も 1 件** — 並行セッションの
  「supersession scan の対象を凍結 bytes へ固定する」推奨は恒真ゲート (fail-open) になると指摘し、
  相手は撤回して自身の worklog と insights を訂正した。台帳に fail-open を推奨する記述が残るのを防いだ。
- **並行セッションから引用した実測 2 件。** (i) `_find_rollout` の全履歴 JSON parse
  (`~/.codex/sessions` は約 106 files/day、約 26 日で倍) — repo 外だが同じ履歴比例の型。
  (ii) **単独計測で 4 倍速くなる並列化が、32 worker の並列受入では guard を 1 秒も速くせず、
  同時走行の critical path を 9.7 秒飢えさせた** (出典:
  `output/insights/2026-08-12_floor-campaign-snapshot-scandir/`)。disk 律速では thread が
  bytes の到着を速くせず待ち行列を伸ばすだけで、**害が隣人側に非対称に出るため単独計測では
  原理的に観測できない**。D104 決定 (4) の同型再発であり、本 wave が batch 化以外の並列化を
  採らなかった判断の裏づけにもなる。
- **CPU 飽和度は本走行では未取得。** PBS 出力に CPU Time が含まれず、wall (Elapse 197S / 208S) のみ。
  基準値は [T-813] base の CPU 2168.12 秒 / Elapse 496 秒 = 平均 4.4 コア (48 中 9%)。
  {{D:no-history-proportional-test-cost}} が併記を義務づけたので、次走以降で埋める。
- **fix は 3 巡 + 親裁定の実行 1 回。** 赤 4 件のうち **production の欠陥は 1 件だけ**で、残る 3 件は
  テスト側の期待値の誤りだった。親が実走しなければ「意味論は落としていない」という子の自己申告のまま
  正当な履歴を過剰拒否する production が land していた。
- **親の prompt 起因の失敗 1 件。** 1 行削除の実行に「3 行以内で報告せよ」と指示した結果、成果物が
  330 bytes になり `check_codex_output.py` の下限 500 bytes で不受理 (`outcome=not_accepted`、
  launcher rc=1、log 0 bytes)。**編集自体は正しく tree に入っていた**ため、
  attempt output と receipt の `validator_rc` を読むまで「子が死んだ」と誤読しかけた。
- **待ち手の pid を `pgrep` で拾い、別 wave の同名 `run_acceptance.sh` を掴んだ。** 受入 lease は
  同時に 3〜4 wave が争うため衝突は常態。producer 自身が `echo $$` で書いた pid file を
  `--pid-file` で渡す契約 (`DW-O01`) を守っていなかった。

## 次の一手差分

### carry

- [T-826]
- [T-813]
- [T-715]
- [T-716]

### 完了

- [T-827] 受入全走の最長テスト群を是正して wall の下界を下げる。約 568 秒 → 187.98 秒 (約 3.0 倍)。
  遅さは T-080 receipt 履歴検査の per-commit git 起動に収束し、batch 2 本へ畳んだ (受理集合不変)。
  重い E2E 11 nodeid は opt-in 化。変異 6/6 KILLED。
  残余は {{T:decompose-batch-vs-optin}} へ移した ((a) batch 化と (b) opt-in 化の寄与分解、
  CPU 飽和度の併記)。
  remaining: none
  base: 1a52af5d1ffcf1a088641fa31218550fd6ba77a284534ce6914d2cc56a126cf5

- [T-869] `test_t793_report.py` の supersession 期待値を D305 追随でなく構造検査へ改めた。
  固定 list を外したため、次に D291 を参照する決定が入っても再発しない。
  [T-810] が起票した限定免除の根拠も同時に消える。
  remaining: none
  base: a17613d11d086a87249cf003d259a430b6a0281335ccf400756972cb4ebd42ad

### 新規

- {{T:decompose-batch-vs-optin}} **P3・新規**: 受入全走の短縮を (a) batch 化と (b) opt-in 化へ分解する。
  `IZANAGI_T080_E2E=1` で同一 workload を作り 1 走。判定閾値は [T-810] の観測幅 16.3 秒 (2.9%) とし、
  差がそれ以内なら「1 走では分解できない」と記録する。事前見込み (E2E fixture 213.40 秒 /
  履歴検査 181.91 秒) は根拠にしない。

- {{T:record-hostname-with-perf}} **P2・新規**: 性能値を主張する走行では dispatch receipt を
  worktree 外へ退避する。ホスト名は `result.hostname` に記録されているが
  `output/pegasus-dispatch/` は gitignore された worktree 内にあり、wave teardown で失われる。
  [T-810] は自分の 2 走分を畳んで消し、同一ノードだったか事後に確かめられなくなった。

- {{T:codex-sessions-history-scan}} **P2・新規**: `tools/codex_reasoning_ab.py` の `_find_rollout` が
  `~/.codex/sessions` の rollout を全件 JSON parse している (1 構築あたり 5 回、306 万行)。
  `~/.codex/sessions` は約 106 files/day で増え約 26 日で倍になるため、
  {{D:no-history-proportional-test-cost}} の repo 外版に該当する。並行セッションが裁定へ回済み。

- {{T:preserve-git-clone-isolation-cost}} **P3・新規**: `git clone --no-hardlinks` で repo 全体を
  複製する箇所が 2 つある (`tools/codex_reasoning_ab.py:1289` の POS/NEG 2 回、
  `test_real_seal_protocol_to_floor_official_core_e2e` の 313MB + submodule)。
  いずれも repo サイズに比例する。隔離の意味論に触るため裁定が要る。同型なので 1 度に裁定できる。
