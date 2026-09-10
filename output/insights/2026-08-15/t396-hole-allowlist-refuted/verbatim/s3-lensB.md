静的レビュー結論: 現行プランは `D344` により `DW-STOP`。実装差分は作れません。pytest・計測は未実行です。

### 所見 1

**所見**

sort 用 compositional grammar は、D344 が却下した typed IR / AST allowlist と実質同じ選択肢である。段 2 プランの「D344 を supersede する」は、親が単独で決められない。

**根拠**

`docs/decisions.md:15215-15218` は文法判定を compiler に委ね、構造検査を単一 `sort(...)` 文までに限定する。`docs/decisions.md:15245-15249` は「純粋な field 読取りと比較演算に制限する typed IR / AST allowlist」を、合成を事前選択へ変えるとして却下し、ユーザー裁定へ返している。

一方、`s2-plan.md:111-158` は field、型、演算子、call、assignment、dereference 等を閉じた grammar で制限し、`s2-plan.md:386` は D344 の却下部分を supersede しようとしている。

**深刻度**

致命的。ユーザー裁定待ち。

**提案**

現 wave は実装差分ゼロで裁定パッケージを返す。grammar を採用するなら、D344 の選択肢を明示的に覆すユーザー再裁定後に、プランと成果物を再作成する。

### 所見 2

**所見**

T-409 の裁定を「trigger 軸に限定し、sort 軸には及ばない」と読む点は正しい。ただし、それは sort grammar の実装許可ではない。

**根拠**

`s4-adjudication.md:98-130` の択一は trigger marker、trigger artifact、数値 literal、trigger / 全軸、freeze 回帰テストで構成される。裁定控えも `rulings-inbox/2026-08-04-t409-implementation-superseded.md:9-25` で 32 正準 trigger 述語への移行を述べ、`:122-128` で T-409 の実装破棄と T-472/T-473/T-474 への分割を確定している。

sort comparator の typed grammar という選択肢集合は T-409 の択一集合に存在せず、別途 D344 で却下されている。

**深刻度**

高。裁定の取り違え自体はないが、許可根拠として使うと停止条件違反になる。

**提案**

T-409 は sort 側の blocker ではないと記録し、D344 を独立した未裁定 blocker として扱う。

### 所見 3

**所見**

親 brief の「sort positive controls 16 件をすべて grammar で通す」は stale であり、段 2 プランと衝突する。

**根拠**

`s1-brief.md:70-76` は sort 軸 16 件を全て受理するよう要求する。しかし `positive-controls.txt:9-39` の内訳は、実 C++ implementation 15 件と `SORT_VARIANT=0` の説明文 1 件である。`s2-plan.md:282-300` も、説明文を parser に渡さず「15 implementation + stock materialization」に分離している。

**深刻度**

高。説明文を grammar の正例にすると、非 C++ を gate-pass させる。

**提案**

実装する場合は grammar positive 15 件と stock system positive 1 件を別 interface として固定する。現 wave ではこの訂正も裁定パッケージに含める。

### 所見 4

**所見**

「`pro_set_.pop_back()` は role 契約違反なので、grammar は契約を狭めない」という主張は、その一例については正しいが、提案全体には当たらない。

**根拠**

role は `coder-v4-autonomous-sort.md:60-75` で複数行の raw comparator 全体を出力対象にし、`:78-89` で利用可能 member と副作用 call 禁止を prose で定める。従って `pop_back()` が禁止対象という局所判断は妥当である。

しかし D127 は `docs/decisions.md:6235-6239` で、raw comparator を role 契約上許す producer に対し consumer だけ boolean AST/DSL で狭めることを明示的に退けている。プラン自身も `s2-plan.md:97-107` で、任意 API call の副作用なしを C++ 意味解析なしには判定できないと認めている。

`.claude/agents/` の変更承認が不要という意味にもならない。承認規律は `docs/decisions.md:1366-1370,1964-1968` にある。

**深刻度**

高。

**提案**

grammar を「既存契約の機械執行」と呼ばず、producer/consumer 契約の変更としてユーザーへ返す。role を変更するなら明示承認、adapter、manifest、review ledger の同時更新を要求する。

### 所見 5

**所見**

