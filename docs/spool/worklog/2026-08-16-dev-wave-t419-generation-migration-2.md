---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t419-generation-migration
seq: 2
title: 環境契約 g2 の活性化を止めた — 既裁定の人間 lockstep と、活性化しても実行時受理が変わらない実測 (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t419-generation-migration)
---

## 本文

- **ユーザー裁定 (2026-08-16 一括裁定、authority: ユーザー) の実施 wave として開いたが、
  実装差分ゼロで止めた。** 裁定は D143 決定 (3) 択 (b)「述語を正とし、較正を取り直して
  登録し直す + 取得時受入検査」と、床値 v2 の再測定を世代移行と同一 chain に限る条件である。
  控えは wave 外の裁定 inbox にあり、canonical へは別 branch が land する。
- **止めた理由は、裁定時の未見事実である。** D272 と較正・凍結の権限束設計は
  2026-08-10 / 2026-08-11 のユーザー裁定で **(i) 環境世代と凍結世代の lockstep
  (片側交代は却下済み)、(ii) 上位束の承認と発効はともに人間**と確定している。
  同設計は段 0 が未完了で、上位 cancellation record の扱いがユーザー裁定待ちである。
  8/16 の裁定控えは上位権限束に一度も言及していない。
  したがって「AI が単独で環境側だけ発効してよい」は 8/16 時点でユーザーが見ていない。
  設計判断は {{D:env-generation-activation-is-human-lockstep}}。
- **裁定のうち 2/3 は既に land 済みだった。** 「較正を取り直す」は第 2 世代の較正が
  取得・登録済み (`quality.status=accepted`、計算ノード実測、48 標本すべて定格) であり、
  「取得時受入検査」も acquisition 経路に 4 箇所 (benchmark 前・後・publish 時 policy 同一性・
  publish 後 bytes 再読) 実装済みだった。**未実施は「登録し直す」= 活性化だけである。**
- **親が段 1 の前提を 3 件、自分で反証した。** (a) 「移行しなければ計算ノードで何も走らない」は誤り
  — canonical clock 述語は期待列の中央値だけを使い、帯検査は観測列にのみ適用するため、
  第 1 世代と第 2 世代で受理帯が完全に一致する。(b) 壁を開けたのは較正の再登録ではなく
  probe 側の巡回方式の結線である。(c) 「世代機構は実装済みで未実施は活性化だけ」は
  上位権限束と protocol 世代 authority の未完成を落とした過度な一般化だった。
  親が段 3 へ渡した対案「活性化を先に。移行前の方が悪い」も、親の実測と敵対レンズが
  独立に反証したため取り下げた。
- **恒真ゲートを 1 件見つけた。** attestation receipt の `effective_clock.method` は
  比較 field として並んでいるが、判定は「両方が非空 str」だけで値の一致を見ない。
  第 1 世代の期待側は素朴法、実行時観測は巡回方式であり、**実体不一致が pass として
  記録されていた**。是正は受理集合を縮小し、活性化前に入れると全 attestation が落ちるため、
  裁定パッケージへ従属項目として返した。{{F:effective-clock-method-vacuous-comparison}}。
- **F10 の再発を 1 件登録した。** pin 前進で参照が腐る構造が、runbook ではなく
  **凍結証拠の完全検証入口**で実現していた。silo の公開検証は今日すでに赤で、
  原因は module 定数側の pin 前進と証拠側 pin の据え置きである。
  環境契約世代の前進でも同型が起きることを本 wave が実測しており、producer も consumer も
  異なる独立 2 例が揃った。「凍結成果物は記録時の値で検証し、live 適格性は別 API で検査する」の
  族一般化は `DW-G03` の閾値を満たす。
- **敵対 2 レンズはともに NO-GO を返し、親の裁定と一致した。ただし理由は同じではない。**
  レンズ A は上位権限束との衝突・歴史 resolver が自己不整合較正を検証済み扱いにする穴・
  seam を receipt に選ばせると受理集合が広がることを挙げた。
  レンズ B は g2 protocol を発行する sanctioned 経路の不在・活性化の不可逆性を挙げた。
  **親はレンズ B の「silo 完全検証が壊れる」を実走で反証した** — 当該入口は今日すでに赤であり、
  正しい severity は「同じ入口に 2 つ目の不一致が加わる」である。
- **安全な部分実装も 4 案すべて不採用にした。** 既知例外の走査領域を広げる案は、
  現時点で ever-active 集合と active 集合が一致するため検査内容が 1 bit も変わらず、
  走査領域を戻す変異が必ず生存する等価変異になる。世代混在の束縛は発火条件を満たす
  artifact path が無い。恒真ゲート是正と seam は上記のとおり単独では入れられない。
- **工数:** codex 子 3 本 (plan 1 / consult 2)。実装子は起動していない (実装差分ゼロ)。

## 次の一手差分

### 更新

