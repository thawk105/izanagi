# 床値 (8b v1 freeze) crash 復帰救出経路 — 実装着手前の技術確認 (2026-08-22)

## 総合結論

**D496 決定3 と旧 §9項8 の優先順位は既に D510 決定4 (2026-08-18) が「8b §9項8」を名指しして
決着済みであり、`docs/phase3-8b-descriptor-design.md` §10.5 (同日付) が対応する設計文
(freeze-wide 事前割当 attempt registry) を既に持つ。** ただし実装は 8c 系
(`orchestrator/campaign/trial_registry.py`) にしか存在せず、8b 系との結合はゼロである。
`trial_registry.py` の公開契約 (schema/path/ARMS/HOLDOUTS/`TrialManifest`) を非互換に
変更して 8b へ転用することは避けるべきだが、**「8b 専用に新規複製する」か「共通 core を
抽出して8c互換facade+8b adapterにする」かは、段3 敵対レンズが独立に発見した約14:1の
行数比 (domain非依存 ~1,738行 vs 8c固有 ~123行) を踏まえてもなお未決着であり、次の
ユーザー裁定へ返す。** 加えて、8b 自身の失敗分類が現状「性能出力を読んだ後」に決まる
実装になっている点 (`s8b_floor_campaign.py`) は、どちらの案を選んでも別途閉じる必要が
ある正しさ上のギャップとして新たに確定した。本 wave は docs のみを変更し、production
実装・測定は一切行っていない。

## 1. 経緯・目的

command 引数は旧 [T-901] を引き継ぐ [T-1484] として、`docs/phase3-8b-restart-runbook.md`
§3.6 (crash 後の復帰可否)・§5 R-5 (裁定未決着) を対象に、D510 の attempt registry 機構を
床値/8b v1 freeze 系へ適用する技術確認を指示した。裁定根拠は D496 決定3・D510 決定4
(2026-08-18、今日 2026-08-22 のユーザー裁定により床値/8b系にも適用範囲を拡張)。

## 2. 段1 brief の要旨

R-5 は「D496決定3 (落ちた構成を測り直す・終端を認めない) と旧 §9項8 (実走後の途中再開は
拒否) のどちらが優先するか」を2026-08-17時点で未決着としていたが、D510決定4
(`docs/decisions.md:21243-21249`) が「8b §9項8の再走全拒否よりD496決定3を優先する」と
名指しで既に答えていることを一次資料で確認した。加えて `docs/phase3-8b-descriptor-design.md`
§10.5 (2026-08-18、D510と同日の再凍結) が同一論点への設計文
(事前割当・消費範囲限定・観測値不変・失敗分類事前確定・単一root) を既に持つことを発見した
(command 引数はこの節を直接名指ししていない)。全文: `verbatim/stage1-brief-and-stage4-adjudication.md`。

## 3. 段2 codex plan の要旨

brief の主張を file:line で独立に再確認し、全て正しいと判定した。加えて brief が持って
いなかった重要な発見を2件追加した。(i) 8b の失敗分類 (`s8b_floor_campaign.py:4773-4840`)
は `measure_fn` 実行**後**に決まっており、D510決定4の「出力を読む前に分類」要件を現行
実装は満たさない。(ii) `trial_registry.py` 自身も内部 event chain の整合性は検査するが
OS レベルの「read-first」事実は証明しないと docstring で明記しており (`:376-379`)、
T-1337 のレビューでもこれは scope 外のまま残っている
(`docs/archive/worklog-phase3-0820-738.md:7-13,27-31`)。R-5 本文の旧→新案 (3節分) を
file:line 付きで起草した。全文: `verbatim/stage2-plan.md`。

## 4. 段3 敵対2レンズの要旨