先行 wave の D96 衝突 refuted 判定は、「機械検査を一切新設できない」という読みを退ける限りでは妥当。しかし、本 plan の grammar を無条件に許可する根拠にはならない。

**根拠**

D96 は `docs/decisions.md:4271-4292` で、raw selector consumer の一般 AST 固定を却下しつつ、受理集合を変える改修には新 D と境界テストを要求する。後続 D97 (`docs/decisions.md:4300-4303`) も D96 の手続を満たして個別機械 gate を追加しているため、D96 は全 domain recognizer の永久禁止ではない。

一方、現在の plan は `s2-plan.md:359-387` で新 D と境界テストを予定しているものの、同じ箇所で D344 の却下案を AI 側の新 D で supersede しようとしている。

**深刻度**

高。

**提案**

D96 の手続は維持する。ユーザー裁定後に、新 D・境界テスト・却下案を同一変更単位に置く。D344 を覆す裁定なしに先へ進めない。

### 所見 6

**所見**

LLM auditor は意味 gate ではない。指定された二文攻撃について autonomous 経路の純増検出力はゼロだが、別の grammar 違反と直接 materializer 経路には条件付きの純増がある。

**根拠**

`auditor_gate.py:198-203` は auditor の `pass` 時に元の machine-pass 結果を返すだけで、`:219-231` も deny-only veto である。`coder_effect_gate.py:58-105` は process、file、network、sleep、escape-hatch の deny table で、`pro_set_` と `pop_back` はない。

しかし `sort_swo_oracle.py:486-548` は hole を単一の非修飾 `sort(...)` 文に限定する。従って `pro_set_.pop_back(); sort(...)` と `sort(...); pro_set_.pop_back();` は既存 oracle が構造拒否する。さらに `p3_s4_loop_sort.py:187-196` は oracle `UNAVAILABLE` を例外化して fail-closed にする。

反面、compiler が受理する generic lambda 等は既存 oracle を通り得る。D344 自身も `docs/decisions.md:15236-15239` で、既存 fixture の generic lambda を compiler は受理すると述べている。

**深刻度**

中から高。効果の主張が過大。

**提案**

純増を次の三つに分けて ablation する。

- 指定二文攻撃: autonomous 経路では純増なし。
- 既存 compiler/oracle が受理する role 外構文: grammar による純増候補。
- 直接 `pipeline` / `buildcache` 経路: sort-specific gate が無いため、最も実質的な純増候補。

「hole を閉じる」とは書かず、どの経路の受理集合を変えるかを限定する。

### 所見 7

**所見**

段 2 が指摘した materialize 済み source の直接経路は実在し、`DW-G05` の一行は書ける。したがって residual は nit ではない。ただし final certified selection と呼ぶのは過大で、現 checkout にはその consumer がない。

**根拠**

`build_admission.py:627,743-754` は trigger predicate だけを再検査する。`pipeline.py:743-778` は source evidence と admission を確認しても sort を見ず、`:851-897` で build へ進む。`buildcache.py:1323-1326,1547-1554` も evidence、allowlist、commit を確認するだけで sort oracle を呼ばない。

その後 `pipeline.py:1183-1257` は verify 通過後に `STAGE_COMMIT` と `fitness_tps` を記録する。`s6_sort_sweep.py:443-459,479-508` は commit の存在を `certified` として `median_tps` 集計へ入れる。なお `layer3_report.py:544-548` は certified-selection consumer が未配線だと明記する。

**深刻度**

高。

**提案**

DW-G05 の一行は次のとおり。

> 塞がなければ、sort-specific oracle を通っていない workload 縮小 source が `pipeline.evaluate()` / `buildcache` から build・verify・bench へ進み、`STAGE_COMMIT.fitness_tps`、s6 の `certified/median_tps`、WAL/provenance の通常候補記録になる（実走は未実施）。

D344 に抵触しない候補は、既存 raw compiler/SWO oracle の receipt を直接 materializer が要求する設計である。

### 所見 8

**所見**

scope 外宣言は三つとも同じ扱いにはできない。sandbox 除外は妥当だが、verifier の予定操作数検査は本丸に近く、T-473 は主張境界との依存を明記すべきである。

**根拠**

