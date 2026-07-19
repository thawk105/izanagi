# エージェント model/effort 経済監査 (2026-07-19)

発端: ユーザー相談「claude/codex エージェントの model 選定・推論深度が無駄に高度な箇所は
ないか。Claude のトークン消費ペースが速い」。監査 workflow (finder 4 + 敵対検証 6 + 抜け
チェック 1、いずれも opus/high または sonnet/high を明示) で全設定面を走査し、フラグ 6 件を
反証側で検証した。運用改善の記録であり、CC 合成実験の結論ではない。

## 確定 (confirmed) と適用

1. **verifier role の effort: high → medium (model は sonnet 維持)** — 本 insight と同一
   commit で適用。根拠: verifier の実務は決定的な `orchestrator/verify.py` の実行と
   exit code / JSON の三値 verdict への写像・中継のみで、serializability 判定は LLM の推論に
   依存しない (D3 の構造化フィードバックも verify.py --json 由来で effort 非依存)。effort:high は
   全 role effort 明示方針時に親継承値を機械固定した経緯 (decisions L2194 の critic-experiment と
   同型) で、タスク難易度による正当化が文書に無い。**コスト効果の訂正 (codex 監査 2026-07-19):**
   当初「pipeline.evaluate 毎に呼ばれる高頻度 role のため実コストに効く」と主張したが誤り —
   常時経路の正しさゲートは非 LLM で、pipeline.evaluate は決定的検査を直接呼び LLM の verifier
   role を spawn しない。medium 化の効果は、セッション/オーケストレーションが verifier role を
   明示起動する場面の経済衛生に限られる。同期連鎖 (manifest claude.effort / review_ledger
   ピン 2 件 / adapter を spec.render_adapter 期待バイトで再生成) を同一 commit で更新。
2. **workflow script 内 agent() の model 省略 = fable 暗黙継承** — guard_agent hook の既知盲点
   (hook は Agent tool しか見えない)。実地検査: 過去 workflow script 10 件中 3 件から **NG 18 件**
   (izanagi-rewrite-audit 5/5、s8b-audit-freeze-execution 11/12、s8b-audit3-fixes 2/2)。
   hook 化は 2026-07-18 既決 (「brittle で偽陽性の害が大きい」) に従い見送り、報告のみの
   standalone lint `tools/check_workflow_models.py` を導入 (拒否しないため偽陽性の害が無い)。
   運用: workflow 起動前の自己検査 + 過去 script の事後監査。
3. **親セッション既定が最上位固定** (`~/.claude/settings.json`: model=claude-fable-5[1m],
   effortLevel=xhigh) — 抜けチェック担当の発見。直近 wave の消費重心は named role でなく
   「親セッション直轄の標準ループ (codex 実行 + opus レビュー fan-out)」であり、親の常時
   最上位設定が最大の駆動源。既定 opus/high + 重い wave のみ /effort・/model で引き上げを推奨。
   repo 外ファイルのため AI からの編集は auto-mode classifier に拒否され、手動変更をユーザーへ
   引き渡し (2026-07-19 ユーザーが引き下げ方針を承認済み)。

## 棄却 (refuted) — 正当と確認された設定

- **codex 敵対相談の reasoning=max 定型**: memory doctrine が triage 済み (最難の敵対検証 = max、
  中位相談 = 中位)。worklog 実績でも実装段は high/medium に落ちており、max は相談段に scope 済み。
- **s6_proposal_rounds.py の opus/high ハードコード** (proposer 60 + scorer 120): 事前登録で
  凍結済みキャンペーンの計測器。いま下げると凍結を破る。将来の非凍結再設計時に scorer の
  引き下げ余地のみ記録。
- **profiler の opus/high**: perf 病理の意味的解釈が本務で正当。
- **opus/high の tool-less 群** (planner-v4 / coder-v4 系 / axis-proposer / selector-8b):
  1 回呼び切りで低コストかつ model tier が実験契約 (synthesisability 実証・wave 比較・auditor
  tier 例外 [agent-architecture.md モデル階層方針]) に組み込まれており変更不可。
