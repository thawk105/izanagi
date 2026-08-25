---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1721-a1-paired-reps
seq: 3
title: [T-1721] A-1 対測定の装置を反復数一般化し事前登録を凍結した — 計測は D905 により投入しない (コード + docs、branch worktree-dev-wave-t1721-a1-paired-reps)
---

## 本文

- 依頼は「A-1 の対測定を、差を判別できる試行数へ引き上げて再実施する」。**装置と事前登録までを
  作り、計測そのものは投入していない。** 理由は下の B1。
- **B1 (計測を投入しない理由)。** `run_campaign` は現 HEAD の enforcement-source closure digest
  `6d497998c4b80a186cd9ee3fc98154e29ddd0aa23f82f7da215558b90e32bf5a` が批准台帳に無いため
  fail-closed する。批准後に `orchestrator/campaign/loop.py` (1 commit) と
  `orchestrator/campaign/pipeline.py` (3 commit) が動いたためである。
  **D905 (ユーザー裁定) が「批准の執行経路は AI が成りすませない実行主体を新設する案だけを採る。
  人間による転記を残して起動直前へ寄せる案は採らない。設計が着地するまで批准は進めない」と
  定めている。** D758 決定 2 / 決定 4 も同旨で、塞いでいるのは AI 側の設計作業だと明記する。
  親は当初「ユーザーへ批准 1 行を依頼する」と報告したが、これは [T-1629] の親推奨 (β) であり
  D905 が名指しで却下した択である。台帳を確かめて**撤回した**。迂回も依頼もしていない。
- **段 3 の敵対相談が親の導出を 5 件壊した。** 全部作り直した。
  - **検出力式が判定規則と別の仮説を解いていた。** `(z_a+z_b)^2 sigma^2/D^2` は「真値 D のとき
    差ゼロを棄却する」確率であり、判定規則の `resolved-above-floor` が要求する「区間全体が
    floor を越える」ではない。真値がちょうど floor のとき上側へ解決する確率は約 2.5% で 0.80 でない。
    判定規則そのものの動作特性から解き直した ({{D:a1-reps-from-decision-rule}})。
  - **判定境界を pilot の絶対 tps で凍結するのは D496 決定 1 違反だった** ({{D:a1-floor-boundary-is-relative-to-the-run}})。
  - **一律 n は絶対規律 4 に触れていた。** workload 別なら 610 rep、一律なら 1,230 rep。
  - **計画分散の超過で判定を上書きするのは未校正な結果抑制だった** ({{D:a1-variance-breach-is-a-flag-not-an-override}})。
  - **再走は性能依存の欠測選択になっていた** ({{D:a1-rerun-only-before-bench}})。
- **確定した事前登録。** 反復数は workload 別に write-heavy 72 / balanced 205 / read-heavy 28。
  read-heavy の 28 は「標本 SD 自身の片側 95% 上側膨張係数が 1.30 以下になる最小の n」という
  下限が効いた値である (n=5 では 2.3724、n=28 で 1.2938)。5 点 SD が使い物にならなかったことが
  本 wave の出発点なので、SD の推定品質にも下限を置いた。合計 610 rep、bench 約 34.2 分
  (前走の実測 3.36 秒/rep から)。到達する動作特性は Monte Carlo で実測し、真値 0 のとき
  floor 内 0.828 / 0.814 / 1.000、真値が floor の 2 倍のとき floor 超え 0.918 / 0.910 / 1.000。
  凍結文書は `output/insights/2026-08-26_paper-story-a1-sized-preregistration/README.md` で、
  policy v2 がその SHA-256 を束縛する。
- **凍結文書を 1 度だけ改訂した。** 段 6 が「campaign の内部再測定 (変動係数による測り直し、
  最も CV の低い回を採る) は性能量による選択だが止められない」を指摘した。上限を渡す引数は
  `pipeline.evaluate` にあるが `run_campaign` が渡しておらず、渡すには `loop.py` の変更が要る。
  同 file は批准 closure に含まれるため scope 外と裁定し、**限界として事前登録へ追記した**。
  受理データは汚染されない (`rounds != 1` は invalid)。まだ 1 回も計測していない時点の改訂であり、
  追加したのは制約であって緩和ではない。
- **段 6 は must-fix 10 件のうち 9 件を採用した。** 最大のものは、結果の再検証が `result.json` の
  保存済み error を権威として再入力していた点で、D920 (同じ走行側が書く投影は独立証拠にしない)
  が禁じる型そのものだった。raw WAL 起点へ直した。事前登録に無い符号分類 `direction` の追加、
  正例 fixture の定数列への弱体化、床値と半幅の本番導出を固定する検査の不在、
  `n-1` 検査が write-heavy 専用だった件も閉じた。
- **段 4 直前の裁定再走査で D919〜D921 を拾った。** 本 wave 開始後に main へ着地していた。
  D920 を設計へ採用し、D921 (不完全な束の扱いはユーザー裁定) とは衝突しないことを確認した
  (本 wave の publish gate は certification ではなく、一度しか作れない公開先を壊れた束が
  永久に占有するのを防ぐ運用上の安全性である)。
- **論文 §8 は動かない。** 段 3 の装置レンズが指摘したとおり、この study は `formal=false` の
  ままなので、走らせても A-1 の「証拠はまだ 1 件も無い」は正式には動かない。正式化には
  D510 決定 7 の後続 (判定器・証拠契約・registry・judge) が先に要る。本 wave は探索値として
  設計した。この択はユーザー裁定へ返す。
