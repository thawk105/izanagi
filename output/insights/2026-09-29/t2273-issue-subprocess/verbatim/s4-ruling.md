# 段 4 裁定 — [T-2273][T-2560] 発行 subprocess の短縮 (2026-09-28)

資料: s1-brief.md、codex/s2-plan-out.md、codex/s3-consult-a-out.md (レンズ A、修正後 GO)、codex/s3-consult-b-out.md (レンズ B、修正後 GO)、pin-closure.md、profile-summary.md。
裁定 inbox 再走査: 新着 full39 (09-28 08:00) は本 wave に無関係。

## 所見の裁定

| # | 所見 | real/refuted | 採否・処置 |
|---|---|---|---|
| A1 | 窓式 `[max(0,p+len(L)-W), min(len,p+W))` は helper の受理文法 (key は literal、値は `.` 以外のメタ文字なし) で等価。反例なし | real (肯定) | 採用。論証を docstring に 2 文で書く |
| A2 | 右端 off-by-one を殺す fixture は単一 alternative の式が要る (三形式の式では最大幅が JSON 形式由来で plain 形式の hit が窓に収まる) | real | 採用。M1 の fixture を単一 alternative・単軸にする |
| A3 | 幅は `getwidth()` の最大値だけを使う。最小値を使えば hit が落ちる | real | 採用 |
| A4 | `MAXREPEAT` 注入 test と変異は等価変異になりやすく自然入力にも無い | real | 採用し plan を変更: MAXREPEAT の分岐自体を置かない。幅が飽和しても窓 `min(len,p+W)` は全文に広がるだけで正しいので分岐は不要。fallback は既存の `L is None` と非 exact `str` だけ |
| A5 | 共通 literal の `in` を外す変異は候補数では殺せない (軸 `find` が同じ 0 候補に落とす) | real | 採用。共通判定の実発火回数を独立に数える番人を置く |
| A6 | `rel` だけで共通判定を cache する変異は「第 1 走で literal A 不在 → 第 2 走で別 literal B 存在」の同一 rel・単軸で殺す | real | 採用 (M5) |
| A7/B2 | 50〜60 秒削減・13 回走査は予測 (profile は呼出し回数を数えていない、fixture は /tmp)。新たな `find` と窓 search の費用が乗る | real | 採用。記録では「上限約 62 秒・予測」と書き、効果は再 profile と実受入でだけ言う |
| B1 | MAXREPEAT test・変異は削れる | real | A4 と同じ処置 |
| B3 | 共通判定の共有だけ (局所化なし) の小差分を先に測る余地 | refuted | 局所化なしでは regex 行 約 46 秒が残り、共通判定だけでは上限 約 16 秒。分けて測ると受入系列が 2 本になり計算量が倍になる。両方を 1 変更単位にする |
| B4 | 同一 key の builder は lock で 1 回、別 key は並行しうる。L node は active_v2 key の builder だけを待つので、child 短縮の和を W_0 に足さない | real | 採用。記録の効果見込みをこの形で書く |
| B5 | 実装後に同じ単独走 profile を 1 回取り直してから系列へ | real | 採用 (計測事前登録 1) |
| B6 | 自己汚染確認は「変更 2 file の conjunction 0 件」と「既知陽性 file を含む別走の陽性対照 > 0」を分ける | real | 採用 |

## plan v2 (実装子への指示の正本)

変更 file の上限: `orchestrator/campaign/s8b_holdout_freeze.py`、`orchestrator/tests/test_s8b_holdout_freeze.py`。

1. `_scan_one` (s8b_holdout_freeze.py:516):
   - 既存の snapshot・compile・`required_literal`・`axis_literals` の導出 (呼出し回数 12 / search_repository を保つ、test :407) は変えない。
   - 軸 literal が非 None の軸について、同じ snapshot の式から `sre_parse.parse(expression).getwidth()[1]` で最大幅 W を 1 回求める (Python 3.10、`import sre_parse`)。最小幅は使わない。飽和値の特別扱いをしない。
   - 共通 literal の `in` 判定は 1 回の `search_repository` 内で (literal, rel) ごとに 1 回にする。memo がある時は `_ScanMemo` に dict を足して保持し、既存の identity 検査・内容変化拒否を通った後にだけ再利用する。memo が無い単独 `_scan_one` では呼出し内の局所 dict。判定は module private の小 helper (例 `_text_contains(text, literal)`) を通し、test が発火回数を数えられるようにする。
   - 軸判定: 旧 :562 の `axis_literal in text` と :564 の全文 search を、module private helper (例 `_search_localized(pattern, text, literal, width) -> bool`) に置き換える。helper は `text.find(literal)` で出現 p を列挙し (次は `find(literal, p + 1)`、重なりを含む)、各 p で `pattern.search(text, max(0, p + len(literal) - width), min(len(text), p + width))` が真なら True。出現 0 件なら False (regex に進まない)。
   - 軸 literal が None・式が非 exact `str`・共通 literal が None の軸は、従来どおり全文 `compiled[axis].search(text)` (既存 fallback、test :388・:398・:475・:508 の挙動)。
   - 例外の型・文言、列挙・open・read・decode・免除、report の canonical bytes は不変 (D512)。production に無効化 knob・環境変数を足さない (D513)。ソースに軸 key と具体値の連続 literal を書かない。
