---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t1050-s8b-admission
seq: 2
---

## {{D:s8b-admission-live-historical-split}}. admission receipt の検証権威を live と historical で分ける

**決定:** S8b portable binary record の admission receipt を検証するとき、期待 policy の権威を
経路で分ける。

- **live 経路** (build → store → portable projection → resume → floor 測定直前 → oracle 実走直前) は、
  `build_admission.py` の公開 policy resolver から現行 policy を独立に再構築して照合する。
  **artifact 内に記録された policy を期待値として使ってはならない。**
- **historical reverify 経路** (published freeze の再検証) は現行 policy との一致を要求しない。
  構造・exact key・canonical outer SHA・subject と record の一致・freeze entry / binding 対応・
  cell 間の policy 一意性だけを要求する。

**理由:**

- artifact 内の policy を期待値に流用すると `P* == P*` の恒真検査になり、gate として無価値になる。
  受理集合が「発行済み」から「整合した JSON を作れる」へ広がる。敵対レビューが独立に検出した。
- policy は `CURRENT_PIN` から導出されるため、pin が進むと過去 freeze の再検証が原理的に落ちる。
  historical 経路に現行 policy 一致を課すと、公開済み freeze を参照する経路が pin 更新のたびに
  停止する。
- 一方 historical 側を無検査にすると、production producer が単一の build run context から生成
  できない混成 freeze を受理してしまう。cell 間の policy 一意性はこれを閉じる最小の要求である。

**却下した選択肢:**

- 全経路で現行 policy 一致を要求 — 公開済み freeze の再検証が pin 更新で落ちる。
- 全経路で policy 検査を任意化 — 呼び出し元依存の受理集合になり、live の gate が死ぬ。
- 期待 policy を artifact から読む — 恒真検査であり検出力ゼロ。

## {{D:s8b-admission-guarantee-scope}}. admission 束縛の保証名を自己整合 provenance に狭める

**決定:** S8b binary store の admission 束縛が保証するのは「発行時に検証した admission の、
保存から oracle 実走直前までの連続束縛」であり、「build gateway が発行したことの証明」ではない。
docstring・insight・worklog にこの文言で書き、暗号学的保証と書かない。信頼根と署名は新設しない。

**理由:**

- durable artifact 上の receipt は、整合した JSON を手で書けば自己発行できる。これを閉じるには
  署名か外部 trust root が要る。
- 同型の問い (承認 receipt の署名と外部 trust root) は既に裁定済みで、署名方式と trust root は
  設けず、自己発行可能な性質を明示したまま受容すると決まっている。本件だけ別扱いにする理由がない。
- 過大な保証名は、後続の consumer に「gateway 発行が証明されている」と誤読させ、
  その前提で受理集合を広げる判断を招く。

**却下した選択肢:**

- 署名 / issuer chain の新設 — 既裁定に抵触する。
- 機械可読な limitation 宣言の追加 — 既存の宣言経路は別族の機構であり、S8b portable record 側には
  発火する既存 artifact path が無い。発火条件を書けない機構は実装しない (DW-G04)。
- 保証名を狭めず実装だけ入れる — 誤読の危険が残る。
