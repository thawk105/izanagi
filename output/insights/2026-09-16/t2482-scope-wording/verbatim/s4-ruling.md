# 段 4 裁定 — [T-2482] (親、2026-09-16)

基準: wave branch を local main a1b40608cbbdefb62846e6224313d12c2bce9dae へ ff-only 済み (全史 provenance 監査 10552 件・新規違反なし)。
段 4 直前の再走査: wave 開始後に main へ入った D2066〜D2068 ([T-2125]・[T-2559]) は文言・閉包に触れない。[T-2125] の artifact_admission.py 差分は import・policy 照合・分類だけで A1/A2 と重ならない。
新 base の閉包再測: a1b40608c = 収載 63 / 発見 162 / 未収載 99。発見集合は e667c8c13 と完全一致 (diff 空)。verifier 3 path・s8b_oracle_report.py は発見集合外、verify_fanout_worker.py への import edge 0 本 (出力 closure-head-a1b40608c.json)。

## 所見の裁定

| # | 出所 | 内容 | 裁定 | 採否 |
|---|---|---|---|---|
| 1 | A-1 / B-1 (must-fix)、親追加実測 | 「subprocess … を含む非 import 委譲は本 map の外」の無条件維持は、収載済みの `verify_fanout_worker.py` (pipeline.py:836 の subprocess 起動先) と矛盾 | real | 採用。除外句を「収載 path の source bytes を除く」に限定。worker の束縛を ssh・interpreter・binary を含む実行全体へ広げない |
| 2 | plan / A-4 / B-2 (should-fix) | brief の「E1 値不変」は記録済み map から再導出する値に限る。artifact_admission.py は収載 path なので新規 lock の E1 は変わる | real | 採用 (brief 訂正、コード変更なし)。不変条件を「E1 preimage 形式と記録済み map からの再導出値は不変」に改める |
| 3 | plan | 62→63 は被覆記述の追随であり「弱める方向だけ」ではない | real | 採用 (記録上の訂正) |
| 4 | A-2 (should-fix) | 受理に効く経路は scope の直接照合だけではない。artifact_admission.py 全 bytes の sha256 が admission receipt の validator.sha256 に入り completeness が現行値と照合する | real (親の一般化の反証) | 記録のみ。**既裁定 D170 (d) が同じ性質を限界として記録済み**で、本 wave に固有でない (同日 [T-2125] も同 file を編集)。コード変更・互換機構は scope 外 (ユーザー指示) |
| 5 | A-3 (should-fix) | B-4 projection hash が当該 file bytes を束縛し、保存 receipt と現行値を照合する | real (親の「bytes pin なし」は事前登録欄に限定すべき) | 記録のみ。事前登録本文が「記入後に閉包 member の bytes が変われば 3 値は同時に無効…書き直す」と既に定める。欄は未記入。scope 外 |
| 6 | A-5 (nit) | 歴史 exact-62 と現行 63 の文言同一は判定上の曖昧さを生まない (型と tuple で分岐) | real | 採用。親 brief の DW-G05 の後半は「文面上の区別」に限定する |
| 7 | B-3 (nit) | 日付の係り先を収載数と分ける | real | 採用 (文言 v2 に反映) |
| 8 | B-4 (nit) | P2 は発行器へ言及せず集合の定義だけでよい | real | 採用。発行器名は snapshot 依存 (autonomous_trial_completeness.py は 09-09 以降に集合内へ入った) なので書かない |
| 9 | plan / B | P3 の 24/36/2 内訳は現行保証文から落とす | real | 採用。親 (P3) を撤回 |
| 10 | A 経路表 | docs/paper-story/figures の provenance JSON 3 本にも scope が残る | real | 記録のみ。現行文言 (curated exact 62) を含まない (repo 全体の逐語 grep で hit なし)。触らない |

(P1) 採用・(P2) 定義句として採用・(P3) 撤回・(P4) 維持。

## plan v2 (実装子への指示の正本)

変更は 3 file・4 アンカーだけ。

A1 `orchestrator/campaign/artifact_admission.py:76-80` `CAMPAIGN_VERIFIER_EPOCH_SCOPE` の連結後の値を、次の逐語へ:

```
enforcement source closure (curated exact 63 path; source-import 推移閉包ではない; 発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、2026-09-16 (a1b40608c) の実測では 162 module、うち収載 63)
```

A2 同 `:81-86` `CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` の連結後の値を、次の逐語へ:

```
同実測の発見集合の未収載 99 module、同発見集合に入らない module、orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、package 外の orchestrator/verify.py、および収載 path の source bytes を除く data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり、完全性を主張しない
```

A3 `orchestrator/tests/test_artifact_admission.py:1371-1381` (`test_real_e0_is_rejected_only_by_certified_epoch_gate`) の `identity_scope` / `excluded_scope` 期待 literal を A1/A2 と同じ逐語の**独立 literal** へ。定数参照へ置換しない。

A4 `orchestrator/tests/test_s1_9pair_figure_provenance.py:74-89` `CURRENT_E0_EPOCH` の 2 field を同じ逐語の独立 literal へ。E0・state・reason_code は不変。

触らない: `PRE_T733_*`、`FROZEN_E0_EPOCH`、`FROZEN_ADMISSION_VALIDATOR_SHA256`、docstring、`CONTRACT_LOADER_RELATIVE_PATHS`、受理述語・`__post_init__` の一致検査、E1 導出、記録済み成果物・insight・docs/paper-story。

