単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze

必読事項の射影: 次の絶対パスを読む。**この射影に挙げた file を読めなければ即停止し、読めなかった path を報告せよ。** 射影外の path を自分で構成して不在だったことは停止理由にしない。

**このレンズに限り、worktree root `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze` 配下の全域検索を明示的に許可する** (`git grep` / `git ls-files` / `find` / `zcat` など)。閉包を取るのがこのレンズの仕事だからである。検索で当たった file は読んでよい。ただし repo の外は読まない。

- /home/SFC/tanab/.claude/jobs/f1ebd45c/tmp/wave-t2288/s1-brief.md — 親の段 1 brief (検査対象)
- /home/SFC/tanab/.claude/jobs/f1ebd45c/tmp/wave-t2288/artifacts/dev-wave-t2288-floor-spec-freeze/s2-plan.md — 段 2 plan (検査対象)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/floor_pair_driver.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/s8b_binary_admission.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/s8b_floor_campaign.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/calibration_verify.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/tests/test_floor_pair_driver.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/phase3-b4-reflux-ablation-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/decisions.md — 見出し検索で該当 D だけ読む
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/env/pegasus/calibration/registered/ — 登録済み較正 4 file
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/insights/2026-09-09/t2288-b4-floor-cellset/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/insights/2026-09-13/t2288-b4-floor-aggregate/README.md

## レンズ B — 閉包と反証

**あなたの仕事は「凍結できない」を反証することである。** 親は「今の main では 3 spec を凍結できない、
差分ゼロで返す」と provisional に裁定した。**その裁定が誤りであることを積極的に示せ。**
示せないなら「示せなかった」と書き、どこまで探したかを閉包として残せ。

具体的に次を攻めよ。

1. **親の「0 件」は閉包として成立するか。** 親は (a) rratio=5 の accepted calibration 0 件、
   (b) tracked な `s8b-binary-admission/v3` receipt の実 instance 0 件、(c) tracked な
   `floor-pair-spec/v3` の実 instance 0 件、と実測したと主張している。
   **path 検索だけで数えた不在は不在の証明にならない。** schema literal・key 名・別命名・
   別 directory・別形式 (埋め込み・gz・base64) も当たって、数え落としを探せ。
2. **較正の代替経路。** `calibration_verify.load_verified_calibration` の `attestation_mode` の
   全値域を読み、rr5 の accepted 較正が無いまま spec を凍結できる合法な mode が本当に無いかを確かめよ。
   `calibration=None` を返す mode を driver がどう扱うかも読め。
3. **build receipt の代替経路。** `artifacts[]` を空にできるか、既存の s8b campaign 成果物から
   receipt を再利用できるか、`_validate_build_receipt` が受ける最小の record は何かを実コードで確かめよ。
4. **「3 spec」の解釈。** D1936 項 7 が要求するのは本当に 3 件か。1 件や 2 件で先に凍結して後から
   足す形が既裁定と両立するか。事前登録 §5 の集約規則 (b)(c) と issuer の実装で確かめよ。
5. **順序の反証。** 「凍結 → 較正取得 → 測定」の順は許されるか。事前登録 §11.1 の手順 4〜7 の順序と、
   spec が calibration を pin する構造から、凍結が較正より前に来られるかを判定せよ。

## 禁止

- schema / validator の拡張案を出さない (D1696)。
- workload 一致要求を外す案を出さない (D15)。
- 床値の測定・較正の取得そのものを計画しない (scope 外)。
- 新しい gate・検査・台帳・一般化を提案しない。
- **正しさゲートを緩める方向の反証を「できる」と書かない。** 反証は「既裁定と絶対規律 2 を守ったまま
  凍結できる」道が実在する場合にだけ成立する。緩めれば通る、は反証ではない。
- file を書かない。commit しない。sandbox は read-only である。pytest 緑は要求しない。静的検査でよい。

## 出力形式

## 総括
3〜6 行。反証できたか、できなかったか。できたなら何が凍結できるか。

## 反証の試行と結果
試行ごとに H3。「仮説」「調べた現物 (file:line / artifact path / 検索語)」「結果」。
**失敗した試行も全部書く。** それが閉包の証拠である。

## 親 brief と plan の誤り
行番号・件数・「0 件」の主張を自分で現物に当たって検算した結果。無ければ「無し」。

## 数え落としの残余
自分が探しきれなかった範囲を名指しする。

## 本報告が保証しないこと

予算が尽きそうなら、途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
