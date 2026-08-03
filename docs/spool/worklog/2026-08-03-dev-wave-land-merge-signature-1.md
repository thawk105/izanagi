---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-land-merge-signature
seq: 1
title: 並行開発を止めていた land の fold 署名判定を trusted main cutoff の外側へ限定した — 敵対レビュー 4 本と変異が「防壁の領域」を 3 度言い当てた (コード + docs、branch worktree-dev-wave-land-merge-signature、受入全走 = Pegasus gen_S 計算ノード request 881289 で 5279 passed / 19 skipped、変異本走 = 8 変異すべて kill)
---

## 本文

- **並行開発が実際に止まっていた。** [T-313] wave の段 9 land が
  `status=fold-failed` / `reason=landed-fold-owned-path` で停止したのが発端。fold 署名検査が
  `git diff-tree -m` で親ごとの差分を見るため、`DW-O23` が指示する「land 前の wave 側 main
  取り込み merge」は、wave 側の親との差分に main が既に取り込み済みの fold 署名を必ず含む。
  fold は 2026-08-02 以降すべての land が `FOLDED.md` を変更するので、**main が動いた後に
  取り込みが要る wave は正規手段では land 不能**だった (rebase / cherry-pick は `DW-STOP` が
  禁じる迂回なので、逃げ道は 1 つも無い)。
- 潜在期間も実測した。`-m` は導入時 `2743e0d` からあったが、`27f693f` が署名を「作成 `A` では
  なく変更 `M`」へ絞ったため、`FOLDED.md` が新規作成だった時期の merge は素通りしていた。
  過去に land できた merge `6af21d7` の当該 status は `A`、[T-313] の merge `ee28642` は `M`。
  **2 回目以降の fold が main に載った時点で発火**する穴で、[T-313] が最初の一本だった。
- **親の当初案は敵対検証で潰れた。** 「累積差分で判定する」案は、hidden fold の後に
  protected tree を base へ戻す履歴を見逃す (fold の効果が消えても canonical 台帳の偽造内容だけが
  残る)。段 2 プランの「三 tree 等式で merge を免除する」案も、免除が **path 単位**であるため
  protected 2 path を main 親から、canonical 台帳を wave 親から採る merge が通る。
  **fold は複数 path を同時に動かす transaction である**という一点で、両案とも破れた。
  採用したのは `{{D:land-signature-outside-trusted-cutoff}}`。
- **段 3 のレンズ A が upstream の安全フィルタで殺された (F45 の再発)。** 最終メッセージだけが
  遮断され、成果物が得られなかった。同一 prompt の再投は F45 のとおり通らないため、
  攻撃語彙を排し「検証関数の仕様適合レビュー」として書き直して再投したところ通った。
  **書き直しの方針が有効である**という実測が得られた。
- **変異が実物の穴を 1 件出した。** 初回 8 件は KILLED 4 / MISMATCH 3 / SURVIVED 1。
  生存した M03 は「trusted parent が複数の octopus で、信頼できない parent も走査する」ことを
  テストが固定していなかった。M04 も同型で cutoff 未指定時の全 parent 走査が未固定だった。
  どちらも「**走査から落とされる側の parent からしか署名が見えない**」fixture が無いという
  同じ形である。負例 2 本を新設して再走し、期待 node ちょうどで KILLED。
  M06 / M07 は kill されたが期待より多くの node が赤で、冗長 gate として記録し
  単独変異の証拠からは外す。初回台帳は `DW-M02` に従い消さず erratum として残した。
- 段 6 の fix は 3 巡した。round 1 = subprocess 削減と量化の固定と land 配線 E2E、
  round 2 = その E2E の fixture が実 planner の検証を通らない FOLDED receipt を書いていた
  (受入が 1 本赤になり実測で判明)、round 3 = 変異が暴いた量化の穴。
- **閉じていない穴を 2 件、意図的に残した。** (i) 署名 2 条件は lock 外 fold の十分条件ではなく、
  canonical 台帳だけを書き換える履歴・`T` (gitlink) を経由する復元・同一 commit 内の A→D は
  今日も受理される。(ii) supervised runner (checker / daemon) は receipt の初期 `base_main_sha` に
  束縛されており、正規 main merge を拒否したままである。いずれも本 wave では受理集合を
  広げも狭めもしていない。
- **禁止集合の置き所を 4 回書き直した。** (1) 親の当初案「累積差分」は段 2 が棄却、
  (2) 段 2 案「三 tree 免除」は段 3 レンズ B が棄却、(3) 採用案「trusted がちょうど 1 つ」は
  **本 wave 自身の land が実測で棄却** — worktree を main から切った直後に main を取り込むと
  両 parent が trusted になり、「main に追いついてから作業を始める」正規形が禁止される
  (F82 の 4 度目)、(4) 補遺 初版「極大 trusted parent を無条件に選ぶ」は**実装子が契約どおり
  停止して棄却** (fix round 3 の octopus 負例と矛盾)。
  最終形は「全 parent が trusted のときだけ極大 trusted parent を選ぶ」で、
  untrusted parent を含む merge の判定は一切変えていない。
  補遺の変異 M09〜M12 は 4 件とも kill (SURVIVED ゼロ)。
- 変異 M11 の走行で無関係な module のテストが 1 本赤になったが、単独再走で緑だった。
  `DW-O18` に従いフレークとして扱い、実装差分へ帰属しない
  (`orchestrator/tests/test_codex_worker_launch.py::test_fake_stdout_matches_observed_cli_event_shape`)。
- 逐語 = `output/insights/2026-08-03_land-merge-signature/`。

## 次の一手差分

### 新規

- {{T:fold-signature-completeness}} **P2・ユーザー裁定要 (本 wave で実測)**: fold 署名 2 条件が
  lock 外 fold の十分条件でない件をどうするか。canonical 台帳のみの書き換え・`T` gitlink 経由の
  復元・同一 commit 内 A→D が受理される。択 = (a) fold transaction の意味検証
  (FoldPlan delta の保存または決定的 replay) まで広げる、(b) heuristic と明記して現状維持、
  (c) 署名に canonical / archive を足す (legacy な canonical 直接編集契約と衝突するため
  その契約の廃止も同時に裁定する)。一次資料 =
  `output/insights/2026-08-03_land-merge-signature/s3-lens-a-spec-conformance.md`
- {{T:supervised-land-cutoff}} **P2・ユーザー裁定要 (本 wave で実測)**: supervised runner
  (checker / daemon) が receipt の初期 `base_main_sha` に束縛され、正規 main merge を
  拒否したままの件。直すには receipt schema へ tested main cutoff を別 field で永続化・
  binding する必要がある。択 = (a) schema 変更して land CLI と揃える、(b) supervised 経路では
  main 取り込みを禁じる運用にする、(c) 現状維持。一次資料 = 同上