2. docstring: 窓式の等価性の根拠を 2 文 (helper の受理文法では全 match が L を含み長さ ≤ W、anchor・lookaround が無いので pos/endpos 付き search は全文 search と同じ真偽)。
3. 既存 test の改訂 (test_s8b_holdout_freeze.py):
   - :427 と :985〜1097 の `SearchSpy.search` を `(text, *args)` を受ける形にし、呼出しごとに (text, 全文か窓か) を記録する。
   - 番人の数える単位を「前置判定を通って局所化 helper (または全文 search) に届いた (軸, text) 候補数」に移す。:427 は陽性 text 5 候補・`ycsb_unrelated` 0 候補。:985 の三段 (optimized / `_derive_required_literal` 無効 / `_scan_one` → reference) は候補数 0 / 5 / 9 と reference 3 回 (["H1","H2","rr50-positive-control"]) を保つ。
   - :985 の fixture に「局所化 helper だけを全文 search の reference 関数へ差し替えた段」を足し、候補数は optimized と同じ・report bytes 一致、optimized 段では窓付き search だけが発火し全文 search が 0 回、差し替え段では全文 search だけが発火することを固定する (M4 の番人)。
   - 共通判定の helper の発火回数を 1 回の `search_repository` で (共通 literal を持つ走査 1 種 × text 数) に固定する番人を 1 本 (M6)。
   - :645 (memo hit で search 0 回) は helper 候補 0 回として保つ。
4. 追加 test (最小): 単軸の等価性 — `_scan_one` を直接呼び、各 text の軸真偽を独立な全文 `re.compile(expr).search(text)` と比較し、`_reference_scan_one` (:917) との report 一致も見る。入力: (a) 単一 alternative の plain 形式が text 末尾ちょうどで終わる (M1)、(b) JSON 形式で match 開始が L の出現より前 (M2)、(c) 自己重なりする literal で最初の出現は不一致・重なる次の出現で一致 (M3)、(d) 値側 `.` が任意 1 文字に一致、(e) 8192 byte 以降の hit (既存 :956 の拡張で可)。式は合成 key を使い実軸の key+値を連続で書かない。共通判定 memo の rel 取り違え (M5): 同一 texts mapping・同一 memo で literal A 不在の式 → literal B 存在の式の順に 2 回 `_scan_one` を呼び、第 2 走の hit を固定。
5. 自己汚染: 親が段 6 で `search_repository(root, files=[変更 2 file])` の conjunction 0 件と、既知陽性 file を含む別走の陽性対照 > 0 を確かめる。growth hold は解除しない。

## 変異の事前登録 (DW-M01、実装前)

kill の期待 node は実装後の probe (全件 SURVIVED 期待の dispatch) で観測し、登録と照合してから final を走らせる。各変異は単一理由 (他層の mask なし) を実装後に確認する。

| ID | 変異 | 殺す番人 |
|---|---|---|
| P0 | docstring の 1 語 | (SURVIVED 期待) |
| M1 | 窓右端 `p + width` → `p + width - 1` | 4(a) 単一 alternative・単軸の per-text 真偽 |
| M2 | 窓左端 → `p` | 4(b) JSON 形式・単軸の per-text 真偽 |
| M3 | 次の出現探索 `p + 1` → `p + len(literal)` | 4(c) 自己重なり・単軸の per-text 真偽 |
| M4 | 局所化 helper の本体を全文 `pattern.search(text)` にする (局所化を外す) | 3 の「窓付き search だけが発火」番人 |
| M5 | 共通判定の memo key を rel だけにする | 4 の M5 test (第 2 走の hit) |
| M6 | 共通判定の memo を外し軸 pass ごとに判定する | 3 の共通判定の発火回数番人 |

## 計測の事前登録 (結果を見る前に固定)

