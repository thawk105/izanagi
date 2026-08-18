---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1162-flock-premise
seq: 1
title: D130 条件 2 は同種の排他の運用前提では閉じない — 残っているのは flock の可否でなく 1 host pair からの一般化で、設計で閉じる道は D216 が既に塞いでいた (docs のみ、branch worktree-dev-wave-t1162-flock-premise、変異 matrix = 実装差分ゼロにつき免除)
---

## 本文

- **条件 2 に残っているのは「cross-node flock が効くか」ではなかった。** [T-361] (bnode001/005) と
  [T-402] (bnode003/004) の 2 回で `/work`・`/home` とも 6/6 `BLOCKED`、`localflock` 無し、
  [T-402] は Execution Host 照合まで通って `dangerous: false` が確定している。
  残るのは **1 host pair から全 pair への一般化**であり、裁定が測定増 (a) を却下した理由と一致する。
  (a) は資源上も機械的にも塞がっている — sanctioned probe driver の
  `FLOCK_LEG_ONLY_SUBMISSION_LIMIT = 1` を [T-402] が 1/1 消費済みで、再走には gate 定数の
  引き上げというユーザー裁定が要る。
- **親が段 1 で描いた「設計で閉じる」道は D216 と正面から矛盾したので撤回した。** 親は
  「注入先の一意性は `_claim_fresh_container` の atomic な `mkdir` が与えるので flock に依存しない」
  と考えたが、D216 は「lock は `--out` へ束縛する。harness の `flock` は repo 絶対 path 由来なので、
  scratch を変えると分裂し、同じ台帳を後勝ちで上書きできる」として、producer 一意性の authority を
  `<out>.lock` = flock に置くと既に決めていた。**`--resume` 枝は atomic claim を一切行わず、
  効く排他は外側の `_out_lock` だけ**であることも実コードで確かめた。
- **代替案として親が挙げた「束ねでは wrapper 経由必須」も既に却下済みだった。** D216 の却下選択肢に
  「機械的 admission が無い状態の『必須』は prose-only であり、旧 direct 経路も台帳 consumer も
  拘束しない」とある。runbook §7.4 の本走 recipe は現に wrapper 非経由の直接起動である。
- **[T-565] の前提は「適用できない」ではなく「適用可否未確定」へ格下げした。** 段 3 レンズ A が
  親の判定を弱めた — 述語を「一つの logical run に node を跨ぐ active owner は一つだけ」と置けば、
  束ねは harness 全体を 1 job に収めるため、retry / resume を重ねない運用なら同型に読める。
  この可否は**ユーザーの運用意思にしか無い**ので、1 問だけ問い返す形で裁定へ返した。
- **親の実測の一般化を 1 件撤回した。** M4 で F203 を「同一 checkout への二重注入の実発生例」と
  書いたが、F203 が共有したのは wave worktree と job dir であって変異 checkout ではない。
  段 3 の 2 レンズが独立に同じ誤りを指した。直接的な資料は F32 である。
- **段 3 は 2 レンズとも独立に否定側で返した** — レンズ A が NO-GO・must-fix 8、
  レンズ B が hold・must-fix 7。**refuted はゼロ**で、親は 15 件すべてを real と裁定した。
  両レンズが独立に重複指摘したのは 3 点 (親の第三の道が裁定の分岐外、wrapper 必須化は
  発火しない保証、F203 の誤一般化)。
- **本 wave が自ら走らせた runtime 測定はゼロである。** 証拠はコード読解と台帳読解、および
  過去 wave の runtime 実測の引用であり、記録でもこの区別を保つ。段 3 レンズ B の指摘による訂正。
- **セッション事象 2 件。** (1) レンズ A の初回走行は codex が自然終了 (rc=0、41 model call、
  673 秒、9983 bytes) したにもかかわらず、出力に Web 検索由来の外部 URL が含まれ evidence chain が
  invalid で不受理になった。Web 禁止を明記して再走し受理された。結論は両走とも同じ NO-GO。
  (2) 待ち手が producer 生存中に rc=0・出力ゼロで終わる事象が 3 度あった。**親は当初これを
  `tools/dev_wave_wait.py producer` の欠陥と判定したが、撤回した** — 全終了経路で必ず出力する
  自作 polling script でも同じ形 (rc=0・出力ゼロ) になったため、原因は待ち手ではなく
  **背景 process が外側で終了させられて rc=0 と報告される**ことである。機構欠陥として
  台帳へ書かない。生存判定は pid の直接確認で行った。
- **エージェント工数**: codex 子 3 本 (consult 3、うち 1 本は evidence 不受理)、いずれも
  `reasoning=max`。受理された 2 本は 674 秒 / 41 model call と同程度。実装子は無し。
- 設計判断は {{D:bundle-flock-premise-not-transferable}}。
- 正本 = `output/insights/2026-08-18_t1162-flock-premise/README.md`

## 次の一手差分

### 更新

- [T-1162] **P2・ユーザー裁定待ち (再提示)**: D130 条件 2 は択 (b) では閉じない。
  同種の排他 ([T-565]) の運用前提は述語が違い、そのまま適用できない。設計で閉じる道は
  D216 が producer 一意性の authority を `<out>.lock` (flock) に置いており、
  wrapper 必須化も同 D で却下済みなので塞がっている。**問い返しは 1 点** — 束ねた変異 job で、
  同一 spec / 同一 `--out` に対する retry と `--resume` をノード跨ぎで同時に走らせない運用を
  約束できるか。約束できるなら [T-565] と同型に閉じられる ((b'))。できないなら、
  (c-1) 条件 2 を supersede して一意所有 + exact 照合へ置換 (D216 の改訂を伴う)、
  (c-2) 射程を `_out_lock` と resume 経路へ縮小、(d) 束ね自体を当面見送る、の 3 択。
  親の推奨は「(b') が使えるならそれ、使えないなら (d) で保留し、transport を進める時点で (c-1)」。
  材料は `output/insights/2026-08-18_t1162-flock-premise/README.md` §4・§8。
  base: 305f48c1162e8b456c4af469d435093c6d154aca7be8dd6855ea91519c437bf4

### 新規

- {{T:codex-web-search-machine-block}} **P2・新規**: read-only codex 子の web 検索を
  **機械的に禁止する**。F217 の恒久対応は「子 prompt に web 検索禁止を明記する」だが、
  2026-08-11 の再発時に `DW-O05` への追記が dev-wave docs の予算で入らず見送られ、
  以後は書き手の記憶だけが担っている。2026-08-18 に 3 度目が発生し、レンズ 1 本
  (673 秒・376 万 token) を丸ごと失った。候補は (a) `tools/dev_wave_codex.py` が
  生成 argv 側で web 検索を無効化する、(b) `tools/codex_worker_launch.py` の stdout 解析が
  重複キーを許容する (F217 の根本原因側)、(c) launcher が prompt へ禁止文を機械挿入する。
  いずれも実装面なので Codex author が要る。**予算を理由に安全義務を落とした形が
  3 度実害を出しているため、docs 追記でなく機構側で閉じる。**
