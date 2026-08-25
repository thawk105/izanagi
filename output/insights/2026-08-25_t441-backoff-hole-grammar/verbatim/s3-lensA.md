段 2 の literal-only 方針は恒真ではなく、共有状態・非決定値・制御フローの大半を閉じます。ただし、現状のままでは小数 literal が genome と実行値を分離するため、条件付きでもまだ実装へ進めません。

## 所見 1 — 小数を許すと宣言 genome と実行値が一致しない

- **区分**: must-fix
- **成果物影響**: `BACKOFF_FIXED=20` と記録された certified variant が実際には `20.5` を実行し、材料レポートの backoff 値、試行台帳の genome、選択結果の帰属が不一致になる。
- **根拠**: [s2-plan.md:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s2-plan.md:82) は小数を受理する一方、[p3_s4_loop.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:967) は `BACKOFF_FIXED=int(coder.value)` とする。帰属検査は [p3_s4_loop.py:880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:880) で float 同値しか見ない。
- **提案する負例ベクタ**:
  - `double now_backoff = 1.5;`
  - `double now_backoff = 20.5;`
  - `double now_backoff = 20.1;` と `double now_backoff = 20.9;`
  - `double now_backoff = 999.999;`

これらは提案された `type/raw-size/character/token-count/parse/semantic` をすべて通ります。`coder.value` を同じ小数にすれば既存帰属検査も通りますが、genome は切り捨てられます。

また `20`、`20.0`、`20.00` は同じ実行値・同じ genome なのに source token が異なるため、[pipeline.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/pipeline.py:117) により別 variant ID になります。「正準十進 literal」という説明とも一致しません。

v1 は `<decimal>` でなく、leading zero のない整数 `1..1000` のみにすべきです。小数を残すなら genome、WAL、campaign identity を exact decimal 対応へ変える必要があります。

## 所見 2 — P2 単独では隠れ適応を閉じず、親 P3 は意味上危険

- **区分**: must-fix
- **成果物影響**: 親 P3 を復活させると、backoff 軸の certified 利得に非決定値、共有状態変更、未初期化値、spin 無効化が混ざり、材料レポートがそれらを backoff magnitude の効果として誤帰属する。
- **根拠**: hole の直前には `start` と未初期化の `stop` があり、後段では値を `uint64_t` threshold へ変換する。[backoff.hh:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/external/ccbench/include/backoff.hh:94)、[backoff.hh:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/external/ccbench/include/backoff.hh:100)。
- **提案する負例ベクタ**: 次表の全件。

到達可能なのは、引数 `clocks_per_us`、先行 local の `start` と `stop`、同クラス static の `Backoff_` と `kMinBackoff` 等、`rdtscp`、`chkClkSpan`、取り込み済み標準ライブラリ、ビルド macro・定義済み macro です。static member function なので、非 static member はオブジェクト無しには参照できません。

| 入力 | 壊す性質 | literal-only v1 の判定 |
|---|---|---|
| `double now_backoff = 20.5;` | genome `20` と実行値 `20.5` の乖離 | **受理**。落とす規則なし |
| `double now_backoff = 20 + (rdtscp() & 1);` | 呼出しごとに変動 | `character.v1` |
| `double now_backoff = 20 + (start & 1);` | 呼出し時刻に依存 | `character.v1` |
| `double now_backoff = 20 + (stop & 1);` | 未初期化値の読出し、未定義動作 | `character.v1` |
| `double now_backoff = Backoff_.load(std::memory_order_acquire) + 20;` | 他スレッドの適応状態に依存 | `character.v1` |
| `double now_backoff = (Backoff_.store(0, std::memory_order_release), 20);` | 共有状態を他スレッドへ漏らす | `character.v1` |
| `double now_backoff = [](){ static double s = 20; return s--; }();` | 単一宣言文内の隠れ適応 | `character.v1` |
| `double now_backoff = 1 / clocks_per_us;` | 整数除算で通常 0、spin をほぼ無効化 | `character.v1` |
| `double now_backoff = clocks_per_us - clocks_per_us - 1;` | `size_t` の unsigned underflow | `character.v1` |
| `double now_backoff = (clocks_per_us > 1000) ? 50 : 25;` | runtime policy 化、scalar genome と乖離 | `character.v1` |
| `double now_backoff = 20 + 0.0 / 0.0;` | NaN 経由の未定義動作 | `character.v1` |
| `double now_backoff = 20 * (1.0 / 0.0);` | inf 経由の未定義動作 | `character.v1` |
| `double now_backoff = -0.0;` | threshold 0、spin をほぼ無効化 | `character.v1` |
| `double now_backoff = 20 + __LINE__;` | macro 展開後の値と genome が乖離 | `character.v1` |
| `double now_backoff = clocks_per_us;` | runtime 値そのもの | `parse.v1` |
| `double now_backoff = stop;` | 未初期化値 | `parse.v1` |

