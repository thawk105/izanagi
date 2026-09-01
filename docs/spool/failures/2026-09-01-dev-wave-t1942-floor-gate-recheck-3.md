---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1942-floor-gate-recheck
seq: 3
---

## 新規

### {{F:seam-registration-disables-its-own-production-path}}. 同じ commit で production 経路へ無条件配線した引数を不適格 seam へ登録し、その経路を到達不能にした [恒真ゲート] [手順漏れ]

- 事象: 床値 campaign の staged FetchContent transport を job script へ無条件配線した commit が、
  同時に同じ引数名を refreeze 不適格 seam 集合へ登録した。結果、official mode は非既定 seam を
  理由に承認 gate の手前で拒否するようになり、**正規 job script を通る走行は pilot でも
  `eligible_for_refreeze` になれなくなった。** この状態が 10 日間気づかれず、後続の裁定
  (承認束縛の設計) は「あとは承認束縛だけ」という前提のまま下された。
- 根本原因: 配線側 (shell の argv) と分類側 (Python の seam 集合) を同じ commit で変えたが、
  **両者を突き合わせる検査が無かった。** commit message は offline build の生死実験には触れて
  いるが、適格性への影響には触れていない。生死実験は「build が通るか」だけを見ており、
  「その走行が適格になるか」を見ていない。
- 恒久対応: {{D:floor-official-transport-seam-conflict}} で機構を確定し、解消案を裁定へ返した。
  検査の実体化は解消案の選択後に行う (どの案を採るかで検査対象が変わるため)。
- 再発検知: 不適格 seam 集合の各要素について、正規の投入経路がその引数を渡していないことを
  機械的に照合する検査。現時点では未実装であり、**この項目は宣言だけの対応ではなく
  「未実装であること」を明示した記録である。**

### {{F:test-fixture-wrote-into-shared-durable-admission-root}}. テストの試行登録簿が共有の耐久 admission root へ実在し、運用判定の根拠に使われかけた [計測汚染] [恒真ゲート]

- 事象: 共有 admission root の `floor-attempt-registries/` に登録簿が 1 本あり、親はこれを
  実 pilot の消費記録と読んで「official の枠は 0 から始まる」と推論した。実際には holdout key が
  `rr23` / `rr79`、`process_identity.execution_uuid` が `campaign-fixture-execution` という
  fixture 値であり、さらに現行 consumer の canonical path と階層が違っていた。
- 根本原因: (a) テストが共有耐久領域へ書ける。(b) 親が成果物の中身 (holdout key・identity) を
  見る前に、directory の存在と件数だけで種類を判定した。
- 恒久対応: {{D:floor-fresh-claim-authority}} で判定の権威を世代 scope の claim に固定し、
  試行登録簿を判定根拠から外した。テスト側の書き込み経路の是正は scope 外として裁定へ返した。
- 再発検知: 共有 admission root の成果物を運用判定に使う前に、`execution_uuid` と holdout key が
  実 freeze の値と一致することを照合する。本 wave では親が段 3 の指摘を受けて実行した。
