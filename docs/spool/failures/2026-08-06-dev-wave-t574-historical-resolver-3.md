---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t574-historical-resolver
seq: 3
---

## 新規

### {{F:readonly-entry-shared-with-live-admission}}. 「read-only 再検証」と分類した入口が live 実走 admission と共用だった [誤分類]

- 事象: 段 1 brief が 4 つの consumer を「publish 済み成果物の read-only 再検証」と分類し、
  そこだけ受理集合を広げれば live 経路は無傷だとする不変条件を立てた。実際には
  そのうち 3 つを含む関数が oracle driver の実走 admission そのもので、通過後に
  marker・WAL・予算が書かれる。段 3 の敵対相談 2 レンズが独立に blocker として検出した
- 根本原因: 入口の性質を**呼び出し元をたどらずに関数名と docstring から**推定した。
  「再検証」と読める名前の関数が、同時に実行の前提条件を満たす gate でもある、という
  二役を見落とした
- 恒久対応: 受理集合を広げる wave の段 1 では、対象関数の呼び出し元を実際に列挙し、
  **その戻り値を消費して副作用を起こす経路が 1 本でもあるか**を file:line で確認してから
  「read-only」と分類する。確認できないものは read-only と呼ばない
- 再発検知: 段 1 brief の scope 表に「この入口の戻り値を消費して書き込みを行う経路」列を設け、
  空欄のまま子を起動しない

### {{F:redundant-gate-counted-as-new-guarantee}}. 新設した検査が既存層と冗長で、変異が単独では殺せなかった [恒真ゲート]

- 事象: 実装子が履歴解決の返り値に対する hash 再検査を 2 箇所へ足したが、変異検査で
  どちらを消しても、両方消しても既存 test は緑のままだった。実際に落としていたのは
  さらに下流にある既存の等値検査で、新設 2 箇所は冗長だった。3 層すべてを外す変異では KILLED になり、
  実効 gate が既存層であることが確定した
- 根本原因: 「fail-closed を足した」ことを、その検査が**単独で受理集合を決めている**証拠と
  取り違えた。前後に同じ入力を拒否する層があるかを、実装前にコードで確認していなかった
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M01` (同じ入力を拒否する層が前後に無いことを
  コードで確認してから登録する) と `DW-M02` (生存したら mask を疑い実効 gate へ再照準し
  両層同時変異まで裏取りする) を、新設検査ごとに適用する。冗長と判明した層は
  「冗長 gate」と台帳へ明記し、単独変異の受理集合 kill 証拠から外す
- 再発検知: 変異事前登録の各行に「この位置の前後で同じ入力を拒否する層」欄を書き、
  空欄で登録しない

## 再発

### F30

- **再発: 2026-08-06** — 三度目。今回は **role 名を key にした pin** を数え落とした。段 1 で
  `grep -rn "<編集する module path>"` を走らせて「publish 済み artifact に旧 hash を pin した
  ものは 0 件」と結論したが、実際には `output/env/pegasus/t419-probe-causality/**/manifest.json`
  が `env_contract_sha256` という **role 名 key** で同 module の旧 sha を保持していた
  (path 文字列を持たないため path 検索に掛からない)。`DW-O09` は F30 の恒久対応として
  「role 名を key に張る pin は key 側でも検索し、path の hit 0 件を pin なしと結論しない」と
  既に明記しており、**本文を読んだうえで path 検索だけで結論した**。段 3 のレンズが訂正した。
  今回は当該 module を変更しなかったため実害はない。恒久対応は `DW-O09` から変更なし
