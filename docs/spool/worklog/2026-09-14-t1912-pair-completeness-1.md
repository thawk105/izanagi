---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: t1912-pair-completeness
seq: 1
title: [T-1912] 対の完全性の束縛は既に着地しており、実装せず裁定へ返した (docs のみ、branch worktree-dev-wave-t1912-pair-completeness)
---

## 本文

- ユーザーが「precursor hash・on/off receipt・proposal・block id を束縛する manifest と完全性
  consumer を実装せよ」と指示した。依頼は carry item の本文をそのまま引いており、**その本文が
  事実でなくなっていた。** 実装せず裁定へ返した。
- **親が自分で測った事実:** `orchestrator/campaign/p3_b4_raw_record_producer.py` の
  `assemble_b4_raw_analysis` は `:2322-2331` で封印 registry と凍結 manifest から
  `expected_binding` (`attempt_id` / `block_id` / `driver` / `registry_sha256` / `manifest_sha256` /
  `precursor_hash = initial_proposal_sha256` / reference 3 値) を構築し、`:2333` で完全一致を
  要求する。raw の precursor は `:2366` で照合済み binding から代入され、arm の自己申告を使わない。
  on/off の source digest は `:2370` で同じ arm ループから生成される。**4 者の束縛は存在する。**
- 正例・負例も同時に着地していた。`orchestrator/tests/test_p3_b4_raw_record_producer.py:2063`
  の `test_m01_assembly_rederives_precursor_from_the_sealed_registry` は、公開済み source の
  precursor を偽値へ書き換えると `source_rederivation` で拒否されることを示す。
- 着地は `227ec68923c8a489be28861c4b2566effe140626` (2026-08-29、raw 試行記録 producer の実装 wave)。
  carry 本文が書かれた 2026-08-27 の **2 日後**である。以後 40 エントリ carry されていた。
- **段 3 の敵対相談 2 本が、レンズを分けたのに独立に同じ blocker へ到達した。** sol は
  「4 性質は現行 assembler の正常出力で既に成立しており、プランの負例は assembler の戻り値を
  後から差し替えないと構成できない」、luna は「4 検査は既存保証と重複する。別 root からの
  選別は残る」と述べた。親は両者を鵜呑みにせず producer と test の現物を読んで再確認した。
- 段 2 プランは「閉包 5 module の外に新 module を置き `p3_b4_material_report._load_and_evaluate`
  へ必須配線する」案だった。技術的には成立するが、発火するのは sanctioned assembler が正しく
  動いた**後にその戻り値だけを改竄した**場合に限られる。ユーザーが本 wave で明示的に scope 外と
  した「仮想リスク向けの gate」に当たるため採らなかった ({{D:pair-binding-already-closed}})。
- **今も開いている経路:** publication を別 root へ複数発行し、結果を見てから有利な root だけを
  材料レポート生成へ渡す選別。issuer 自身が `publication_under_a_different_root_is_not_prevented`
  と非保証に明記しており、assembler も提案 consumer も渡されなかった側の存在を知らない。
- 親 brief の誤りを 3 件、insight の訂正節へ残した。(i) 「現状は on==off しか見ていない」は
  純粋契約層だけの話で production 経路では偽、(ii) DW-G05 の成果物影響を追加検査へ帰属できない、
  (iii) 閉包 5 module の pin を hash 字面だけで検索して「機械検査なし」と結論したのは誤りで、
  `p3_b4_analysis_prereg_consumer.py:703` 以降の AST 検査が member 列と呼出し順を固定している。
- 逐語と裁定パッケージ: `output/insights/2026-09-14/t1912-pair-completeness/`。
- 段 8 の自己改善候補は 1 件 — `DW-S01` の「人間手番待ちは git / 成果物で済を照合し」を
  「無い」と書かれた項と実装側検索まで広げる案。**収容せず落とした。** D730 / D782 の手順を
  当てた結果、(i) 最小の言い換えでも L1 層が 10660 bytes となり予算 10625 bytes を 35 bytes 超え、
  (ii) 予算のために他の安全義務を削らない、(iii) 同型の独立 3 例は無い (本 wave の 1 例のみ)、
  (iv) 上限引き上げは最後の手段。同節は既に (F35) を指しており、その F35 へ本 wave の再発を
  追記したので、読み手は新しい形態へ到達できる。上限引き上げには至っていない。
- 工数: codex 子 3 本 (段 2 plan 1 本、段 3 consult 2 本)。段 5・6 は裁定により省略。
  実装面の差分はゼロなので変異 matrix は免除 (`DW-S04`)。受入全走は免除せず実走した。

## 次の一手差分

### 更新

- [T-1912] **P1・ユーザー裁定待ち**: pair の完全性のうち、block id・precursor・proposal・
  on/off receipt の 4 者を封印 registry と凍結 manifest へ束縛する部分は、2026-08-29 の
  raw 試行記録 producer 実装 (`227ec6892`) で sanctioned assembler に着地済みであり、
  正例・負例も付いている。**残るのは publication 間の選別だけである** — 別 root へ複数の
  publication を発行し、結果を見てから有利な root を材料レポートへ渡す経路。これを閉じるには
  publication を跨ぐ append-only の権威が要り、D1936 前文の「付随する gate・台帳・汎用化を
  足さない」および同項 8 の「母集合を作るための追加基盤は採らない」と衝突する。裁定は 3 点 —
  (a) 本項をこの残件へ書き換えて carry するか本項を完了として新規起票するか、(b) publication 間
  選別を閉じるか、(c) 事前登録 §7.2 / §10 の「強制しない」記述のうち偽になった部分を追補訂正するか。
  詳細と逐語は `output/insights/2026-09-14/t1912-pair-completeness/`。
  base: 7670b6d1d87132aec2fe8ae2f0c7c205366bee77480da09c25951ae9049308b0
