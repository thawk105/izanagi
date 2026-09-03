---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-a1-fanout
seq: 1
title: A-1 pilot を workload 単位の 3 job へ割った — 分割が開く規律 2 の穴と未 gate の build 流路を塞いだ (コード + テスト、branch worktree-dev-wave-a1-fanout、変異 5/5 KILLED + 等価 1 SURVIVED)
---

## 本文

- **ユーザー裁定 1: 「codex に相談して決めて」。** 依頼は「pilot を走らせて sizing まで出す」
  だったが、着手前の実測で pilot が走らせられないことが確定した。事前登録の発効 5 箇所
  (D1435 / D1479) が未実施で、`_require_policy_ready_for_execution` が
  `submit` / `measure` / `complete` / `materialize` の 4 入口すべてを閉じている
  (親が main の checkout で live 実行して確認)。さらに依頼が明示した「複数ノードへ分割投入」を
  現行機構が満たせない (`#PBS -b 1`、workload 選択の引数なし)。この 2 点をユーザーへ返したところ、
  A/B の択一を codex への相談つきで委任された。
- **ユーザー裁定 2: 「いいよ。後は推奨通りで」。** 相談 2 レーンは独立に「workload 単位で
  ノードへ割る」へ収束し、lane luna がそれを**案 C** (policy JSON と事前登録の bytes を変えず
  producer 側だけを直す) へ狭めた。親は案 C を採り、実装を本 wave で、発効を人間手番として
  後段に置く順序をユーザーが承認した。
- **依頼が名指した正本が、同じ依頼が名指した機構と別 study を指していた。** 依頼は正本を
  worklog 1142 と `2026-08-16_t1142-n-pilot-prereg/preregistration.md` としたが、この文書は
  8b oracle の `n` 導出 pilot (12 cell、rr20/rr80 holdout) の事前登録であり、名指された機構
  (`paper_story_a1_paired.py`、各 workload 60 対) とは別物である。A-1 の正本は [T-1777] と
  `2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`。機構側を先に当たったため
  実害は出ていない。
- **親 brief の誤りを相談が 3 件突き返し、親が現物で追認した。** (1) 「6 時間枠は楽ではない」は誤り
  — 旧 A-1 走行は 3 workload 全体を約 416 秒で終えている。(2) その根拠に引いた「検査 1 回 23 分」の
  引き方が誤り — あれは read-heavy の混合区間の上端であって本 pilot が使う legacy verify の単価では
  ない。(3) 「編集は 2 file」も誤りで正しくは 3 file (親の閉包検査を変数名で引いたため、変数名を
  含まない policy JSON が漏れた)。
- **棄却した finding。** 段 3 で「registry を変える必要がある」「v2 凍結成果物へ波及する」
  「3 job が queue で直列化される」はいずれも refuted。段 6 で「MF2 前半が塞がっていない」
  「MF1 が恒真」「MF3 の CPU 成分 validator が恒真」も refuted。
- **生き残った変異 1 件は穴ではなく冗長 gate だった。** probe で
  `M1-f1-emptied-namespace-failclosed` が SURVIVED した (赤 node 0)。契約どおり他層の mask を
  先に疑わせたところ、同一入力では手前の parse と直前 gate が必ず先に拒否すると `path:line` 付きで
  確定した。**分岐は削除していない** — 別 process が検査の合間に証拠を公開する競合状態でなら
  到達するため。`DW-M03` に従い冗長 gate と明記して単独変異の証拠から外した。
- **セッション異常: Codex の利用枠が枯渇して段 5 が中断した。** 実装子が model call 22 回・
  file 1 個の編集を終えた時点で upstream の利用枠上限に当たり、`outcome=not_accepted` /
  `failure_class=f45_missing_output` で停止した (復帰予告は 9/7)。同時に走っていた他 wave の
  codex 子も 8 本前後から 1 本へ減っており、アカウント単位の枯渇である。親は途中成果を
  「未完了・未監査」と明記した commit へ保全し、ユーザーへ (a) 復帰待ち (b) エンジン切替の
  裁定を求めた。翌日ユーザーから「codex 使えるようになった」と通知があり、同じ prompt に
  「前任の 307 行をまず監査してから続けよ」を足して再投入した。**再投入した実装子は前任の
  実装に実際の欠陥を見つけた** — 規律 2 の関門が壊れた intent を無視する fail-open になっており、
  fail-closed へ書き直している。