P2 の「単一宣言文」は lambda 即時呼出しや comma expression を排除しません。したがって親 brief の「P2 だけでほぼ全部落ちる」は過大です。段 2 が P3 を退けた方向自体は正しいものの、さらに整数だけへ閉じる必要があります。

## 所見 3 — NaN、inf、負値について親が説明した C++ 挙動が誤っている

- **区分**: must-fix
- **成果物影響**: 材料レポートが「比較が偽」「無限 spin」と誤分類し、実際には未定義動作を含む候補を再現可能な意味クラスとして記録してしまう。
- **根拠**: [s1-brief-addendum.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s1-brief-addendum.md:27) に対し、実コードは浮動値を比較せず、[backoff.hh:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/external/ccbench/include/backoff.hh:104) で積を `uint64_t` に変換してから比較する。
- **提案する負例ベクタ**:
  - `double now_backoff = 0.0 / 0.0;`
  - `double now_backoff = 1.0 / 0.0;`
  - `double now_backoff = -50;`
  - `double now_backoff = -0.0;`

NaN、inf、表現範囲外の負値から `uint64_t` への変換は、単に「比較が偽」「最大 threshold」になるとは限りません。未定義動作として扱うべきです。負のゼロだけは積がゼロとなり、threshold 0 になります。

literal-only v1 は `/` と `-` を `character.v1` で落とすので防壁の方向は正しいですが、親の危険理由は訂正が必要です。

## 所見 4 — BNF、lexer、semantic の境界が互いに矛盾している

- **区分**: must-fix
- **成果物影響**: 同じ grammar version でも実装者により受理集合と WAL の拒否 rule ID が変わり、試行台帳と certified 選択の再現性が失われる。
- **根拠**: [s2-plan.md:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s2-plan.md:82) の BNF は指数・leading zero・suffix を構文外にする一方、[s2-plan.md:98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s2-plan.md:98) と [s2-plan.md:174](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s2-plan.md:174) はそれらを semantic reject としている。
- **提案する負例ベクタ**:
  - `double now_backoff = 1e2;`
  - `double now_backoff = 001;`
  - `double now_backoff = 1.0f;`
  - `double now_backoff = 1.0_backoff;`
  - `double now_backoff = 1..0;`
  - `double now_backoff == 1;`
  - `double now_backoff = 0.99999999999999999999;`
  - `double now_backoff = 1000.0000000000000000001;`
  - Python の `str` として末尾に lone surrogate `\ud800` を持つ入力

とくに次が未凍結です。

- `1e2` を C++ preprocessing-number 1 token とするか、`1` と `e2` に分けるか。
- `1..0`、`1.0_backoff` を最長一致で 1 token とするか。
- 範囲を数学的な十進値で比較するか、Python `float` へ丸めた後に比較するか。境界 2 例は前者なら拒否、後者なら 1 または 1000 に丸めて受理し得ます。
- UTF-8 byte 数を数える際、lone surrogate を固定拒否へ射影するか、encode 例外を外へ漏らすか。

正しい BNF を逐語実装するなら、`1e2`、`001`、suffix は `parse.v1` です。semantic は整数性と `1..1000` の exact range だけを担当させるのが明確です。

現行 pin で、正しく実装した literal-only BNF に「受理したが C++ 構文として build が落ちる」固有例は見つかりません。受理言語が有効な単一宣言の部分集合だからです。一方、macro 環境まで含めると所見 8 の残余があります。

## 所見 5 — 新しい type/raw-size gate は production 上で遅すぎる

