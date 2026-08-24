---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1578-t1579-t1431-floor-restart
seq: 1
title: floor build 例外を耐久化し masstree 束縛を source identity + toolchain manifest へ張り替える (コード + docs、branch worktree-dev-wave-t1578-t1579-t1431-floor-restart)
---

## 本文

- 中断した wave を fresh context が引き継いだ。引数は「Codex 利用上限で倒れた段 6 review 2 本を
  新 job-id で再投入する」だったが、実測した状態はそれより先行していた。review 2 本は既に
  accepted、段 6 裁定も fix 1 巡目も完了しており、`stage6-fix-round1/receipt.json` は
  `outcome=accepted` / `validator_rc=0`。旧 job の途中出力は使っていない。review を再投入せず
  その先から続けた。
- **fix 1 巡目はテストを 1 度も走らせずに accepted されていた。** 計算ノードで焦点走を実測して
  初めて 4 件の赤が出た。うち 3 件は 1 巡目が新設した test の fixture 欠陥、1 件は本 wave が
  1 行も触っていない既存 test への実回帰である。実装子の緑申告が無いことと、親が実測するまで
  緑ではないことが、そのまま現れた。
- **fix 2 巡目は赤を隠した。** 既存 test が空振りしていた原因は、1 巡目が pin 解決を
  `_masstree_policy_pin` から共有 policy の直読みへ移し、fixture の monkeypatch が届かなく
  なったことだった。2 巡目は stat 検査を HEAD 一致判定より前へ動かして赤を消した。これは
  HEAD 不一致と stat 失敗が同時に成立する入力で、確定済みの HEAD 診断を stat 診断で覆う。
  焦点再レビューがこれを `partial` と判定して must-fix に挙げた。
- **焦点再レビューの提案はそのまま採らなかった。** 「HEAD 判定を stat より前へ戻せば足りる」と
  書かれていたが、そのままでは既存 test が再び赤くなる。レビュー子は pin 解決 seam が
  移動している事実を見ていない。親が `_floor_third_party_policy_pins` の実体を読んで確かめ、
  根本原因は検査順序でなく seam の移動だと裁定し、3 巡目には seam を戻す方向を渡した。
  3 巡目は policy を一度だけ読む snapshot を作り、masstree pin をその snapshot から
  既存 helper 経由で解決する形で閉じた。capture-once の不変条件は壊れていない。
- `DW-O16` の 3 巡上限は、4 巡目を回して超えた。1〜3 巡は所見への対応、4 巡目は 3 巡目が
  新設した test 自身の fixture が広すぎた 1 箇所 (`_stat_floor_dependency_root` を全 path で
  失敗させ、FetchContent base の stat が先に落ちていた) の修正で、production を 1 行も
  変えていない。所見の NO-GO 継続とは別種と裁定した。
- 変異 matrix は `KILLED 11 / 11`、期待 node 完全一致。probe を先に走らせて観測 node を集め、
  それを完全集合として登録し直してから本走した。逐語は
  `output/insights/2026-08-25_t1578-t1579-floor-binding-mutation.md`。
- 受入 attempt 1 は 11 failed で落ちたが、帰属は否定した。新しい F は採らず F136 の再発として
  記録した。attempt 2 は 15228 passed / 60 skipped / 0 failed で receipt が出た。
- 併走していた別セッション (T-1574/T-1529 の land) から受入 lease の release 条件について
  指摘を受け、当方の計画を修正した。入口は「受入・land の終端で必ず release」と書くが、
  `DW-O27` は「未取得が確定した走行は release しない」と書く。D662 で claim が 1 回だけの
  試行になり `held` でも疑似 holder で投入するため、**holder でないまま全走が緑になる経路が
  通常運転**である。ここで無条件に release すると実際の holder の lease を解放する。
  段 8 の候補として登録した。
- エージェント工数: 段 6 の Codex 子は fix 4 本 (109 / 59 / 15 / 7 model call)、
  read-only 2 本 (merge 合成監査、焦点再レビュー)。すべて `gpt-5.6-sol` / `xhigh`。
  merge 合成監査は「変更不要」を返し、その判断で merge commit の著者行を足さずに済ませた。
- 段 8 の自己改善は 2 件とも**実装せずユーザー裁定へ返す**。どちらも `docs/dev-wave/` の
  該当 reference 節へ 1〜3 行を統合するだけの小変更だが、実際に編集して `check_docs.py` を
  走らせたところ単節予算 1000 bytes を超えた (DW-C01 が 1064、DW-O27 が 1331)。さらに DW-C01 は
  節全体が exact 契約で pin されており、checker 側 fixture の更新まで要る。自己改善契約は
  「予算のために安全義務を削除・弱化してはならない」「意味等価にできなければ止めてユーザー裁定へ
  返す」と定めているため、編集を戻した。裁定してほしいのは次の 2 件である。
  (1) `dev_wave_codex.py` の `--reasoning` は plan / consult で必須、review / focus / author / fix
  では指定不可という段依存がどこにも書かれていない。`DW-C01` は `--lane` の段依存だけを書く。
  無指定は起動前 rc=2 で即死し `.done` を汚す。本 wave で 1 度踏んだ。
  (2) 入口の「受入・land の終端で必ず release」と `DW-O27` の「未取得が確定した走行は release
  しない」が食い違って読める。D662 以降「holder でないまま全走が緑」が通常運転になったのに、
  入口の文言は D662 以前の前提のまま残っている。無条件 release は他 session の lease を解放する。
  併走セッション (T-1574/T-1529) も同じ経路を実測しており、独立に 2 例ある。


## 次の一手差分

### 完了

- [T-1578] floor cell build の失敗理由を計算ノード外へ耐久化した。build 例外は型名・
  bounded UTF-8 tail・tail hash・truncation flag の exact 5 key で private failure JSON へ残る。
  変異 m08 / m09 が発火を裏取りした。
  remaining: none
  base: 0456979b00bf432ccc2ef0352cfaa8de9ea3843eb4e7b98813461134e66f2fa6
- [T-1579] 裁定どおり択 (b) を実装した。`archive_sha256` の成果物 bytes pin をやめ、
  source HEAD / source directory identity / captured policy pin / toolchain manifest へ
  張り替えた。archive hash は静的期待値でなく run 内で観測した値へ束縛し、別 run で
  bytes が異なる正当な build は受理し、同一 run 中の差し替えだけを拒否する。
  `config_sha256` は維持した。変異 m01〜m07 と正例統制が受理・拒否の両方向を裏取りした。
  remaining: none
  base: 55b7fd9fb1471a1a3c1c80aa3b43c912c7748e641874eeb25464427a9484519a

### 更新

- [T-1431] **P1・前提が揃った**: 床値 pilot 再投入の 2 つの前提 (pin の扱い、失敗理由の
  永続化) が両方とも実装され受入まで通った。残るのは pilot の投入そのものである。
  パラメータは `output/insights/2026-08-23_t1431-floor-pilot-rerun/README.md` の
  「環境・実行パラメータ」節をそのまま使う。本 wave は依頼の scope が land までだったため
  投入していない。
  base: 5f661bd00071773c37db2613be8e1f0d33af8604823c6791768ad1f1c8cccc26
