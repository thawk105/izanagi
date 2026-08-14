---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t1076-waiter-bytes-contract
seq: 2
---

## {{D:waiter-executed-bytes-gate}}. 受入投入前に待ち手の束縛 source bytes と新 tip の blob を照合する

**決定:** `tools/dev_wave_wait.py` の acceptance 経路は、受入 command を投入する直前
(prerun fingerprint 確定後、`run_logged` の前、merge の有無に依らない共通経路) で、
module 初期化直後に束縛した自 source inode の bytes の sha256 と、
`<prerun tip>:tools/dev_wave_wait.py` の blob 内容の sha256 を照合する。
不一致および照合不能はすべて stage `restart-required` (rc=70) で停止する。

**保証の範囲を狭く定める。** この契約が主張するのは「canonical direct 起動、または origin が
束縛 source と同一 inode を指す file loader 経由で、**module 初期化直後に束縛した source inode の
bytes**」であって、Python が compile した bytes そのものではない。loader が source を読んでから
module-level で FD を束縛するまでの窓は、同じ file 自身の中では消せない。
gate 導入より前に起動された process も本契約の被覆外である。

**理由:**
- 既存 receipt field `waiter_blob_sha` は、発行側も land 側も同じ tip の tree から算出する。
  実行体の検査としては恒真であり、旧コードのまま新 main を merge した待ち手を区別できない。
- 実行体を観測する既存機構は無い。`_behind_count` は commit 数、tree fingerprint は tree の状態、
  D254 の全史 provenance 関門が束縛するのは provenance checker であって待ち手ではない。
- 照合不能を通す設計にすると、束縛できない環境が検査回避の抜け道になる。停止側へ倒す。

**却下した選択肢:**
- claim 前に main の blob と比較する早期照合 — 待ち手は wave 版を実行するため、同 file を編集する
  wave では main 版と恒久的に不一致になり、その wave の受入を永久に拒否する。
  照合対象は merge 後の固定 tip でなければならない。
- pathname の現 inode 同一性を合否条件に含める — 待ち手は自分を再実行しないため、pathname が今
  どの inode を指すかは「何を実行しているか」に影響しない。同内容の原子的置換まで拒否する
  過剰拒否になる。束縛時の symlink / 非 regular 検査と、読取中に束縛 FD の bytes が動いた場合の
  拒否は維持する。
- 起動形を `__spec__ is None` に限定する — origin が束縛 source と同一 file を指す file loader
  経由のロードは、照合対象の source を曖昧にしない。一律拒否は安全性を足さず、正当な走行を止める。
- receipt に実行 bytes の sha256 を field 追加する — gate 通過が「実行 bytes == その tip の blob 内容」を
  含意するため冗長で、schema 昇格自体が同型の事故源になる。

## {{D:waiter-gate-rollout-not-by-schema-cutoff}}. 契約の rollout 被覆は receipt schema の世代交代で強制しない

**決定:** 上の gate を持たない旧 process を機械的に締め出す目的で、受入 receipt schema を
互換なしで上げ、land 側を新 schema のみ受理へ切り替えることは行わない。
残るのは rollout 被覆の窓 (gate 導入前に起動された process) であり、これを契約の一部として
完了形で報告せず、窓の存在と fresh process からの再投入手順を runbook へ明記する。

**理由:**
- 裁定された契約は「受入投入前に照合して止める」ことである。schema の世代交代は別機構であり、
  受理集合を変える範囲が裁定文を超える。
- schema cutoff は投入前に止めない。旧 process を通常どおり走らせ、実測 318〜2755 秒を消費させた
  **後に** land で拒否するだけである。契約の強化版ではなく、より遅くより高価な別の関門である。
- 並行 wave が常時複数走る運用では、cutoff の瞬間に走行中の receipt と、cutoff 前に完走していた
  受領証まで一律失効する。狙った母集団と無関係な巻き添えが大きい。

**却下した選択肢:**
- 排水方式 (旧 process が全て終了してから世代交代する) — 並行 wave が常時あるため窓が来ない。
- activation tip による grandfather (land は旧 schema の受領証を、その tested tip が gate 導入 commit を
  含むときだけ拒否する) — 巻き添えが無く、狙った母集団だけを正確に落とせる。本 wave では
  実装しないが、rollout 被覆を閉じる案としては最も筋がよい。gate 導入 commit の sha は
  その commit を作る前には書けないため、2 段活性化が要る。設計裁定はユーザーへ返す。
