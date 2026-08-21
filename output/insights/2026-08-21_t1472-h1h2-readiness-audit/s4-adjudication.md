# 段4 裁定 — T-1472 H1/H2 readiness audit

## 裁定方針

段2 (codex plan) と段3 (敵対2レンズ sol/luna) の所見は全て一次資料の file:line 照合に基づく
正当な訂正であり、**全件 real、全件 scope 内で採用**する。refuted はない。scope 外へ返す所見もない
(いずれも「このwaveのblocker table記述の精度」に関する指摘であり、新しい設計判断や実装を要求しない)。

実装面はゼロ (docs-only)。`DW-M01` (変異事前登録) は該当しない — 変異するコードが無い。
**「実装しない」裁定とし、段5・6を飛ばし `4→7→8→9` で進む。**

## 所見一覧と反映方針

| # | 所見 (出典) | 裁定 | README.md への反映 |
|---|---|---|---|
| 1 | g10 は発効済みと確定できない (lensA-1) | real | epoch を「record存在」と「active/effective」に分離して記述。v4断定を撤回 |
| 2 | v2 candidate producer は実在する、誤断定だった (lensA-2) | real | 「producer不在」→「producerは実在、ratified active freeze の発効が未成立」に訂正 |
| 3 | D555後のjudge状態は分解して書くべき (lensA-3) | real | 「judge_combined 撤去済み・production consumer ゼロ」と分解 |
| 4 | oracle gate floor-null/budget-null は8/10-11の記録 (lensA-4) | real | 日付を明記し、現行状態は未確認と書く |
| 5 | certifying formal と non-certifying registered の混同 (lensA-5) | real | 「certified formal launch は不可。non-certifying 実行は証拠に数えない」と限定 |
| 6 | Codex roster/worktree/lease/handoff 所有者確認が欠落 (lensA-7) | real | fork A (occupancy) 結果を統合した専用節を新設 |
| 7 | artifact存在/不在の pilot-vs-formal 混同 (lensA-8) | real | pilot path と formal path を分けて列挙 |
| 8 | 停止条件の詳細不足 (lensA-9) | real | terminal status 表を追加 |
| 9 | confirmed_by/at は人間性の機械証明でない (lensA-10) | real | D356 と同型の限界として明記 |
| 10 | exact command 専用行の欠落 (lensA-11) | real | 専用行を追加 |
| 11 | §6の12条件を C01〜C12 個別4段階で評価すべき (lensB-1) | real | lensA の詳細表をそのまま blocker table の該当節へ組み込む |
| 12 | P2根拠4つは重複計上、決定的根拠は1つ (lensB-2) | real | 決定的直接根拠 (`p3_autonomous_workload_trial.py:883-896`) を先頭に置き、他は corroboration と明記 |
| 13 | P3の「稼働中」はworklog単体では導けない (lensA-6 / lensB-3) | real (射影範囲内で正当) | **fork A の ListAgents 直接実測で補完** — 射影に無かった証拠を段4で統合し、両方を出典として明記する (下記「所有者・占有状況」節) |
| 14 | 次の一手の実行主体 (Codex/人間) が曖昧 (lensB-4) | real | 各行に実行主体列を追加 |
| 15 | draft文書を現行状態へ一般化 (lensB-5) | real | 観測時刻・測定HEADを明記し、「未確定」を許容する書き方にする |
| 16 | 結果推測に読める表現 (lensB-6) | real | 「現行gateはcertified outputを受理できない」への書き換え、性能・勝者は未観測と明記 |

## P3 (重複タスク) の最終統合判断

lensA/lensB の指摘 (worklog単体では稼働中を示せない) は正当。ただし本 wave は fork A で
`ListAgents` を直接実測しており、これは射影されていなかった別経路の証拠である。統合結果:

- **実測で確認**: T-425 / T-972 / T-1438 / T-1458 は `ListAgents` 上に対応する稼働中セッションが
  存在する (T-1458 は2セッション同時)。これは「稼働中」の直接証拠であり worklog carry より強い。
- **未実測**: 各セッションが実際に H1/H2 前提コンポーネントの同じファイル・同じ scope を
  編集しているかまでは、worktree 名からの推測に留まり、diff 内容までは検証していない。
- **T-1371**: 名指しセッションなし。worktree (locked) の存在と worklog 未クローズは確認済みだが、
  生存プロセスの直接証拠はない。
- 結論: command の「T425/T972/T1371/T1438/T1458 と重複する場合は実験を起動しない」は、
  そもそも本 wave が read-only 監査であり実験起動権限を持たないため充足している。加えて
  上記の実測により、これらのタスクは高い確度で H1/H2 前提整備の同時進行作業であると判断する
  (worktree 名と ListAgents のタスク説明文の対応による推測 + 稼働中の実測、diff 内容の完全一致は
  未検証)。

## 人間 lockstep の実行主体分離 (lensB-4 の反映)

D356 (oracle spec の人間承認は機械強制されない) を踏まえ、次の一手は主体を明示する。

- **人間が行う (Codex/AIは代行しない)**: rr80/rr20 calibration の登録、g1→g2 activation、
  paired judge の n/delta_min/sd_max の確定と承認、8b §8 再凍結の承認、T-424/T-272 要求閉包の
  判断または D145 決定5の再訪裁定、oracle spec の staged diff review、scope-B Q3 ガード
  (T-139状態・ノード単独性) の確認。
- **AI (Codex/Claude) が行ってよい**: 各 receipt・artifact の存在確認、file:line 根拠の提示、
  到達可能性 (reachability) の静的検査、欠落の列挙。**充足の断定・承認 bytes の生成はしない。**

## 次の一手

段7 (記録) で `README.md` (blocker table 本体) を上記反映方針に従って完成させ、worklog/decisions
spool fragment を書き commit する。段8 (自己改善)・段9 (終端) を経て wave を終える。
実験本体・人間 lockstep の実行は本 wave の範囲外 — 別 wave/別セッションでユーザーが行う。
