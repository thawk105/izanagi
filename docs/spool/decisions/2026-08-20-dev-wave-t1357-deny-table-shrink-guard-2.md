---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1357-deny-table-shrink-guard
seq: 2
---

## {{D:deny-table-shrink-guard}}. 禁止 identifier 集合の縮小検知は、構造比較でなく意味的 probe + AST allowlist で行う

**決定:** `coder_effect_gate.DENY_TABLE` のような禁止 identifier 集合が個別に黙って縮んでも
既存テストが検知しない穴は、(1) category 別 frozen literal を独立に保持し (2) frozen の全 identifier
について実際の scanner (`scan_host_effects` 等) を呼び出して期待挙動を assert する意味的 probe で
閉じる。frozen literal 自身の自己参照防止は、denylist (禁止識別子の列挙) ではなく allowlist
(単一代入の強制 + RHS ノード形状を `Dict`/`Tuple`/文字列 `Constant`/`frozenset(...)` 直呼びだけに
限定し、`Name` は `"frozenset"` のみ許可) で AST 静的検査する。production と frozen literal を
同一 commit で協調して縮める編集 (byte pin の同一性だけを見て意味を見ない攻撃) は、この設計では
意図的に scope 外の既知残存として扱い、コメントで明記する。

**理由:**
- 構造比較 (`current ⊇ frozen` を identifier 集合の差分だけで見る) は、identifier 文字列が残ったまま
  scanner の照合ロジック側が壊れる変異を見逃す。scanner を実際に呼ぶ意味的 probe はこれを内包する。
- denylist 方式の自己参照防止 ("`DENY_TABLE` という名前を禁止する" 型) は、別名 (`_SOURCE =
  DENY_TABLE` 等) や複数代入 (安全な代入の後に危険な再代入を続ける) で回避できる。許可される形を
  数え上げる allowlist はこの種の回避に対して構造的に閉じている。
- 2026-08-18 wave651 が実証した「pin は bytes 同一性しか証明しない」という一般教訓
  (禁止 bullet を1行削り pin を整合再承認すれば緑のまま通る) は、production と frozen literal の
  協調改変にも同型で当てはまる。`tools/mutation_harness.py` は複数ファイル同時変異を実際に
  サポートしており技術的には閉じられるが、production 側の暗号的 pin 新設は絶対規律5 (段階導入・
  盛らない) に反し、真の攻撃対象 (role-contract pin) を閉じない限り部分的な効果しかない。
  この判断は [T-1357] 固有ではなく、同種の「禁止/許可集合の frozen 化」を今後行う wave 全般に
  適用できる設計判断として記録する。

**却下した選択肢:**
- **denylist 方式のまま個別の禁止名を増やす。** 新しい迂回経路 (エイリアス等) が見つかるたびに
  列挙を追加する後追い対応になり、閉じた保証にならない。
- **frozen literal の hash pin を追加する。** 誰かが frozen literal を編集すれば hash も同時に
  再計算されうるため、bytes 同一性の保証しか得られず、真に守りたい「意味」を証明しない
  (wave651 が pin 一般について示した限界と同型)。
- **production と frozen literal の協調改変も本 wave で閉じる。** 真の攻撃対象である
  role-contract pin (`.claude/agents/coder-v4-autonomous-sort.md` 側) は別 scope のまま残るため、
  DENY_TABLE 側だけを暗号的に固めても実効性が低く、絶対規律5 に反する。
