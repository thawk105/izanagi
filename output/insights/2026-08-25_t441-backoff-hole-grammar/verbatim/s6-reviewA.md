pytest と build は未実走です。全必読資料と commit 前後を読み、公開 pure validator の判定だけを直接照合しました。

## Tier 1 対照

| 規則 | 判定 |
|---|---|
| T1-1 | 空拒否は実装済みだが、宣言数 1 の規則に完全包含され、受理集合を単独では縮めない。 |
| T1-2 | 不十分。括弧付き追加宣言子と Python/C++ の空白差を通す。 |
| T1-3 | 不十分。間接 lvalue 書換えと内側 scope の直接初期化宣言を通す。 |
| T1-4 | `if`・loop・try/catch の追加拒否は straight-line の射程内。ただし attribute 付き label を通す。 |
| T1-5 | `static` / `thread_local` の exact token 拒否は裁定どおりで、単独の検出力もある。 |
| T1-6 | `value` の数学的整数性と 1..1000 は正しい。`20.0` の許可も無損失整数という裁定内。ただし literal 帰属が前方一致なので実行値整合は破れる。 |
| T1-7 | `quarantine()` 内の順序と docstring は一致。ただし production 入口では例外になり WAL 分類されず、上限値も裁定外に狭められている。 |
| Tier 2 | 関数呼出し・算術・三項などは概ね開いている。1024 token と nesting 64 は裁定外の過剰拒否。 |

## 所見 1 — 数値 token の前方一致で実行値と genome が乖離する

- **区分**: must-fix
- **成果物影響**: 実行時 backoff 100・16・20 の fitness が、それぞれ `BACKOFF_FIXED=1`・`20`・`2` として certified 選択、材料レポート、WAL に帰属し得る。
- **根拠**: [_scan_number()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:224) は C++ pp-number 全体を 1 token にする一方、[_NOW_BACKOFF_RE](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:907) は十進表記の接頭辞だけを捕る。pure probe では次の 3 形が grammar と attribution の両方を通った。
- **提案する負例ベクタ**:
  - `value=1`, `double now_backoff = 1e2;` — 実行値 100。
  - `value=20`, `double now_backoff = 020;` — C++ の実行値 16。
  - `value=2`, `double now_backoff = 2'0;` — 実行値 20。
  - 現行テストの `value=100` と `1e2` だけでなく、接頭辞と一致する誤 value を必ず拒否させる。

## 所見 2 — T1-3 は indirect lvalue による再束縛を見逃す

- **区分**: must-fix
- **成果物影響**: `BACKOFF_FIXED=20` の候補が実際には 30 を実行し、その誤帰属 fitness が certified 選択と critic 還流へ入る。
- **根拠**: [rebinding 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:458) は `now_backoff` の直後または括弧を除いた直後に代入演算子がある場合しか見ない。配列添字や pointer arithmetic を挟むと通る。
- **提案する負例ベクタ**:
  - `double now_backoff = 20; (&now_backoff)[0] = 30;`
  - `double now_backoff = 20; *(&now_backoff + 0) = 30;`
  - 両方とも現行 pure validator と attribution を通った。

## 所見 3 — 括弧付き declarator で T1-2 の単一宣言子を回避できる

- **区分**: must-fix
- **成果物影響**: 単一宣言子でない source が build/certify に入り、受理集合と variant/source 参照が裁定より広がる。
- **根拠**: [_has_additional_declarator()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:334) は comma の後で `*`・`&`・`&&` だけを飛ばし、直後が identifier の場合しか検出しない。C++ の括弧付き declarator は直後が `(` なので見落とす。
- **提案する負例ベクタ**:
  - `double now_backoff = 20, (other) = 0;`
  - `double now_backoff = 20, (*callback)() = nullptr;`
  - 前者は現行 pure validator と attribution を通った。

## 所見 4 — 入れ子宣言と attribute 付き label が flat token 検査を抜ける

- **区分**: must-fix
- **成果物影響**: T1-3/T1-4 違反候補が diff reject されず、試行台帳では build または certified 候補として記録される。
- **根拠**: [_top_level_statements()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:310) は brace 内の `;` を文境界にせず、[_has_label()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:355) は label 直前が `]` の形を認識しない。両形とも現行 validator が受理した。
- **提案する負例ベクタ**:
  - `double now_backoff = 20; { double now_backoff(30); }`
  - `double now_backoff = 20; { double now_backoff{30}; }`
  - `double now_backoff = 20; [[likely]] bypass: ;`

## 所見 5 — Python の Unicode 空白を C++ token separator と誤認する

