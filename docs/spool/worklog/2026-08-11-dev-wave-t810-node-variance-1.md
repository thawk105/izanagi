---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t810-node-variance
seq: 1
title: ノード間性能差の測定 protocol を設計だけ確定した — 敵対 4 本が blocker 21 件、親の誤り 3 件を子が正した (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t810-node-variance)
---

## 本文

- **依頼はユーザーの直接指示**: 「[T-810] の測定 protocol を設計してください。(中略) 同一 binary・
  同一 workload を N ノードへ同時投入して 1 回分の時間で分散を得る新規測定 protocol として、
  目的・N・割付け・推定量・『成果物へ流入させない』ことを事前固定した設計パッケージを返して
  ください。実走はせず設計のみ、B 系並走ガード 3 条件を適用してください。pilot は複数割当て
  (= 複数ノード) で走るため、ノード間分散の実測根拠は同時信頼領域の解釈を支えます。」
  正本を `docs/pegasus-node-variance-protocol.md` として新設した。**実装面 0 byte。**

- **依頼の前提を 2 つ更新した (段 1 実測)。** (i) 「CC ベンチのノード間比較が存在しない」は
  半分だけ正しい。**登録済み calibration は 2 件あり互いに別ノード** (第 1 世代 bnode011 /
  第 2 世代 bnode048)、同一 head・同一 workload・同一 thread で平均差 1.774%。ただし
  UTC 日付で 19 日 (実経過 18.27 日) 離れ binary bytes も違うので完全交絡であり、結論
  (ノード間分散を答えない) は変わらない。**runbook の「bnode011 単独」は 2026-08-06 以降 stale
  だった**ので訂正した。(ii) **「同一 binary」は既存経路では自動的に成立しない** —
  2 件の build 引数の差は 26 要素中 4 要素、すべて `/scr/<job id>` の job 一時 path で、
  node-local build が path を binary へ焼き込む。共有 path で 1 回 build して bytes を配る設計が
  要る (gflags/glog は `BUILD_SHARED_LIBS=OFF` の静的リンクなので構造的には成立する)。

- **親自身の誤りを 3 件、子が正した。**
  (i) 段 1 brief (P1) の「T-139 は 3 arm を同一 cluster 内で測るのでノード効果は contrast で
  相殺する」は**分母条件について偽**。共通加法効果は `劣化幅 − κ·stock` に残る。段 2 起草が
  反証し親が代数で確認した。(ii) 段 6 1 巡目で親が書いた「ドリフトは主推定量の分母に入らないので
  結論の向きを歪めない」は**推定対象と推定量の混同**。推定量は `MS_A − MS_E` の差なので、
  共通ドリフトが `MS_E` を膨らませると**ノード差を過小評価する**。(iii) 親が `τ_U` を
  「成分ごとの上限の積」で定義しながら assurance は κ 単独の F 反転で計算していた。
  **主区間で測ると assurance は 0.80 でなく約 0.62** (レビュー B が Monte Carlo で実測)。
  対数尺度の単一式へ変えて整合させた。

- **親が退けた所見が 2 件。** (i) 段 3 レンズ A の「単一 arm は T-139 pilot を**支えない**」は
  強すぎる。共通乗数モデルの下では cluster 間分散のうちノード起因成分に上限を与えられる。
  識別できないのは loading の形であって上限の計算ではないので、目的の削除でなく scope 限定を採った。
  (ii) 同レンズの「`CV/√10` は独立性未確認だから SE でない」は機序が違う。親が計算した lag-1
  系列相関は両 record ともほぼ 0 (−0.11 / −0.01) で自己相関は支持されない。実在するのは傾きである。

- **親が独立に計算した数値 (子の主張の裏取りを含む)。** 実 record の反復内下降傾向 =
  bnode048 が相関 −0.6590 (t=−2.48, df=8、両側 5% 有意)、bnode011 が −0.2985 (非有意)。
  設計点の assurance は主区間そのものに対する Monte Carlo で `N=13,R=10` が 0.8462 /
  1 ノード脱落後 0.8080。**焦点レビューが 1000 万 draw で独立再現し、40 万 draw の当選数
  (338,491 / 323,211) まで一致した。**総測定回数 130 が最小であることも全探索で確認された。

- **敵対検証は 4 本 + 焦点 2 本、すべて NO-GO から入った。**段 3 = blocker 6 (統計) + 8 (実行可能性)、
  段 6 = blocker 8 (事前固定性) + 7 (事実誤り)、焦点 1 巡目 = 残 blocker 6 (**うち 4 件は親の
  1 巡目修正が持ち込んだ回帰**)、焦点 2 巡目 = 残 blocker 1 + must-fix 3。最終的に全件を修正した。
  特に「node×round 交互作用 gate」は cell あたり 1 観測では残差と分離できず**発火しえない条件**
  (`MS_E > 2·MS_E`) だったので、推定可能な「傾きの不均一性 gate」へ置き換えた。

