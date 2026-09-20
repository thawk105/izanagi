# 段 1 brief — [T-2609][T-2656] 全史 provenance 監査の dispatch 判定と per-commit コスト

基準: main `b7f970dfa507558f7fb669a5ab38958d6c76b57c`、wave worktree `.claude/worktrees/dev-wave-t2609-t2656-provenance-cost`。
起点: 台帳 entry 1487 (T-2609)、1518 (T-2656)、D2148 項 8 (外側 timeout は全区間、短い hang タイマーは外す)。

## 研究前進 (土台)
全 wave の land 関門 (DW-O25、D254: 全史 provenance 監査が login で 480 秒以内に rc=0) と受入前 merge 段 (D2129) の監査が、
受領証再利用の効かない走で全史 11,769 commit を login で監査する。混雑した login では 428〜574 秒 (entry 1487) で 480 秒を超え、
研究 wave の land が rc=29 で止まる。per-commit コストを落として login 全史を 480 秒に確実に収め、論文成果の land を止めないのが目的。
完了判定: 改善前後の login 全史走 (同条件・交互) で wall が下がり、判定・findings・rc・公開出力が 1 bit も変わらず、変異で既知違反の検出が不変。

## 段 1 で実測した前提 (一次資料: job dir `probe/`、`profile-compute-1.stdout.txt`、`login-regular-1.json`)
1. dispatch 経路の失敗率: 残存する provenance task 受領証 86 件のうち infra rc=16 は **3 件 (3.5 %)**。3 件とも計算ノード側の監査本体は
   「新規違反なし」で完走しており、失敗は前後処理 (08-25 `_SignalAbort: signal 15` = 呼び出し側からの SIGTERM、09-08 / 09-09
   `orphan-hold-release-failed`)。真の違反検出 rc=1 が 4 件、実行不能 rc=2 が 1 件。「別 wave で rc=16 が 5 回」の残り 2 件は撤去済み worktree の記録。
2. キュー待ち: `queue_wait_s` 中央値 5.2 秒、p90 6.8 秒、**最大 537.6 秒** (09-19 23:04)。100 秒超は 3 件 (537.6 / 278.7 / 138.4)。
3. 計算ノード全史 (bnode003、48 CPU、32 worker、11,769 commit、受領証なし): **wall 41.7 秒、CPU 288 秒** (子 user 97.8 + sys 153.3、自身 37)。
   subprocess 累積 1,128 秒の内訳: `show -s --format=%P` 11,308 回 332.5 秒 (29 %)、merge の `diff --name-only` 8,502 回 235.7 秒 (21 %)、
   `interpret-trailers --parse` (repo cwd、`_ai_agent_values`) 13,993 回 225.8 秒 (20 %)、non-merge の `diff-tree --name-only` 7,061 回 210.6 秒 (19 %)、
   隔離 `interpret-trailers` 11,315 回 62.4 秒 (6 %、1 回 5.5 ms)、`diff-tree --cc` 1,418 回 59.6 秒 (5 %)。祖先索引・pickaxe は合計 1.4 秒。
   関数別: **`_commit_paths` 838.9 秒 (66 %)**、`validate_message` 386.4 秒、`_isolated_parsed_trailers` 136.2 秒 (subprocess 62.4 との差 74 秒が tempdir 等)。
   → 起点 T-2656 の順位 (trailer → 隔離 fs → path → 祖先) と実測の順位 (**path 取得 → trailer → 隔離 fs → 祖先**) は逆。
4. login 正規走 (headroom → bounded scope、同 tip の受領証あり): **wall 14.9 秒、CPU 7.5 秒、ピーク 94.6 MB**。
5. 受領証は環境 digest で 7 partition に分かれ (checker sha は同一 `5cb709cbca5d`、差は `LANG`/`LC_*`/`GIT_EDITOR`/`GIT_PAGER` と config 行数)、
   さらに **attributes fingerprint が index の全 path の祖先 directory 集合に依存する**ため、新 directory (毎 wave の insight dir) を足す tip を跨ぐと
   全 partition で失効する (計算ノード probe: 同 partition の受領証と `attributes` だけ不一致、tracked `.gitattributes` は root の 1 件で 08-23 以来不変)。
   → land の全史監査はほぼ毎回全史へ落ちる構造。D2045 の再訪候補 (本 wave の scope 外、次の一手へ)。
6. `login_headroom.grant_budget` の入力はメモリ bytes (観測余裕・生存予約・前回ピーク) だけで CPU / load を見ない (T-2609 の主張どおり)。
7. login 全史 baseline (受領証無効化、正規経路、07:30 JST、load 10.9 → 18.9): **wall 88.1 秒、CPU 368 秒 (user 131.4 + sys 236.7)、ピーク 725 MB**。
   起点の 428〜574 秒は混雑時の値で、CPU 総量 368 秒 (計算ノードの 288 秒より sys が +83 秒) を 32 スレッドで奪い合うと wall が CPU 総量に近づく。
   headroom は前回ピーク 94.6 MB から 118 MB と見積もり、下限の 1 GB を予約した (実ピーク 725 MB は予算内)。