D1651 要素照合: path 数 (63) / 推移閉包でない / 未収載数 (99) / 非 import 委譲の除外 (収載 path の source bytes だけ除く) / 完全性非主張 — 全要素残る。
D1884 強さ: 62→63 は既収載への追随。発見集合の定義句・日付・「発見集合に入らない module」・未収載 69→99 は限定を強める。source bytes の除外限定は収載済み 1 本の事実記述で、実行全体の保証へ広げない。旧文言より強い保証を読ませる句はない。

## 規模上限

production 差分は 2 定数の文字列だけ (新規 import・関数・分岐なし)。test 差分は literal 2 か所だけ。これを超える差分は差し戻す。

## 変異の事前登録 (DW-M01)

本 wave の差分は説明文字列だけで受理集合を変えない。DW-M03/M08 に従い、以下は **kill ではなく diagnostic sensitivity pin** として別枠記録する。期待 node は完全集合で、初回は probe (全件 SURVIVED 登録で観測 node を集める) とし、確定後に本走で完全一致を見る。

| ID | 位置 | 単独変異 | 期待する赤 (probe で node を確定) |
|---|---|---|---|
| M1 | A1 | `curated exact 63 path` → `curated exact 62 path` | test_artifact_admission.py::test_real_e0_is_rejected_only_by_certified_epoch_gate と test_s1_9pair_figure_provenance.py の CURRENT_E0_EPOCH 照合を通る test |
| M2 | A1 | `; source-import 推移閉包ではない` を削除 | 同上 |
| M3 | A2 | `未収載 99 module` → `未収載 69 module` | 同上 |
| M4 | A2 | `収載 path の source bytes を除く ` を削除 (must-fix 句) | 同上 |
| M5 | A2 | `、完全性を主張しない` を削除 | 同上 |
| M6 | A3 | test 側だけ `162 module` → `161 module` | test_artifact_admission.py::test_real_e0_is_rejected_only_by_certified_epoch_gate だけ |
| M7 | A4 | test 側だけ excluded_scope の `同発見集合に入らない module、` を削除 | test_s1_9pair_figure_provenance.py の CURRENT_E0_EPOCH 照合を通る test だけ |

単一理由性: 各変異の赤は literal と定数の不一致だけで、他層 (受理述語・E1) は同じ入力を拒否しない。production 変異は module import 前の file 置換で行う (monkeypatch しない)。

## 焦点走・受入

焦点走 (commit 後): orchestrator/tests/test_artifact_admission.py、orchestrator/tests/test_s8b_oracle_report.py、orchestrator/tests/test_s1_9pair_figure_provenance.py (定数参照と literal を持つ consumer test、grep で確定)。
受入は `tools/dev_wave_wait.py acceptance` の既定経路で最終 tip に 1 回。

## 記録 (段 7)

- decisions fragment: D1896 をユーザー直接指示 (2026-09-16) が上書きし単独で文言を直したこと、日付付き snapshot の採用理由、発見集合が収載不変でも動く新事実。
- worklog fragment、insight (実測・probe hash・子の逐語・変異台帳)。
- 限界: D170 (d) と B-4 事前登録本文が既に定める file bytes 束縛は本変更でも発火する (本 wave 固有でない)。

## 追補 1 (段 6、2026-09-16) — レビュー B should-fix を採用し A2 の逐語を改める

レビュー A: 所見ゼロ (逐語一致・受理述語不変・歴史値分離を確認)。レビュー B: must-fix 0 / should-fix 1。
should-fix の内容: A2 の「収載 path の source bytes を除く data/schema、生成物、subprocess、…」は
「除く」が直後の `data/schema` だけを修飾すると読む余地があり、例外の係り先が一意でない。
裁定: real、採用。意味を変えず、例外を「本 map の外であり」の直後の括弧に置く。保証は広げない
(収載 path の source bytes が map の内であることは tuple の定義そのもの)。

A2 (v3、実装子への逐語):

```
同実測の発見集合の未収載 99 module、同発見集合に入らない module、orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり (収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない
```

A1 は v2 のまま。A3・A4 の excluded_scope literal は A2 v3 へ追随。
変異 M4 の置換対象を ` (収載 path の source bytes は委譲先であっても本 map の内)` の削除へ改める (probe 未投入のため spec を更新)。

## 追補 2 (段 6 焦点再レビュー後、2026-09-16) — M4 の erratum と補走

焦点再レビューの新規 should-fix: probe / final の M4 は追補 1 の登録 (先頭空白 + 括弧句 ` (収載 path の source bytes は委譲先であっても本 map の内)` だけを削除) と異なり、括弧句 + 読点を削除して先頭空白を残す形で走った (連結結果 `…本 map の外であり 完全性を主張しない`)。
原因: fix 子が文字列 literal を `外であり "` / `"(収載 …` の 2 行に分けたため、登録どおりの anchor が source 上で行境界を跨ぎ、`--plan-only` が anchor count=0 で止まった。親が 1 行に閉じた anchor へ再照準した。
裁定: real、採用。意味 (source bytes の例外句を落とす) と赤の理由 (literal 不一致) は同じだが、登録どおりの単独変異の実測ではない。final 走は完走させたうえで、行境界を跨ぐ anchor (old = `外であり "\n    "(収載 … 本 map の内)、` → new = `外であり"\n    "、`) で **M4x を補走**し、連結結果を `…本 map の外であり、完全性を主張しない` にする。期待 node は M3/M5 と同じ 4 node (probe で観測済みの集合) を KILLED 期待で登録する。probe / final の M4 は erratum として台帳に残す (DW-M02)。
