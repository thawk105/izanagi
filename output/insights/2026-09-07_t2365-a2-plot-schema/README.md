# [T-2365] / [T-2364] A-2 の図生成器を新 schema へ通し、新しい identity で attempt を取り直す

2026-09-07、wave `dev-wave-t2365-a2-plot-schema`。base main `cf4273f5671ecda87c6f1b76148df239ce043ead`。

## この wave が達成したこと

1. **図生成器が新しい形式の認証成果物から図を作れるようになった** ([T-2365])。
2. **新しい identity で A-2 attempt を取り直し、その成果物から実際に図を作った** ([T-2364])。
3. 取り直しを塞いでいた**実測済みの阻害要因 1 件**を見つけて閉じた (起動時の依頼には無かった)。

## 起動時の依頼に無かった、最も重い発見

**取り直しは現行コードでは 1 分も走らなかった。**

親は段 3 と並行して attempt `t2364-20260907a` を実投入した。2 workload とも約 50 秒で
`driver_rc=2` で終わった。

```
paper-story A-2 indeterminate: [Errno 22] Invalid argument: <attempt root>/receipts/condition-gate-<workload>.admissions.jsonl
```

機序は次のとおりである。

- `_write_condition_gate_admissions_x` が `_atomic_write_bytes_noreplace` を呼び、これが
  `renameat2` の「既存なら失敗する」フラグを使う。
- **計測領域も repo も Lustre であり、Lustre はこのフラグを実装せず EINVAL を返す。**
  親が `stat -f` で両方 Lustre であることを実測した。
- 同じ関数は `materialize` でも使われるが、そちらには EINVAL 退避が既にあった。
  **file 用の新しい writer が同じ穴を退避なしで再導入していた。** 導入は T-2337 の
  commit `1e22c4cbd`、同型事故の先例は `5dcea6e56`。
- **test が緑だったのは pytest の一時領域が xfs (同フラグ実装あり) だからである。**
  production は初回実走で落ちた。

直し方は親が Lustre 上で実測して決めた。`ln` は成功し、既存名への `ln` は EEXIST で失敗する。
よって hard link は「既存なら失敗する不可分な公開」をこの FS で正確に満たす。directory 用の
既存退避は hard link できないため claim file で直列化しており不可分でないと自ら記しているので、
file には流用しなかった。

**修正が効いたことは実走で確かめた。** 再投入した `t2364-20260907b` は、前回落ちた受領証を
2 workload とも書き、最後まで走った。

## 同じ族の 2 例目が独立に出た

段 5 投入直前に local main を見たところ、`79707198f` に **A-1 の wave が約 20 分前に同じ
Lustre の公開失敗を踏んだ記録**があった。向こうも同じ directory で実測し、
`RENAME_NOREPLACE` は errno 22、`flags=0` は成功、と記録している。

`DW-G03` が族一般化に求める「同型欠陥が異なる producer で独立に 2 件再現」は**これで満たされた。**
ただし A-1 側は稼働中の別 wave の編集面であり、ユーザーが本 wave の scope を明示的に絞っている。
**本 wave では一般化せず、裁定パッケージとして返す。**

なお向こうの記録は `flags=0` を退避候補に挙げているが、`flags=0` は既存を黙って置換する。
**file の公開には hard link の方が強い** (既存名へのリンクは EEXIST で失敗し、置換が起きない)。
族一般化の裁定ではこの差を保つべきである。

## 段 3 の敵対相談が変えた設計

### pin が自己申告に落ちる設計を却下した

段 2 のプランは、bytes pin を CLI 引数 (`--certification-sha256` など) で渡せるようにしていた。
段 3 のレンズが、**対象 file とその期待 hash を同じ呼び手が渡せる設計は pin を
「呼び手が言うとおり」を確かめる恒真判定へ落とす**と指摘した。凍結 certification の `status` を
書き換えて自分で計算した hash を添えれば、偽の判定を載せた図を publish できる。

