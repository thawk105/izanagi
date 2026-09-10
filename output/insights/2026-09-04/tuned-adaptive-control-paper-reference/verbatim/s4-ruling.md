# 段 4 裁定 — [T-2186] / [T-2239] 調整済み adaptive の実対照を論文側へ結ぶ

## 確定した (P1)

- **(P1-a) 対照図を `docs/paper-story/figures/` へ昇格させない。台帳から現物を直接参照する。確定。**
  ただし**根拠を親の brief から差し替える**。親は「未認証だから昇格できない」と書いたが、
  これは強すぎた。実際の根拠は 3 つである。
  (i) copy 先の bytes は元 provenance が束縛する出力ではないので、証拠の鎖が切れる。
  (ii) 新しい paper figure を検査する consumer が存在しない (既存 consumer は fig2b / fig2c / fig4 の
  basename を個別に固定しており、directory 全体を見る consumer は無い)。
  (iii) 既存の PNG / PDF / provenance は凍結物である。
  未認証であることは**昇格を許さない必要条件**として残るが、単独の根拠にはしない。
- **(P1-b) `tools/plotting/FIGURE_CONVENTIONS.md` を変更しない。確定。**
  規約は「何を描くべきか」を定め、個々の図の所在は図の台帳が持つ、という責務分離が既に成立している。
  所在を規約へ書くと、成果物の改名・昇格のたびに一般規約が更新対象になる。
- **(P1-c) `orchestrator/tests/test_backoff_figure_provenance.py` の `BASELINE_BY_GENOME` を
  変更しない。確定。** ただし**根拠を差し替える**。「3 定数を出す producer が実在しない」は誤りで、
  `tools/pegasus/probes/t2187_adaptive_const_probe.py` は 3 定数を genome へ出す。正しい根拠は
  「その producer は別 schema へ出すので、**この v2 consumer surface には producer がいない**」
  ことと、既存 3 campaign の WAL に 3 定数の出現が 0 件であることである。
  さらに本 wave が参照する図の生成器 `plot_t2187_adaptive_consts.py` は、既定セル以外に
  そのセル名 (`s1-u2560`) を label として付け、既定セルがちょうど 1 つ存在することを構造的に
  要求する。したがって carry が恐れた誤 label 事故は**この経路では起こらない**。

## 実装しない

**実装面 (コード・テスト・実行可能 script・機械設定) の差分は 0 とする。** 段 5・段 6 を飛ばし
`4 -> 7 -> 8 -> 9` とする。Codex `role=author` は立てない。変異 matrix は免除する
(DW-S04 の「実装面の差分ゼロの wave」)。受入全走は免除しない。

## 所見の real / refuted と採否

### sol レンズ

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| S1 | 節名と basename だけでは到達経路が閉じない。解決可能な link にせよ | **real** | 採用。scope 内 |
| S2 | 「現在は図へ到達不能」という DW-G05 は事実より強い | **real** | 採用。DW-G05 を狭める |
| S3 | worklog fragment は成果物影響を持たないので nit | **real** | 採用 (分類のみ)。段 7 の記録義務として書くが、依頼を満たす成果物には数えない |
| S4 | 昇格しない境界は実在欠陥に対応しており仮想 gate ではない | **real** | 採用。現方針を維持 |
| S-B1 | 5 セルは provenance にあるだけでなく実際に描かれる | **real** | 親の実測と一致。維持 |
| S-B2 | brief の検索コマンドは archive を除いておらず「0 件」と一致しない | **real (nit)** | 採用。archive 除外を明記して訂正 |
| S-B3 | 「T-2186 差し替え完了」の射程が広すぎる | **real** | 採用。「10 単位の差し替えは着地済み。論文側導線は本 wave で閉じる」へ限定 |
| S-B4 | 「3 定数 producer が実在しない」は一般化しすぎ | **real (nit)** | 採用。(P1-c) の根拠を差し替え済み |

