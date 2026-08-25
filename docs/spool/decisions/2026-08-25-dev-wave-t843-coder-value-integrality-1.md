---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t843-coder-value-integrality
seq: 1
---

## {{D:coder-value-exact-integral-domain}}. coder value を bool でない 1..1000 の整数へ閉じる

**決定:** 段 4 backoff 軸の `coder.value` は、exact な built-in `int`、または有限で整数値を持つ
exact な `float` のうち `1 <= value <= 1000` を満たすものだけを受理する。それ以外は既存の
`AttributionMismatch` で拒否する。拒否 seam は `CoderProposal.__post_init__`、
`assert_value_literal_consistent()` の冒頭、`drive_iteration()` の最初の文の 3 か所とし、
`run_one_iteration()` は整合検査を `Genome` 構築より前に行う。`load_proposal_file()` は
JSON の raw 値をそのまま渡し、`float()` 正規化を行わない。

**理由:**
- 非整数 value は value と hole literal が一致すれば整合検査を通る一方、genome は `int()` で
  切り詰めた値を記録していた。実行した binary と台帳 genome が別値になり、certified な選択結果の
  帰属 (どの値で測ったのか) が台帳から言えなくなる。
- 記録側を実値へ揃える案は構造的に成立しない。`BACKOFF_FIXED` は CMake define から
  C++ 前処理器の `#if BACKOFF_FIXED >= 0` へ入る。`-DBACKOFF_FIXED=20.5` は
  `error: floating constant in preprocessor expression` で compile 不能であることを実測した。
  したがって受理側で拒否する以外に選択肢がない。これは受理集合を狭める方向であり絶対規律 2 と整合する。
- 値域 1..1000 は新設ではなく既存契約の強制である。`orchestrator/codex_roles/manifest.json` は
  同 role の `value` を `type: integer`, `minimum: 1`, `maximum: 1000` と既に定義している。
  欠けていたのは harness 側の強制だけだった。
- coercion を挟まないのは、`float(value)` を通すと JSON の `true` が `1.0` に、numeric string の
  `"20"` が `20.0` になり、宣言型と異なる入力が受理される経路が残るためである。
- seam を 3 か所に置くのは、`CoderProposal` が mutable dataclass であり構築後の改変で
  単層 gate を迂回できること、および `drive_iteration()` の入口停止経路が
  `run_one_iteration()` に到達しないことによる。兄弟軸の trigger-gating driver は既に
  `drive_iteration` 冒頭で候補契約を再検査しており、同じ形を踏襲した。

**却下した選択肢:**
- 台帳側を実値へ揃える — 前処理器が非整数 macro を評価できず compile 不能。
- 単一 seam (構築時のみ) — mutable dataclass の事後改変と入口停止経路を素通しする。
- role 文書の改訂 — manifest が既に整数を要求しており、契約文でなく強制側の欠落だった。
- Codex role 出力検証 (`orchestrator/codex_roles/policy.py`) への整数性追加 — 同経路は
  logical schema 検証を先に通り、manifest の `type: integer` が既に非整数を拒否する。
  生きた穴ではないため足さない。

## {{D:backoff-hole-expression-attribution-open}}. 計算式による帰属不一致は未閉鎖のまま裁定へ返す

**決定:** hole の初期化子が計算式のとき、宣言値と実効値が食い違ったまま整合検査を通る経路は
本 wave では閉じない。設計択一としてユーザー裁定へ返す。

**理由:**
- 整合検査の literal 抽出は代入値の後端を束縛せず、先頭の数値が宣言値と一致した時点で通過する。
  抽出できない自由式に対する fallback 枝は、さらに緩く「宣言値が実装のどこかに数値として
  現れること」しか要求しない。実測した通過例:
  `value=20.0` / `now_backoff = 20.0 * 2.0;` (実効 40)、
  `value=40.0` / `now_backoff = 40.0 / 2.0;` (実効 20)、
  `value=50.0` / `now_backoff = std::ceil(50.0 * 1.5);` (実効 75、fallback 枝)。
- これは値が整数でも成立するため、整数性の強制だけでは帰属不変条件は閉じない。
- 閉じる唯一の形は「初期化子は宣言値そのものの数値 1 個でなければならない」と要求することだが、
  それは `src/coder-spec.md` が coder へ明示的に与えている合成自由度 (リテラル・計算式・
  既存 API 呼び出しのいずれでもよい、計算式を正例として掲げる) の撤回にあたる。正しさの修正ではなく
  coder に何を合成させるかという研究上の能力設計であり、実装せず裁定へ返す。

**却下した選択肢:**
- 本 wave で初期化子を単一 literal へ限定する — 上記の理由により、裁定を経ずに合成自由度を
  撤回することになる。
- 実効値を評価して台帳へ記録する — C++ 式の評価を harness に持ち込むことになり、
  段 4 の編集面定義を超える。

**推奨 (裁定待ち):** 初期化子を宣言値そのものの数値 literal 1 個に限定し、`src/coder-spec.md` の
該当記述を撤回する案を推す。帰属できない certified 結果は成果物として無価値であり、
表現の自由度は探索の幅であって正しさではないため。現状維持を採る場合は、帰属主張を
「宣言値が実装に現れること」までに弱めて明記する必要がある。