- **区分**: must-fix
- **成果物影響**: T1-2 を満たさない source が文法を通り、diff rejection ではなく compiler/build abort として試行台帳の理由と参照を変える。
- **根拠**: [tokenizer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:241) の `character.isspace()` と attribution の `\s*` は C++20 の token separator より広い。`double\u00a0now_backoff = 20;` は現行 grammar と attribution を通った。
- **提案する負例ベクタ**:
  - `double\u00a0now_backoff = 20;`
  - `double\u3000now_backoff = 20;`
  - homoglyph 対照として `double now_back\u043eff = 20;` は `declaration-count` で拒否すること。
  - ASCII space、tab、改行だけを正例に固定すること。

## 所見 6 — 資源上限が裁定外に狭く、Tier 2 を過剰拒否する

- **区分**: must-fix
- **成果物影響**: 裁定上は開いている算術・括弧式が `BACKOFF_GRAMMAR` で落ち、certified 候補集合と試行件数が不要に減る。
- **根拠**: [4 KiB / 1024 token / nesting 64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:40) は実装子の独自判断。既存 effect gate は [256 KiB / 4096 token](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/coder_effect_gate.py:112) であり、T1-7 は token/nesting 上限の追加を裁定していない。code point 4096 は UTF-8 byte 4096 に完全包含され、単独の検出力もない。
- **提案する負例ベクタ**:
  - 1024 token 正例: `"double now_backoff = " + "+ " * 1019 + "20;"`。
  - 1025 token 境界: 同じ式で `1019` を `1020` にする。現状は拒否されるが、Tier 2 算術として受理すべきか裁定が必要。
  - nesting 64 正例と nesting 65 の対。
  - raw-size は `"double now_backoff = 20;"` を space で 4096 byte と 4097 byte に調整した対。
  - 上限を変更するなら既存値の移動なのか、新しい狭化なのかを親裁定へ返す。

## 所見 7 — production preflight は rejection にならず iteration を例外終了させる

- **区分**: must-fix
- **成果物影響**: cap 超過候補では `res.digest`、reject WAL、whiteboard 行が生成されず、試行台帳から候補と拒否理由が欠落して loop が中断する。
- **根拠**: [assert_value_literal_consistent()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:926) が `BackoffGrammarViolation` を送出し、[run_one_iteration()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:1039) は layout/WAL 作成前にこれを呼ぶ。`quarantine()` 単体なら固定 `BACKOFF_GRAMMAR` になるが、production 経路はそこへ到達しない。
- **提案する負例ベクタ**:
  - `"#define X 1\ndouble now_backoff = 20;" + " " * 4096` — 旧経路では `HOLE_ESCAPE`、現 production では例外。
  - `"double now_backoff = 20; std::system(\"x\");" + " " * 4096` — 旧経路では `HOST_EFFECT`、現 production では例外。
  - `run_one_iteration()` の期待値を `outcome="rejected"`、固定 rule ID、WAL 2 record、whiteboard `rejected` にする。

なお cap 内で既存理由を優先する限定は、[module docstring](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:16) と [quarantine docstring](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:217) で一致している。

## 所見 8 — 入力長と content fingerprint が digest、WAL、critic へ残る

- **区分**: must-fix
- **成果物影響**: reject 候補の長さ・同一性・低エントロピー本文を critic が推測でき、次候補と最終 certified 選択に非許可の構造情報が還流する。
- **根拠**:
  - [diff_quarantine.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/diff_quarantine.py:91) が `byte_length` と短縮 SHA-256 を evidence に入れる。
  - [p3_s4_loop.py:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:342) は implementation 全体から決定的な `diffq-<hash>` を作り、[WAL](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:366) の top-level variant に置く。
  - [critic renderer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/critic/digest.py:1201) は `HOLE_ESCAPE` 等の evidence をそのまま描画する。
  - host-effect の `first_byte_length` 等も [WAL digest](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:271) に残る。
- **提案する負例ベクタ**:
  - `#define SENTINEL_LENGTH_123456 1\ndouble now_backoff = 20;`
  - 全 WAL record の payload だけでなく `record.variant` も検査し、`byte_length=`, `sha256_12=`, implementation 由来の決定的 commitment が出ないことを要求する。
  - critic 出力にも同じ否定 assert を置く。

## 所見 9 — 新テストが実装の誤りを共有し、backoff 固有の判定順 mutation を殺せない