親はこれを採り、**repo 所有の pin 表**へ改めた。key は certification の repo 相対 path、
CLI が選べるのは「どの成果物か」だけである。新しい attempt を図にするには **repo へ entry を
足す commit が要る。**

### caption の主張を証拠の範囲まで下げた

段 2 は D1198 の条件関門について「適用済みを導出する」と書いていた。レンズが、成果物が
保存しているのは admission の canonical record までで、元の supply / meaning records は
残らないと指摘した。**「関門を実施し通過した」ではなく「そう記録された受領証が束縛されている」
までしか言えない。** 生成した図の gate 文はこの範囲に収まっている。

### 実装不能な field 名を正した

段 2 は `cert status="bound"` と書いていたが、`bound` は最上位 `status` ではなく cell ごとの
`source_binding_status` である。そのまま実装すると新しい成果物を全部拒否するところだった。

## 段 6 のレビューが見つけた「発火しない保証」

レビュー A は実装自体に契約違反を見つけなかった一方、**足された検査のうち、外しても既存 test が
1 件も赤にならないものを 4 件**名指しした。とくに重いのは、新版の正例が全部 test 用の抜け道
(`expected_hashes` kwargs) を通っており、**pin 表を迂回する退行を検出できない**ことだった。

fix 子が 4 件すべてを閉じ、**足した検査それぞれを殺す最小の変異 10 件を実際に当てて、
対応する node が赤になることを確認した。**

## 親が自分で作り込んだ欠陥

図を生成したところ、caption の先頭が `Figure 5.` の決め打ちで、**新しい図 fig6 も 5 を名乗った。**
凍結済みの図 5 と番号が衝突し、論文素材に誤った相互参照が入る。

図番号を出力 prefix の basename から導く形へ直した。新しい CLI 引数は足していない。
凍結図の prefix は `fig5_` なので導出結果は同じ文字列になり、**凍結図の caption は 1 byte も
変わらない** (子が UTF-8 1788 bytes の完全一致を確認)。

この変更で、図番号の検査が pin 表の検査より前に発火するようになり、出力 prefix が `fig<N>_`
形式でなかった既存 test 4 件が別の理由で落ちた。**受理集合は変わっておらず**、どちらの経路でも
拒否される。当該 test の prefix を正当な形へ改めた。

## 取り直しの結果

attempt `t2364-20260907b`、request `981476.nqsv` (rr5) / `981477.nqsv` (rr50)。

| workload | cell | role | src_token | median (tps) | 効果 |
|---|---|---|---|---|---|
| rr5 | `rr5-stock` | stock | `stock` | 2,438,295 | — |
| rr5 | `rr5-fixed10` | adopted | `955b452a332d…` | 3,987,794 | **+63.5485%** |
| rr50 | `rr50-stock` | stock | `stock` | 3,756,230 | — |
| rr50 | `rr50-fixed5` | adopted | `21def77c944b…` | 4,297,929 | **+14.4213%** |

outer status は **`observed-positive`**。4 cell すべて `source_binding_status=bound` で、
stock cell は `stock`、adopted cell は非 `stock` の token を持つ。**D1644 が求めた
「patch が効いた木だけを受理する」向きが実走で成立した。**

**旧 attempt `t2022-20260828c` の `reject` を取り消すものではない** (絶対規律 7)。あちらは
patch が当たっていない木で内蔵 backoff の有効/無効を測った別の事実であり、記録として残る。
両者を前後比較として読んではならない。

## 実走した検査 (すべて親が実走)

| 対象 | 件数 | rc |
|---|---|---|
| 統合後の焦点走 (2 file) | 192 passed | 0 |
| 段 6 fix 後の焦点走 | 200 passed | 0 |
| 図番号 fix 後の焦点走 | 4 failed / 198 passed | 1 |
| prefix fix 後の焦点走 | 202 passed | 0 |
| provenance full 監査 | 8510 件、新規違反なし | 0 |