- **区分**: must-fix
- **成果物影響**: oversized・型不正候補が `BACKOFF_GRAMMAR` として台帳へ記録されず、例外停止または既存 `HOST_EFFECT` に誤分類され、資源上限の受入証拠も成立しない。
- **根拠**: 帰属検査は [p3_s4_loop.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:967)、文字列分割・diff 合成は [p3_s4_loop.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:182)、256 KiB gate は [coder_effect_gate.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/coder_effect_gate.py:576)。新 grammar はこれらの後へ置く計画である [s2-plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s2-plan.md:119)。
- **提案する負例ベクタ**:
  - `implementation = None`
  - `implementation = ["double now_backoff = 20;"]`
  - `canonical + " " * (4096 - len(canonical))`
  - `canonical + " " * (4097 - len(canonical))`
  - `canonical + " " * (256 * 1024 + 1 - len(canonical))`
  - `canonical + "\ud800"`

`None` は新 type rule に届く前に regex または `.split()` で例外になります。256 KiB 超は新 raw-size rule に届く前に既存 lexer-malformed、すなわち `HOST_EFFECT` になります。4097 byte も、拒否前に edited source と unified diff を構築します。

したがって [s2-plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s2-plan.md:68) の「256 KiB より先に小さく閉じる」は、提案された配線順では偽です。

type と raw-size だけは materialization・帰属 regex より前の preflight に置く必要があります。その場合、「既存拒否理由を常に先に残す」は oversized 入力について両立しないため、「新 cap 内の入力に限り既存理由を保存」と契約を限定すべきです。上限ちょうど 4096 で後段検査を飛ばす経路自体は見つかりません。

## 所見 6 — 変異事前登録の一部は規則の検出力を証明しない

- **区分**: must-fix
- **成果物影響**: 変異レポートが緑でも character・token・depth・semantic の実装漏れを検出した証拠にならず、試行台帳の rule ID と材料レポートの「恒真性反証」が過大になる。
- **根拠**: [s2-plan.md:186](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s2-plan.md:186) の kill 対応と、括弧を character 段で禁止する [s2-plan.md:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s2-plan.md:69)。
- **提案する負例ベクタ**:
  - character gate 削除変異: `double now_backoff = rdtscp();`
  - token cap 削除変異: `double now_backoff = 20; x`
  - semantic 削除変異: `double now_backoff = 0;`、`double now_backoff = 1001;`
  - raw cap 削除変異: 4097 byte まで outer space で padding した正しい文
  - depth 検査用: `double now_backoff = (20);`

問題点は次のとおりです。

- character gate を消しても exact parser が `rdtscp()`、コメント、Unicode を拒否します。受理集合は変わりません。stage/rule ID を assert するテストなら変異を殺せますが、allowlist の非恒真性証明ではありません。
- token cap を消しても EOF 必須 parser が 6 token 目を拒否します。
- `1e2` と `001` は BNF どおりなら semantic へ届かず parse reject なので、semantic 削除変異を殺しません。
- depth 上限 0 は、括弧が先の character gate で落ちるため production 上は到達不能です。

allowlist 全体は恒真ではありません。しかし、各規則の独立検出力を主張してはいけません。変異試験は「受理集合を広げる変異」と「拒否 stage を変える変異」を分けるべきです。

## 所見 7 — P1 は偽で、P2/P4 も無条件賛成にはできない

- **区分**: must-fix
- **成果物影響**: 明示承認なしに実装すると既存 producer が許す安全な式まで不受理となり、受理集合と「LLM synthesisability」の意味が scalar 整数選択へ変更される。
- **根拠**: role は [coder-v4-autonomous.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/.claude/agents/coder-v4-autonomous.md:58) で値域だけを示し、[coder-v4-autonomous.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/.claude/agents/coder-v4-autonomous.md:60) の `<式>` を限定していない。骨格は [silo-backoff-fixed.patch:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/patches/silo-backoff-fixed.patch:66) で既存 API 呼出しも許している。
- **提案する負例ベクタ**:
  - `double now_backoff = 20.;`
  - `double now_backoff = 2e1;`
  - `double now_backoff = 20.0f;`
  - `double now_backoff = +20;`
  - `double now_backoff = (20);`
  - `double now_backoff = clocks_per_us * 0 + 20;`
  - `double now_backoff = static_cast<double>(BACKOFF_FIXED);`
  - `double now_backoff = Backoff::kMaxBackoff;`

これらは C++ として安全な値または定数式ですが、literal-only v1 は character または parse で拒否します。この保守性自体は、producer 契約を同時に改訂する明示承認後なら許容できます。

