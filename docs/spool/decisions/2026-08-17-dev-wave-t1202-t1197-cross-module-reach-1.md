---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1202-t1197-cross-module-reach
seq: 1
---

## {{D:cross-module-reachability}}. 8c 事前登録の到達判定は宣言 root からの import 束縛だけを辿る

**決定:** 評価器 `s8c_preregistration_evidence.py` の到達判定を、同一 module 内の top-level 定義
だけを辿る形から、契約が宣言する root module を起点に**実際の import 束縛だけ**を辿る canonical
`(repo 相対 path, top-level 関数名)` graph へ置き換える。bare name の集合比較を exact target
比較へ変える。ユーザー裁定 2026-08-16 /rulings 全件 第 3 回 択 (ii) の実装である。

具体の受理規則は次のとおり。いずれも満たさないものは**到達と数えない** (fail-closed)。

1. **import 解決**: `from . import X` / `from .X import y` / `from .X import y as z` /
   `import a.b.c` / 複数名 `from . import a, b, c` を exact に解決する。module 名から path への
   解決候補は `a/b/c.py` と `a/b/c/__init__.py` の 2 つだけで、exact 1 blob のときだけ解決する。
   wildcard import、`getattr`、`importlib`、lambda、`functools.partial`、instance method は追わない。
2. **binding の一意性**: import 名も local 名も、当該 scope での束縛がちょうど 1 回でなければ
   解決しない。local import、`for`、`with`、`except as`、walrus、`global`、`nonlocal` による
   shadow を保守的に列挙し、1 つでもあれば解決不能へ倒す。package `__init__.py` の
   top-level 複合文も読み、同名 export があれば曖昧として閉じる。
3. **module-level alias**: `_lookup = env_contract.lookup` の形は、単一 `Assign` / `AnnAssign` で
   target が単一 `Name`、RHS が `Name` または静的 `Attribute` chain のときだけ解決する。
4. **限定 value-flow**: callable の**既定引数は witness にしない**。local 名がその関数内で
   ちょうど 1 回だけ解決可能な callable へ代入され、かつその代入が call を**支配する**ときだけ
   束縛する。keyword 引数 `k=v` による仮引数への伝播を辿る。位置引数と `*args` が見えた
   仮引数は hard-block する。
5. **限定 dict carrier**: 単一 `Assign` で束縛され、RHS が keyword 引数のみの `dict(...)` で、
   subscript 代入が str literal かつ target key と異なる key に限られ、`**carrier` として
   ちょうど 1 回 splat される carrier だけを辿る。target key への代入、非 literal key、
   `update` / `pop` / `del` / `|=`、literal dict splat、carrier 再束縛はいずれも carrier を
   使用不能にする。
6. **死んだ枝の除外**: 静的に確実な literal だけを定数と判定し、定数偽 `if` の body、
   定数真 `if` の `else` 節、定数偽 `while` の body、同一 block 内で無条件
   `return` / `raise` / `continue` / `break` の後に続く文、およびどこからも呼ばれない
   nested function 配下の call を到達から除く。変数・関数呼び出し・比較式は「不明」として
   両枝を残す。**除外は受理集合を狭める方向にだけ効かせる** — 不明なものを除外すると
   実在する強制を不在と報告する誤診断になり、本改修の目的と逆向きになる。
7. **終端 target の所在**: 終端 target の**定義 path** は契約が宣言する evidence path 集合の
   中でなければならない。中継 module は宣言外でよい。production tree の外
   (`orchestrator/tests/` 等) は拒否する。
8. **上限**: module 512 / depth 64 / callable state 2048 / raw bytes 16 MiB。超過は
   `reachability-limit-exceeded` の `ERROR` とし、`commit-blob-read-error` へ畳まない。
   上限に触れないことは「実 tree の全条件がどの上限にも触れない」検査で担保する。
9. **証拠**: 宣言外の中継 module も commit blob から読み、読んだ blob は `EvidenceRef` に載せる。
   判定に効いた bytes を report から消さない。契約 JSON の `required_evidence` は増やさない。

