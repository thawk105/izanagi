---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-t2867-silo-contrast-impl
seq: 1
title: [T-2867] silo-function-policy 軸の生成器対照を実装し、計算ノードで LLM×C++・LLM×IR・機械生成 IR の各 1 評価を通して見積りを取り直した (コード + docs + insight、branch dev-wave-t2867-silo-contrast-impl)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`): 草稿 (`docs/silo-policy-generator-contrast-preregistration.md`、D2263) の起草 insight §5 の部品を Codex author で実装し、段階 F の生死確認の job Elapse で草稿 §11.3 を取り直し、発効束を埋めた見積りを返して止める。記録は `output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md`、設計判断は {{D:silo-policy-contrast-impl}}。
- 計算の確認: 段 1 で見込み約 3〜3.5 node 時間、段 4 で見込み約 2.8・上限約 5.4 node 時間を示した。ユーザーの「続けて」(2026-09-29 18 時台 JST) を投入の了承と解釈して生死確認を投入した。実績は生死確認 5,114 s ≈ 1.42 node 時間 + 開発の検査 約 0.6 node 時間 (受入を除く)。
- 9 段の全段。段 3 相談 A は NO-GO (must-fix 6)・B は縮小 8 件、段 6 レビュー R1 は NO-GO・R2、焦点再レビューは 3 巡とも NO-GO で所見は巡ごとに細くなり、DW-O16 の上限の後は親がテストと変異で閉じた。fix は 9 回 (うち 2 回は生死確認で見つけた結合欠陥)。
- 生死確認で結合欠陥が 2 件見つかった。(a) 1 job の全 slot で 1 つの authorization session を共有し、2 つ目の slot で `binding mismatch` (series 1 の 3 本が stock の後に停止、request 35824・35825・35835)。(b) round tool が coder role の `{"proposal": ...}` を剥がさず preview が schema 不合格 (series 2 の LLM 2 系列の原提案 1、A を誤って 1 消費)。どちらも単体テストが実物を差し替えて通っていた (新しい F は採らず、既存 F649・F1054 の再発として記録)。
- 生死確認の成立: random×IR (series 2) の評価 1 は certified・品質正常・job Elapse 265 s、LLM×IR (series 3) は原提案 1 が critic → coder → preview → auditor (pass) → finalize で 6 分 2 秒、評価 1 は certified・256 s、LLM×C++ (series 3) は 7 分 27 秒、評価 1 は certified・289 s。job 1 (stock + 初期点 2) は 5 本とも成立し 718〜759 s。値は各 1 観測で、生成器の比較の証拠ではない。
- 変異: `72810ed01` で 14/14 KILLED (束ね経路 1 job 364 s)、最終実装 commit `4fbe4b26a` で m16 (fix 9 を壊す) を足して 15/15 KILLED (373 s)。fix 8 は新旧両走 (修正前のコードに同じテストを入れると同じ `binding mismatch` で赤、修正後は緑)。
- 焦点走の非帰属赤: login local 実行で T-2871 の結合テスト 3 件が `IZANAGI_EXPLORATION_OUTPUT_ROOT は repository 外` (login の `/tmp/.git` による既知の偽赤、計算ノードでは緑)。wiring probe の赤は未 commit の新 file を数えたもの (commit 後 65 passed)。
- 受入 1 回目 (tested main `8fe87f852`、post-claim merge 後の tip `328389a8f`): 28,180 passed / 11 failed。`test_t810_coordinator.py` の 3 件 (`cannot read worktree registration: file is absent`) は他 session の worktree 撤去の途中状態による非帰属 (land 調整役が撤去由来と明言)。本 wave に帰属する 8 件は閉じた一覧への登録漏れと新テストの自走で、fix 10 で直した: 台帳照合の HEAD 取得を新しい subprocess から既存 helper (`pipeline._current_repo_head`) へ、静的 10 µs の `BACKOFF_FIXED` build sink を審査済み一覧へ (build 前に既存の条件 gate を通ることを確認)、hook の registry golden に launcher と親の 2 行、新テスト 6 本に自走入口。直した後の焦点走 (計算ノード) は 1,372 passed / 6 skipped / 失敗 0。
- セッションの出来事: 手動 worktree 作成が他 session の同時作成と競合して約 27 分、submodule 初期化 tool は `runtime-io-failure update-no-fetch` を 2 回返し、同じ git 命令 (`submodule update --init --recursive --no-fetch`) を直接実行して初期化した (9 秒、3 段とも正しい SHA で中身ありを実物で確認)。DW-O08 の「同じ引数で 1 度再実行し、なお赤なら止める」からの逸脱で、tool が落ちた原因 (内部の時間上限か) は切り分けていない。land 調整役の依頼で git 書込みを一時停止 (ユーザーの push、約 20 分)。hook は main の admission registry を読むため、wave で登録した launcher を直接呼ぶと「未登録」で拒否され、job dir の script 越しに呼んだ (hook の説明どおり許可される監査可能な作業物)。40 桁 SHA を手で書き 2 回誤った (rev-parse の出力を貼って回避)。

## 次の一手差分

### 更新

- [T-2867] **P2・実装着地、生死確認 3 本成立 → 発効と系列数 (n = 12 か 10) はユーザーが決める**: silo-function-policy 軸の生成器対照の実装 (driver の系列 identity と slot ごとの計測 campaign、機械生成 IR と初期点の口、stock・静的 10 µs・score の slot、job body の contrast mode、系列台帳、G_rand と (1+1)、起動器、round tool と 1 原提案ごとの `claude -p` 親、report) を着地させ、計算ノードで LLM×C++・LLM×IR の 1 iteration と機械生成 IR の 1 評価を通した (記録 `output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md`、{{D:silo-policy-contrast-impl}})。
  草稿 §11.0 に実測で取り直した見積り (4 arm × n = 12 は約 61〜70 node 時間、n = 10 は約 51〜59、いずれも job Elapse の単価からの換算。LLM は 1 原提案 5.7〜8.0 分、直列 23〜96 時間、週上限までの機会数は未測定)、§12.1 に発効束の実値の案を足した。未発効。
  次は、発効束と規模の択一をユーザーへ示す (/rulings)。D2277 項 3 の再提示条件 (T-2867 の見積りが揃う) もこれで満たしたので、[T-2850] と並べて順番と規模を示す。score job・参照 job (静的 10 µs を含む) と進化×IR は計算ノードで未実走で、本走の最初の単位で確かめる。
  base: 0b8e0291eb5aa91df1871f25340ac79848a111e62d9d48369714b578990840f1
