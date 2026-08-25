---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1434-manifest-cli-cost
seq: 3
title: [T-1434] task manifest の CLI 入力口と費用の部分正規化計算を接続した (コード + テスト、branch worktree-dev-wave-t1434-manifest-cli-cost、変異 matrix = baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **親が scope を 1 件広げた。** `--task-manifest` を足すだけの実装は現状より正しさを弱める。
  実装前は task manifest が module 定数で工程途中に差し替える経路が無いが、option を足すと
  packet 作成から検証までを別々の manifest で実行でき、しかも凍結成果物のどれにも digest が
  無いため検出されない。交換できる対象に verdict の受理集合と positive/negative の分類が
  含まれるため、絶対規律 2 が scope 定義に優先すると判断した
  ({{D:task-manifest-cli-requires-digest-chain}})。
- **段 1 brief の「実測した前提」3 項目が誤りだった。** 段 3 の両レンズが独立に指摘し、
  親が現物で裏取りした。(1) `supervise_pair` は `task_manifest` 引数を持たない。
  (2) resource 行を作るのは `_replay_manifest` ではなく `_aggregate_verified`。
  (3) キャッシュ書込は**単価が不明なのではなく、正規 receipt が数量を保存していない** —
  単価は snapshot に実値がある。3 番目は「価格不明」の意味を取り違えており、
  完全な費用に何が要るかの見立てを変えた。
- **親の provisional 裁定 P1 を撤回した。** 事前登録文書の到達度更新を in-scope としていたが、
  ユーザーが「勝手に in-place 改訂しないこと」と明示していた。§13 と D674 の原文を読む限り
  run 開始後の凍結には当たらないが、判断が割れる場面で指示を狭く読む根拠が無いため撤回した。
  到達度の食い違いは裁定パッケージへ文面案つきで回す。
- **段 6 の両レビューが独立に NO-GO を出した。** レビュー A が「実装を壊してもテストが緑のまま
  通る変異」を 21 件挙げたことが決定的で、588 件緑を正しさの証拠として採らなかった。
  must-fix 8 件を採用した。うち 2 件は親裁定の適用漏れ (`verify-snapshot` へ fallback を
  適用していない、`append-verdicts` が即時拒否要求を満たしていない) で、親の落ち度である。
- **費用が certified な判定を落とす件で両レンズの評価が割れた。** レンズ A は
  「`valid` が false になるから過大平均は通らない」、レンズ B は「費用が `valid` を殺すのは
  裁定違反」。両立する形は 1 つしかないため、費用は判定を動かさず分母の内訳を機械可読にする、
  という対で実装させた ({{D:cost-is-descriptive-not-a-gate}})。
- **変異 matrix だけが検査の穴を掘り当てた** ({{F:mutation-registration-counted-one-link-for-a-whole-chain}})。
  digest 連鎖を consumer ごとに 8 分割して登録したところ、`append-verdicts` と
  `reveal-mapping` の packet state 検査を外す変異が 588 件緑のまま生存した。
  分割しなければ 1/1 KILLED で通っていた。production は正しく、検出力だけが不足していた。
- **fix 子が親の未追跡成果物を消した** ({{F:codex-child-deletes-parent-untracked-output}})。
  job dir の控えから復元した。以後は書き込み権の子を起動する前に commit する
  ({{D:commit-parent-artifacts-before-workspace-write}})。
- 変異の本走が計算ノードへの投入失敗 (rc=16) で 2 件目で停止した。テストが 1 件も走らず
  失敗 node を抽出できないため harness が fail-closed で止まったもので、変異の結果ではない。
  `qstat -Q` の応答を確認して `--resume` で再開した。`--resume` は `--attempt-out` に
  既存 file を要求する。
- 子の工数: codex 9 本 (plan 1・consult 2・author 2・review 2・fix 2)。
  最初の plan は `--reasoning` 未指定で rc=2、起動せず。
  子は 4 本とも計算ノードの投入 preflight 失敗で pytest を 1 件も実走できず、
  全て「実装済み・未実走」と正直に申告した。テストは親が 4 回実走した
  (3 failed→緑、527→559→588→590 passed)。
- 別セッションから、受入全走で `test_s8b_floor_campaign.py` の 11 件 + 順序依存 1 件が
  高負荷下で赤くなる周知を受けた。先方は後に「main 単独の全走も同じ高負荷下で回しており
  負荷を交絡因子として除いていなかった」と自分の結論を撤回した。
  切り分けとして「11 固定 + 1 可変」の指紋と `git reflog show main --date=iso` を教わった。

## 次の一手差分

### 更新

- [T-1434] **P1・[T-189] 事前登録文書の実装・実走**: (a) task manifest の CLI 入力口と
  (c) 費用の部分正規化計算を接続した。(b) adjudication 層の task-specific oracle 対応は
  §8 の独立 oracle ledger 待ちのため着手条件を満たさず、scope 外とした。
  残る未解決点と、本 wave が新たに開けた項目は次のとおり。
  費用を §11.2 の resource 指標・§12 の gate 表・overall へ接続すること (部分被覆の扱いは
  事前登録の意味規則でありユーザー裁定が要る)。正規 receipt へキャッシュ書込の数量を保存し
  完全な費用を出すこと (receipt schema と price snapshot の新しい登録世代が要る)。
  `_certification_scope` を改訂して費用を certified field にすること。
  事前登録文書 §5.2 / §5.3 / §10 の到達度記述の差し替え (本 wave は同文書を編集していない。
  文面案は output/insights/2026-08-25_t1434-manifest-cli-cost/ のレビュー B 逐語にある)。
  `SCHEMA_VERSION` を 2 のまま受理形を変えた点の世代区別と移行契約。
  served model attest の不在。
  base: 5401f10ea96d1f8e7d965590a4d30369441d4da0b1216c0fb8ec970a1cb71977
