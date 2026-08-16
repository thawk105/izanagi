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
6. **死んだ枝の除外**: 定数偽 branch (`if False:` / `if 0:`) 配下と、どこからも呼ばれない
   nested function 配下の call は到達から除く。
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

## {{D:decider-version-v2}}. 到達判定の cross-module 化に伴い判定器の版を v2 へ上げる

**決定:** `DECIDER_VERSION` を `s8c-decider/v1` から `s8c-decider/v2` へ bump する。
あわせて、版一致検査が恒真にならないよう exact assert を 1 本置き、`v2 -> v1` 変異で
kill されることを変異 matrix で実証する。

**理由:**
- D458 決定 (1) は、判定器・評価器・射影のいずれかで受理集合・拒否理由・射影された判定入力の
  意味を変える変更を、bytes 差の有無に関わらず bump の対象としている。本改修は条件 12 の
  拒否理由を `environment-contract-consumer-absent` から
  `allocation-enforcement-consumer-absent` へ変えるため該当する。
- 不一致 fixture をすべて「current と異なる版」へ動的化すると、bump 自体を削除しても
  版関連テストが同じ論理で通ってしまう。これは「この行を消しても緑」の恒真な保証であり、
  版が意味を代表するという D458 の設計を無効化する。exact assert がその穴を塞ぐ。

**理由 (被害の範囲):**
- 凍結記録の tip は legacy schema で `decider_version` を持たず、D458 決定 (3) により既に
  `decider-version-unbound` である。よって bump で失効する現用 capability は無い。
- 版 literal を使う既存 fixture は 1 file 内の 7 箇所に閉じており、いずれも
  「current と異なる版」または exact type 差の検査へ是正できる。

**却下した選択肢:**
- bump しない — 新版の受理意味が旧版の版名のまま記録され、発効判定が旧版の意味で緑を出しうる。
- 凍結記録を新 schema で再発行して発効させる — 発行は別 owner の所有であり、本改修の
  scope 外である。診断を真にすることと発効させることは別の問題である。
