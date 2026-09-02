---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2176-dense-cycle4-fixture
seq: 1
title: [T-2176] clean な長さ 4 巡回の負例を足した — 当該変異は既存スイート全体を素通りしており、新テスト単独で殺した (コード + テスト + insight、branch worktree-dev-wave-t2176-dense-cycle4-fixture、変異 before SURVIVED → after KILLED)
---

## 本文

- 依頼は D1455 の実装。**production の差分は 0** で、足したのは手製 fixture
  `orchestrator/tests/fixtures/r9_dense_cycle4/` (2 file)、新テスト
  `test_dense_cycle4_clean_g2`、在庫 `_V2_FIXTURE_FILES` の 2 行、fixtures README の表 1 行。
- **穴が実在したことを実測で確定した。** 変異 M2 (clean な入力に限って長さ 4 以上の巡回を
  報告と `total` から落とす) は、**変更前 HEAD の木では SURVIVED** だった。verifier を参照する
  17 file・1562 node のどれも赤にならない。変更後の木では KILLED になり、赤くなったのは
  新テスト 1 件だけである。DW-M08 の「新旧両走」を 2 アームで走らせた結果で、数値の正本は
  `output/insights/2026-09-02_t2176-dense-cycle4-fixture/mutation-matrix.md`。
- **無条件版の変異 M1 だけを見ると穴を見落とす。** M1 は変更前から既存の r5 テストが殺していた。
  r5 が担っていたのは `non-serializable` というグラフ事実の検出までで、`missing_txids=46` で
  integrity が unclean なため certified へ倒れる経路は担っていない。M1 と M2 を対で登録して
  はじめてこの区別が見える。無条件版だけを登録していれば「既に塞がっている」と誤読していた。
- **親 brief の前提が 2 つ覆った。** (a) 1 file 構成は段 2 のプラン子が realizability を根拠に
  却下した。1 file = 1 thread は逐次実行なので、T3 が genesis を読んだまま最後に commit する
  実行を表せない。2 thread へ変えた。(b) `fixtures/README.md` の 179 行目を訂正する親の裁定は、
  段 3 の検査 B が D1466 を名指しして覆した。同記述の訂正は T-2177 が所有し、r5 の
  グラフ検出と certified 遷移の区別を落とさずに書くことを D1466 が要求している。本 wave は
  表へ 1 行足すだけにし、179 行目には触れていない。親が段 1 で D1466 を引いていなかった。
- **同一性層は「壊した変異」と「何も変えない変異」を区別しないことを、別の分母で再現した。**
  `dsg.py` を 1 byte でも変えると `CONTRACT_LOADER_RELATIVE_PATHS` の HEAD blob 束縛が発火し、
  分母 1562 node のうち 97 node が `contract-loader-drift` で赤になる。等価変異 M3 でも同じ
  97 node が赤になり、M1・M2 の失敗集合はこれを部分集合として含む。D1422 / エントリ 1176 が
  53 node で測った現象と同型である。本 wave の変異走ではこの 97 node を deselect した
  (`--collect-only` で 1465/1562 になることを確認済み)。
- 段 6 の敵対レビューは 2 本とも must-fix ゼロだった。レビュー A は新テストの 13 個の assert を
  1 つずつ含意関係で判定し恒真なものが無いことを確認、レビュー B は在庫・件数・集合を pin する
  検査を悉皆検索して `_V2_FIXTURE_FILES` 以外に無いことを確認した。所見ゼロは変異なしで緑と
  数えず、上記の変異 matrix を実走した。
- **意図的に塞がなかったものを 1 つ記録する。** file 名と `thid` の対応 (T3 の frame を
  `trace_0.log` へ移し `trace_1.log` を空にする改変) は新テストの pin では捕まらない。
  仮想リスク向けの検査器新設は scope 外としたため、捕まらないことを insight に明記した。
- **セッション異常。** (a) `tools/dev_wave_wait.py producer` が producer 生存中に rc=0 で戻る
  事象を 3 回観測した (`/proc/<pid>/stat を読めないため pid-only へ縮退します` の直後)。
  `.done` の不在で毎回気づけたが、`.done` を見ずに完了と読めば未完の成果物を採ることになる。
  {{F:producer-waiter-returns-while-alive}} に記録した。(b) DW-M08 の「変更前 HEAD の木」を
  自分で作る際に submodule 初期化を落とし、before アームの baseline が 84 件赤になって
  harness の fail-closed で 1 走を捨てた。(c) F810 (submodule 初期化 tool の 1 回目が必ず落ちる)
  を今回も再現した。
- **段 8 の自己改善は 3 候補を routing し、docs 編集は 0 件で閉じた。** (a) F810 の再発と
  (b) 待ち手の早期復帰は failures fragment へ送った。(c)「比較用に自分で作る木にも submodule
  初期化が要る」を `DW-M08` へ 1 文足す案は、`check_docs.py` が
  `L1.5 unique footprint 9743 bytes > 予算 9696 bytes` で拒否した。D782 が委任する D730 の手順に
  従い、既存記述から意味を保ったまま 47 bytes を削る余地を探したが見つからず、本件の実測例は
  **1 件で D730 が例外収容に求める独立 3 例に満たない**ため、上限は引き上げず収容を見送った。
  義務そのものは `DW-O08` に既にあり、失敗台帳側に「手で作った比較用の木にも適用される」と
  明記してある。同型が 3 例に達した時点で収容を再検討する。
- 子は 6 本 (plan 1・consult 2・author 1・review 2)。いずれも rc=0 で採用 gate 緑。

## 次の一手差分

### 完了

- [T-2176] 密な txid の手製 fixture `r9_dense_cycle4` と負例テストを足し、当該変異が既存スイートを
  素通りしていたこと、および新テスト単独で殺すことを DW-M08 の新旧両走で実測した。
  remaining: none
  base: ce09db784e9a28a7cc63d46aef9cae50fe04ff1a59f59dcc0f48803b44eaf4ae

### 新規

- {{T:downstream-longcycle-independent-check}} **P2・新規**: verifier が誤って `certified=True` を
  発行した場合、campaign pipeline・commit receipt・artifact admission・oracle driver / report・
  層 3 report はいずれも DSG を再計算せずその値を運ぶため、同じ壊れ方が全層を通過する。
  downstream に verifier から独立した長周期の意味検査を要求するかを裁定する。根拠の file:line は
  `output/insights/2026-09-02_t2176-dense-cycle4-fixture/verbatim/s3-lensB.md` の所見 4。
