---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t139-q1-canonical-decision
seq: 1
title: 第 7 束 Q1 (a) の canonical decision を起草し、D320 の例外範囲が未裁定であることを実証して裁定へ返した (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t139-q1-canonical-decision)
---

## 本文

指示は「第 7 束 Q1 (a) が定めた canonical decision を起草して land する」だった。**起草した。
そして起草したからこそ、land できない理由が実証された。** 段 2 のプランと段 3 の敵対 2 レンズ
(`sol` / `luna`) が**独立に NO-GO** を返し、親が段 4 で追認して実装差分ゼロで裁定へ返した。
裁定パッケージ V1〜V5 = `output/insights/2026-08-13_t139-q1-canonical-decision/package.md`。

**指示文の要約に誤りが 1 件あった。** 指示は Q1 (a) を「固定 envelope + namespaced projection」と
書いていたが、canonical worklog エントリ 516 の逐語では**それは Q2 (a)** であり、**Q1 (a) は
受理述語の穴 4 件を 1 本の canonical decision で閉じること**である。`DW-S01` の F31 に従い本文を
採り、両方を 1 本に収める方針とした。レンズ B が独立に照合してこの解決を追認した。

**止めた最大の理由は D320 の例外範囲がユーザー未裁定であることである (V1)。**
時系列を実測すると、第 7 束 (2026-08-13 00:0x〜00:1x JST) は D320 も K1 も名指ししておらず、
K1 (D320 と Q1/Q2 (a) の衝突) が起票されたのは**その 2 時間後** (02:0x JST) で、一度も
ユーザーへ問われていない。**そして本 wave の起草で、衝突が回避不能であることが初めて実証された** —
B1 を閉じるには `record_items` / `receipt_schema` role を supersede する新しい exact-byte
approval payload が要り、これは D320 が列挙する「commit への束縛」そのものである。
作らずに閉じる案は (a) validator を常時拒否 = 受理集合が空 (R3 (a) が禁じた当のもの)、
(b) §7.1(12) の CMakeCache leg を落とす = 受理述語の弱化 (絶対規律 2 違反) の 2 つしかない。

**親の段 1 暫定裁定 (P2) は誤りだった。** 正しくは 2 層に分かれる。approval manifest **そのもの**は
新設物ではない — D320 の**前日**に D282 が exact bytes 承認した schema の**必須 field** であり
(`preregistration.required` に `approval_manifest`、型 `blobRef`)、§7 と §7.1(19) が 2 箇所で明示的に
要求している。**しかし新 approval payload と conformance vector の digest pin は D320 の列挙に
該当する。** 前者だけを根拠に「D320 の射程外」と書くことはできない。

**B1 は「欠落」ではなく承認済み 2 文書の矛盾であることが分かった。** §7.1(12) は CMakeCache の
再読を validator の必須責務と定めるが、schema が持つ CMakeCache 由来の値は 2 boolean の申告値
だけで、§8 はその field を受理条件の入力に使うことを名指しで禁じ落ちるテストを要求している。
**使ってよい唯一の入力が、使ってはならないと書かれている。**

**起草が踏んだ落とし穴 4 件を次 wave の必須要件として記録した。**

- **承認済みの数値契約を書き直していた (blocker)。** 起草は transcript の数値を `2^-80` 格子の
  dyadic 区間としたが、承認済み追補 A は認証区間を `p_k^U − p_k^L ≤ 1e-9` の外向き丸め区間演算で
  固定し、`J` の選択規則と `design_not_feasible` の条件まで書いている。レンズ B が検出し、
  親が `addendum-a-reissue.md:724-748` を直接読んで確認した。canonical に書けば `J` と
  main の `consumed_cluster_slots` 要素数が動く。
- **§8 の禁止を「単独では使わない」へ弱めていた (blocker)。** 承認済み §8 は単独か併用かを
  区別していない。この言い換えを canonical に書くと、engine ごとに受理集合が分岐する。
- **実在しない field 名で契約を書いていた。** `correctnessCompile` の field は `configure_argv`
  ではなく `argv` である。**直前 wave の K4 と同型の事故が、同じ T-139 系列で独立に 2 度目。**
- **D234 (iii) の祖先 root が二義的だった。** `F_r*` を選ぶと固定 core ref が条件を満たせず、
  全 receipt が恒久拒否される。