- **セッション異常 2 件。** 段 6 の fix 子が稼働中に焦点走を投入して 148 failed を得た
  ({{F:tests-run-while-workspace-write-child-edits}})。変異 baseline が dispatch の待ち行列上限
  900 秒に当たり `rc=16` で止まった ({{F:mutation-baseline-rc16-queue-wait}})。どちらも
  実装の赤ではない。
- **変異は再照準を要した。** 初回 probe で policy の「自由度 = 反復数 - 1」検査が生存した。
  直後の凍結設計値との固定値比較が同じ入力を先に弾く冗長 gate だったためである。DW-M02 に従い
  実効 gate (固定値比較) へ再照準し、両層同時変異まで裏取りした — 固定値比較だけを潰すと
  2 node、両層を潰すと 3 node (df 分が増える) が赤化し、遮蔽関係を実証した。
  単独 df 変異は冗長 gate として本走の証拠から外した。
- **変異本走は baseline 緑 (233 passed) のうえ、登録 9 件が全件 KILLED。** SURVIVED と MISMATCH は 0。
  spec・台帳・再照準の erratum は `output/insights/2026-08-26_t1721-a1-sized-mutation/`。
  正例対照 (受理集合を過剰に狭める向き) は 23 件の検査を赤化した。
- **受入 1 回目は 15 failed / 16,586 passed で戻ったが、非帰属と判定した。** 赤は
  `test_s8b_floor_campaign.py` 11 件、`test_codex_worker_launch_budget.py` 3 件、
  `test_s8b_oracle_driver.py` 1 件で、**本 wave の差分が触った file を 1 つも参照しない**。
  floor campaign 系は `_real_output_snapshot` が `output/` 配下全体の bytes を走行前後で
  突き合わせる形であり、受入が 2 shard で走る間に片方の dispatch が
  `output/pegasus-dispatch/` へ受領証を書けば必ず壊れる。本 wave が `output/insights/` へ
  足した file は commit 済みの静的内容なので前後どちらの snapshot にも同じく現れ、この検査を
  壊さない。**赤くなった 3 file を単独再走したところ 596 passed / 8 skipped / rc=0 で
  1 件も再現しなかった。** `DW-O18` に従い受入を 1 回だけ再走した (反復していない)。
  投入時のマシンは他 wave の変異 harness 5 本と Codex の子 6 本が同時に走る高負荷だった。
  **受入 2 回目は 16,601 passed / 60 skipped / `child-green` で通った。**
- **親が受入の走行中に追跡 file を編集する違反を自ら踏んだ。** 受入 2 回目の投入直後に worklog
  fragment を編集した。数十秒で気づいて repo 外へ退避し `git checkout --` で clean へ戻したため
  受入は緑で完走したが、これは本 wave が {{F:tests-run-while-workspace-write-child-edits}} として
  記録したのと同じ型の再発である (向きは「子の稼働中に測る」ではなく「受入の稼働中に書く」)。
- **段 8 の改善候補 2 件を予算超過で取り下げ、裁定パッケージへ回した。** どちらも発火実績があり
  routing 先も一意に決まるが、`DW-O18` は 998 bytes で単節予算 1,000 に対し残り 2 bytes、
  `DW-M07` は 978 bytes で残り 22 bytes しかない。必要な 1 文は約 80 bytes である。
  `DW-O18` の本文は 1 文ごとに別個の義務を担っており、意味等価に 70 bytes 以上を落とせない。
  **予算のために安全義務を削らない**契約に従い縮約を止めた。恒久対応そのものは failures 台帳と
  memory で成立しており、欠けているのは dev-wave 手順書への統合だけである。
  択は (a) 単節予算を上げる (独立審査対象)、(b) 別 wave で意味等価に縮約、(c) 記録だけで足りるとする。
- 焦点走は変更 3 file と参照関係で引いた consumer test 5 file で 1,094 passed / 4 skipped。
  skip 4 件は CCBench の template patch 未適用による既存の環境 skip で、本 wave の新設検査では
  ないことを `-rs` 付き再走で実測した。

## 次の一手差分

### 更新

- [T-1721] **P2・ユーザー裁定待ち**: A-1 対測定の装置と事前登録は凍結済み
  (反復数 72/205/28、判定規則、policy v2、凍結文書の hash 束縛)。**計測の投入だけが残る。**
  D905 により、批准の執行設計 ([T-1629] の (γ)) が着地するまで進めない。
  併せて「`formal=false` のままの探索値として走らせ論文 §8 は据え置く」か
  「D510 決定 7 の後続を先に実装して正式化する」かの択をユーザーへ返す。
  base: 8e6cc52e2b84179a2dc4fb072e9a0684710e2adc94302eaae32a2d7a0a5acce1

### 新規

- {{T:a1-interleaved-pairing}} **P2・新規**: A-1 の対の作り方を交互配置へ改める。
  現行は arm ごとに build して全反復を通すため、balanced では 1 arm の区間が約 615 秒になり、
  同じ番号どうしを引く「対」の時間隔もそれだけ開く。この交絡は反復数では消えない。
  実装は `orchestrator/campaign/loop.py` か `pipeline.py` を要求し、どちらも批准 closure に
  含まれるため、批准の執行設計が着地した後に着手する。
- {{T:a1-policy-binding-is-intra-commit-only}} **P3・新規**: A-1 の policy 束縛は同一 commit 内で
  しか効かない。policy・その SHA・source binding を別 commit で揃えれば任意の反復数が通る。
  hash は整合性を示すが外部からの承認を示さない。恒久的な対処は承認主体の新設であり、
  批准の執行設計と同じ問題に帰着する。
