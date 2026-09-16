単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s1-brief.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s1-brief.md` — 親 brief (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s2-plan-out.md` — 段 2 plan (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/verbatim-rulings.md` — 既裁定と事前登録の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-calibrations-summary.txt` — 親の実測 (registered 較正 8 件)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-admission.txt` — 親の実測 (admission と effective-clock method)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-calibrate-argv.txt` — 親の実測 (calibrate argv と実走ログ)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/phase3-b4-reflux-ablation-preregistration.md` — 事前登録本文 (§0、§1、§5、§5.1、§11)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/CLAUDE.md` — 絶対規律 (規律 2・3・6・7)

上記以外に repo 内を読んでよい (`docs/decisions.md`、`orchestrator/campaign/floor_pair_driver.py`、
`orchestrator/campaign/calibration_verify.py`、`orchestrator/campaign/env_contract.py`、`orchestrator/campaign/layer3_report.py`、
`orchestrator/calibrator/`、`output/env/pegasus/calibration/registered/`、`docs/spool/*/README.md`)。

## レンズ A — 正しさ境界・事前登録・授権範囲

plan を守らせず検査せよ。**親 brief 自身も検査対象である。** 次を攻撃する。

1. **授権の範囲。** (P1) の `reps=5` は「calibrator の出力を採り、承認は AI が本委任の下で行う」(D1641 決定 3) の
   射程に入るか。calibrator 出力から導けない値を AI が承認することは §11.1 の「AI が起草した候補値を無裁定の既定値として
   凍結へ入れない」に抵触しないか。抵触するなら、どう書けば委任の内側に収まるか (または裁定パッケージへ返すべきか)。
2. **A-4 の導出は「値の起草」か「既裁定の反映」か。** 「3 workload × 較正が支える 1 セル」という具体列は D1641 決定 3 の
   逐語「3 workload × §5 に列挙する contention セル」の反映として成立するか。§5 に列挙が無い以上、AI が集合を決めた形に
   ならないか。1 セルに畳むことで D1641 が意図した「contention セル」の複数性を黙って落としていないか。
3. **C 群の値非依存性。** (P3) の適格条件 (c1)〜(c5) と採用順序 (submit_epoch 最小) が、D2044 項 11 の「値に依存しない」
   「結果を見る前に」を満たすか。特に (c5) (effective-clock method の現行一致 / D1537 除外集合) は「較正の測定値を見て選ぶ」
   形に堕ちていないか。採用順序を「最早」にした理由 (D1311 の型) は較正にも成り立つか。
   規則の適用結果が rr50 で g2 を選ぶことを親が先に知っている点は、事後選択に当たるか (較正は床値の結果ではない、
   という反論の強さを検査せよ)。
4. **規律 2・3・7。** loader / binder の受理集合を変えない「人手の選択規則」とする設計は D1696 と整合するか。
   逆に、規則が人手責任のままで機械検査が無いことを「保証」と誤読させる文面が plan / brief に無いか。
   §11 への追記が既存文を書き換えていないか (追記のみ)。
5. **T-2465 の追記内容。** 4 点 (担当者指名・対象集合・統計関数・採用証拠の受理) の反映が D1641 決定 1〜3・D1695・
   D1887・D1936 末尾の逐語を超えていないか。特に「採用証拠の受理」は D1641 決定 2 の「採用裁定は測定後に AI が
   本委任の下で行い D として記録する」の反映であって、受理済みを意味しないことが文面で保たれるか。
   n=62 への言及が失効した 59 を復活させないか。driver の変更単位 (D1453 / D1694) の扱いは正しいか。
6. **A-5 の裁定パッケージ。** 何を要るかの列挙が、値の起草に踏み込んでいないか。逆に、§11.1 の逐語上 AI が候補を
   書いてよい範囲を過小に見積もっていないか。

## 制約

- 書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 所見は「real / refuted / scope 外」の候補として、根拠 (file:line または既裁定 D 番号の逐語) を必ず添える。
- 出力は NFC。U+0300〜U+036F を使わない。

## 出力形式

以下の H2 見出しをこの順で書く。**全部 `#` 2 個の H2** で、`###` は使わない。最後の節は必ず `## 総括` とする (`### 総括` と書いてはならない)。

## 授権の範囲 (P1)
## A-4 の導出 (P2)
## C 群の値非依存性 (P3)
## 規律 2・3・7 と D1696
## T-2465 の追記 (P4)
## A-5 裁定パッケージ
## 親 brief の誤り
## 総括
