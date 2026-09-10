## 判定の要旨

親の「現時点では実施せず返却」は妥当です。ただし、B-2 の「AI は承認 commit を作れない」と、B-3 の「pointer 発効自体が D328 と衝突する」は過剰です。

## 過剰保守の検査

- **refuted** — `AI-Agent: none` は、ユーザーが承認内容を確定し、AI が機械的にファイル追加と Git 操作だけを行う場合には成立し得ます。`_assert_user_commit` が検査するのは非 merge、逐語の trailer、H の祖先性であり、誰が内容を選んだかではありません。`orchestrator/campaign/s8b_ratified_freeze.py:537-549`、`docs/ai-provenance.md:67-74`。  
  したがって「AI が commit するには provenance を偽るか検査を緩めるしかない」という親検算は過剰です。AI が承認判断をした場合だけ `AI-Agent: none` が不正になります。

- **refuted** — approval と active pointer は同一 commit に、対象の二つの record だけを追加する設計です。ユーザーが世代、approval 内容、pointer の参照先を確定した後なら、AI がその exact bytes を準備する解釈は可能です。`orchestrator/campaign/s8b_ratified_freeze.py:1189-1210`、`docs/phase3-8b-descriptor-design.md:395-405`。

- **real** — ただし A は現在実行できません。spec の canonical path は不在で、現在の contract test は durable spec がゼロであることを要求します。`brief.md:19-29`、`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-143`。hash だけを書いても loader は path の bytes を読み、hash 一致と schema を検査するため不十分です。`orchestrator/campaign/s8b_oracle_spec.py:182-200,258-274`。

- **real** — B も現時点では実行不能です。v2 世代 record がなく、candidate producer の前提である budget approval pin と official、かつ `eligible_for_refreeze` が true の floor result が未成立です。`parent-verification.md:25-33`、`orchestrator/campaign/s8b_holdout_freeze.py:1368-1404`、`orchestrator/campaign/s8b_holdout_freeze.py:1212-1259`。

## 委任の射程

- **real** — 「AI へ委任」は、既存の設計と T-803 を読む限り、承認対象の内容を AI が創作してよいという許可ではありません。T-803 は承認者をユーザー、記入時点を将来の実凍結手番と明記し、先行設計もユーザーによる内容確認を要求しています。`brief.md:10-15`、`docs/archive/worklog-phase3-0811-419.md:525-529`、`docs/archive/worklog-phase3-0811-416-417.md:1142-1147`。  
  AI が spec の schedule、run contract、除外理由などを選べば、人間 reviewed spec という意味が失われます。

- **refuted** — したがって「AI は承認手続きに関与できない」という読みは広すぎます。正しい境界は、ユーザーが内容を確定した後の hash 計算、canonical path への配置、record の機械的整形までです。A の hash 定数を AI が実装ファイルへ書く場合は、Git 操作だけの代行とは別に、`docs/ai-provenance.md:46-57` の実装面と trailer を判定する必要があります。

## D328 の射程

- **refuted** — approval と pointer の構造的発効そのものは、D328 が保留した「実装と測定の同一性検証」と同一ではありません。D328 は正しさゲート、admission、防壁検査を保留対象外と明記しています。`docs/decisions.md:14786-14808`。また module 自身も record、approval、pointer 連鎖を構造層として説明しています。`orchestrator/campaign/s8b_ratified_freeze.py:1-18`。

- **real** — しかし現在の実装は層を完全には分離していません。`load_ratified_freeze` は approval 連鎖の後に世代内容の同一性検証を呼び、`reverify_published_freeze` は full validation を呼びます。`orchestrator/campaign/s8b_ratified_freeze.py:1315-1327,2840-2855,3244-3254`。report と judge は official manifest が存在すればこの再検証へ進みます。`orchestrator/campaign/s8b_oracle_report.py:1753-1770`、`orchestrator/campaign/s8b_oracle_judge.py:361-378`。  
  よって親の B-3 は「pointer の設置自体が D328 違反」ではなく、「pointer を設置した後に、保留中の同一性検証を発効済みと誤表示しない consumer 境界が必要」という意味に修正すべきです。D328 の解除は別途、ユーザーの明示命令が必要です。`orchestrator/campaign/freeze_verification_hold.py:14-65`。

## 返却内容の不足

- **real** — 親の返却案は事実報告としては足りますが、ユーザーが次の一回で選べる選択肢と担当、発火条件が不足しています。少なくとも次を分けるべきです。

  - A は「ユーザーが exact spec bytes を確定済み。AI は配置と hash 記入だけを行う」か、「spec 内容が未確定なので producer、設計、承認を先行する」か。
  - B は「official floor と budget approval が成立した後、ユーザー確定内容から AI が candidate と approval、pointer の準備をする」か、「D328 の明示解除まで pointer 発効を待つ」か。
  - D328 は第五束の「整合を確認」を解除命令とは扱わず、解除するか、保留 marker を保ったまま downstream を拒否するかを明示すること。
  - 担当を、内容確定はユーザー、candidate 生成は AI、機械的 record 準備は AI、承認判断と D328 解除はユーザー、と分けること。

D302 も、hash は識別子に過ぎず、approved spec からの内容再導出が必要だとしています。`docs/decisions.md:13993-14019`。hash 記入だけを「承認完了」と返却文に書いてはいけません。

## 記録の落とし穴

- **real** — land する場合は canonical 台帳を直接編集せず、`docs/spool` の worklog fragment として commit し、land lock 内の fold に任せます。`docs/dev-wave/core.md:87-100`、`docs/dev-wave/operations.md:132-147`、`docs/spool/README.md:1-5,80-102`。

- **real** — land しない場合、fragment は母集合に入らず、branch を破棄すると消えます。`docs/spool/README.md:122-127`。したがって branch と fragment の commit を保持し、裁定 package を repo 外 inbox にも控え、親へ branch 名、tip、fragment path を渡す必要があります。scratchpad だけに置いてはいけません。`docs/handoff/README.md:12-20`。

- pytest は実行していません。緑とは判定していません。

## 総括

親の返却判断は妥当。ただし、B-2 は過剰で、B-3 は consumer 境界の問題へ限定すべきです。

返却 package に追加すべき項目:

- ユーザー確定 bytes と AI 機械準備を分けた A の選択肢。
- v2 世代、official floor、budget approval、canonical path の発火条件。
- approval と pointer の内容、担当者、commit provenance。
- D328 を解除するか、保留中の downstream を拒否するかの選択肢。
- land 成功前は未記録として branch、tip、fragment、repo 外控えを保持する規則。