1. **再 profile (系列投入の前提):** 実装 tree で段 1 前と同じ単独走 profile (同じ test node、同じ py-spy 引数、generic dispatch) を 1 回取る。child の sample 数を段 1 前の 4,313 と比べ、**70 % 以下 (30 % 以上の短縮) なら系列へ進む**。満たさなければ系列を投げずに記録して止める。
2. **系列:** A = 測定準備時の local main (clean worktree)、B = A + 本 wave の実装 commit (clean worktree)。`IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` の直接投入、順序 A,B / B,A / A,B、門番 = 他 session の受入 leader ≤ 1 ∧ load1 ≤ 60 (前 wave と同じ)。温めは両 tree で collect-only を 1 回。E1: login collection の A/B 差が本 wave の追加 test node だけであることを確認。infra 失敗は同じ位置で取り直し (上限 4 走)。
3. **判定量:** 対 i の Δ_i = W_0(A) − W_0(B)、r_i = Δ_i / W_0(A)。集計器は前 wave の `t2273pi_ab_analyze.py` (Codex author、逐語は前 wave insight の probe-source.md) をそのまま使う。
4. **land 区分:** (i) 3 対すべて Δ > 0 ∧ r の中央値 ≥ 10 % → land。(ii) 3 対すべて Δ > 0 ∧ 中央値 < 10 % → 小さい改善として land (出力等価な変更で検出力の喪失が無く、ユーザー方針「目標値は合否判定ではない」に従う)。(iii) それ以外 → land しない (再 profile の child 短縮は記録に残す)。
5. **5 分上限 (別判定):** B の W_max 3 走の中央値 ≤ 300 秒か。届かなければ残る律速 (最遅 shard・W_1・pre) を記録する。
6. **補助量 (判定に使わない、報告だけ):** 各対の W_1・W_2・pre・post・O_max と対差。最遅 shard の番号。
7. **計算量:** (下の erratum E1' を参照)

### erratum E1' (2026-09-29 07:29 JST 固定、系列 01-A・02-B 完了後、**W の値を親が閲覧する前**)

- 事実: 01-A・02-B (rc=0) の後、03-B の投入前検査が旧 E1「A/B 共通 node の 3 shard 割付の完全一致」の不成立で停止した。collection 差は新設 8 node ちょうど (成立)、shard-0 の共通 node 4,302 件は完全一致、新設 8 node は全て B の shard-1、shard-1/2 間で分割が変わった (A/B の木で決まる決定的性質で、残る対も同じ)。
- 改訂: E1 の割付一致の要求を「各対の **shard-0 に選択された A/B 共通 node の multiset の完全一致**」に限定する。collection 差の条件・各走の緑・HEAD と clean・系列順序・skip 一致など他の有効性条件は不変。01-A・02-B を含む全対へ一律に適用し、対ごとの例外は認めない。W_0 の Δ・対率、land 区分 i / ii / iii、B の W_max 中央値による 5 分判定は不変。
- 付帯条件 (段 6 の賛否相談 `codex/s6-e1-pro-out.md`・`codex/s6-e1-con-out.md`): 旧 E1 による判定を `undetermined` として並記する。各走の 3 shard の実行 host の重なりを報告する。W_1・W_2・pre は A/B で shard の test 集合が違うため各走の値と構成を並べるだけにし、対差を実装効果と呼ばない。W_max の変化を shard-0 の実装効果だけに帰属させない。
- 集計器の改訂は Codex author (probe の移植子と同じ木) に行わせ、改訂後の集計器の sha256 を系列再開前に記録する。
- 記録 (2026-09-29 07:38 JST、系列再開前・W 未閲覧): 改訂前 sha256 `b8a0f097b23f53a6386fbed2e18a2d774fa78eed06f0f34d85f9567b6c5aee95`、改訂後 `50e1cc79cd563def6dbc684de8c29438fcfe2732192d591b673fc7be35c5df54` (Codex fix、子 branch fix-t2273is-probe-1 の 093592384、前 wave の系列の再集計で値・区分不変と合成入力の正負を確認)。

8. **計算量 (元の 7):** 実績単価 (前 wave: 受入 1 走 ≈ 879 node 秒、焦点走 ≈ 347、変異 ≈ 668、温め 111、単独 profile 212) から、再 profile 0.06 + 焦点走 2 回 0.2 + 変異 0.19 + 温め 0.03 + 系列 6 走 1.46 + 記録前受入 0.25 + 実施済み profile 0.07 ≈ **2.3 node 時間** (取り直しで最大 +1.0)。2 node 時間以上なので、再 profile の結果を添えて系列投入前にユーザー確認する。