**理由:**
- 契約自身の `reachable_from` が C12 で `"main -> run_trial -> env_contract.lookup"` と
  cross-module の hop を明示しており、契約は最初から cross-module 到達を意図していた。
  評価器がそれを実装していなかっただけである。証拠範囲の独断拡大ではない。
- 宣言 path 集合に閉じると、C12 の実 chain が通る中継 module 2 本が宣言外であるため、
  裁定 (ii) が構成上実装不能になる。裁定を実装不能にする解釈は採れない。
- 既定引数を witness にすると、実配線を削っても述語が「到達」と報告する。これは実在しない
  強制を実在と報告する方向の拡大であり、規律 2 が禁じる形である。実測でも production 経路は
  当該 callable を常に明示的に渡しており、既定引数は一度も使われない死んだ束縛だった。
- 上限を実 tree の閉包より小さく取ると、target が実在しない条件の診断が
  `reachability-limit-exceeded` にすり替わり、「実際に不在なものは依然 `UNSATISFIED`」という
  受理条件を壊す。上限は暴走止めであって意味論的 gate ではない。

**却下した選択肢:**
- 到達判定を宣言 evidence path 集合に閉じる — C12 の中継 module 2 本が宣言外であるため
  裁定が構成上実装不能になる。
- callable の既定引数を無条件に may-reach edge として辿る — 実配線を削っても到達と報告する
  false positive を作る。段 2 プランの推奨案だったが敵対レビュー 2 本が独立に指摘し却下した。
- `**kwargs` 経由を一律に非 witness とする — 実 production chain が dict carrier を 2 段通るため、
  字義どおり適用すると裁定が目的を達しない。限定した不変 carrier だけを許す形へ改めた。
- 到達判定の緩和で条件を充足させる — 述語を満たすための細工であり規律 2 が禁じる。
  本改修は診断を真にするだけで、条件の充足可能性は変えない。

## {{D:decider-version-hold}}. 評価器の拒否理由の導出を変えるが判定器の版を追加 bump しない

**決定:** 本改修は条件 12 の拒否理由の導出を変えるが、`DECIDER_VERSION` を
`s8c-decider/v2` のまま据え置き、追加の bump も新しい凍結世代の発行も行わない。
`decider_version` の identity assertion は literal を保ち、不一致 fixture の値生成だけを
「current と異なる版」の動的 helper にする。

**理由:**
- 2026-08-17 のユーザー裁定 (worklog 622) が「第 5 世代を発行して完結する推奨 (a) は却下、
  検証済みの改善の着地を優先する」と定めた。理由は「版と性能を論文が結び付けないので、
  版の厳密な前進に費用を払わない」であり、2026-08-12 の既定方針
  (論文主張に要るのは粗い provenance のみ) の再確認である。
- 着地直前の実測で衝突は既に消えている。main の `DECIDER_VERSION` は
  対になる [T-1167] の着地により既に `s8c-decider/v2` で、凍結世代 g5 が同じ版を束縛する。
  判定器 module は main と本 branch で blob 一致であり、本 wave 側に版の差分は残っていない。
- 追加 bump を行えば新しい凍結世代の発行が必要になり、`prepare_revision` の
  spurious-revision 検査により保護対象の正本 doc か証拠契約の改訂が必須になる。
  裁定はこの費用を払わないと定めた。
- 版 fixture をすべて「current と異なる版」へ動的化すると、bump 自体を削除しても
  版関連テストが同じ論理で通る。これは「この行を消しても緑」の恒真な保証である。
  identity assertion を literal に保つことがその穴を塞ぐ。逆に不一致 fixture の値を
  literal で書くと、将来 v3 へ上げた瞬間にその値が「不一致」でなくなり fixture が壊れる。
  両者は逆向きの要求なので使い分ける。

**この決定が保証しないこと (限界宣言):**
- **D458 決定 (1) はこの面で発火しない。** 同決定は「判定器・評価器・射影のいずれかで
  受理集合・拒否理由・射影された判定入力の意味を変える変更は版を bump する」と定めるが、
  本改修は条件 12 の拒否理由の導出を変えたうえで版を据え置いた。これは規範との不整合であり、
  上記ユーザー裁定による**明示的な受諾**である。判断は `effective` が False で
  実害のある capability が存在しない現状に依存しており、発効後は成り立たない。