### luna レンズ

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| L1 | 生きた入口で未認証の数値と但し書きが離れており、数値だけ引用できる | **real** | 採用。scope 内 (規律 2 の本題そのもの) |
| L2 | 「昇格条件は T-2189 の決着」は正しさ検査を十分条件にしている | **real** | 採用。必要条件であって十分条件ではないと書く |
| L3 | 新節に Pegasus と旧 `linux-baremetal` の非結合境界が隣接していない | **real** | 採用。同じ段落へ書く |
| L4 | figures README には caption 正文の pin があり、検証集合に無い | **real** | 採用。親の実走集合へ `test_s1_9pair_figure_provenance.py` を加える。新規 test は作らない |
| L5 | A-1 v2 の `static10 - adaptive` は live な既定 surface として実在する | **real だが scope 外** | 不採用 (実装しない)。凍結 policy が `formal=false` / `promotion_prohibited=true` / `result_authority=exploratory` を宣言しており、D1506 は既定 adaptive の測定自体を禁じない。したがって現時点で規律違反ではない。**裁定パッケージ候補**としてユーザーへ返し、worklog へ非該当として記録する |
| L6 | 凍結境界への byte 変更提案は無い | **real** | 確認。維持 |
| L-B1 | 「T-2186 完了・carry は stale」は完了の射程を混同している | **real** | 採用。carry は書かれた時点で正確であり、変わったのは「図が既にあったので新規計測が要らなかった」ことだけ、と書く |
| L-B2 | brief の producer 不在は広すぎる (プランは正しく限定) | **real** | 採用済み |
| L-B3 | 図の実体・セル数・環境の親実測は独立照合できた | **real** | 維持 |
| L-B4 | 実装差分 0 は維持可能。A-1 legacy を不存在扱いしない | **real** | 採用。L5 のとおり記録する |

## プラン v2 — 確定した変更面

| file | 変更 | 内容 |
|---|---|---|
| `docs/paper-story/figures/README.md` | **追記** | 図一覧の直後へ「調整済み adaptive の実対照 (論文図へ未昇格)」節。(a) PNG / PDF / provenance への**解決可能な相対 link**、(b) 同じ軸に並ぶ 3 系列の名指し、(c) 旧 fig2b / fig2c と環境・CCBench 版・patch・反復設計・集約・`clocks_per_us` が違うので同じ図・表・時系列・再現判定へ畳まないこと、(d) 未認証であり variant 採用・certified 性能結論の根拠にしないこと、(e) 論文図への昇格は correctness の決着を**必要条件**とし、それだけでは昇格しないこと |
| `docs/paper-story/README.md` | **追記 2 箇所** | (1) 未認証の数値段落の冒頭へ、その数値が未認証の trace-disabled 観測値であることを隣接させる。(2)「今後の基準線」へ、現物は figures 台帳の新節から辿ること、fig2b / fig2c を調整済み adaptive の対照として代用しないこと、参照が閉じるのは「並べて指す」までであることを足す |
| `docs/spool/worklog/<...>-1.md` | **新規** | 段 7 の記録。T-2186 / T-2239 の終端、A-1 legacy の裁定パッケージ候補、非該当の記録 |

**凍結物は 1 byte も変えない。** 既存図・provenance・各版 snapshot・`claim-evidence/`・
旧 campaign report 3 件・既存 insight は不変。

## 不変条件 (再掲)

- 調整済みの値は variant 採用の根拠に使わない (絶対規律 2)。
- Pegasus の値と旧 `linux-baremetal` の図を同じ図・表・時系列・再現判定へ畳まない。
- 新規計測・再作図をしない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない。

## DW-G05 成果物影響 (訂正版)

親は brief で「論文執筆者は図へ到達できない」と書いたが、これは強すぎた。実際には
`docs/paper-story/README.md` -> 一次資料の insight -> 埋め込まれた図、という 2 段の経路が既にある。

**正しい欠陥はこうである。** 図の台帳 (`docs/paper-story/figures/README.md`) に調整済み対照が
**1 行も登録されておらず**、基準線を定める段落からその図を**直接選べない**。台帳だけを読む執筆者は、
登録されている fig2b / fig2c を引く。これらは既定 adaptive しか適応側に持たない図であり、
D1506 が「機構の優劣を何も言っていない」と定めた比較を論文へ入れることになる。

## 段 7 前に親が実走する検査

- `python3 tools/check_docs.py`
- `python3 -m pytest orchestrator/tests/test_s1_9pair_figure_provenance.py` (caption 正文 pin、L4)
- `python3 tools/spool_fold.py --dry-run`
- 受入全走 (免除しない)
