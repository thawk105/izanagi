---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2288-b4-floor-aggregate
seq: 1
title: [T-2288] B-4 床値の集約規則を事前登録へ追補し、既存 floor pin へ渡す配線を作った (docs + コード、branch worktree-dev-wave-t2288-b4-floor-aggregate)
---

## 本文

- 依頼は D1936 項 7 (= D1855 案 B) の実装。着手前の実測で、**床値の実測そのものは本 wave では
  開始できない**ことを確認した。凍結 spec は calibration を 1 件だけ束縛し cell ごとに
  workload 一致を要求するが、登録済み較正 3 件はすべて rr50 / 48 スレッドで、rr95 と rr5 は 0 件。
  `floor-pair-spec/v3` の実体も schema 文字列検索の範囲で 0 件だった。裁定の理由文も
  「取得には項 6 の停止原因解消が先に要る」と述べている。よって本 wave は**規則と配線に限定**し、
  較正取得と測定は scope 外とした。「将来も不可能」とは書かない (段 3 の反証を採用)。
- **段 3 の敵対相談が親 brief の過大主張を 8 点訂正した。** 主なもの — 「足りないのは集約規則だけ」は
  summary が spec の閉包を覆っていることの検査も要る、「spec を pin すれば閉じる」は summary の被覆と
  §5 対象集合への適合までは含意しない、「Fraction 比較で下振れを防ぐ」は誤り (有限 binary64 の
  順序は float 比較と同じで、Fraction の意味は exact 保存)、「受入は login node のみ」は runner の
  場所判定と矛盾、「変異は対応 test だけを赤にする」は共有検査では成立しない。
- **凍結範囲の検算を子が独立に行った。** 実コードから純粋関数を抽出してメモリ上で §5.1.1 の
  raw / semantic 両 hash を再計算し、現行値と一致させたうえで挿入位置ごとの可否表を作った。
  237 行直後は範囲外で安全、§6 直前は生バイトが変わる。親も追補を入れた後に両 pin 不変を実測した。
- **段 6 のレビュー 2 本が must-fix を 2 件出した。** (1) 実装が「異なる spec 同士でも window の
  出力先を共有してはならない」という**追補に無い受理条件**を足しており、契約より狭かった。除去した。
  (2) 追加テストがすべて内部関数を直接組み立てる単位で、**閉包検査や再構成比較を削除しても到達しない**。
  段 4 で登録した正例が未作成だった。
- **fix 1 巡目が親の指示の誤りを指摘して止まった。** 親が要求した負例「期待 spec 列と summary を
  同時に 1 組落とす」は、残りの閉包が一致する以上、追補に拒否の根拠が無い。追補 (f) が
  「期待列が結果より先に選ばれたことは証明しない」と明記している以上、これは人手の採用責任の側である。
  親が当該負例を撤回した。一方、同じ巡で出た「既存 helper の monkeypatch は迂回になる」は採らなかった —
  それは既存 issuer テスト全体が使う定型の seam であり、本 wave が検査する機構ではない。
  この裁定を渡した 2 巡目で公開経路の正例と公開 API 負例 4 件が実装された。
- **変異検査が実在の欠落を 1 件出した。** probe 走行で 8 変異中 7 件が検出されたが、
  「各 spec の窓はちょうど 2」の要求を「1 以上」へ緩める変異だけが**失敗 node 0 件で生き残った**。
  正例がすべて 2 窓なので、緩める向きを誰も検出できなかった。fix 3 巡目で窓 1 件・3 件の負例を足した。
  本走は 2 度行い、1 度目は M4 の期待 node が 14 件で観測 15 件と食い違った (足した 3 窓負例も
  M4 で赤になる)。観測の完全集合で再登録し、再走で 8/8 KILLED・baseline PASSED・wrapper rc=0。
  1 度目の結果は消していない。公開経路の正例は M1・M4・M7 を殺しており、空回りではない。
- 親が実走した検査は issuer 79 passed、material report 49 passed、事前登録 consumer 33 passed、
  `tools/check_docs.py` 違反なし、`tools/check_ai_provenance.py` full で 9713 件・新規違反なし。
  **最終受入全走は本記録 commit と段 8 の commit を固定した後に既存 acceptance 経路で実行し、
  耐久 receipt を共通 land が検証する。**
- エージェント工数 — 段 2 plan 1 本、段 3 敵対 2 本、段 5 実装 1 本、段 6 レビュー 2 本、fix 3 本の
  計 9 子。すべて `tools/check_codex_output.py` rc=0。実装子と fix 子はいずれも sandbox で
  pytest を実走できず (login node の hook 拒否と runner rc=16)、実走はすべて親が行った。
  子は「未実走」を緑と書かず正直に申告した。
- 設計判断は {{D:b4-floor-aggregate-rule}}。実装・相談・検査・生証拠の所在 =
  output/insights/2026-09-13/t2288-b4-floor-aggregate/README.md。

## 次の一手差分

### 更新

- [T-2288] **P1・較正取得待ち**: 集約規則の追補と集約発行・受理の配線は着地した。残るのは
  rr5 / rr95 の較正取得 (D1936 項 6 / [T-2515])、workload 別 3 spec の凍結、床値の実測、
  §5 floor 欄の記入。
  base: 74af6834852d99e79c5e452736a400ae11757fa8886221075c815d03bae8bc80

### 新規

- {{T:b4-aggregate-material-report-positive}} **P2・新規**: 集約成果物が材料レポートまで届く
  正例を作る。合成 repo に prerun publication と raw analysis が無く、公開 builder へ渡せないため
  本 wave では §5 pin 解決までで止めた。
