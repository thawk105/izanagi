---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t817-epoch
seq: 2
---

## 新規

### {{F:new-gate-preempts-downstream-checks}}. 新設 gate の変異が、事前登録した期待 node の 30 倍を赤にした [事前登録の不完全] [変異]

- 事象: [T-817] の変異本走で MUT-4 / MUT-5 / MUT-7 が MISMATCH。段 4 で登録した期待 node は
  各 1 件だったが、実際の kill は 31 / 8 / 30 件だった。SURVIVED ではなく、検出力は十分にある。
- 根本原因: 新設した中央受理 gate が発火すると**後段の検査が走らない**。gate を壊す変異は
  受理層より下流の全経路を巻き込むため、`test_nontrigger_historical_campaigns_remain_admitted`
  の全 param のように、一見無関係な既存テストが同じ分岐に依存し始める。段 4 の事前登録時点で
  この集合を完全に列挙するのは現実的でない。
- 恒久対応: `DW-M08` が既に許している「初回を probe と明記し、期待 node を完全集合として
  再登録して再走する」手順で閉じる。採用の根拠は **baseline が完全に緑 (rc=0、赤 0 件) である**
  こと — 観測された赤がすべて注入変異由来だと言えるのはこの条件が成り立つときだけである。
  probe 台帳は消さず erratum として残す。
- 再発検知: 受理層・admission・gate を新設する wave では、段 4 の事前登録に
  「この gate が発火したとき走らなくなる後段検査の件数」を見積もり欄として書き、
  1 件しか登録していないなら probe 前提で計画する。

### {{F:non-conflicting-merge-hides-semantic-breakage}}. 行が競合しなかった面に、取り込みの意味破壊が 3 件あった [取り込み] [合成監査漏れ]

- 事象: [T-817] wave へ local main を 69 commit 取り込んだところ、`git merge` が報告した競合は
  1 ファイル 1 hunk だけだったが、conflict marker が出なかった面に 3 件の破壊があった。
  (a) main から入った `require_admitted_campaign` 呼び出し 2 件が purpose を省略しており、
  本 wave が必須化した引数を満たさない。(b) main 側 wave [T-856] が新設した合成 fixture が
  `campaign_verifier_epochs` を持たないため、本 wave の gate が fail-closed で発火し、
  下流 assertion が 2 件落ちた。
- 根本原因: 3-way merge は**行の重なり**だけを競合として報告する。片側が「呼び出し規約を厳しく
  した」ときに、もう片側が**その規約を知らずに新しい呼び出しを足した**場合、行は重ならないので
  自動 merge が成功してしまう。競合ゼロは意味が保たれた証拠ではない。
- 恒久対応: 呼び出し規約・受理集合・必須引数を変える wave の取り込みでは、競合の有無に関わらず
  Codex `role=author` へ**合成監査**を明示的に依頼する。監査の形は「変更した識別子の全呼び出しを
  AST で数え上げ、新契約を満たす件数と満たさない件数を報告する」。本 wave では実呼び出し 65 件の
  うち production 16/16・test 48/49 という数え上げで穴が特定できた。
- 再発検知: 合成監査の報告に「満たさない件数」欄を必須にする。ゼロと書くなら何を母集合として
  数えたかを併記させる (`DW-O17` の実装面 path 判定だけでは行が競合しない破壊を捕まえられない)。

## 再発

### F301

- **再発: 2026-08-16** — [T-817] wave の受入全走で
  `test_t671_source_binding.py::test_production_contract_loader_binding_call_sites_are_exact`
  が赤になった。本 wave が epoch 導出のため `artifact_admission.py` へ
  `contract_loader_binding.capture_contract_loader_binding()` を 1 箇所足したが、
  同 file の呼び出し位置を exact な Counter で pin している側を数え落としていた。
  **前回は bytes hash の pin、今回は呼び出し位置 (file 名 + 関数名 + 属性名) の pin** で、
  いずれも「編集面 path を key にした検索」を実行していれば段 1 で見つかっていた。
  焦点走 28 file にこの pin test が入っておらず、**受入で初めて出た**。
  fix 後に live な exact pin / golden を 17 面数え上げ、全面一致を確認している。
