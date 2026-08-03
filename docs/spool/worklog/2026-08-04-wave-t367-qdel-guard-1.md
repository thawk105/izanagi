---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t367-qdel-guard
seq: 1
title: [T-367] 走行中ジョブへの qdel を fresh qstat gate で禁じる — 敵対検証で blocker 4 件を land 前に閉じた (コード + docs、branch worktree-wave-t367-qdel-guard)
---

## 本文

- ユーザー裁定 (b) ((138) で確定) を実装した。commit `6d311b1` (実装)、`cbe4867` (逐語)。
  `dispatch_compute` の 4 つの qdel 経路を `_fresh_qstat_gated_qdel()` へ集約し、
  直前の fresh qstat が「rc=0 かつ対象 request が一意に可視かつ状態が QUE/HLD」の
  ときだけ qdel を発行する。設計判断は {{D:fresh-qstat-gate-scope}}
- **敵対検証で blocker 4 件を land 前に閉じた。** 段 3 の 2 レンズと段 6 のレビュー 2 本 +
  焦点再レビュー 2 回が独立に出したもの。(i) 対象 request と状態を同じ block に束縛せず
  malformed な rc=0 応答で RUN を QUE と誤判定できた (両レンズが独立に指摘)、
  (ii) qdel 後の signal に once-only latch がなく二重発行と結果喪失が起きた、
  (iii) gate scanner の空白 grammar が既存 parser と不一致で制御空白付きの state 行を
  見落とした、(iv) state 値の語彙を field 種別に束縛せず `Request State = Queued` のような
  交差形を取消可能と誤判定した。いずれも実装子の自己申告では closed とされており、
  **独立レビューがなければ land していた**
- **親の provisional 裁定 (P2) は敵対レビューに反証されて撤回した。** 「gate の qstat は
  1 回でよい (immediate retry は可視性遅延用だから)」という根拠が事実誤認で、実コードは
  非ゼロ transient だけを retry していた。transient 限定 bounded retry へ改めた
- **親の実測 3 件は射程が過大だったため brief を訂正した。** `test_overall_walltime_..._qdels_running_job`
  が緑であることは「fake scheduler が qdel command を観測した」ことの実証であって、
  実 NQSV が RUN 中の job を削除する証拠ではない (**実機 kill は未実測**)。
  production caller は `run_tests.py` だけでなく `check_ai_provenance.py` もある。
  campaign 本走は現行 task enum (`tests` / `provenance`) を通らないため、現在の直接影響は
  開発テストと provenance の transport 証拠に限られる
- **変異 12 件は SURVIVED ゼロ。** 初回 11 件で KILLED 6 / MISMATCH 5。MISMATCH のうち 4 件は
  期待 node ⊆ 実際の赤 node で、登録が控えめだったことによる。**M08 (過剰拒否の正例検出) は
  親の登録が実効 gate を突いていなかった** — `gate["allowed"]` は receipt の記録用 field で
  qdel 実行を止めないため、変異が「常時拒否」になっていなかった。`DW-M02` に従い初回結果を
  erratum として残し、`if state not in {"QUE","HLD"}` を常時拒否へ変える M08R へ再照準して
  再走し、22 テスト (期待 5 件をすべて含む) が赤になることを確認した。
  台帳 = `output/insights/2026-08-03_t367-qdel-guard/mutation-ledger.json` と同 `-2.json`
- **この実装が保証しないこと** (過大な保証を書かないため明記する)。
  (i) qstat と qdel は atomic でないため「qdel 時点で RUN でない」ことは保証しない。
  保証は「直前 snapshot が取消可能だったときだけ発行する」まで。
  (ii) gate が見送った job は孤児として残る。これは裁定 (b) が受け入れた帰結である。
  (iii) receipt 永続化中・直後に来た signal は disk 上の receipt に反映されない競合窓がある。
  (iv) 実 NQSV に対する kill / 非 kill は未実測 (fake scheduler での検査のみ)
- **受入全走は 5430 passed / 19 skipped / 1 failed。** 赤は
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`
  で、原因は別セッションが commit した非 UTF-8 blob (`2026-08-03_t361-t362-cluster-probes` の
  probe evidence) を `ruleops.py inventory` が拒否すること。**local main `3d24878` に存在し、
  本 wave の 2 commit は ruleops にも当該 evidence にも触れていない**ため差分に帰属しない。
  単独再走でも再現したためフレークではない。新規項目として起票する
- 工数: codex 子 12 本 (plan 1 / 敵対レンズ 2 / 実装 1 / レビュー 2 / fix 3 / 焦点再レビュー 2、
  他に変異 harness の dispatch 13 job)。段 6 は fix 3 巡で `DW-O16` の上限に到達した
- **段 8 の自己改善候補 2 件は `docs/dev-wave/**` の合計 byte 予算 (25,200 に対し現在 25,196) が
  塞いだ。** [T-369] (b) と同型の 2 例目であり、`DW-G03` の独立 2 例を満たす。候補は
  (i) `DW-M01` へ「記録 field でなく受理集合を実際に変えることをコードで確認する」を足す
  (本 wave の M08 登録誤りが実測。`DW-M08` の診断 pin 判定を登録時に前倒しする意味の明確化)、
  (ii) `DW-M05` へ「変異 harness の実行中に親の受入全走を重ねない」を足す
  (同じ checkout を一時変異するため全走が変異版を読みうる。本 wave で 1 度重ね、
  赤の帰属切り分けに全走 1 回 4.5 分を要した)。**縮約では 52 bytes を意味等価に空けられず、
  dev-wave 系の外出しは D94 却下案 (a) として既出**のため、予算の再配分はユーザー裁定へ返す

## 次の一手差分

### 完了

- [T-367] fresh qstat gate を 4 経路へ実装し、敵対検証と変異で裏取りして land した。
  保証の射程と残余リスクは本文に明記した。
  remaining: none
  base: 8eadde755aef3784c31ba20d304aae7f27422e0c0888cc07191cc253f98acf21

### 新規

- {{T:orphan-job-reconciliation}} **P1・新規**: gate が qdel を見送った孤児 job の後始末。
  現在は receipt と人間向け警告を出すだけで、次回投入・source 復元・worktree 廃棄を止めない。
  `mutation_harness` が runner 終了後に source を復元するため、孤児が復元後または次変異の
  source を読むと変異台帳の実行実体と記録が食い違う。[T-368] と同じ束
- {{T:qdel-target-discovery-identity}} **P2・新規**: request ID discovery が job name 先頭
  10 文字と submission-dir 部分一致の**一方**だけで候補を確定する。同じ nonce 接頭辞を持つ
  旧 job を誤って対象にしうる。exact request-name と exact path field の双方要求へ狭める案
- {{T:guarded-qdel-proof-chain}} **P2・新規**: `qdel.attempted=true` かつ `gate` 不在の
  v2 receipt は「旧 unconditional 実装 / gate bypass / 新実装」を区別できない。
  本 wave では `cleanup_policy` を必須化したが、schema 版管理と scheduler executable identity
  までは含めていない。[T-366] と近接
- {{T:receipt-persist-signal-window}} **P3・新規**: receipt 永続化中・直後に到着した signal が
  disk 上の receipt に反映されない競合窓。閉じるには receipt 永続化の atomicity が要る
- {{T:ruleops-non-utf8-blob-red}} **P2・新規**: `ruleops.py inventory` が repo 内の非 UTF-8 blob
  (probe の raw 出力) を拒否し、受入全走が 1 件赤になる。main `3d24878` 時点で発生。
  ツール側で binary blob を skip するか、probe evidence の保存形式を改めるかの択一
