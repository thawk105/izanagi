---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-token-hygiene
seq: 1
---

## {{D:claude-session-ledger}}. 開発ループの消費計測は claude 側を新設し codex 側は既存 ledger に委ねる

**決定:** claude セッション transcript を集計する read-only 台帳
`tools/claude_session_ledger.py` を新設する。codex 側は実装しない。
消費の観測はこの 2 本 (claude 側の新台帳と既存の codex worker 台帳) の閉集合で行い、
第 3 の parser を作らない。

台帳は観測値と推測値を分けて公開する。母集団 (走査 root・project/cwd filter・時間窓と
その判定根拠・走査件数・読めなかった件数・打切りの有無) を必ず報告に出し、黙って決めない。
model call と tool 呼び出しを別 field にする。raw token を費用・課金・枠消費と名乗らない
(サブスク運用のため実費ではない)。

**理由:**
- 消費の大きい方である claude 側が完全に未計装だった。`grep -rln "claude/projects"` の hit は
  archive の 1 件のみで、production の参照はゼロだった。
- codex 側は既に計装済みである。新たな parser を足すと同じ raw log に二つの token 定義が生まれ、
  どちらが正本か決まらなくなる。
- 計測なしでは、どの削減施策も before/after で検証できない。D100 が既に
  「token は observable proxy であって hard cap ではない」と定めており、本 ID はその observable を
  claude 側へ広げるだけで、封筒の強制力は主張しない。

**却下した選択肢:**
- claude と codex を 1 本の report で扱う — 既存 ledger と二重管理になる。
- 使い捨てスクリプトのまま運用する — 本 wave の段 0 が実際に、二重計上・母集団未定義・
  model call と tool call の混同という誤りを同時に持っていた。再現可能な形に固定する必要がある。
- 消費量から金額を出す — cache read / cache write は単価が異なり、
  サブスク運用では実費でもない。台帳が費用を名乗ると誤った最適化の根拠になる。

## {{D:effort-downshift-needs-controlled-experiment}}. codex の reasoning effort 引き下げは観察値で決めず既存 A/B 装置へ送る

**決定:** dev-wave の worker 契約が規定する reasoning effort を、
運用ログの観察値を根拠に引き下げてはならない。引き下げの可否は
`tools/codex_reasoning_ab.py` の paired・blind・非劣性の評価だけが決める。
本 ID は現行の effort 規定 (段 2 と段 3 は max、段 5 は high) を変更しない。

**理由:**
- 観察ログでは effort が stage と交絡している。契約が段 2・段 3 を max、段 5 を high と
  固定している以上、effort 別の消費差は難易度・turn 数の差と分離できない。
  実測でも max 群は model call 数自体が high 群の 1.44 倍あり、
  入力総量の 2.02 倍という比を effort の因果効果とは呼べない。
- 検出力を下げる変更は、規律 2 (正しさゲートを緩める変異を許さない) の対象である。
  トークン節約は最適化圧力であり、最適化圧力は必ず正しさ側を攻撃しに来るという前提で扱う。
- 「max は 2 倍高い」という前提をテストや契約へ凍結すると、品質差を測らないまま
  production routing を変える経路が制度化される。

**却下した選択肢:**
- 段 2 のプラン起草だけ high へ落とす — 起草物は後段が必ず攻撃するので安全に見えるが、
  弱い起草が must-fix と fix 巡回を増やし、消費と正しさが同時に悪化する経路を排除できない。
  この比較こそ paired 評価の対象である。
- 一律 max のまま放置する — 節約施策にならない。観察を A/B へ送ることで前へ進める。

## {{D:no-fixed-token-rates-in-entry-docs}}. 往復コストの換算率を入口文書へ書かない

**決定:** 「1 往復あたり N トークン」のような固定換算率を `CLAUDE.md` や
dev-wave の入口・reference へ書かない。消費に関する規律は、数値を持たない不変条件と、
実測できる telemetry の側に置く。

**理由:**
- 換算率は母集団・session 長・context 成長率に依存し、介入した瞬間に変わる。
  入口文書へ書いた数値は stale 化しても誰も再測定しない。
- 数値を規律として書くと、依存関係のある呼び出しまで無理に 1 応答へ束ねる誘因になり、
  中間結果を見てから次を決める判断や、診断に必要な出力を切り捨てる方向へ働く。
- 「独立した tool 呼び出しは 1 応答に束ねられる」「ファイル読取に汎用シェルを使わない」は
  既に実行面の system prompt に存在する。入口文書へ再掲しても新しい強制力は生まれず、
  常時読量だけが増える。

**却下した選択肢:**
- 計測値を入口へ転記して規律にする — 上記のとおり stale 化と過剰束ねを招く。
- reference へ節を新設する — dev-wave 4 文書の aggregate 予算は余地 13 bytes しかなく、
  削除先を特定しないまま追記できない。予算引き上げは提案しない。