- **子の環境からはテストを実走できない。** 段 5・段 6 の全 codex 子が `qstat` の
  `EACCTAUTH Unknown user-id` で計算ノードへ投入できず、いずれも「実装済み・未実走」と正しく
  申告した。焦点走 9 file と変異 matrix と受入全走はすべて親が実走した。
- **エージェント工数。** codex 子 8 本 (plan 1、consult 2、review 2、author 2 [うち 1 本は枠切れで
  中断]、fix 3、merge 合成監査 1)。すべて `gpt-5.6-sol` / `xhigh`。
- **変異の wrapper は環境主張で赤になったが測定は緑。** 本走は KILLED 5・SURVIVED 1 (等価変異)・
  MISMATCH 0・期待と実測が 6/6 完全一致・`child_rc=0`。一方 wrapper の共有木事後検査は
  `shared_snapshot_matches: false` で rc=125。親の worktree は走行前後とも clean であり、
  走行中に local main が 2 commit 進んだことが変化源である (並行 wave の着地)。
  変異自体は固定 commit の使い捨て worktree で走っており、測定の緑と wrapper の環境主張は別物である。
- **受入は 1 回空振りした。** 1 回目は claim 前の provenance 事前検査が `queue-wait-timeout` で
  rc=70 (`child_started: false`、テスト本体は 1 行も走っていない)。D612 の混雑上書きは
  `run_tests.py` にしか効かず、この経路の待ち時間は 900 秒固定で上書き口が無い。2 回目で
  `child-green` を取得した。

## 次の一手差分

### carry

- [T-2224]
- [T-2225]

### 更新

- [T-1777] **P2・ユーザー手番 (発効)**: A-1 の対の配置。**(1) coordinator 実装は着地済み**
  (`08a17b3b3`)。**(1.5) 事前登録の起草は完了した** (2026-09-02)。本文は
  `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`
  (SHA-256 = `8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc`)。
  **(1.7) workload 単位の 3 job fan-out を実装した** (本 wave、案 C)。事前登録と policy JSON の
  bytes は変えていないので、発効手順はそのまま使える。ただし**手順書 §4.1 が名指す行 locator 4 件と
  `docs/pegasus-runbook.md` §7.7 の「A-1 は 1 job」という記述は、本 wave の着地で古くなった**
  ({{T:a1-fanout-docs-followup}} が所有)。**残るのは発効だけで、これは人間の手番である**
  (D1383 / D1391)。編集は 5 箇所 — driver の事前登録 pin 2 本、policy JSON の `preregistration`、
  policy bytes に連動する `V3_PILOT_POLICY_SHA256`、未凍結を固定している正例テスト、および
  sized 形状 fixture の `preregistration` 戻し。手順・実行順・commit 前後に分けた検査コマンドは
  `output/insights/2026-09-01_t1777-pilot-preregistration` §4 が正本。
  (2) 発効後に pilot を 60 対/workload 測る (未走)。(3) pilot から対 SD とブロック実効 sigma を
  出し、独立 seed の simulation で反復数を認証する。(4) `paper_story_a1_paired.v3-sized.json` と
  その事前登録を凍結する (未作成)。(5) 本走を投入する。
  凍結済みの現行 study は据え置き、bytes を変えない。
  base: 5c1077acdce31063c381b84b4efd14b05b4651a6bfa420f9c696c28a8431c69d

### 新規

- {{T:a1-fanout-docs-followup}} **P2・新規**: A-1 の 3 job fan-out 着地に合わせて 2 つの docs を
  直す。(a) `output/insights/2026-09-01_t1777-pilot-preregistration/README.md` §4.1 が名指す
  行 locator 4 件 (driver `:175-176` / `:168-170`、test `:1386-1390` / `:1018-1020`) を着地後の
  位置へ更新する。**この file は発効手順であって事前登録本文ではないので、編集しても pin 対象の
  hash は動かない。** (b) `docs/pegasus-runbook.md` §7.7 の「A-1 は 1 job」と単一
  submission/completion topology の案内を、workload 別 3 request・group receipt/failure・
  job 別 evidence・group completion の運用へ更新する。**発効より先に済ませる**と、
  人間が古い行番号を頼りに発効することを避けられる。
