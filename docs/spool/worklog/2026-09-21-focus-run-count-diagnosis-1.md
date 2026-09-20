---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: focus-run-count-diagnosis
seq: 1
title: 焦点走 (計算ノード dispatch) の本数と wall を直近 landed 12 wave の job log から集計し契約の充足条件と照合した — 27 本 / 10,602 秒のうちノード開始前の待ちが 74 % (二峰: < 30 秒 14 本、337〜1,020 秒 12 本)、契約は job 数でなく充足条件を定め、D325 の単独走 (別 process) を計算ノード焦点走の log で確認できた変更 test file は延べ 22 中 2、契約を変えずに減らせる分は候補ごとの固定費 (21〜735 秒 / 本) で裁定パッケージへ (診断のみ・実装 0 行、branch worktree-focus-run-count-diagnosis)
---

## 本文

- ユーザー依頼 (2026-09-21、`/dev-wave` 引数の逐語は insight `verbatim/origin.md`) の範囲で 1 wave。起点 local main `5efd69367` (worktree 作成 07:33 JST、開始 gate rc 0)。一次資料は
  `output/insights/2026-09-21/focus-run-count-diagnosis/README.md` (母集合・4 区間の出所・本数と wall・契約の充足条件・目的別内訳・充足状況・候補ごとの固定費・裁定パッケージ・判定不能・レビュー対応表)。
  専用 handoff は repo 外 (`/work/1/SFC/tanab/dev-wave-jobs/handoff/`)、生 log・解析 script は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-focus-run-count-diagnosis/` (script は `verbatim/scripts.sha256` で束縛)。
- 段構成 (DW-C00): 軽量版 + 診断 wave の最小 — 段 3 相談 1 本 (codex read-only、lane luna、medium)、段 5 なし (実装面 0 行、D95 の docs-only 例外)、段 6 独立 read-only レビュー 1 本 + 焦点再レビュー 1 本 (DW-O16)、変異免除 (DW-S04)、受入全走は免除せず。
- 実測 (12 wave = land 記録の mtime 順、2026-09-20 23:13 t2243 〜 09-21 05:26 t2797): 計算ノード焦点走 27 本 (t2804 2、t2803 7、t2344 4、walldecomp 2、t2814 2、t2810 3、residue 4、t2797 3、他 4 wave は 0)。
  wall 合計 10,602 秒 = ノード開始前の待ち (NQSV footer の Created→Started、QUE・PRR 等) 7,861 秒 74.1 % + RUN 2,306 秒 21.8 % (pytest とほぼ同じ、job 内 overhead 1.4 秒) + collection 345 秒 3.3 % + 投入前 90 秒 0.8 %。
  待ちは二峰 (< 30 秒 14 本 平均 8.9 秒、≥ 300 秒 12 本 337〜1,020 秒 平均 632 秒)。1 wave あたり 2.25 本 / 14.7 分 (焦点走のある 8 wave では 3.38 本 / 22.1 分)。
- 段 3 相談 A の 18 所見 (must-fix 8) を全件採用し、親の brief を訂正した: 母集合 (t2807 → t2243)、「契約最小 17〜19 本 / 契約内 19 / 契約外 8」の撤回 (契約は tip ごと・unit ごとの job 数を定めない)、
  単独走の読み (親案「多 file 走への包含で可」は D325 の「別 process」「全走の緑はその file 単独の緑を含意しない」で撤回)、t2810 の集合不足は T-2813 land (22:49) 前の実行、
  residue f1 の赤は 92 failed / 65 errors、held 走の「同 job 化不可」は process と job の混同、効果算術は job 廃止 / 同 job 化 / 重複削除を分ける、混雑帯の待ちは全体平均 291 秒でなく帯別 632 秒。
- 新事実 (親の実測): 各 wave が main へ入れた test file (wave × file の延べ 22) のうち、計算ノード焦点走の log で D325 の字面 (別 process の単独走) を確認できたのは t2803 の 1 と t2344 の 1 (単独走 4 本 = 緑 3 + 走行中 commit の非帰属赤 1)。
  依頼文の「単独走と inventory 群の同 job 化」は、同一 pytest process への統合なら D325 を変える。契約を変えない形は 1 job 内の複数 pytest invocation で、現行 `run_tests.py --force-dispatch` は 1 argv = 1 invocation (runner 側の対応が要る)。
- 裁定パッケージ (insight §7、実装しない): R1 単独走の読み ((i) D325 の字面を運用に戻す = 条件付きで最大 +20 job / (ii) 多 file 走への包含で足りると改訂 = 契約変更)、R2 1 job 内の複数 invocation (runner 改修、受理集合不変、R1 (ii) でも held の env 分離 735 秒 / 例は残る)、
  R3 手順起因赤は既存手順の徹底 (確認補助、拒否条件の新設は gate で scope 外)、R4 merge 後の焦点走は既存証拠で充足済みなら投げない、R5 別 worktree からの並行投入は D289 の既定の具体配置として段別時刻を持つ wave で測る。
- 段 6 レビュー A (codex read-only): NO-GO、must-fix 6 (削減比較値の合算、t2344 f4 の同居先、+20 job の導出、単独走の量化、最終 tip の充足表示と R4、R1 (ii) で R2 不要とした誤り) / should 6 / nit 1 → 全件 README を訂正。
  焦点再レビュー (codex focus): GO、must-fix 0、前段所見は closed 11 / partial 2 / regressed 0 → 残り should 2 / nit 1 も訂正。派生値 (27 本・10,602 秒・74.1 %・表 A・固定費) は両レビューの再計算と一致。
- 検査: 三軸語走査 (`s8b_holdout_freeze search`) の hit 4 件は既存の official 成果物 (本 wave の file に hit なし)、末尾空白は verbatim の codex 出力 3 本の可逆正規化 (NORMALIZATION.md、原文 sha256 は job dir の原文と一致) 後に緑、NFC 違反 0、`check_docs.py` 違反なし・`spool_fold.py --dry-run` rc 0 (本 fragment を置いた後、記録 commit 直前)。
- 工数: codex 3 本 (consult 1、review 1、focus 1)、計算ノード job 0 (焦点走・変異なし、受入のみ)、login 走 = 抽出・集計 script (read-only)。

## 次の一手差分

### 新規

- {{T:focus-solo-run-reading}} **P2・ユーザー裁定待ち**: DW-O26「変更 test file は受入前に単独走で確認する」(正本 D325 = 別 process、追加 dispatch 原則 0 本) の運用。直近 12 wave で計算ノード焦点走の log から字面どおりの単独走を確認できた変更 test file は延べ 22 中 2 (単独走 4 本 = 緑 3 + 非帰属赤 1)。(i) 字面を運用に戻す (既存走の形を変えずに別 job で満たすと最大 +20 job。1 job 内の複数 pytest invocation を runner に足す実装案件と対) か (ii) 多 file 焦点走への包含で足りると DW-O26 / D325 を改訂する (契約変更、DW-O26 は check_docs の exact pin) か。一次資料は `output/insights/2026-09-21/focus-run-count-diagnosis/README.md` §4・§5.2・§7。
