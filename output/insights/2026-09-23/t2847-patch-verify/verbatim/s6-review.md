## 判定

NO-GO

## must-fix

以下、`R` はレビュー対象の `output/insights/2026-09-23/t2847-patch-verify/`、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/runs/` を指す。修正対象は README のみ。

1. **§1・§3.1・§3.4：V03 の分類が段4裁定と一致しない。**
   `J/s3-1/verifier/0003.json` は X＝1,213,194、巡回＝5,510、version dup＝6,692。`R/verbatim/s4-ruling.md` の分類は「期待と違う層の counter が非0」を「別の層で検出」としている。「期待した層も出た場合は除外」という規定はないため、注記だけにして「別の層で検出0本」と集計する根拠が不足している。V03 の単独条件と4 thread条件を区別し、期待層の検出と期待外の併発を集計に反映すること。patch単位で排他的に集計するなら、その集約方法も明記する。

2. **§1：動的発火を確認した範囲を言い過ぎている。**
   「10本をbuild・発火」「write-intentの4本では、改竄が動的に起きた痕跡がtraceにある」は、§3.2自身の限定と矛盾する。
   `J/t152-1/env/pegasus/characterization/t152_write_intent_coverage.json` の ptrswap は `write_ops=["U"]`、`write_intent_total=0`。`J/t152-1/verifier/0007.json` は135,589取引・1,190,447書き込みで、比は8.7798。これらからpointer交換の発火は確認できない。eraseの平均差も、取引ごとの改竄を直接観測した証拠ではない。結論を「10本をbuild・実走」「4本ともSかつI行0、動的な痕跡の確認範囲は各行のとおり」に限定すること。

3. **§2.1：`resolve_evidence`への差し替え説明がsourceと異なる。**
   READMEは `buildcache.build` と `source_digest.resolve_evidence` の両方にcompilerとcacheを渡すと書く。実際の `R/verbatim/launcher-source.md` は、前者に `cc,cxx,cache_root`、後者には `cxx` だけを渡す。`J/s3-1/meta.json`・`J/s5-1/meta.json` の `replaced_names` も、それぞれ `buildcache.build(cc,cxx,cache_root)` と `source_digest.resolve_evidence(cxx)`。この2つを分けて記述すること。

## should

1. **§3.2：過去との差をemitterだけに帰属させない。**
   「との違いはemitterの有無であり」は原因を限定しすぎる。設計書§5.1は2026-07-29の別branchの記録であり、今回の `J/t152-1/meta.json` はpin=`e9e477ca…`、compiler=11.4.0。emitterだけを変えた比較ではない。「emitter不在という設計上の期待と整合する」に留める。

2. **§3.2・§4：opswapの停止理由と、観測したprefixの限界を明確にする。**
   `J/t152-1/verifier/0006.json` は取引1・書き込み6・`abort_reasons={}`。driver JSONの `runs.opswap.abort_exercised=true` はabortの発生を示すが、その原因や時系列までは示さない。「deleteへの置換後の取引がcommitしていない」という説明は削るか未検証仮説と明示し、§4に「certifiedの対象は観測された1取引で、進行性の保証ではない」と補う。

## nit

- **§1項3：参照節が違う。**
  write-intentの観測先は§3.3ではなく§3.2。照合先は `J/t152-1/verifier/0004.json`〜`0007.json`（4件ともcertified=true）。

## 照合した項目の一覧

数値の転記自体に不一致は見つからなかった。分類上の不一致は上記must-fix 1。

| 照合対象 | 件数・結果 |
|---|---|
| verifier全文 ↔ `raw/verifier-summary.jsonl` | 18出力、数値328項目すべて一致。rc・巡回・取引・書き込み・integrity各counter・P理由別件数・報告G2件数を含む |
| READMEの取引あたり書き込み | 5件一致：8.7826／7.7817／9.7767／6.0／8.7798 |
| X理由別件数 | 5件一致：455,140×2、606,597×2、494,700 |
| checks／gate3 | 25述語を確認。s3＝5真、s5＝8真、t152＝5真・4偽、s2＝3真 |
| condition gate | 10変異すべてadmitted=true、supply・meaningともgreen |
| request ID・Elapse・driver rc | 各4件一致。140＋134＋185＋209＝668秒、約0.19 node時間 |
| hostname・compiler | 各4件一致。全jobでg++-11、11.4.0 |
| metaのコピー・差し替え一覧 | コピー4件一致。差し替え20項目はsourceと一致。READMEのcache説明だけ不正確 |
| launcher SHA256 | fenced blockから再計算し `bc955855c2cb426b73023aa3d0f43b72262d952fb020499310689d861cc276cc` と一致 |

`verifier/000N.json` とdriverのrun名の対応も、判定・取引数等で18件照合した。

| job | 0001からの順序 |
|---|---|
| s3 | stock_single → lockskip_single → lockskip_high → early_unlock_single |
| s5 | stock_single → erase_single → swap_single |
| t152 | stock_single → stock_abort → bomb_smoke → erase → forge → opswap → ptrswap |
| s2 | norw/S2 → norw/legacy → highkey/S2 → highkey/legacy |

重点項目のうち、以下は妥当だった。

- **V06：** P＝756,171の独立した観測があるため、commit＝0でも期待層の検出と分類できる。空履歴でもIになるという注記も適切。
- **V02 legacy：** 対象keyに届かない条件でのSは設計書の条件付き期待と一致する。
- **V09〜V12：** SかつI行0は段4裁定の「盲点として期待どおり」に一致する。driver rc=1を成功に書き換えず、4つの偽checkと分けている点も適切。
- **起動器：** 指定sourceにpatch適用・condition gate・verifier判定を置換する処理は見つからない。s2の部分実行も開示されている。ただし、元driver内部との厳密な同値性や「tracked実装差分ゼロ」は、今回指定された資料だけでは独立に確証できない。

## 総括

生出力と数値表は整合している。NO-GOの理由は、**裁定と異なる分類、発火確認範囲の過大表現、差し替え説明の誤記**である。

指定資料内では、正しさゲートの緩和、性能比較、範囲外のgate・検査・台帳追加は認められなかった。READMEの修正で対応でき、追加実走や実装変更は要求しない。