- **ユーザー裁定へ回す設計択一 5 件 (Q1〜Q5)。**親は既定値を決めて文書へ書いてあるので、
  覆す場合は該当 field を差し替えるだけでよい。詳細は
  `output/insights/2026-08-11_t810-node-variance-protocol/s4-adjudication.md` §5。
  Q1 materiality `τ*` = 0.6% (親推奨) / 0.3% / 1.2%。
  Q2 目的の範囲 = 感度上限に限定 (親推奨) / 単独 snapshot / 交差設計へ拡張。
  Q3 N・R の目的関数 = 総測定回数最小 (親推奨、13×10) / 総ノード秒最小 / 同時ノード数最小。
  Q4 occasion = 1 occasion のみ (親推奨) / 2 回目追加 / ホスト指定の複数 occasion。
  Q5 runbook §7.5 の stale 訂正 = 本 wave で実施 (親推奨、**実施済み**) / 別 wave。

- **副産物: runbook を 3 箇所訂正した。**(i) 「bnode011 単独」を 2 件・別ノード・完全交絡へ。
  (ii) 「job の内側で比較が閉じている fan-out は**無条件でよい** — node は共通因子として相殺される」
  を条件つきへ。**差が消すのは共通加法 offset だけ、比が消すのは共通乗数だけで、対照差と水準値を
  混ぜた量はどちらも残る。**(iii) 新 protocol への参照と 2 段承認の明示。

- **セッション事象:** 段 3 レンズ B が 2 度落ちた。1 回目は上流の `Selected model is at capacity`
  (rc=1、出力ゼロ)、2 回目は `max_cli_reported_tokens` 到達で SIGTERM (rc=-15、出力ゼロ)。
  同上限は `DW-O01` が「非権威の運用既定」と明記しているので 400 万へ引き上げ、prompt に
  「全文ダンプを避け rg の該当行だけ見る」「予算が尽きそうなら書き切る」を足して 3 回目で成功した。
  **job-id は prompt 内容から導かれるので、`-o` だけ変えた再投入は既存 receipt に当たって拒否される**
  (`NG: 既存の完全な receipt は上書きできない`)。prompt を別ファイルにして解決した。

- **検査:** `python3 tools/check_docs.py` rc=0、`git diff --check` 無違反。
  **変異 matrix は免除** — 実装差分ゼロで kill を観測する面が無い (機械 gate を 1 つも新設していない)。
  先例は worklog (418) の docs-only wave。**受入全走は免除しない** —
  `docs/pegasus-runbook.md` を実 repo から読むテストが 4 file 実在する
  (`grep -rln pegasus-runbook orchestrator/tests/` = `test_calibrator_certify.py`,
  `test_check_ai_provenance.py`, `test_check_docs.py`, `test_schema_v2.py`)。
  `docs/README.md` も `test_check_docs.py` が読む。
  **1 走目 (bnode010、request `903811.nqsv`、543 秒) は赤 1 件で終わった** —
  `test_codex_worker_launch.py::test_check_receipt_rejects_unknown_and_duplicate_fields` の
  終了検証述語 2 本の不成立で、**F57 の再発である** (本 fragment seq 2 に追記した)。
  同 node の単独再走は 1 passed / 3.27 秒 / rc=0 で再現せず、本 wave の差分は docs のみで
  同 test file へ到達しえないため `DW-O18` により帰属しない。**この記録を含む tip で受入を投げ直した。**
  **2 走目の結果値は本エントリに含まれない** — land は wave HEAD と tested tip の厳密一致を
  要求するため。値は wave の報告が持つ。

- **エージェント工数:** codex 子 6 本成功 + 2 本失敗 (段 2 起草 1、段 3 敵対 2 (うち B は 3 投で 1 成功)、
  段 6 レビュー 2、段 6 焦点 2)。段 5 実装子は docs-only のため不使用。

## 次の一手差分

### 更新

- [T-810] **P3・ユーザー裁定待ち (Q1〜Q5)**: 測定 protocol の設計は
  `docs/pegasus-node-variance-protocol.md` として確定した (目的・推定量・N=13/R=10・割付け・
  非流入をすべて事前固定)。**残るのは 5 件の設計択一の裁定と、走行前提の実装である。**
  実装は {{T:node-variance-impl}} が所有する。
  base: 47d334708f945fc5d4fdacf67beb0689b9b2646b1f2e1ff677b5343f4240f79e

### 新規

- {{T:node-variance-impl}} **P3・新規**: ノード間分散 protocol の走行前提を実装する。
  `docs/pegasus-node-variance-protocol.md` の「走行の承認関門」第 1 段の (a)〜(g) =
  N-job barrier と共有 release と取り消し marker と coordinator 側の開始ばらつき測定、
  専用 PBS wrapper (単独性確認・静穏 gate・binary 配布と照合・投入 argv 正規形)、
  runner の argv allowlist、repo 外 root の方針注入と測定ノード上の repo 不在、
  単一 fail-closed validator、並走ガードの機械化、予算 admission。
  **Q1〜Q5 の裁定が出るまで着手しない** (設計値が動くと実装もやり直しになる)。
  **実装面のため Codex author 必須。**
- {{T:living-docs-node-variance}} **P4・新規 (段 6 レビュー B-10、本 wave では未対応)**:
  `docs/pegasus-node-variance-protocol.md` を `tools/check_docs.py` の `LIVING_DOCS` へ加える。
  現状は同 checker の path 規律・参照規律の回帰検出対象になっていない。
  **本 wave が実施しなかったのは、これが `tools/` のコード変更 = 実装面であり、
  docs-only wave の親は直接編集しないためである** (Codex author が要る)。
  成果物影響 = 未実施なら同文書の参照崩れを機械が検出しないが、受理集合・台帳の値は変わらない。