**refuted にしたもの:** 「既存承認 blob を in-place 書換えする案になっている」「D292 を暗黙解除して
いる」「Q1/Q2 を取り違えている」「`submission.py` に short-write 検査と fsync が無い」
「D305 が単一 role 公開 API を要求している」の 5 件。特に最後から 2 番目は親も実測で確認した —
`orchestrator/qualification/submission.py:143-164` に `O_EXCL` + `O_NOFOLLOW` + 書込みループ +
file `fsync` + directory `fsync` が実在し、欠けるのは read-back 検証だけである
(直前 wave の K4 の判定が現物で裏付けられた)。

**scope 外の real 所見を 1 件返した** (`s1-startup-gate-deadlock.md`)。
**main が全 background job wave の起動 gate を恒久的に赤にしている。**
`docs/handoff/2026-08-13-known-red-octopus.md` は commit `aedc04ec` (05:18 JST) で main に
tracked のまま復元された — land が `docs/handoff/` 直下の削除を rc=21 で拒むためである。
一方 `DW-O20` が背景 job に必須とする `check_wave_startup.py --external-handoff` は
`--forbid-worktree-handoff` を含意し、同 path に README.md 以外があると rc=1 になる。
**main 単独で再現する。** 本 wave は untracked handoff を 1 件も作っておらず
(`git status --short docs/handoff/` = 0 行)、`DW-O20` の趣旨は満たしているため本 wave 由来としない。
**この判断自体もユーザー裁定へ返す** — `DW-STOP` を親の裁量で越えたと読まれうるためである。

**工数と異常:**
- codex 子 3 本 (plan 1 / consult 2)。実装子ゼロ (docs-only)。所要は plan 20 分、consult 14 分。
- **待ち手が producer 生存・成果物不在のまま exit 0 を返す事象を再度観測した** (F282 の独立 2 例目)。
  3 点照合 (成果物実在 + `.done` + producer 死) で捕捉し、親側で照合する待ち手を自作して回避した。
- 起草前に `check_docs.py` と `spool_fold.py --dry-run` を骨格 fragment で通し、
  形式経路を先に検証した (ともに rc=0)。fold の暫定採番が並行 land で D378 → D379 とずれることも
  実測した。

**前回 wave との差。** 前回 (land2-q4) の NO-GO は「どちらの裁定が有効か」という手続の問いだった。
本 wave は**実際に起草して独立に攻撃させた**ため、返す問いが具体になった — D320 の例外範囲を
`F_r*` / manifest fold root / vector digest pin の**対象ごと**に問え、回避経路が無いことが
実証され、起草が踏む落とし穴 4 件が次 wave の brief にそのまま入る。

## 次の一手差分

### 更新

- [T-139] **P1・ユーザー裁定待ち (V1〜V5)**: 第 7 束 Q1 (a) の canonical decision を起草したが、
  **D320 の例外範囲が未裁定**であることが実証されたため実装差分ゼロで返した。V1 = D320 の既定を
  T-139 の 3 対象 (approval manifest / 新 exact-byte approval payload / conformance vector の
  digest pin) のどれについて上書きするか。V2 = B4 の数値契約は追補 A を参照束縛するだけにするか。
  V3 = B1 の申告値を常に受理入力から外すか。V4 = conformance vector index の trust edge を
  approval payload 側へ置くか。V5 = Q1 と Q2 を 1 本に収める構成を維持するか。
  正本 = `output/insights/2026-08-13_t139-q1-canonical-decision/package.md`。
  **pilot / 本走は依然として投入不可** (D292 は 1 bit も動いていない)。
  base: 5da2584f1ace2e58ba03aaf991b94b01bfb57a9cd5af599be835adbe69a4e72f

### 新規

- {{T:devwave-startup-gate-vs-land-handoff-protection}} **P1・新規**: main の `docs/handoff/`
  滞留ファイルと land の control-plane 保護が衝突し、2026-08-13 05:18 JST 以降に起動する
  background job の dev-wave はすべて `check_wave_startup.py` が rc=1 になる。main 単独で再現する。
  裁定候補 = `output/insights/2026-08-13_t139-q1-canonical-decision/s1-startup-gate-deadlock.md`
  (S-1 起動 gate 側を直すか land 側を直すか、S-2 `docs/handoff/README.md` の削除契約を是正するか)。