**レンズ sol (正しさ境界)**: 失敗分類の post-hoc 性を real な未解決欠陥と確認。
novelty search (`s8b_holdout_freeze.py` の `unknownness_check`) は repo 上の既知性しか
検査せず、統計的独立性 (再抽選バイアス) は §10.4 の測定近接性ラベルが別途扱うべき問題と
整理した。§10.5 の「落ちた構成の次slotだけ消費」は、crash点4 (観測開始後) の再抽選
バイアスの具体的な扱い (どの attempt を主値にするか等) までは規定していないと指摘。
段2 の R-5 書き換え案には、より保守的な (「揃う場合だけ許可」でなく「現HEADでは許可しない」)
言い回しを提案した。全文: `verbatim/stage3-lens-sol.md`。

**レンズ luna (整合性・実効性・所有範囲)**: **決定的所見 — 「8b専用の新規複製が最善」は
未検証。** attempt state machine 本体 (`trial_registry.py:1818-3555`、約1,738行) は
ほぼドメイン非依存で、8c固有部分は acceptance (`:3432-3555`、約123行) に集中する。
共通 core 抽出＋8c互換facade＋8b adapter の方が保守面で有利な可能性があり、段2 plan は
この比較を行っていないと指摘した。D649 が却下したのは T-1472 scope (judge・3表・
validatorの重複実装) であり、8b attempt registry の再利用可否そのものではないことを
確認 (brief の記述を追認)。D649以降 (D650〜D659) と今日の worklog を全件確認し、本件を
覆す新規裁定はないと確認。並行 wave 衝突は現時点で実体としては低リスクと live 実測した。
全文: `verbatim/stage3-lens-luna.md`。

## 5. 段4 裁定 (親)

**裁定: 実装しない (`4→7→8→9`)。** 両レンズの全13所見を real として採用した
(refuted 判定分もその反証内容自体を real として採用)。最重要の帰結は、luna 所見6により
当初の (P1)「8b専用対応物を作る」という暫定判断を**確定推奨として維持できない**と判断した
ことである。`trial_registry.py` の公開契約を非互換に変更しないことは確定するが、
実装形状 (専用複製 vs 共通core抽出) は次のユーザー裁定へ返す。裁定の全文・所見表・
R-5 更新方針は `verbatim/stage1-brief-and-stage4-adjudication.md` の「段4 裁定 (親)」節を
正本とする。decisions への反映は `{{D:t1484-floor-restart-registry-recommendation}}`
(fold 後の実番号は `docs/decisions.md` を参照)。

## 6. 稼働中 wave との重複確認

`ListAgents` (51 peer session) の実測により、本件と直接編集面が重なる稼働中セッションは
確認できなかった。luna レンズが `git worktree list` を実測し、`trial_registry.py`/
`p3_autonomous_workload_trial.py` を直接触る生存 worktree は無く、
`autonomous_trial_completeness.py` (T-1458 が編集中) 経由の遅延 import
(`:880-884`) による間接結合のみが残ると確認した。これは本 wave の blocker ではなく、
将来の実装 wave が着手時に再確認すべき事項として記録する。

## 一次資料索引

- D496 全文: `docs/decisions.md` (grep `^## D496`)。
- D510 全文: `docs/decisions.md` (grep `^## D510`)。
- D649 全文: `docs/decisions.md` (grep `^## D649`)。
- `docs/phase3-8b-descriptor-design.md` §9項8 (269-320)・§10.4〜§10.7 (506-565、
  2026-08-18再凍結の規範本文)。
- `docs/phase3-8b-restart-runbook.md` §3.6 (283-325)・§5 R-5 (352-438、本waveの更新対象)。
- T-1179/T-1337/T-1353 の一次資料: `docs/archive/worklog-phase3-0816-595-596.md:990-995`、
  `docs/archive/worklog-phase3-0818-643.md:592-596`、
  `docs/archive/worklog-phase3-0818-650.md:546-582`、
  `docs/archive/worklog-phase3-0820-738.md`。
- T-1472 の先行監査 (D649 の一次資料): `docs/archive/worklog-phase3-0822-815.md`。
- 本wave verbatim: `verbatim/stage1-brief-and-stage4-adjudication.md`・
  `verbatim/stage2-plan.md`・`verbatim/stage3-lens-sol.md`・`verbatim/stage3-lens-luna.md`。
