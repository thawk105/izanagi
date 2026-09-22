---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2857-silo-policy-stage-c
seq: 1
title: [T-2857] silo-function-policy 軸の段階 C を実装・実測し C 段出口 6〜9 と生死確認を満たした — 骨格 patch・api header・型付き構文検査 (契約 fixture 85 本)・単独 TU compile・UBSan harness 1 回・probe と焦点方策・既存 3 負例の軸 ON 積み直し・機構変異 9 件を Codex author が書き、計算ノードの coverage 33 case・61 check と smoke 5 case・30 check がすべて真。あわせて [T-2856] 手順書 §4 の第 3 列と段階 E の planner 例外を commit (コード + test + patch + docs + 計測 JSON + insight、branch worktree-dev-wave-t2857-silo-policy-stage-c)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-22/t2857-silo-policy-stage-c/verbatim/request.md`): [T-2856] の docs を commit し、D2214 の必須条件どおり段階 C を Codex author で実装・実測する。記録 = 同 insight の README、設計判断 = {{D:silo-policy-stage-c}}。
- 起点 = local main `8fd2a2f5c` (fresh worktree、開始 gate rc=0 は 08:53 JST)。wave 中に local main を 3 回取り込んだ (`eef04f5a7`、verifier v3 の変更を含む `bc3b23953`、`56ce0f244`)。正しさ防壁 (新しい受理検査・lock ループの骨格) に触れ受理集合も変わるので、DW-C00 により段 2・3・6 の独立検証子を省かなかった。
- **計算投入のユーザー確認:** 段 4 で用途別に積み上げ直した見積り (約 0.9〜2.4 node 時間、設計時の換算 2.41〜4.12 は受入を外側 wall で数えていた) を示し、「全体を承認 (合計 2.4 node 時間を上限、超えそうなら止めて再確認)」を得た。質問から回答まで約 10 時間 (09:5x → 19:4x JST)。
- **T-2856 (docs):** 手順書 §4 の見出しを 3 型に、表に第 3 列と新 3 行、段階 E の planner 例外 (commit `4c0eb08b9`)。段 3 相談 B の所見 8 で §4 の trigger 注記と §7.3 の射程を局所修正 (`8f87239bd`)。第 3 列は段階 B の設計の採用に基づき、段階 C 以降の実施ではまだ裏付けられていないと明記した。
- **段 4 の主な裁定:** 受理契約は仮引数名の省略を許す明確化だけを足す、焦点試験は実 `TxExecutor` 用の専用 fixture を作らず YCSB + probe で到達を実測、生死確認は `pipeline.evaluate` + 認可 + campaign layout を使わず既存 coverage driver と同じ診断 build 経路。plan の専用 fixture 案と evaluate 案は過剰として不採用。
- **段 6 は fix を 6 巡 (+ 1 本) 回した。** レビュー 2 本の must-fix (交差検査の不整合、prefix unlock 変異の方策の書き違い = 親の C1 投げ文の誤り)、焦点走の赤、計算ノードの実走で 1 走に 1 件ずつ見つかった実行時の欠陥 (gate への companion 強制 → 依存物未 build での gate の前処理失敗 → owner 行の非一意 → 上限出口の変異の方策が到達しない)、焦点再レビュー 1 巡目の must-fix (prefix unlock を出口ごとに分ける) の順。fix 2 巡目の根拠にした「site 数の不一致」は read-only 調査子の静的な推定で、実機の理由 code は fix 2 の後に初めて取れた (裁定 3 巡目で訂正)。4 巡目で実装子に全 case の外部交点の照合表を作らせてから、残る実行時の欠陥が出なくなった。焦点再レビューは 2 巡 (NO-GO → GO)。
- **段 4 裁定の誤りの訂正:** 「hook の実呼出しを 1 か所消すとその照合だけが赤」は誤り (符号の連動で赤は複数照合)。判定を赤・緑の集合の完全一致に直した。事前登録した変異 M-CHK-EMPTY は後段に隠れる過剰決定のため登録から外した。上限出口の変異の方策は事前登録の `maxwait` から `retry` へ替えた (到達しない構成での空振り、到達の証拠を判定に要求)。
- 計算ノードの使用: 焦点走 10 回 計 820 秒・coverage 6 回 計 2,958 秒 (うち最終 = request 18328.nqsv の 1,016 秒)・smoke 1 回 793 秒 (以上 job Elapse)、変異 probe 3 回と final 2 回の runner 時間 計 2,207 秒 (待ち行列込みの上限値)。合計 6,778 秒 ≈ 1.88 node 時間 (上限値) で、承認上限 2.4 node 時間の内側。受入全走は本記録の commit の後に行い、結果は land の受領証に残る。
- 変異 matrix (段 4・段 6 で事前登録した 15 件、独立 clone の固定 commit `0a4b38abe`、dispatch): final は 15 / 15 KILLED・期待 node と完全一致、基準走は PASSED。事前登録からの変更は M-CHK-EMPTY の削除 (過剰決定) と M-GATE-DOM の照準し直し (条件式の形は既存の交差検査が分岐を見ずに数えるため生存) (insight §3.5)。
- 工数: Codex 子 = plan 1、consult 2、author 4、review 2、fix 7 (fix-1〜6 と 6b)、focus 2 の計 18 本。Claude の調査子 2 本 (sonnet、pin 閉包の調査と gate 拒否の原因の静的調査)。login: UBSan harness 1 回。

## 次の一手差分

### 完了

- [T-2856] 手順書 §4 の第 3 列と段階 E の planner 例外を commit した (`4c0eb08b9`・`8f87239bd`)。
  remaining: none
  base: 9202ac8b5c34b56a98104e6c72a69f6e6de264f7bd3c1dc823ffa59187fd75ba
- [T-2857] 段階 C を実装・実測し、C 段出口 6〜9 と手書き方策の生死確認を満たした (記録 = `output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md`)。
  remaining: none
  base: 051914df04bcd16e4a51c71461c96483013b5c65847b988cfd2098af4232d4fe

### 新規

- {{T:silo-policy-stage-d}} **P1・新規 (計算は投入前にユーザー確認)**: silo-function-policy 軸の段階 D (IR の機械偵察) を行う。
  - 設計 `output/insights/2026-09-21/silo-function-synthesis-space/README.md` §5 の型付き有限 IR (停止性・算術安全を構成で保証) の生成器・列挙・偵察 driver を Codex author で書き、段階 C の骨格・検査器・診断経路 (`orchestrator/campaign/silo_policy_coverage.py`) を再利用する。
  - 投入前にタスク合計の node 時間を示してユーザー確認を取る (設計時の換算は 1.15〜2.69 node 時間。段階 C の実測単価で出し直す)。
  - 偵察の結果は二値 (床を超える地形の有無) だけを後段へ渡す (手順書 §3-D の firewall)。継続 / 見直しは人間判断。
