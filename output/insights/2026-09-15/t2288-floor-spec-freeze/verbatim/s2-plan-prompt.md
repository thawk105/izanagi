単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze

必読事項の射影: 次の絶対パスだけを読む。**この射影に挙げた file を読めなければ即停止し、読めなかった path を報告せよ。** 射影外の path を自分で構成して不在だったことは停止理由にしない。

- /home/SFC/tanab/.claude/jobs/f1ebd45c/tmp/wave-t2288/s1-brief.md — 親の段 1 brief
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/floor_pair_driver.py — 凍結 spec の loader と束縛検査
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/s8b_binary_admission.py — build receipt の発行器と検証器
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/p3_b4_floor_artifact_issuer.py — 集約成果物の発行器 (着地済み)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/tests/test_floor_pair_driver.py — 凍結 spec の合成 fixture (どんな値が通るかの現物)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/phase3-b4-reflux-ablation-preregistration.md — 事前登録。§5 の floor 欄 (集約規則の追補を含む) と §11.0〜11.3
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/decisions.md — D15 / D1641 / D1694 / D1695 / D1696 / D1936 項 6・項 7 / D1974 を見出し検索で引く。全文を読まない
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/env/pegasus/calibration/registered/ — 登録済み較正 (4 file)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/insights/2026-09-09/t2288-b4-floor-cellset/README.md — 先行 wave の確定事項
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/insights/2026-09-13/t2288-b4-floor-aggregate/README.md — 直前 wave の確定事項

## 依頼

**「今の main (`0600887d9`) で、workload 別 3 spec (`floor-pair-spec/v3`) を凍結できるか」を file:line 粒度で起草せよ。**

凍結とは、`floor_pair_driver.load_frozen_spec` が strict に受理する JSON を repo へ commit することを指す。
3 spec は read-heavy (rr95)・balanced (rr50)・write-heavy (rr5) の 1 workload ずつである (D1936 項 7 / D1855 案 B)。

具体的には次を出せ。

1. **spec の必須欄を 1 つ残らず列挙する。** `floor_pair_driver.py` の parser と `_bind_checkout_inputs` を
   読み、各欄について「exact key 集合」「型・値域」「束縛検査が要求する外部 artifact」を file:line で示す。
2. **各欄の値を、今の repo にある tracked artifact だけで埋められるかを判定する。**
   埋められるなら、その値の権威 (D 番号または artifact の絶対パス) を名指しする。
   埋められないなら、**何が無いのか**を artifact の種類と個数で示す。
3. **workload ごとに答えを分ける。** rr95 / rr50 / rr5 で結論が違うなら違うと書く。
4. **較正に依存する欄と、依存しない欄を分離する。** 依頼の中心はここである。
   「rr5 / rr95 の較正取得を待たずに凍結できる範囲があるか」に答えよ。
5. 埋められない欄があるなら、**それを埋めるために必要な作業を、既裁定と衝突しない形で列挙する。**
   どの既裁定が何を禁じているかを D 番号で示す。

## 禁止

- **schema / validator の拡張案を出さない。** D1696 が「測定前の follow-up wave で schema と validator を
  拡張する案は採らない」と裁定済みである。
- **workload 一致要求を外す案を出さない。** D15 が却下済みで、2026-09-09 の wave が段 3 で反証されている。
- **placeholder・仮値・未取得 artifact への前方参照で欄を埋める案を出さない。**
- **床値の測定・較正の取得そのものを計画しない。** この wave の scope 外である。
- 新しい gate・検査・台帳・一般化を提案しない。
- file を書かない。commit しない。sandbox は read-only である。書込可能 tmp が無いので pytest 緑は
  要求しない。静的検査でよい。テスト実走は親が行う。

## 親 brief の検査

親 brief の (P1-a)(P1-b)(P1-c) と実測表は**検査対象**である。誤っていれば名指しで訂正せよ。
行番号・件数・「0 件」という主張はすべて自分で現物に当たって確かめよ。

## 出力形式

次の H2 節をこの順で書く。

## 総括
3〜6 行。3 spec それぞれの凍結可否と、可否を決めた前提を 1 行ずつ。

## spec 必須欄の充足表
表。列は「欄 (file:line)」「要求」「rr95」「rr50」「rr5」「較正依存か」。

## 凍結できない欄と、欠けている前提
欄ごとに、欠けている artifact の種類・個数・それを作る producer の所在 (file:line) と、
それを今作ることを禁じている既裁定 (D 番号) を書く。

## 親 brief の誤り
無ければ「無し」と書く。推測で埋めない。

## 本報告が保証しないこと
静的読解にとどまる範囲、実走していない検査を明示する。

予算が尽きそうなら、途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
