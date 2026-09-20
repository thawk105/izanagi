# [T-1871] 必読資料の逐語 (親が job dir へ射影、2026-09-20)

## A. D1441 (docs/decisions.md 45587〜45603 行、逐語)

```
## D1441. 非列挙は固定予算の下での操作的定義へ改める (2026-09-02)

**決定:** 復活条件の「非列挙」を「固定予算の下で操作的に列挙し尽くせない」へ定義し直す。
骨格が新しい状態を持つ案はこの軸では追わない。レンズ本数の数え方は規則にしない。
段階 A の人間 gate はやり直さない。

**理由:**
- 厳密な意味的無限を維持すると条件自体を撤回するほかなく、軸が失われる。
- 新しい状態を持つ骨格を追うには D48 の proxy 禁止に対する別の明示裁定が要り、本裁定の射程を超える。
- レンズ本数の規則化は裁定境界の変更にあたる。

**却下した選択肢:**
- 意味的無限を維持して条件を撤回する — 軸の復活経路を失う。
- レンズ本数を規則化する — 裁定境界の変更を副次的に行うことになる。

## D1442. 床値の依頼が指す量の確定はユーザーに留保する (2026-09-02)

```

## B. 対象箇所: docs/phase3-main-experiment.md 170〜173 行 (2026-07-12 追記「旧 headline 主張の扱い」、逐語)

```
**旧 headline 主張の扱い:** 削除せず scope 限定で保存 — 非列挙のコード片軸 (D48 差し戻し事項の
消化後または将来軸) が実体化し偵察が floor 超地形を確認した場合にのみ検証可能。**F 段の拘束:**
主張 S の下で trigger-gating の軸内実計測は headline 判定に寄与しない — F 段継続は 8c 配線検証の
最小 iteration に限定、動作点再ホストは 8b または非列挙軸の事前登録と束ねた別途正当化を要する。
```

## C. insight §6 裁定 1〜4 (output/insights/2026-09-01_t1871-nonenum-axis-stage-b-package.md 175〜232 行、逐語)

```
## 6. ユーザー裁定を求める事項

### 裁定 1 (中心) — 復活条件の「非列挙」をどう定義するか

`docs/phase3-main-experiment.md` 2026-07-12 追記の「非列挙のコード片軸」の意味を確定させたい。
壁 1 により、この語の読み方が軸の存否そのものを決める。

- **択 a — 「固定予算の下で操作的に列挙し尽くせない」へ定義し直す。**
  D1067 は既に主張を「固定予算・固定編集面の下で、事前登録した非 LLM 生成器より高い score」へ
  狭めている。この主張に意味的無限は要らず、必要なのは
  「事前登録した生成器の試行予算では到達 truth-vector を覆い尽くせない」ことだけである。
  代償 = 拘束力ある事前登録 (`docs/phase3-main-experiment.md`) の文言改訂を伴うため、
  D1012 の作法により日付付き・ユーザー承認付きの発火 commit が要る。
- **択 b — 厳密な意味的無限を維持する。** この場合、壁 1 によりコード片軸は原理的にどれも不適格であり、
  旧 headline 主張の復活条件は到達不能である。条件そのものを撤回するのが筋になる。
- **択 c — 判断を保留し、B-5 と後段 ([T-1872]) の休眠を継続する。** 現状維持。

**親の推奨は択 a。** 理由 = 壁 1 は個別の hole の欠陥ではなく条件の書き方の問題であり、
D1067 が主張範囲を狭めた時点で意味的無限は既に不要になっている。
択 b は誠実だが、復活条件を撤回すると旧 headline 主張の保存自体が無意味になる。

### 裁定 2 — 骨格が新しい状態を持つ案を、この軸で追うか

段 6 レンズ 3 は「骨格所有の連続 abort 数は D48 が予約した『既存メンバ読取の拡張』を越えており、
同一軸の契約改版か新しい複合軸かを段階 A の人間 gate で裁定し直す必要がある」と指摘した (R19)。
加えて R15 が「この量は絞り込んだ fitness 信号である」と示している。

- **択 a — 追わない。** 既存メンバ読取の範囲に留め、壁 2 を「この hole では両立しない」と結論する。
- **択 b — D48 の proxy 禁止に対する明示裁定を置いた上で追う。** 「いま失敗し続けている度合い」を
  gate の入力として許すかどうかは、規律 2 に触れる設計判断であり、AI の裁量で決めるべきでない。
  許すなら、どの範囲まで (連続数のみ / 閾値比較のみ / 上限付き) を同時に決める必要がある。
- **択 c — 段階 A へ戻し、axis-proposer に別 hole を提案させる。**

**親の推奨は択 b を検討した上で、まず択 a。** 理由 = R15 の指摘は構造的で、
「fitness 信号ではない」という区別を実装で保証する手立てが本 wave では見つからなかった。
規律 2 の面を持つ判断を、証拠の裏付けなしに親が採るべきでない。

### 裁定 3 — レンズ本数の数え方を規則にするか (裁定境界の変更)

本 wave では、親が段 4 で中心設計を差し替えた結果、**段 3 の 2 レンズが差替え後の版を見ていない**
状態が生じた (R20)。一般規則にするなら次の形になる。

> ドメイン正本がレンズ本数を指定する設計レビューでは、dev-wave 段 4 の裁定で中心設計を
> 差し替えた場合、差替え後の版を要求本数のレンズが検査するまで出口 gate を満たしたとしない。
> 段 3 のレンズ数を、差替え前の版に対するものとして本数へ算入しない。

これは**親の裁定権限を制約する規則**であり、裁定境界の変更に当たる。
`docs/skill-self-improvement.md` の dev-wave 終端は、この類型を実装せず裁定パッケージへ送ると定める。
よって本 wave では採用せず、採否をユーザーへ返す。行き先候補 =
`docs/dev-wave/workers.md` の `DW-S03` または `docs/dev-wave/core.md` の `DW-S04`。

### 裁定 4 — 段階 A の人間 gate をやり直すか

裁定 2 で択 b または択 c を採る場合、`docs/axis-onboarding.md` の段階 A 人間承認 gate を
改めて通す必要がある (R19)。この gate の判定材料には
「提案の hole 位置と骨格が既存軸台帳と構造的に異なるか」が含まれる (D47 必須条件 4)。

---
```