`orchestrator/verifier/model.py:37-48` の `Txn` は実際の reads/writes しか持たず、`:132-148` の integrity も expected commit 数は持つが、予定操作数との照合を持たない。grammar は入口表現を狭めるだけで、この不変条件を代替しない。

D127 は `docs/decisions.md:6235-6239` で rootless sandbox backend 不在を理由に sandbox を別 wave としているため、今回の除外は妥当である。D344 も `:15227-15230` で raw C++ comparator の synthesisability を研究上の範囲としている。

また `s2-plan.md:238-250` は sort grammar ID を共通 build admission policy に入れ、sort を使わない campaign も identity/cache rotation の対象にする。これは `build_admission.py:458-477` の共通 policy と衝突し、scope と費用を全軸へ広げる。

**深刻度**

高。

**提案**

sandbox は scope 外のままとする。予定操作数は別 task として優先度を上げ、grammar をそれの代替と主張しない。T-473 は実装を分離してよいが、synthesisability と finite-policy-selection の材料主張を変更するなら報告境界を同時に更新する。policy ID は軸別に分けるか、全 campaign の cold invalidate を新 D で明記する。

### 所見 9

**所見**

`DW-M01` の単独理由性を満たさない変異が、plan の一覧に残っている。

**根拠**

`docs/dev-wave/mutation.md:5-7` は、前後に同じ拒否層がなく、無効化時の赤理由が一つであることを要求する。`docs/failures.md:556-571` の F28 も同じ多層防御の失敗を記録している。

単独変異の帰属が曖昧になる例は次のとおり。

- `pro_set_.pop_back(); sort(...)` の SWO grammar gate 削除。既存の `sort_swo_oracle.py:486-548` が先に拒否する。
- `#include`、コメント、行末 backslash、`system`、無条件 loop の拒否。DiffQuarantine または `coder_effect_gate.py:58-115` が先に拒否する。
- 非 SWO comparator。grammar は通っても SWO oracle が拒否するため、grammar の kill にはならない。
- oracle `UNAVAILABLE` の fail-open 変異。入力が grammar 不適合だと grammar 側の拒否に隠れる。
- `pipeline` / `buildcache` の再検査 call 削除。upstream gate を経由する fixture では、削除しても前段で赤になる。

逆に、compiler/SWO が受理する generic lambda や `a.key_[0]` を grammar-only negative にすれば、grammar の単独理由を作れる可能性がある。

**深刻度**

高。変異結果を誤帰属する。

**提案**

段 4 では、各変異に「入力・前段の判定・期待 reason・下流呼出し回数 0」を記録する。前段にも拒否される入力は kill ではなく diagnostic sensitivity とし、直接 materializer 用には upstream を全て通る専用 fixture を作る。

### 所見 10

**所見**

親の三度の誤りは新型ではなく、主に F73 の「防壁の射程誤認」。軸限定の gate を全体の gate 不在と取り違えている。

**根拠**

`docs/failures.md:2337-2357` の F73 は、実在する複数 module の機械強制を一部または全体へ誤一般化した型である。今回も、sort-specific syntax contract の不在、`pro_set_` の deny table 不在、oracle unavailable の扱いを、SWO oracle や共通 fail-closed を含む全関所の不在へ拡張している。

`docs/failures.md:7073-7092` の F287 とも「不在を全件・全経路で立証しない」という近縁性がある。ただし今回、検索出力を切ったことまでは確認できないため F287そのものとは断定しない。F21 は live wiring 未検証の近縁だが、今回の中心は wiring 不在ではなく射程誤認である。

**深刻度**

高。次 wave の前提実測を汚染する。

**提案**

段 1 で「gate inventory」を一枚作る。入口から下流への順方向表と、各 gate symbol から caller への逆方向表に、file:line、拒否条件、UNAVAILABLE 挙動、直接 caller、既存 test を必ず記録し、その表なしに「gate は無い」と書かない。新型 failure tag は不要。

## 総括

- sort grammar は D344 の却下案と選択肢集合が一致し、現 wave は `DW-STOP`。  
- T-409 は trigger 限定だが、sort への許可裁定ではない。  
- 直接 materializer 経路と verifier の予定操作数欠落は実在し、grammar とは別の優先課題である。