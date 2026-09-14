---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-b7-regression-materials
seq: 1
title: B-7 の材料として 3 workload の判定を退行込みで併記し、配置を段 3 の指摘で results 系列へ戻した (docs のみ、branch worktree-dev-wave-b7-regression-materials、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- **成果物は `docs/paper-story/results/2026-09-14-b7-all-workload-regression.md`。** 現行環境・正式
  protocol で判定の出ている 3 workload の 6 cell を、2 attempt に分かれた記録のまま横断で併記した。
  入口 `docs/paper-story/README.md` の results 表へ 1 行、stale 注記へ独立段落 1 つを足した。
  新しい測定は 1 件も行っていない。既存の凍結物の bytes は変えていない。
- **配置は段 3 の点検で差し戻した。** 段 2 の計画は成果物を `output/insights/` 側へ置き入口から
  ポインタで指す案を推していた。段 3 の点検が **D1631 の却下選択肢に「本 wave の insight に置いて
  README から指す」と「README の stale 注記だけで済ませる」が逐語で載っている**ことを指摘し、
  親が現物で確認して results 系列の新稿へ差し戻した。段 2 が案の根拠に引いた「一項目の決着を
  届けたいだけなら、版を足さずに stale 注記で指す」は**版 (日付つきスナップショット) についての
  規則**であり、results 系列の配置判断へは効かない。
- **単位の裁定。** results 系列は「1 file = 1 結果 (1 protocol または 1 campaign 群の完走)」を
  単位とする。今回は protocol instance・source commit・投入日・ホストが違う 2 attempt の併記なので、
  この単位に収まるかが割れた。**「campaign 群」は事前登録された群を要求しておらず、既存の
  observed-positive 稿自身が独立した 2 campaign をまとめている**ことを根拠に、単位を
  「事前登録の失敗条件 (e) が報告を求める『全 workload』の集合」として稿の §0.1 に明記した。
  これは既存契約の適用であり、新しい一般則を作っていないので decisions へは送らない。
- **段 3 が親 brief の誤り 3 件を実測で出した。** (a) A-6 の abort 率 (0.1547 / 0.145) の出所を
  attempt 記録 README と書いたが、同 README に掲載はなく、出所は campaign WAL の
  `bench_done.payload.leading_indicators.abort_rate` で、事後解析がそれを転記していた。
  子は外部 WAL の現物まで辿って確かめた。(b)「一次資料はすべて worktree 内の tracked file」と
  書いたが、A-6 の raw JSON と WAL は別の measurements root にある。(c) 旧 fig5 の用途制限を
  「取り直しまで」と書いたが、2026-09-11 の追補で**期限なし**に改まっている。3 件とも稿へ反映した。
- **留保の非対称を段 3 が見つけた。** 段 2 の文面案は「rr95 で負の中央値効果を記録した。floor 超の
  退行、有意差、再現性は判定しない」と退行側だけに留保を掛けていた。両 attempt の
  `a4_noise_floor_status` は `open` なので、**勝ち筋 (+63.5485% / +14.4213%) にも同じ留保が掛かる。**
  正負共通の留保へ改めた。放置すれば退行だけが不確かで利得は確立済み、と読める非対称が残っていた。
- **床値が open のときの報告義務の扱い。** 失敗条件 (e) は「他の workload で**床値超の**退行がある」を
  前件とする。床値が未確定である以上、前件の成立は立証できず、同時に「発火しない」と確定した
  わけでもない。**発火判定としては字義の読みを採り、報告方針としては隠さない側を採った** —
  正負をそろえて載せ、載せたこと自体を義務の履行として宣告しない形にした。
- **scope 外と裁定して直さなかったものが 1 件ある (発見の記録)。** 入口の stale 注記は A-2 の新
  attempt について「results 系列の表への登録も未了」と書いているが、**同 README の results 表には
  日本語稿と英語稿の行が既にある。** 入口の中の自己矛盾である。段 3 は「B-7 の材料への導線にも
  限定にも必要ない別項目の状態訂正だから削るべき」と判定し、親はそれに従って追記へ入れなかった。
  **本 wave はこの矛盾を訂正していない。** 依頼が「本題の報告だけ」と指定し、D1986 前文も付随する
  一般化を足さないと定めているためである。
- **B-7 の充足は宣告していない。** 稿は (1) 2 attempt を統括する単一の正式実験が存在しないこと、
  (2) adopted の genome が workload ごとに違い同一 variant の転移を測っていないこと、
  (3) 床値が open で正負いずれも floor 超を判定できないこと、(4) D1645 の解除条件を判定しないこと、
  を限定として書いた。2026-09-05 版 §8 の B-7 が書く「要件は満たされていない」を訂正していない。
- **A-6 の単独 results 稿は存在しない。** 本稿は横断の表であり、A-6 の 1 attempt の一次資料全体から
  作った結果節ではない。段 6 の点検は「A-6 単独稿は別 wave の仕事でよい」と判定した。次の一手へ起票した。
- **段 6 の敵対レビュー 2 本が must-fix 2 件・nit 4 件を出し、親が全件反映した。** must-fix は
  (a) §1.1 の共通設定の出所が過広だった (CCBench pin・perf・trace-disabled build は policy の
  `performance_common` に無い)、(b) results 系列の規則が一次資料に数える raw manifest への導線が
  落ちていた。**焦点再レビューは must-fix 0 件で、残った nit 1 件 (§2.3 の見出しが本文より過広) も
  直した。** 焦点再レビューは追加した SHA-256 2 件を現物で再計算し、掲載した測定値が fix の前後で
  byte 単位で同一であることも確かめた。
- **Codex 子 6 本 (plan 1 / consult 2 / review 2 / focus 1)。全件 `outcome=accepted` /
  `stop_reason=completed`。** 受領証の requested / recorded はいずれも `gpt-6-astra`。plan と consult の
  effort は 2026-09-10 の裁定どおり `medium` を明示した。review と focus の effort は docs 権威から
  導出され caller は指定できない (受領証に effort 欄は無い)。読み取りだけの子なので実走は全て親が行った。
- **実装面 (コード・テスト・script・機械設定) の差分は 0 である。** 変異 matrix は `DW-S04` の免除。
- **受入全走を 1 回空振りさせた。** 段 7 の fragment を書いた直後に投入したため、作業木に untracked の
  fragment が残っており `stage=prerun-clean rc=70` で claim 前に止まった。`DW-O20` の「untracked を
  残して gate を走らせない」が既に塞いでいる型で、親の順序のミスである。`DW-S04` の「受入全走は段 7 の
  記録前に実走し結果を worklog へ書く」と `DW-O12` の「land 対象 tip への最終受入投入は `DW-S07` と
  段 8 の commit 完了後に行う」は文面として衝突するが、**後者が「取り違えると land が rc=23 になる」と
  明示しているので後者を採り、受入結果は本エントリに書かず記録 commit 後の tip で 1 回だけ走らせた。**
- **段 8 の自己改善候補は 2 件で、どちらも routing しなかった。** (a) 上記の受入順序の衝突は
  `DW-O12` に同一発火点の正本が既にあり、D271 の新規節登録条件を満たさない。(b) `DW-O09` の pin 閉包を
  docs のみの wave で走らせるときに何を列挙するか (系列規則・入口の表・ポインタ) の記述が無い点は、
  本 wave で実害が出ていない (results path と入口を pin する test は 0 件と実測) ので記述を増やさない。
- decisions / failures へ送る項目は無い。

## 次の一手差分

### 新規

- {{T:b7-requirement-adjudication}} **P2・未裁定**: B-7 (全 workload の退行込み報告) の要件充足の
  扱いを裁定する。材料は `results/2026-09-14-b7-all-workload-regression.md` にそろったが、
  (a) 同一 variant を他 workload へ当てた比較が無い、(b) 両 attempt の床値が `open` で floor 超を
  判定できない、(c) 2 attempt を統括する単一の正式実験が無い、の 3 点が残る。追加測定を行うか、
  限定付きで充足と扱うか、未了のまま置くかを決める。本 wave は充足を宣告していない。
- {{T:a6-single-results-draft}} **P3・新規**: A-6 read-heavy 認証 (attempt `a6-20260908b`、
  outer `reject`、効果 −5.7841%) の単独 results 稿を書く。横断稿は 1 attempt の一次資料全体からの
  結果節を兼ねない。同系列の規則どおり、権威 bytes・raw manifest・WAL・裁定の全体から作り直す。
