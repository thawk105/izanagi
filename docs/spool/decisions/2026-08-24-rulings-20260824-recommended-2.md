---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: rulings-20260824-recommended
seq: 2
---

## {{D:floor-rescue-recovery-event-ruling}}. 8b は外部証拠と fencing を備えた専用 recovery event で死んだ attempt を引き取る

**決定:** 計測 process の消失で terminal を書けなくなった 8b attempt は、別 process が
scheduler accounting 等の外部証拠を検証した場合に限り、専用 recovery event で引き取れるようにする。
event は 8b だけに許可し、誰が stale を宣言できるかを fencing で制限する。共通 core へ明示的な
semantic handler を実装し、event 名を profile の許可表へ足すだけの実装は認めない。

**理由:** 現行の owner 束縛では、PBS の時間切れ・node 障害・SIGKILL で分類主体そのものが消えると
attempt が永久に未完了になる。これは D496 の「行き止まりを作らない」と D510 の事前割当再走を
実現不能にする。一方、owner 束縛を全体で緩めると 8c の受理集合まで広がり、D672 に反する。

**却下した選択肢:**
- terminal の owner 束縛を全体的に緩める — 8c を含む既存の受理集合を広げる。
- 引き取りを作らない — 落ちた構成を測り直せず、既裁定の救出経路が成立しない。
- profile の event 表だけを増やす — semantic 未実装 event が terminal として扱われた実測済みの穴を再導入する。

## {{D:floor-rescue-estimand-ruling}}. 観測開始後の再走は外因性を外部証拠で確認できる失敗理由だけに限る

**決定:** 観測開始後に落ちた反復は、性能と独立な外部要因を信頼側の外部証拠で確認できる場合だけ、
次 attempt の値を主値へ昇格できる。対象は node 障害と scheduler による外部中断の閉じた集合とし、
wall timeout、単なる PID / process 消失、自己申告だけの失敗は含めない。実装前に理由の exact 値と
証拠源を凍結し、分類は性能出力を読む前に create-only 受領証へ残す。

**理由:** すべて永久欠測にすると事故 1 回で cell が行き止まりになる。すべての次 attempt を採ると、
完走しやすい run の条件付き性能へ estimand が変わる。wall timeout は遅い run ほど起きやすく、
性能との相関を除けない。外因性を証明できる理由だけに限れば、行き止まりを減らしつつ
結果を見た後の再走選択を防げる。

**却下した選択肢:**
- すべて永久欠測にする — 統計的には保守的だが D496 の行き止まり禁止に反する。
- 次 attempt を理由を問わず主値へ昇格する — 元の床値と同じ量だと主張できない。
- wall timeout や単なる process 消失を retryable にする — 性能との相関または証拠不足を除けない。

## {{D:s8c-terminal-reason-tightening-timing}}. 8c の分類理由と terminal 理由の一致検査を次の正式利用前に必須化する

**決定:** 8c の既存成果物と今回の互換 facade の受理集合は遡及変更しない。一方、次の正式 8c 走行または
凍結世代更新より前に、事前分類受領証の失敗理由と terminal の再走理由の一致検査を必須化する。
それまでは現行経路を新しい正式証拠の生成に使わない。

**理由:** 現行 8c には、分類時に失敗理由なしで封印し、性能値を見た後で retryable 理由へ付け替えて
次 slot を得られる実在の reward-hacking 経路がある。直ちに互換 facade の受理集合を変えると
D672 の実装条件を後から破るが、期限なしの現状維持は絶対規律 2 に反する。版境界で締めれば、
過去成果物を保ったまま次の正式利用を安全にできる。

**却下した選択肢:**
- 今回の互換抽出へ遡及して即時に締める — D672 が要求した受理集合不変を破る。
- 期限を置かず現状維持する — 値を見た後の再走選択を正式系列へ残す。

## {{D:known-violation-active-zero-metric}}. known-violation は不可逆な歴史群と新規群を分け、新規増加ゼロを目標にする

**決定:** known-violation の総数 0 は目標にしない。過去 commit の不変な違反を「不可逆な歴史群」として
固定し、現在の契約下で新しく生じた違反を別群で数える。運用目標は新規群 0 とし、新規登録は
従来どおり高優先度で解消する。遡及訂正枠の一回性は解除しない。

**理由:** 既存違反の大半は履歴を書き換えない限り消せず、総数 0 の唯一の実現手段は監査文法を緩めるか
遡及訂正機構を恒久的に開くことになる。どちらも監査の意味を薄める。新規増加 0 は現在の機構を
緩めずに制御でき、生成器修理の効果も測れる。

**却下した選択肢:**
- 総数 0 のため遡及訂正枠を再開する — 「後から補記すれば通せる」恒久経路を作る。
- 文法を緩めて既存違反を通す — 違反当時から有効だった正しさ gate を後退させる。

## {{D:known-violation-entry-storage-ruling}}. known-violation の entry 単位格納は独立検査を同じ wave で置換する条件で認める

**決定:** known-violation 台帳を 1 finding 1 file の entry 単位格納へ移してよい。既存の独立した
逐語 literal mirror は単純削除せず、同じ実装 wave で次の検査へ置換することを着手条件とする。

- 複合 key、filename と本文の一致、重複・未知・欠落 key の厳格拒否
- tracked な regular file だけを読み、symlink・untracked・ignored と HEAD 不一致を拒否
- データ directory 自体を実装面として分類
- 既存全 entry の実 commit finding との照合と、公開 stdout の逐語検査
- 投影外 consumer の byte / literal pin を含む read-only 閉包確認

同じ finding の並行登録競合は fail-closed のまま残し、競合ゼロを保証しない。

**理由:** 単一 Python tuple と逐語 mirror の共通末尾は、並行 wave の競合と手解決による新しい違反を
反復生成している。一方、逐語 mirror は受理判定が読まない ruling / note の改変を検出する独立防壁で、
代替なしに畳むと裁定根拠を偽造・消去できる。上記検査を同時に置けば、防壁を保ちながら共通編集面を減らせる。

**却下した選択肢:**
- 現状維持 — 台帳編集由来の違反生成器を温存する。
- 逐語 mirror だけを削除する — 正しさ防壁の単純な弱化になる。
- データを docs-only 面へ置く — Codex author 契約の抜け道になる。