P1〜P4 の判定は次です。

| 前提 | 判定 |
|---|---|
| P1 | **反対**。段 2 の判断が正しい。明白な契約縮小 |
| P2 | **条件付き賛成**。表面の複文は閉じるが、lambda・comma を単独では閉じない |
| P3 | **反対**。runtime policy、整数昇格、共有状態、帰属不一致を生む |
| P4 | **条件付き賛成**。validator 内順序は採用可だが、production 全体の type/raw 順序を先に直す必要あり |

したがって現時点では、段 2 自身が述べる「設計凍結 + 裁定パッケージ」が正しい停止点です。

## 所見 8 — 32 形の実測は quarantine の生死だけで、純増検出力を証明しない

- **区分**: must-fix
- **成果物影響**: 材料レポートが「unsafe certified candidate を新規に 25 件拒否できる」と読める記述になり、実際の certified 受理集合と参照先を過大に変更する。
- **根拠**: 追補は [s1-brief-addendum.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t441-backoff-hole-grammar/s1-brief-addendum.md:3) で `quarantine(write=False)` のみを測定した。一方、production では帰属検査がその前にある [p3_s4_loop.py:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:969)。
- **提案する負例ベクタ**:
  - `""`
  - `goto izanagi_skip;`
  - `static double s; s = s * 0.9;`
  - `double now_backoff = Backoff_.load(std::memory_order_acquire);`
  - `double now_backoff = (Backoff_.store(0, std::memory_order_release), 50);`
  - `double now_backoff = 50 + (rdtscp() & 1);`

測っているのは、特定 pin・特定 template において構造検疫と有限 denylist が文字列を受理したかだけです。次は測っていません。

- 帰属検査を含む `run_one_iteration` 全体
- C++ の compile/link 成否
- verifier、bench、COMMIT、certified acceptance
- 実行時に本当に値が変化・共有漏洩したか
- cache/replay/WAL 上の grammar policy binding

空実装、未定義 label への `goto`、`now_backoff` を宣言しない断片は quarantine が通っても build で止まります。数値を含まない `Backoff_.load` は現行帰属検査で先に止まります。一方、最後の 2 例は帰属検査を通し得る有力な end-to-end 負例ですが、それでも build・certification は未測定です。

したがって引ける結論は「現在の quarantine には hole 形状の allowlist がない」までです。「純増検出力」は、quarantine 単体に対する字句的な増分と限定して書く必要があります。

## 所見 9 — raw 文法と macro 展開後の C++ に parity gate がない

- **区分**: backlog
- **成果物影響**: 将来 header または build flag に macro が追加されると、同じ受理文字列が build failure または別の実行コードになり、source 参照と certified 受理結果が pin 間で変わる。
- **根拠**: 文法は raw implementation を検査するが、C++ macro 展開はその後である。現行の直接取り込み header には `double` または `now_backoff` の macro 定義は見つからないため、現 pin の実抜けとは断定しない。
- **提案する負例ベクタ**:

```cpp
#define now_backoff )
double now_backoff = 20;
```

候補部分 `double now_backoff = 20;` は文法を通りますが、preprocess 後は構文不正になります。同様に `now_backoff` を別識別子や式へ展開する macro は実行意味を変えます。

現在の pin では backlog でよいものの、受理正例を実 translation unit で compile する parity test、または hole 前で `now_backoff` 等が macro 未定義であることを固定する検査が必要です。digraph、trigraph、Unicode escape は現 character gate が先に拒否します。ユーザー定義 literal suffix も parse-negative として固定すべきです。

## 総括

- **must-fix は 8 件**です。最も危険なのは、小数 literal を受理しながら genome を `int(coder.value)` にするため、certified variant の宣言値と実行値が直接食い違う所見 1 です。
- **プランは現状のままでは条件付き採用不可**です。明示的な role 契約縮小の承認に加え、v1 を整数 `1..1000` のみに変更し、lexer/semantic、production の type/raw 順序、変異試験を凍結した後なら採用できます。
- **親 brief で誤っている点**は、P1、P2 単独の検出力、P3 の安全性、「純増検出力」の射程、NaN/inf/負値が outer spin に及ぼす具体的機序です。実測 1 の正しい表現は追補どおり `25/32 quarantine 受理` であり、certified 受理を測ったものではありません。

静的検査のみで、pytest・build・実行時 probe は走らせていません。