- **codex adapter の一律 gpt-5.6-sol/high**: D54 初版が意図的に統一 (「製品 adapter 差とモデル
  品質差を同時に持ち込まない」。記録当時は 12 role、selector-8b 追加で現行 13)。現況の正確な
  三軸は native active 0 / static dormant adapter 13 / runtime activation blocked (D55–D56) で、
  blocked の間 codex 側の推論コストはゼロ (codex 監査 2026-07-19 で表現を訂正)。ただし adapter は
  将来再開時の契約の正本であり、精査すると calibrator / coder は導入時から gpt-5.6-terra / medium
  に段付け済みで、未段付けは verifier のみだった (当初の「sonnet 系 3 role が一律 sol/high」という
  報告は truncate された grep に基づく誤り — 本 insight で訂正)。verifier の codex 列は 2026-07-19
  ユーザー裁定で terra/medium へ再ピンした (D61、専用固定ルールは削除せず新値で維持)。

## 頻度の実像 (finder: frequency)

named Phase-3 role は合成ループ休止中でほぼ休眠 (通算 1 桁台の呼び出し)。直近 6 wave 超の
消費は「親セッション直轄の標準ループ」= codex gpt-5.6-sol (high/max) 実行単位 + opus レビュー
2 レンズ/単位 (wave あたり 7〜17 本) が支配的。opus レビューの fan-out は品質要件として妥当と
判定されたが、量としては最大の Claude 消費源であり、軽微な機械的変更ではレンズ数を落とす
余地がある (規律ではなく都度判断)。

## 監査自体の品質注記 (正直に)

- finder 1 体 (codex-adapters 担当、opus/high) が縮退出力 (`summary: "test"`, flags 空) を返した。
  同面は callsites finder と mismatch 検証者が独立に裏取りし、D54 本文も親が直接確認したため
  結論に穴はないが、「opus/high でも構造化出力が縮退することがある」実例として記録する。
- 一次資料 (フラグ・verdict 全文): 本セッションの監査 workflow 出力 (wf_8179c10a-92e)。要旨は
  本 insight に凍結し、逐語はセッション transcript のみ (F20 に従い結論はここへ)。

## 適用変更のレビュー (Claude + codex の二重独立)

- **Claude workflow (wf_46317951-147、opus/high × 3 レンズ → refute 検証)**: real 5 / refuted 1。
  scanner 2 件 (postfix `++`/`--` とプロパティ名キーワードの除算誤認による見逃し、computed key の
  偽 NG)、tests 3 件 (WARN fail-open の exit 契約・--dir 再帰・集計/読取失敗が未固定)。全件修正済み。
- **codex exec (gpt-5.6-sol / reasoning=high / read-only、2 レーン)**: 契約監査レーンは findings 5
  (major 2)。major = ①verifier のコスト根拠の事実誤認 (上記で訂正)、②lint が effort 省略を見ない
  (xhigh 親では effort 継承は無害でない → WARN 化で対応)。minor 3 (12/13 role 数と三軸の混同、
  時制、hooks/README の「偽陽性の害が無い」が強すぎ) も本 insight・README 側で修正。同期手順は
  「正規 (ピン独立再計算一致・adapter バイト一致・--write 不使用)」と裏書き。scanner レーンは
  初回プロンプトの「攻撃」表現が OpenAI 安全フィルタに誤検知され失敗 → 中立表現で再実行し完走。
  findings 7 (major 2): 採用 = 文字列/regex 終端の値トークン消失による見逃し (終端マーカーで修正)、
  private field `#in`、`${}` 内深度 0 カンマ、関数定義の誤認・optional call、括弧包み opts、
  テストの位置・集計固定。不採用 = 「effort WARN は model-only 契約超過」(codex 契約レーンの
  「effort を見ないのは穴」指摘と正反対 — 規律の正本 [model/effort 両明示] と実測 [過去 script
  全件 WARN=0 = ノイズなし] から契約レーン側を採る裁定)、制御文直後の statement 位置 regex と
  getter/unicode-escape key (現実の workflow script で非発生 — 既知限界として docstring に記録)。
- 教訓: 監査文書の事実主張 (頻度・コスト) は、コードの実呼び出し経路まで突合してから書く。
  Claude 側レビューは自作コードの機序には強いが、この事実誤認は codex 側だけが検出した —
  製品をまたぐ二重レビューの実益の実例。