## D. insight §4 壁 1 (同 113〜126 行、逐語)

```
## 4. 中心的な発見 — 二重の壁

この hole で非列挙のコード片軸を作ろうとすると、性質の違う壁に 2 枚ぶつかる。

### 壁 1: 有限幅の壁 (定義の問題)

**C++ の観測はすべて有限幅である。** 入力空間が有限なら、そこから boolean を返す述語の集合も必ず有限になる。
`unsigned` の counter を足しても、幅を w とすれば入力点は最大 R×2^w で頭打ちになる (R14)。
**したがって「非列挙」を厳密な意味的無限として要求する限り、コード片軸は原理的にどれも不適格である。**
これはこの hole の欠陥ではなく、条件の書き方の問題である。

現行の復活条件 (`docs/phase3-main-experiment.md` 2026-07-12 追記) は
「非列挙のコード片軸が実体化し、偵察が floor 超地形を確認した場合にのみ検証可能」と書いており、
「非列挙」の意味を定義していない。**この語を厳密な意味的無限と読むなら、条件は到達不能である。**
```

## E. D1789 / D1790 (docs/decisions.md 54183〜54220 行、逐語)

```
## D1789. 発効後の事前登録は、文面の瑕疵でも書き換えず erratum で訂正する (2026-09-08)

**決定:** 事前登録が発効し、その規則で解析を回した後に文面の瑕疵 (曖昧さ・限定漏れ・
自己言及の陳腐化) が見つかっても、**文書の bytes を書き換えない。** 訂正は insight の erratum 節に
「どう読んで実装したか」と併せて記録する。次の版 (次の cohort 向けの事前登録) で本文へ取り込む。

**理由:**

- 事前登録の bytes は成果物と解析器が sha256 で pin する束縛である。書き換えれば sha が変わり、
  その版で回した解析結果との対応が切れる。
- 「規則を変えていない、字句を直しただけ」は書き手にしか分からない。読み手には結果を見た後の
  編集としか見えず、事前登録が果たすべき役割そのものが消える。
- 瑕疵の指摘は結果を見た後に来る。そこで文書を触れる運用にすると、抜け道が常設される。

**却下した選択肢:**

- **文面だけ直して sha を貼り直す** — 解析器・テスト・成果物の pin をすべて追随させることになり、
  「結果を見た後に事前登録を触った」履歴が残る。数値が変わらないことは弁明にならない。
- **瑕疵を記録しない** — 二通りに読める箇所は、片方の読みだと成果物が全件不適格になるものもある。
  どう読んで実装したかを残さないと、後から検証できない。

## D1790. 測定時点の束縛と現行の解析規則は、別々の定数として pin する (2026-09-08)

**決定:** 凍結成果物を後から再解析する解析器は、**成果物が記録しているべき事前登録 sha (測定時点の版)**
と、**解析規則の正本として渡される文書に要求する sha (現行の版)** を、独立した定数として pin する。
どちらの側も「任意の値を受理する」形や「複数版のいずれかを受理する」形へ緩めない。

**理由:**

- 絶対規律 7 の帰結である。成果物が測定時点の版を記録しているという事実は後から変わらない。
  一方、解析規則は改訂されうる。この 2 つを同一視すると、規則を改訂した瞬間に既存の成果物が
  全件不適格になり、再測定なしの再解析ができなくなる。
- 逆に両版を受理する形へ広げると、どの版の束縛で測られた成果物かを解析器が区別できなくなる。

**帰結として、この形の解析器は特定の cohort 専用になる。** 新しい版で測った成果物は同じ解析器の
受理集合に入らない。**これは意図した狭さであり、将来 cohort 用の互換層は作らない。** 新しい cohort を
解析するときは、その cohort の束縛を持つ解析を別に用意する。

```