- [T-419] **P1・ユーザー裁定待ち (新しい問。2026-08-16 の実施 wave が実装差分ゼロで止めた)**:
  凍結 protocol の contract hash pin を世代列への照合へ変える方針 (2026-08-12 /rulings、(b)) は不変。
  **問: 環境契約の第 2 世代を、較正・凍結権限束の完成を待たずに発効するか。**
  択一は (a) 待つ = 権限束を完成させ、既裁定どおり lockstep かつ人間の承認 / 発効で発効する
  (親の推奨) / (b) 環境側だけ先に発効する = D272 が名指しで却下した片側交代を本件に限り解除する /
  (c) 上位束を待たず seam と検査網の補強だけ先に land する。
  従属して裁定を要する項目が 3 件ある — (i) `effective_clock.method` の恒真比較を実体一致へ
  変えるか (受理集合の縮小)、(ii) 自己不整合な旧較正を歴史 resolver が検証済みとして
  受理し続けてよいか、(iii) 第 2 世代を active にする根拠を `quality.status=accepted` だけに
  置いてよいか。
  **止めた理由**: 環境世代の単独交代は D272 と較正・凍結権限束の既裁定
  (lockstep + 承認 / 発効はともに人間) に反し、同設計は段 0 が未完了でユーザー裁定待ちを
  1 件抱えている。8/16 の裁定控えは上位権限束に一度も言及していない。
  **急ぐ根拠は無い** — 実測で、活性化は実行時の受理挙動を変えない
  (第 1 / 第 2 世代で clock 受理帯が完全一致)。
  一次資料 = `output/insights/2026-08-16_t419-generation-migration/` (択一の全文は
  `s4-adjudication.md` §6、実測は `parent-measurements.md`)、
  設計判断 = {{D:env-generation-activation-is-human-lockstep}}。
  base: 5261447d65a68df7143d7f86da2181831d4ab821235aaea84927c9f97ff742dd
- [T-420] **P2・着手条件は依然として未成立 → 上位権限束の完成待ち**:
  「U-2 着地後に driver を再走させる」という下流関係は不変。
  ただし 2026-08-16 の実測で、**U-2 が塞いでいるのは実行時 attestation ではない**ことが判明した
  — canonical clock 述語は期待列の中央値だけを使うため、較正を再登録しても受理帯は変わらず、
  壁を開けたのは probe 側の巡回方式の結線である。
  U-2 が実際に開けるのは、certified receipt が自己不整合な較正と実体不一致の計測方式を
  記録し続ける状態の解消と、床値 v2 の chain である。
  base: aeb5c890511686d1bd79d5ded78a14b078c539e2cd3a53e5e085da6dc1166658
- [T-475] **P2・予言した破綻を実測で確認 → 設計は上位権限束へ合流**:
  凍結 floor protocol は、環境世代を進めると **歴史検証は通り live admission が拒否する**
  ことを worktree の一時変異で実測した (移行前は両方とも通る)。
  同様に新規へ転じる current gate は floor 投入 admission・ratified live launch・
  holdout candidate producer の 3 経路である。
  一方 silo 完全検証と prediction seal は活性化以前から別理由で閉じており、
  移行の影響として数えてはならない。
  世代付き移行の設計そのものは較正・凍結権限束 (段 0 未完了) の所有へ合流する。
  base: bf290cc8210bdad3406f2c7f755383469e0e028c5527a1c7bdc2b49030d497aa
- [T-478] **P2・残る 5 構成要素の現況を実測 → (d) が床値 v2 を直接阻む**:
  (a) 部分実装 (活性化由来 registry と authorize receipt はあるが全入口が同じ receipt を
  受け取らない)、(b) 部分実装 (campaign lock v2 に hash はあるが campaign preimage が
  execution authority を覆わない)、(c) 未実装、(e) 部分実装。
  **(d) 起動 wrapper の結線は未実装で、これが床値 v2 の発行経路を直接塞いでいる** —
  protocol writer は旧固定 path へ create-only で書き、実凍結領域への任意 path 書込みは拒否され、
  投入 admission と job script も旧固定 path を hardcode している。
  seam を作る際、path と hash の authority は receipt に選ばせず人間承認済み上位束の
  generation record から解決しなければならない (submitter が検証対象を選べる受理拡大になる)。
  base: 04ac8d038feb13c225abbf03d19ad960e2804b32eb7c48d6bf1764df034c5c27
- [T-987] **P1・裁定済み (2026-08-16、択 (b) + 条件) → 床値 v2 の実測は世代移行の後**:
  裁定は択 (b) = 現 gitlink で床値を再測定して v2 を作る、条件 = 再測定は世代移行 wave と
  同一 chain でのみ実施する。**実測で、択 (b) が要求する pin は既に承認定数側へ入っている**
  (承認定数と現 gitlink が一致し、凍結 protocol 側だけが旧 pin のまま)。
  したがって残るのは protocol の再発行だけだが、その sanctioned な発行経路が存在しない
  ([T-478] (d))。世代移行が上位権限束の人間手番待ちである以上、本項も同じ待ちに入る。
  base: dc5cd83fcf318f40675e86edc4415c123ab5c122678c449fb42bd7bb68cf0a1e
