---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2797-b5-effect-bundle
seq: 1
title: [T-2797] B-5 生成器対照の発効束 draft を完成させ、本走の投入経路を実装した — 事前登録 §12 の採取、逆順組の schedule、LLM の exact model を起動構成で固定、rep 1 は 5 rep 維持、N1 はコード不変、推奨 k = 3・総 wall 40 倍 (コード + テスト + insight、branch worktree-dev-wave-t2797-b5-effect-bundle)
---

## 本文

- 依頼 (D2200 項 1 の段階認可の残り 3 つ: §12 の採取・rep 1 の確認・N1 の確認) を 9 段で処理した。insight は `output/insights/2026-09-22/t2797-effect-bundle/README.md`、設計判断は
  {{D:b5-registered-launch-path}} と {{D:b5-effect-bundle-draft}}。
- **依頼の前提を覆した事実 (段 1):** 「残りは採取だけ」ではなく、本走を投入する経路が試走専用のままだった (driver が header に試走の cohort と purpose を固定、launcher は試走 4 job の形だけ、
  LLM arm の prompt 生成器は repo 外の試走専用 script、知識射影は write-heavy だけ、role 子は alias 起動)。D2216 が schedule・launcher を発効束の段へ送っていたので、段 4 で
  最小の投入経路を scope に入れた (段 3 相談 B の「repo 外で足りる」は、job dir の原本消失 F1034 と配置性質の test の置き場を理由に不採用。理由と反対論は D に記録)。
- **訂正 (段 3):** brief の「read-heavy の検査費で walltime が大きく不足しうる」は、引用した B-8 の検査秒が extime 10 秒の trace だったので過大だった (3 秒へ換算して費用表を作った)。
- **exact model:** Claude Code の公式 docs を subagent で確かめ (alias は時間とともに更新、`ANTHROPIC_DEFAULT_OPUS_MODEL` で alias を完全 ID に固定可、subagent 定義の `model:` は完全 ID 可)、
  role 定義は sha256 が role adapter・review ledger に束縛されているので変えず、B-5 の親 session の起動構成で固定した。`ANTHROPIC_DEFAULT_OPUS_MODEL` は API キーでも課金経路の切替でもない
  (段 6 レビュー B も「課金経路の切替」の攻撃は不成立と判定)。
- **レビュー:** 段 3 相談 2 本 (must-fix A 2・B 5)、段 6 敵対レビュー 2 本 (A NO-GO must-fix 2・B NO-GO must-fix 4)、焦点再レビュー 1 本 (closed 8・partial 3・regressed 0)。
  最重要は (1) 最後の評価の後の critic の不一致は driver が handshake を待たないので欠測にできない → critic を「次の原提案の前に還流する分だけ」に限定、(2) A だけを消費する拒否の親手順の欠落、
  (3) 承認対象を後の main へ広げる一文。全所見の採否は insight の `verbatim/s4-adjudication.md`・`s6-adjudication.md`。
- **検査の結果:** 焦点走 f1 (17 file) 2,732 passed / 14 skipped / 0 failed、f2 (fix 後 7 file) 1,072 passed / 5 skipped / 0 failed。変異 final 26 / 26 一致 (KILLED 25・等価 SURVIVED 1、
  MA9 は kill 先の erratum)。provenance 全史監査は各 commit 後に新規違反なし。受入全走は本記録の commit 後、同じ tip で land 直前に 1 回行う (本エントリの時点では未実施)。
- **計算量 (第 31 回裁定の線):** 焦点走 202 s + 変異 probe ≤ 1,122 s + final ≤ 1,115 s ≈ 0.68 node 時間 (受入を足しても 2 node 時間の線の内側の見込み)。
- **異常・near miss:** insight に置いた `diff` の出力 (`.diff`) が commit 前の provenance 検査で実装面と判定された (F698 の型、改名で解消)。環境契約の世代を当初誤って書いた (試走の build path と
  `env_contract.lookup` の返り値で照合して訂正)。実装子 B への「tool は subprocess を起動しない」という字面が既存関数の内部の git 呼出しと衝突し、fix を 1 巡足した ({{F:child-prompt-ban-vs-existing-internals}}、前段 Tier0 wave に続く独立 2 例目)。
  `.diff` の件は F698 の再発として記録した。待ち手を 1 本余分に張った (即停止)。
- **並走:** T-2795 (K2 pair 再投入)・T-2849 (比較基盤設計、D2220 は B-5 の事前登録・cohort を変えないと明記)・ComSys 原稿 wave が land。main の前進は docs・insight だけで、本 wave の所有 file との重なりは無かった。
- 工数: codex 子 = plan 1 + consult 2 + author 2 + fix 3 (B1 / A1 / B2) + review 2 + focus review 1 の 11 本 (いずれも gpt-6-astra / medium)。Claude subagent 1 本 (Claude Code 公式 docs の確認)。

## 次の一手差分

### 更新

- [T-2797] **P2・ユーザー裁定待ち (発効束の 1 行再提示)**: 発効束の draft が揃った (insight `output/insights/2026-09-22/t2797-effect-bundle/README.md` §1 の 1 行、束
  `bundle/b5-effective-bundle.draft.json`)。本走の投入経路 (driver の registered 出力・job body の受け渡し・launcher の schedule と stage 投入・LLM 巡 tool と model 記録) は本 wave で land。
  推奨 = k 3 (W 63,777 s / W_stock 16,341 s)、総 wall 上限 = 試走 job Elapse 総和 61,261 s × 40 = 2,450,440 s、D39 決定 2 の改訂 (B 10 / A 30、3,600 s 上限と収束停止の不適用) の明示承認。
  承認後 (AI): 発効 commit (draft の status と effective 節だけを変える) → 発効 commit の固定 checkout で校正 job (`orchestrator/tests/test_b5_tier0.py::test_live_*`) → 本走 117 job
  (3 block × 3 stage、同時 LLM 系列 4、親は 1 系列 1 session を `claude --model claude-opus-5 --settings bundle/b5-parent-settings.json` で起動、手順は `bundle/b5-llm-parent-template.md`)。
  base: 5530c056e6453133dd9eefd4fb7229baea718cbe0baac04d505e33f88f9852e0