## F. docs/phase3.md 285〜294 行 (同 doc の更新契約、逐語)

```
## 旧主実験の事前登録 — `docs/phase3-main-experiment.md` へ分離 (2026-07-05, D35)

主実験 (後続段 6) の事前登録 = 反証可能な主張・headline 比較 4 対照 (silo stock 最良 / クロスプロトコル
stock 最良 / ランダム変異 / 機械 sweep) とその操作的定義・LLM ablation・統計計画 (floor 流用禁止・
サンプル設計・Holm 補正・天井の不在・deceptive 相当の検証・検証相の配線)・失敗条件 (a)〜(e) は
`docs/phase3-main-experiment.md` に事前登録してある。同文書は元の本文を消さず、既知結果を開示した
日付付き改訂だけを append-only で重ねる契約である。D52 は D50/F 段等の結果を見た後の複合改訂で、
主張 S と「失敗条件 (g) 発火時に S' へ縮小する規則」を固定した。その規則が 2026-07-13 の S-3 棄却で
実際に発火した。一方、8b の workload 特化は旧比較の結果から
独立した新しい主張なので、既知結果を pilot と明示し、未見 holdout・descriptor ablation・全件報告を別の
```

## G. 先例: docs/backoff-policy-performance-preregistration-erratum-1.md 1〜16 行 (逐語)

```
# adaptive backoff の step policy 腕 — 事前登録 v1 の正誤表 1

`docs/backoff-policy-performance-preregistration.md` (v1、sha256
`2f5170c99dda9dd70647a611bff798b6e54c5e29b60e872cd755e5b8515cc25c`) の **§3.2「腕の間で許す差」に
満たしえない要求が 2 つ**あった。本書はその訂正であり、v1 の bytes は 1 byte も変えない
(18 成果物が v1 の sha256 を束縛として記録しているため)。

## 0. いつ、どうやって見つけたか

**2026-09-08、18 block の測定が完走した直後、事前登録した解析を当てた 1 回目で構造検査が
拒否して判明した。**

- 拒否の逐語: `artifact-invalid: ...: source bytes differ between policy arms`
- **この時点で throughput の値は 1 つも観測していない。** 拒否は構造検査であり、推定値・CI・
  判定語のいずれも計算されていない。訂正の内容も outcome に依存しない。
- 訂正で変えるのは**成果物を受理するかどうかの identity 述語だけ**である。推定量・等価域・
```

## H1. docs/README.md 19 行 (逐語)

```
- `phase3-main-experiment.md` — 主実験の事前登録
```

## H2. docs/README.md 45〜52 行 (逐語)