焦点走はすべて計算ノードへ投入した。

## 段 1 で親が実測した事実

- `materialize` は `tracked_destination` が既存だと拒否する。現行 policy の宛先は凍結済みの
  `2026-08-24` の dir なので、**policy を変えずに取り直すと必ず失敗する。** 起動時の依頼が
  触れていない新事実だった。
- `_protocol_preimage` は `tracked_destination` を含まない。**宛先を変えても `protocol_sha256` は
  変わらない。** 張り直したのは policy file の byte hash の golden 2 箇所だけである。
- 出荷 policy は A-2 と A-6 の 2 本に限定されている。3 本目を足すと driver 本体の編集が要るので、
  既存 policy の宛先を改める形を採った。

## 残した項目

- **Lustre の `RENAME_NOREPLACE` 依存の族一般化。** 独立 2 件が揃ったので `DW-G03` の条件は
  満たされているが、A-1 側は別 wave の編集面であり本 wave の scope 外。
- `full` certification の materializer への exact 再導出 ([T-2366])。本 wave が作った欠陥ではない。

## 変異 matrix

probe → 較正 → 本走 の 3 段で行った。台帳と spec は同 dir に置く。

| 変異 | 内容 | 本走 |
|---|---|---|
| M1 | Lustre の EINVAL 退避を消し、EINVAL を送出したままにする | **KILLED** |
| M2 | 退避の公開手段を hard link から「既存を置換する rename」へ変える | **KILLED** |
| M3 | pin 表に key が無いとき、呼び手が計算した hash を期待値にする | **KILLED** |
| M4b | 新版でも旧版の raw cell schema を受理する | **KILLED** |
| M5b | 新版でも旧の固定 gate 文を出す | **KILLED** |
| M6b | `source_binding_status` の検査を**両層とも**消す | **KILLED** |
| M7 | policy の `tracked_destination` を旧 leaf へ戻す | **KILLED** |

**7/7 KILLED、SURVIVED 0、baseline 緑 (rc=0)。**

### probe 走が明らかにしたこと

probe (全件 SURVIVED 登録で観測 node を集める段) で 3 件を再照準した。

- **M4 は 15 node を落とし、単一理由に帰属しなかった。** 定数を変えると current profile 全体が
  壊れるためである。受理を広げる向きの狭い変異 (新版でも旧版の raw schema を許す) へ変えた。
  段 3 の lensB がこの型を事前に予告していた。
- **M5 の SURVIVED は等価変異だった。** profile の値は `current-full` であって `current` ではなく、
  親が書いた変異は挙動を変えていなかった。実装の欠陥ではない。
- **M6 の SURVIVED は 2 層 mask だった。** `source_binding_status` の検査が 2 箇所にあり、
  上位層が下位層を隠していた。`DW-M02` に従い両層同時変異へ再照準して KILLED を得た。
  **この構造は変異試験だけが明らかにした。**

### 本走の erratum

本走 (`mutation-ledger-final.json`) で M3 が MISMATCH になった。原因は**親の登録ミス**である。

段 6 の fix 子が M3 相当の変異を当てて 4 node を報告したが、子が当てたのは
「pin 表を常に迂回する」形の変異であり、spec に登録した変異は
「表に key が無いときだけ迂回する」形だった。**別の変異で測った node 集合を写したため、
期待と実測が食い違った。**

実装の欠陥ではない。実測された完全集合 2 件を期待値にして M3 だけ再走し
(`mutation-spec-m3-rerun.json` / `mutation-ledger-m3-rerun.json`)、**KILLED を得た。**
初回の MISMATCH は `DW-M02` に従い台帳に残す。

### 親が走行中に犯した手順違反

本走の 1 回目 (`final3`) は、**親が変異走の最中に repo へ記録 file を書いた**ため、harness が
未追跡 file を検出して停止した。変異走は走行中の作業ツリー不変を要求する。記録を先に commit し、
clean tree で走らせ直した。
