---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2594-d1640-holdout-label-erratum
seq: 1
title: [T-2594] D1640 の保持群ラベル逆転を追補で正し、凍結側は 1 byte も触らなかった (docs のみ、branch worktree-dev-wave-t2594-d1640-holdout-label-erratum、実装面の差分 0 なので変異 matrix は DW-S04 により免除)
---

## 本文

- **既裁定の実施だけを行った。** D1986 項 2 (2026-09-14、ユーザー裁定) が「決定側の記述を追補で
  正す。凍結側は触らない」と確定していた。本 wave はその追補を
  {{D:d1640-holdout-label-erratum}} として着地させた。凍結側の再作成も読み替えも再裁定しない。
- **凍結側が正であることを、コード同士の一致だけでなく承認記録まで遡って確認した。**
  2026-07-16 の 8b 設計発効で **ユーザー自身が「holdout = H1 (rr80) + H2 (rr20)」を選択**している
  (`docs/archive/worklog-phase3-0714-0716.md`)。producer・`HOLDOUT_BINDINGS`・凍結成果物
  `output/s8b-freeze/holdout_freeze.json`・8b descriptor 設計 §3.1 がすべて同じ対応で、
  当該定義 4 行は `31426fb9a` (2026-08-29) と byte 一致する。誤りは D1640 の記述の側だけにある。
- **親 brief の断定 3 件を、段 3 の敵対相談 2 本が同じ向きで倒した。採用して弱めた。**
  (a) 「H1 の境界が過小になり受理集合を広げる」は無条件では成立しない — どちらが過小になるかは
  rr80 と rr20 の参照値の大小に依存し、他方の境界は過大になるので両 holdout を合わせた受理集合は
  一般に包含関係を持たない。参照測定は未取得で、読み比率から大小は決まらない。
  (b) 「割り当てを見る機械 gate は無い」は広すぎた — holdout の key 集合・workload 束縛・値の型・
  有限性・符号の検査は実在する。ただし単位と向きは、事前登録側が空でない文字列かを見るだけで、
  凍結値との一致を照合するのは判定器の側である (段 6 レビューの指摘で検査主体を分けた)。
  いずれにせよ欠けているのは**各値が指定された holdout の stock 参照から算出されたことの照合**である。
  (c) DW-O09 閉包で親が「歴史 blob を pin」と書いた `_D574_AUTHORITY_REF` の 2 番目の field は
  `BlobRef.commit`、つまり**歴史 commit** である (`orchestrator/preregistration/blobref.py`)。
  結論 (末尾追記なので既存 pin は動かない) は変わらないが、根拠の型を取り違えていた。
- **引数の前提 1 件が一次資料と食い違っていた。** 依頼は「台帳 ID が無いので起票から行う」と
  述べていたが、本件には T-2594 が採番済みだった (D1986 項 2 の「対象」、`docs/spool/FOLDED.md` の
  採番 receipt、worklog の active carry)。新規起票はせず既存 ID を閉じた。
- **T-1875 の持ち越し本文が二重に陳腐化していた。** 「着手前に T-2594 の裁定が要る」と書かれたまま
  だったが、裁定は 2026-09-14 に出ており、追補は本 wave で着地した。同じ fragment で更新した。
  T-1875 自体は完了にしない — 完了証明層・D1326 の順序・§10.2 の残る解除条件はそのまま残る。
- **実装面の差分は 0** (`docs/**.md` のみ)。D95 決定 1 により Codex 実装子は起動せず、
  変異 matrix は DW-S04 により免除した。段 2・3・6 の read-only 子は、規律 2 の面に触れるので省いていない。
- **段 3 の scope 外 real 所見 2 件は実装せず、裁定パッケージとしてユーザーへ返した。**
  (a) 事前登録の holdout 別パラメータと判定器の対比パラメータの接続確認、(b) 参照 artifact の
  holdout・測定条件・算出値を結ぶ照合の新設。依頼が「検査・台帳の追加は scope 外」としたため
  新規 T を切っていない。
- **段 6 の敵対レビュー 2 本は blocker 0、must-fix 1。** 正しさ境界レンズが、追補の
  「事前登録の validator が単位と向きを検査する」という記述を検査主体の取り違えとして倒した。
  親が実装で裏取りして文面を分けた。整合レンズは指摘 0 で、T-1875 置換本文の逐語照合と
  fold 着地形の 5 対象 SHA-256 一致を独立に確認した。
- **エージェント工数 (receipt 実測。計 45 call / 2,574,783 token):** 段 2 plan = 10 call /
  521,804 token / 347 秒、段 3 sol = 6 call / 296,642 token / 186 秒、段 3 luna = 14 call /
  1,023,324 token / 339 秒、段 6 sol = 6 call / 251,885 token / 123 秒、
  段 6 luna = 9 call / 481,128 token / 219 秒。

## 次の一手差分

### 完了

- [T-2594] D1986 項 2 に従い、D1640 の保持群ラベルを H1 = rr80 / H2 = rr20 と正す追補
  {{D:d1640-holdout-label-erratum}} を記録した。凍結側は 1 byte も変えず、paper-story 入口の
  「最新スナップショット以後に確定したこと」へも届けた。
  remaining: none
  base: 4746b5956204e6824af5c3eca0341ce8110c3a27ec377ffd9ff0cff6dec53b4b

### 更新

- [T-1875] **P2・裁定済み (2026-09-05、AI 委任) → 参照測定と実装は D1326 の順序のまま待ち
  (2026-09-14 に前提を実測)**:
  `delta_min` は holdout ごとに「pilot 前に凍結 `PerfConfig` で測る stock silo の
  session-median × 0.03」、向きは on − off、単位は絶対 tps (D1640)。
  **2026-09-14 の実測で、§10.2 の検証 consumer は既に実在し発火することを確認した
  (充足)。残る blocker は完了証明層で、12 条件中の充足は C10 の 1 件だけである
  (`d9bbdb6b0`)。** さらに §10.2 の解除条件のうち pilot の完全 block 成立・schedule
  generator と manifest の固定・§8 の再凍結とユーザー承認が未了。
  **保持群ラベルの追補は 2026-09-16 に {{D:d1640-holdout-label-erratum}} で着地した。
  D1640 は H1 = rr80 / H2 = rr20 で適用する。** 本追補は参照測定の投入も値の記入も認可しない。
  証拠 = `output/insights/2026-09-14_t1875-delta-min-gate/`。
  base: 62260ed165d5bb8e13cc2dd2de39e9518f908f9634646d476f4a0a246f8bfcd2
