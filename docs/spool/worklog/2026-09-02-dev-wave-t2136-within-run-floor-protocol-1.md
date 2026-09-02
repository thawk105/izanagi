---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2136-within-run-floor-protocol
seq: 1
title: [T-2136] within-run 較正へ protocol を記録し、層 3 を認定較正へ接続した — 配線までで、非 silo の値が成果物へ入るには後続が要る (コード + テスト + docs、branch worktree-dev-wave-t2136-within-run-floor-protocol、変異 matrix = baseline PASSED・KILLED 10・SURVIVED 0・MISMATCH 0・期待 node 29 件完全一致)
---

## 本文

生産側 (certify 経路) が canonical genome を記録し、消費側の層 3 が環境契約の pin した
認定較正を候補に採るようにした。設計判断は {{D:within-run-genome-from-receipt}} と
{{D:layer3-contract-pin-additive}}。逐語と裁定パッケージは
`output/insights/2026-09-02_t2136-within-run-floor-protocol/`。

- **本 wave は配線までである。** 非 silo の within-run floor が公式材料レポートへ入るように
  なったとは主張しない。認定用 launcher が silo の define と target を直書きしており、
  非 silo floor の取得、環境契約世代の登録、活性化が後続として残る。
  起票文の「この 2 つが残る限り入らない」は必要条件の主張であり、閉じたのはその必要条件である。
- **親の裁定を子が 2 回訂正した。** (i) 親は「非 TRACE の CCBENCH define を全部回収する」を
  忠実として支持したが、段 3 のレンズが「軸を欠く受入証も形式だけ canonical で通る」穴を挙げた。
  全軸の存在要求を足して閉じた。(ii) 親は段 4 で「v2 は pin 1 件だけを候補にする」と裁定したが、
  段 3 のもう 1 本のレンズが、その規則では別環境の実在する動作点の値が失われることを
  実データで示した。和集合へ差し替えた。この 2 件目は本 wave で最も重い訂正である。
- **親が段 4 で置いた「レポート schema を変更しない」という制約を、段 6 で自ら解除した。**
  根拠語の 3 分類が計算されているのに一致時のレポートへ載らず、schema が旧 1 値に固定されていた。
  D829 (schema を producer の実測値域へ合わせる) と D828 (この schema への加法的変更では版を
  上げず required も変えない) を根拠に enum を広げた。親の運用上の制約であって既裁定ではない。
- **親の pin 閉包の列挙が不足していた。** 段 3 のレンズが、環境契約の活性化記録、複数の試験、
  複数の手順書、派生成果物を欠いていると指摘した。凍結 bytes は本 wave で 1 bit も変えていないが、
  保全回帰の対象範囲は親の当初列挙より広い。
- **実装子は sandbox から pytest を起動できず、「実装済み・未実走」と正しく申告した。**
  実走はすべて親が行った。実装子と fix 子はいずれも commit を作らず、禁止対象への変更は 0 件。
- **段 5 の実装は焦点 3 file では緑だったが、親の consumer 焦点走で 65 件の赤を出した。**
  新しい pin 解決が「出力 root は必ず `<repo>/output` だ」という偽の前提で repo root を
  深さ固定に逆算しており、入れ子の出力 root で `output/output` の二重 path を作っていた。
  署名一致ではなく assertion 本文で自分起因と判定し、fix 子へ渡して閉じた。
- **段 3 のレンズは、親が指定した修正方針だけでは閉じないことも示した。** pin を無条件に
  strict 解決する限り、較正を同梱しない既存 campaign では「pin file 不在」でレポート自体が
  出なくなる。加法的 best-effort へ設計を確定した。
- **auto-merge が競合 0 件で成立したあと、焦点走で 5 件の赤が出た。** 原因は merge を
  commit していない木では現在の閉包を解決できないことで、変更した層 3 本体は当該閉包の
  24 path に含まれない。merge を commit して 377 件緑に戻した。実装の回帰ではない。
  合成の妥当性は独立の合成監査 (real 所見 0 件) と受入全走で確認した。
