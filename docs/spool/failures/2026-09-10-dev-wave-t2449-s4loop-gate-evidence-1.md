---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2449-s4loop-gate-evidence
seq: 1
---

## 新規

### {{F:frozen-record-read-as-live-contract}}. 過去実走の凍結 evidence を「現行 producer を縛る live 契約」と読み、依頼された成果物を子が自ら scope から落とした [手順漏れ] [ドリフト]

- 事象: 段 2 のプラン起草で、親が「red arm record の bytes を hash 束縛する consumer が存在するなら
  argv 追記は採用不能」という条件を子へ渡した。子は
  `output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/full-file-sha256.json` が
  red canonical record を内包する過去 evidence を whole-file sha256 で束縛していることを見つけ、
  条件が成立したと判定して、**依頼が明示していた成果物 (preprocess argv の採取) を自ら scope から
  落とした**。プラン本文には「live consumer は無い」「固定 digest golden も無い」と自分で書いており、
  それでも凍結 manifest の存在だけで撤回している。
- 根本原因: 親が渡した条件が、**(a) 現行 producer の出力を再導出して比較する live 契約**と、
  **(b) 過去実走の bytes を記録しただけの provenance 記録**を区別していなかった。
  (b) は producer を変えても 1 bit も動かないので、変更を禁じる根拠にならない (絶対規律 7)。
- 恒久対応: 親が子へ「hash 束縛があるなら不採用」型の条件を渡すときは、live 契約と過去実走の
  provenance 記録を区別して書く。hit した pin について「その値を再導出して比較する経路が今も走るか」を
  子に答えさせ、走らないものを禁止理由に数えない。
- 再発検知: 段 3 の敵対レンズに「段 2 が『存在する』と断定した束縛を自分で引き直せ。検索語が狭い
  可能性を疑い、別の検索語を使え」を入れる。本 wave では親の独立実測
  (`git grep -ln "full-file-sha256"` が `*.py` / `*.json` / `docs/*` で 0 件、凍結 hash と insight dir 名の
  全文検索 hit は archive worklog・decisions・当の insight 自身・別 insight の逐語だけ、対象 3 test file の
  64 桁 hex literal も 0 件) と、段 3 の 2 レンズが独立に同じ結論へ達したことで捕まえた。