```
- `backoff-policy-performance-preregistration.md` — step policy 腕の trace 無効な性能 ([T-2417]) の
  事前登録。3 腕の全 6 permutation で位置と一次持越しを均衡させる 18 block、対内 log 比の判定式と
  対称等価域、標準偏差の 2 参照級にもとづく反復数の根拠、構造違反と測定欠測を分ける規則、
  18 seed の逐語一覧、未認証であることの機械的隔離と自動撤回機構が無いことの明示、束縛の正本
- `backoff-policy-performance-preregistration-erratum-1.md` — 上記 v1 の正誤表 1。
  腕をまたぐ source bytes 一致と block をまたぐ binary identity 一定が、どちらも
  step policy の source 置換と build の非再現性ゆえに成立しえないことの実測と、
  identity 述語だけを訂正して「3 腕は互いに異なる」正の対照を足した記録。
```

## I. B-5 事前登録 docs/b5-generator-contrast-preregistration.md 68〜73 行 (逐語)

```
**D1409 の「非列挙」の条件は変更しない。** D1409 がユーザー裁定へ返した定義は D1441 (2026-09-02) で
「固定予算の下で操作的に列挙し尽くせない」へ改められている。本書はこの定義を変えず、**本書の候補集合
(1000 点、B = 10) がその定義を満たすかどうかの判定も行わない。** 有限の候補集合で固定予算の生成器を比べる
ことと、非列挙のコード片軸が実体化して旧 headline の復活条件 (D52) が満たされたと主張することは別である。
本書の対象は前者だけであり、後者は本書の主張に含めない。候補集合が完全列挙可能であること (§2) は、
D1409 の二重の壁が解けたことを意味しない。
```

## J. 凍結 verifier の source 照合 orchestrator/campaign/s1_known_axes_freeze.py 864〜871 行と 903〜918 行 (逐語)

```
_HISTORICAL_CODE_PATHS = frozenset({
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/s8a_trigger_sweep.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/backoff_sweep.py",
    "orchestrator/campaign/s6_sort_sweep.py",
    "orchestrator/campaign/p3_s4_loop_sort.py",
})
```

## J2. 同 903〜918 行

```
    resolver = source_resolver or (lambda rel: ROOT / rel)
    source_count = 0
    for source in _iter_sources(doc):
        path_rel, expected = source.get("path"), source.get("sha256")
        if not isinstance(path_rel, str) or not isinstance(expected, str):
            raise FreezeError("source path/sha256 が文字列でない")
        if known_historical and historical and path_rel in _HISTORICAL_CODE_PATHS:
            continue
        path = resolver(path_rel)
        if not path.is_file():
            raise FreezeError(f"source が存在しない: {path_rel} -> {path}")
        actual = _sha256(path)
        if actual != expected and not (known_historical and path_rel in _HISTORICAL_CODE_PATHS):
            raise FreezeError(
                f"source sha256 不一致: {path_rel} recorded={expected} actual={actual}")
        source_count += 1
```

## K. 8b oracle driver の呼び出し orchestrator/campaign/s8b_oracle_driver.py 506〜519 行 (逐語)

```
    if adapter_refusals is None:
        try:
            known_record = freeze.get("known_axes_freeze") if isinstance(freeze, Mapping) else None
            if not isinstance(known_record, Mapping):
                raise OracleDriverError("known_axes_freeze source record がない")
            known_path_text = known_record.get("path")
            if not isinstance(known_path_text, str) or not known_path_text:
                raise OracleDriverError("known_axes_freeze.path が空でない文字列でない")
            known_path = _resolve_recorded_path(known_path_text, root=root)
            s1_known_axes_freeze.verify(
                known_path, source_resolver=lambda relative: root / relative,
            )
        except Exception as exc:
            refusals.append(f"known-axes-freeze-verify: {type(exc).__name__}: {exc}")
```

## L. 段 1 実測 (親、DW-O19 一時変異 → git checkout -- で復元済み)

```
baseline: doc sha256 = e544de1969dd4df13dc42aa3d165e22b70fab2ab399dc011baa46359727bea45
[s1_known_axes_freeze.verify()] OK  held_checks=['s1-known-axes.ccbench-submodule-head-pin']
doc 末尾に 1 行追記後: doc sha256 = ac7607224729b0039ee70767e25f106ca7782abec8d82a5da29e1ffc49d54c19
[s1_known_axes_freeze.verify()] RED FreezeError: source sha256 不一致: docs/phase3-main-experiment.md recorded=e544de19… actual=ac760722…
復元後: git status --porcelain 0 行、sha256 = e544de19… (HEAD blob と一致)
(s1_measurement_freeze.verify() は baseline でも generator sha256 不一致で赤 = 本 wave と無関係の既存状態)
```