- **ユーザー裁定へ返す項目が 3 件ある。** (a) 有効な環境契約が pin する較正 g1 は
  自分の時計述語を 48 本中 1 本で通らない既知例外であり、本 wave の接続はこれを層 3 へ
  新規受理する。既存成果物の値は 1 件も変わらない (現存レポートは全て別環境の v1)。
  (b) 認定を通らない経路で今後作られる genome 不在 record も、作成時期を問わず silo と
  仮定される。閉じるには内容 hash の台帳か producer の再設計が要り、ユーザーが scope 外と
  指定した追加物に当たる。(c) 非 silo 値の実投入に必要な後続 (launcher 一般化、較正の再取得、
  契約世代の登録と活性化) の順序と主体。
- 実測: 焦点走は編集 3 file が 377 件緑、凍結 bytes 回帰と内容走査・AST 走査を含む
  consumer 群が 480 件緑 (7 skip)、一度 65 赤だった群が 633 件緑。
  変異 matrix は merge commit 束縛で baseline PASSED・KILLED 10・SURVIVED 0・MISMATCH 0、
  期待 node 29 件が完全一致。provenance 全史監査 rc=0。
  受入全走の結果は land の受領証を正本とする。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 3、fix 1)。いずれも
  model=gpt-5.6-sol、effort=xhigh、outcome=accepted。受入は main の進行により 3 回投入した
  (1 回目と 2 回目は main 取り込み要求で、テストの赤ではない)。
- **段 8 の改善候補 2 件は、いずれも byte 予算に阻まれて入れられなかった。**
  実装せず候補として残す。予算のために既存の安全義務を削る道は採らない。
  (a) `DW-M01` へ変異 spec の `category` 語彙 (`negative` / `positive` / `both-layers` の 3 語で
  他は起動前に rc=2) を 1 行足そうとしたが、`docs/dev-wave/**` の L1 unique footprint が
  10737 bytes となり予算 10625 bytes を超えた。節単体には余裕がある (525/1000) が層で溢れる。
  (b) `DW-O27` へ受入の rc=70 分類 (`merge-message-provenance` は
  `--merge-message-file` 未指定、`merge` は wave が claimed main を含まないこと) を足そうとしたが、
  同節が 992/1000 bytes で余地が 8 bytes しかない。どちらも tool の失敗文言が自己説明的で、
  実害は plan-only 1 回と受入投入 2 回のやり直しに留まった。

## 次の一手差分

### 完了

- [T-2136] within-run 較正の producer へ protocol を記録させ、層 3 を認定較正へ接続した。
  配線までで、非 silo の値の実投入は後続 (launcher 一般化・再取得・世代登録と活性化) に残る。
  remaining: none
  base: 487dc01554cd0d36349a0b3fc12faf041bab968f65034ea39656ebbcbf9b6ba3

### 新規

- {{T:certify-launcher-protocol-generalization}} **P2・新規**: 認定用 launcher
  (`tools/pegasus/certify_calibration.sh`) が `CCBENCH_*` と `ycsb_silo.exe` を直書きしている。
  producer が非 silo の genome を記録できるようになっても、この wrapper が非 silo の較正を
  生産できない。protocol と軸を引数化し、生産できる protocol の集合を実測で示す。
  これを終えるまで非 silo の within-run floor は公式成果物へ入らない。
- {{T:noncertify-floor-record-legacy-assumption}} **P3・新規**: 認定を通らない経路で今後
  作られる genome 不在の within-run record も、層 3 は作成時期を問わず silo と仮定する。
  D1374 の歴史的 record への限定が効いていない。閉じ方は内容 hash の allowlist か
  producer の再設計かで受理集合への影響が違うため、着手前にユーザー裁定を要する。