- この不整合は**機械検出されない**。D458 本文自身が「受理意味を変えたのに bump しなかった
  場合は検出しない。bump 忘れは裁定が受け入れた手動 provenance の範囲に残る」と明記し、
  検出 gate の新設を「bytes 凍結の再導入であり裁定に反する」として却下している。
  本決定はその既知の限界の上に乗る。新しい検出機構・pin・束縛機構は作らない。
- 版が「受理意味を代表する」という D458 の設計は、この面では成立していない。
  `s8c-decider/v2` は [T-1167] の allocation 節縮小の意味を代表するが、
  本改修が変えた到達判定の射程は代表していない。

**却下した選択肢:**
- 版を v1 へ戻して着地する — 裁定控えが衝突未消滅時に書いた「択 (b) 相当」だが、
  着地直前の実測でその前提 (main が v1、g4 が最新) は消滅している。戻せば別タスクが
  着地させた bump を本 wave が取り消すことになり、g5 が v2 を束縛しているため
  不変検査が赤になる。
- 第 5 世代を発行して完結させる — 保護対象の正本 doc か証拠契約の改訂を伴う。
  ユーザー裁定が却下した。
- 受諾を機械可読な registry へ登録する — 設計規範への受諾済み逸脱を登録する汎用機構は
  repo に存在せず (最も近い `KNOWN_PROVENANCE_VIOLATIONS` は provenance 領域限定)、
  新設は同じ裁定の理由 (版の厳密な前進に費用を払わない) と矛盾する。
  D458 自身が使っている「この決定が保証しないこと」節の慣行で残す。

## {{D:main-owned-gate-order}}. 別タスクが着地させた gate 順序と述語は本 wave で反転させない

**決定:** 条件 12 の評価では、対になる [T-1167] が着地させた形をそのまま保つ。
すなわち allocation gate を第 1 gate に置き、その述語
(`{"read_binding","check_reservation"}` の module-local 到達と `allocation_consumer` の定義)
と helper の signature を変えない。本改修の cross-module 到達判定は、この gate を通過した
後段の env/guard gate にだけ適用する。

**理由:**
- local main には `test_c12_allocation_binding_gate_precedes_environment_gate`
  (両 consumer 不在の木で reason が allocation になることを固定) と
  `test_c12_allocation_binding_helper_rejects_check_without_read_binding`
  (helper を直接呼んで signature を固定) が実在する。順序も signature も偶然ではなく、
  別タスクが意図的に決めてテストで固定した設計判断である。
- 順序を本改修側へ反転させても、実 tree の判定は 1 つも変わらない。
  `read_binding` / `check_reservation` は cross-module でも `run_trial` から到達しない
  (呼び出し点は `s8b_oracle_driver` と `s8b_floor_campaign` の 2 箇所だけで、前者を import する
  production module は 0 件、後者の production importer 3 件はいずれも当該関数へ届かない)。
  効果ゼロで他タスクの設計を反転させる変更は採らない。
- 本改修の cross-module 機構が今日の実 tree の条件 12 で発火しないことは欠陥ではない。
  [T-1167] は allocation 節を**実現可能な**形へ縮小した。それが満たされた瞬間に評価は
  env/guard gate へ進み、そこが module-local のままなら誤診断が再び出る。それを防ぐのが
  本改修の役割である。

**却下した選択肢:**
- gate 順序を env/guard 優先へ戻す — 上記 2 テストの書き換えが必要になり、
  「既存テストの期待値を変えない」規律に反する。実 tree の終状態も変わらない。
- allocation gate の到達判定も cross-module へ広げる — helper の signature が変わり
  直接呼びのテストが壊れる。実 tree の verdict は変わらない (どちらでも不到達)。
- 終端 target の定義 path を条件自身の宣言 path へ限定する — 条件 9 の正規 target が
  条件 10 の宣言 path にあるため、条件 9 の reason が変わる。契約は正当に別条件の
  宣言 path にある consumer を参照している。所見自体は real なので別タスクへ送る。
