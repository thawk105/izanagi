---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: t979-cheap-history-scan
seq: 1
---

## 新規

### {{F:self-referential-argv-guard}}. guard が自分の pin 対象から argv を導出しており、定数自身の変異を通した [恒真ゲート]

- 事象: 高価 argv を凍結 tuple 定数に閉じ、`_git` へ渡す直前に
  「完成 argv が凍結定数のいずれかと一致するか」を検査する guard を置いた。
  builder を差し替える変異は止まるが、**定数そのものへ `-C` を足す変異は比較対象も同時に
  変わるため素通りする**。`-C` を 2 回書くのは `--find-copies-harder` と同義であり、
  受理集合を承認外に拡大する変異だった。実際に止めていたのはテスト側の literal 比較だけで、
  「production の機械 guard が禁止 flag を殺す」という主張は成立していなかった。
- 根本原因: guard の判定基準を、guard が守るべき対象そのもの (凍結定数) から導出した。
  自己参照の比較は恒真であり、対象が動けば基準も動く。
- 恒久対応: 判定基準を**対象から導出しない独立 literal** で書く
  ({{D:cheap-first-history-scan}} の argv 検査 = 許可 token 集合・`-C` と `-M` の重複禁止・
  `--find-copies-harder` の不在)。凍結定数との完全一致検査は多重防壁として残すが、
  安全性の根拠には数えない。
- 再発検知: 変異 M6 (高価 argv 定数へ `-C` を足す) を負例として
  `orchestrator/tests/test_t080_freeze_migration.py` の変異 matrix に事前登録した。
  fix 前は赤 1 件 (テストの literal 比較のみ)、fix 後は赤 14 件 (うち 13 件が production guard 由来)。
- 検出経緯: 段 6 の敵対レビュー 2 本が独立に摘出した。段 2 起草・段 4 裁定・段 5 実装はいずれも
  通していた。**変異を走らせる前に静的レビューが捕まえた near miss** であり、
  land 前に閉じたため production 事故には至っていない。

### {{F:coverage-inventory-without-tracing-judgment-order}}. 判定順を追わずに既存検査の被覆を棚卸しし、純増検出力を誤って主張した [テスト代表性]

- 事象: 段 1 brief が「既存の near-copy テストは `--find-copies-harder` の追加を検出しない
  (flag を足しても near-copy は `C` のままで dst OID が一致しないため `False` のまま通る)」と書き、
  この検査の新設を「純増」として計上した。**実装は OID 比較より先に
  `status in {M,D,R,C,T} and path in paths` を見る**ため、harder が付くと near-copy は
  `C <target> <copy>` になり対象 path が paths に入り、判定は `True` へ変わって既存テストは赤になる。
  既存検査は実際には検出していた。
- 根本原因: 被覆の棚卸しを、条件の**評価順序**を実コードで追わずに、条件の存在だけを見て行った。
  短絡評価では先に真になる条件が後続の条件を隠す。
- 恒久対応: 検査を新設する wave の「純増検出力」は、**既存検査を実際に赤にする変異を 1 件
  構成できたときだけ**「純増ゼロ」と書き、構成できないときは「純増」と書く。
  本 wave では新旧両走 ({{D:cheap-first-history-scan}} の検出器移動の実証) がこの役割を果たし、
  wave 前 HEAD へ同一変異を当てて赤 1 件を実測した。DW-M08 の新旧両走をこの用途にも使う。
- 再発検知: 段 3 の敵対レンズが親 brief 自身を攻撃対象に含める契約 (`DW-S03`) が検出した。
  親は指摘を synthetic repo の実測 (`-M -C` / `-M -C --find-copies-harder` / `-M -C -C` の
  raw 出力と判定値の対照表) で裏取りしてから採用した。
- 影響: 誤りは段 4 裁定で訂正済みで、受理集合にも成果物にも波及していない。
  ただし**この誤りを信じたまま二段構えにしていたら、`--find-copies-harder` の検出器が
  静かに消えたことに気づけなかった** (二段構えでは near-copy が高価走行に到達しないため、
  既存テストは緑のまま通る)。