## scope
- (1) T-2656: per-commit subprocess の削減を実測順に。候補 (a) `_commit_parents` の `show %P` 11,308 回 → 一括取得 (`_batch_commit_messages` の format に `%P` を足す、
  または `_build_ancestry` の `rev-list --parents` 行から引く)。(b) non-merge の `diff-tree --name-only` 7,061 回 → 一括 (`git log --no-walk=unsorted --stdin -z --name-only`
  は merge で意味が変わるので non-merge だけ、merge は現行のまま)。(c) `_ai_agent_values` の同一 message への 2 回呼び出し (validate_message と
  validate_implementation_author、2,224 回) を 1 回に。(d) 隔離 parse の `TemporaryDirectory` 11,315 回 → 監査 1 走で private dir 1 つ (cwd は空 dir のまま)。
  merge の `diff --name-only` × 親 + `--cc` は判定に直結 (D721) するので候補列挙の一括化に留め、`--cc` 判定は不変。
- (2) T-2609: CPU 時間を dispatch 判定に足すか — 実測 (1)〜(5) に基づき段 4 で決める。
- 変更面の実アンカー: `tools/check_ai_provenance.py` の `_batch_commit_messages` (1209)、`_isolated_parsed_trailers` (1262)、`_ai_agent_values` (1323)、
  `validate_message` (1470)、`validate_implementation_author` (1599)、`_commit_parents` (1636)、`_commit_paths` (1696)、`_normal_commit_audit` (1938)、
  `_audit_history` (2423)、dispatch 判定 `main` (3391〜3520)。テスト: `orchestrator/tests/test_check_ai_provenance.py` (8,261 行、246 test、
  `_commit_paths(commit)` / `_commit_parents(commit)` / `_batch_commit_messages(selected)` の 1 引数形を pin)。consumer: `tools/dev_wave_land.py`、
  `tools/dev_wave_wait.py`、`tools/mutation_harness.py`、`tools/task_run_check.py`、`tools/codex_reasoning_ab.py`。

## 親の provisional 裁定 (攻撃対象)
- (P1) `_ai_agent_values` の `%(trailers)` 置換は見送る — ambient config (`trailer.separators` 等) を含む等価性証明を本 wave に持ち込まない (D2033 と同じ理由)。
- (P2) CPU 時間を dispatch 判定に足さない — dispatch は受領証再利用を失い (計算ノードは clean env で別 partition)、queue 待ちの尾が 538 秒、基盤失敗 3.5 %。
  login の全史を T-2656 で短縮する方が land 関門 (480 秒) に確実に効く。段 4 で login 全史 baseline と改善後の実測を比べて確定する。
- (P3) 一括取得は D2033 と同じ fail-closed: 出力の形・件数・OID 一致のどれかが崩れたら部分結果を捨てて既存 per-commit 経路へ戻す。
- (P4) merge commit の path 判定 (`_paths_changed_from` × 親 → `_combined_diff_paths`) は判定内容に直結するため、subprocess 数を減らしても判定式を変えない。

## 不変条件
検査対象 commit 集合・判定・findings・rc・公開出力は 1 bit も変えない (D2033)。`authoritative = args.rev_range is None` と `--force-dispatch` は不変。
既知違反 (registry 56 件、post-baseline 3 件) の検出は変異で確認する。fallback は fail-open にしない。新 gate・台帳・一般化を足さない。
規律 2 を緩めない。dispatch 系 command に呼び出し側 timeout を付けない。

## 成果物と分割
実装 commit (Codex author、`tools/check_ai_provenance.py` + テスト)、変異 matrix (既知違反の検出・fallback の発火・一括結果の検査)、
insight README (実測表 + 改善前後の login 全史対比)、worklog / decisions fragment (T-2609 の裁定)。
段 2 plan 1 本 (codex、file:line)、段 3 相談 1 本 (2 レンズ: 等価性攻撃 / fail-closed 攻撃)、段 5 author 1 本、段 6 review 2 本 + fix。
実測環境: 対比は login (正規経路、受領証無効化、交互 2 ラウンド以上)、内訳は計算ノード probe。
DW-O08/O09/O10: checker は freeze / oracle gate / proof chain の閉包に含まれない (check_docs / freeze への grep で hit 0)。DW-O13: gate 新設なし。
DW-G05: 放置時は land 関門で rc=29 が出て成果物の land が止まる。値・受理集合は変わらない。

## 段 4 訂正 (相談 A-N6 / B-S2 / B-N4 を受けて、数値の意味と一般化の強さを直す)
- 「`_commit_paths` 66 %」は worker の `_normal_commit_audit` 累積時間 (1,272.8 秒) に対する比率 (838.9 秒) であり、wall の 66 % ではない。
- 「隔離 parse の tempdir 等 74 秒」は関数累積と subprocess 累積の差で、tempdir 単独の費用でも wall 短縮の上限でもない。
- 「計算ノードは clean env」は誤り。provenance task は `env_mode="inherit"` (allowlist 空) で **PBS job の環境を継承する**ため、login シェルの `LANG`/`GIT_EDITOR` が届かず受領証の partition が変わる。cold な land (改版直後・新 directory 導入後) では dispatch に受領証の追加損失は無い。
- 「428〜574 秒 → CPU 総量 368 秒の奪い合い」は説明候補であり、I/O 待ちとの分離は未測定。「480 秒に確実に収まる」は書かず、改善前後の同時刻帯対比を完了判定にする。
- 基盤失敗 3/86 (3.5 %) は残存受領証の標本値で、Wilson 95 % 区間は 1.2〜9.8 %。撤去済み worktree の欠測を補正しない。queue 待ち分布は共有 queue の他 task に依存し provenance 固有ではない。
- attributes fingerprint の失効条件は「新しい祖先 directory を持つ tracked path が index に加わる」こと。頻度: 直近 60 main first-parent commit のうち 30 (50 %) が該当 (毎 wave の insight dir)。
- `D2148-item8.md` の初版は別 D の項 8 を切った誤りで、段 3 前に D2148 の範囲で切り直した。