- **区分**: must-fix
- **成果物影響**: 帰属汚染や `HOST_EFFECT`→`BACKOFF_GRAMMAR` の subtype 変更を入れても焦点テストが成功し、材料レポートの rejection 集計と critic 入力が誤る。
- **根拠**:
  - [数値 spelling テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py:322) は `value=100, 1e2` の拒否だけを固定し、危険な `value=1` を見ない。
  - [scanner テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py:241) は marker 以外の multiline・空行・tab・indent・exact bytes の assert をすべて維持しており、移動自体に実質的緩和はない。ただし sort marker へ移ったため backoff の grammar/effect 合成順は検査しない。
  - [既存理由テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py:551) の HOST_EFFECT 入力は grammar-valid なので、grammar を scanner より前へ移す mutation でも同じ subtype になる。
  - resource テストは token 1024/1025、nesting 64/65 の exact 境界を持たない。
- **提案する負例ベクタ**:
  - `int now_backoff = 20; std::system("x");` は grammar-invalid と HOST_EFFECT の重なりとして `HOST_EFFECT` を期待。
  - `#define X 1\nint now_backoff = 20;` は grammar-invalid と HOLE_ESCAPE の重なりとして `HOLE_ESCAPE` を期待。
  - 所見 1〜5 の全 vector を `validate_backoff_implementation` 単体だけでなく、attribution と `quarantine(write=False)` の合成テストに入れる。
  - disclosure テストでは plaintext sentinel だけでなく長さ・hash・WAL variant を検査する。

## 所見 10 — 恒真・mask 関係が実装子報告より多い

- **区分**: must-fix
- **成果物影響**: mutation 材料レポートが「各規則が受理集合を独立に縮めた」と誤記し、T-441 防壁の検出力を過大評価する。
- **根拠**:
  - T1-1 空拒否は T1-2 宣言数に包含される。実装子申告どおり。
  - exact な再宣言拒否は T1-2 の「宣言数ちょうど 1」に包含され、T1-3 の再宣言部分には独立 witness がない。
  - `while(true)` / `for(;;)` は grammar より先の HOST_EFFECT に mask される。T1-4 全体は `return` や条件付き loop で live。
  - code point 4096 は byte 4096 に完全包含される。
  - [tokenize 後の `not tokens`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:378) は先行する `implementation.strip()` の空検査に包含される。
  - `single-declarator` の最終 return だけを除いても、検出 branch が exact declaration へ追加せず `declaration-count` に落ちる。mutation は [検出 branch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:435) を変えなければ受理集合を広げない。
- **提案する負例ベクタ**:
  - 空文字では rule ID 変化と受理集合変化を別 mutation として記録する。
  - `while(true){}` と `while(condition){}` を分け、前者は mask、後者は T1-4 の独立 witness とする。
  - code point check 単独除去は `SURVIVED/包含` と明記する。
  - semantic mutation と最終診断 return 削除 mutation を分離する。

## 所見 11 — consumer closure テストは別名・別 materializer の追加を検出しない

- **区分**: backlog
- **成果物影響**: 将来別 ingress が追加されると文法外 bytes が build へ入り得るが、closure テストは現行 1 点のまま成功し続ける。
- **根拠**: [closure テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py:637) は関数名または attribute 名が `render_hole` の `ast.Call` だけを数える。既存 `quarantine()` call を残したまま、別名 call や独自 text replacement を追加すれば `observed` は変わらない。
- **提案する負例ベクタ**:
  - fixture module に `alias = render_hole; alias(base, marker, implementation)` という第二 ingress を追加し、closure 検査が赤になること。
  - より堅くするなら materializer を一つに封じ、検証済み backoff receipt なしでは candidate text を受け取れない API にする。

## 総括

- **must-fix は 10 件**。最も危険なのは数値 token の前方一致で、`value=1` と `double now_backoff = 1e2;` が grammar・attribution の両方を通り、実行値 100 を genome 1 に certified 帰属できる点。
- commit `6935fcae` は現状のままでは条件付き採用不可。少なくとも数値 literal の完全 token 解釈、indirect rebinding、C++ 宣言構文、production preflight の WAL 化、資源 cap の再裁定を先に直す必要がある。
- 親裁定で誤っている点:
  - T1-6 だけでは `20` / `20.0` / `20.00` は正準化されない。implementation bytes と source digest は依然別である。
  - t441.m03 の「空検査を外すと受理集合が広がる」は誤りで、宣言数規則に mask される。
  - 「lambda 即時呼出しが Tier 2 で開いている」という総称は過大。通常の `[] { return 20.0; }()` は T1-4 の `return` で拒否される。
  - 一方、条件分岐・loop・try/catch の拒否は straight-line の射程内、`20.0` value は数学的整数かつ無損失変換なので裁定内と判断する。`001`・suffix・UDL を grammar 単体で拒否しないことも Tier 2 の opaque expression と整合するが、帰属検査まで安全であることを意味しない。