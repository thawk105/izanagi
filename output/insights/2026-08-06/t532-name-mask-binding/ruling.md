# 段 4 裁定 + プラン v2 — [T-532]

段 3 の敵対 2 レンズはいずれも NO-GO。親が全所見を裏取りしたうえで裁定する。

## 所見の裁定

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-1 | mask 31 alias + 外側 whitespace で `assert_s1b_pairing` を迂回し、gate と ident が意味上同一の文書を受理できる | **real** (親が l.612/614 を確認、`expected` は文書自身から構築されるため自己無矛盾) | 不採用 | **scope 外** → 裁定パッケージ |
| A-2 | `name` が非 str で `__eq__` を偽装すると membership を通過する | **real** (predicate 側は exact str を要求、`EqualToCanonicalPredicate` が既存の脅威モデル) | 採用 | 内 |
| A-3 | 正例が mask 4/8/31 しか固定せず、「4/8/31 以外を拒否」する欠陥実装が全テストを通る | **real** | 採用 | 内 |
| A-4 | 完全診断文言に依存した負例は、検査を恒偽化したとき走査順の先頭で落ちて道連れ赤になる (偽 kill) | **real** (worklog 233 で同型を実害として記録済み) | 採用 | 内 |
| A-5 | emitter 名の単射性を検査しておらず、正引きの前提が恒真扱い | **real** | 採用 | 内 |
| A-6 | (B)(C) の実測から「generator は自由に編集してよい」へ一般化できない | **real** (記述の欠陥) | 採用 | 内 (記録の是正のみ、コード変更なし) |
| B-1 | brief の DW-G05 が実装と一致しない (`name` は試行台帳に記録されず、certified 選択の consumer は現 checkout に存在しない) | **real** (親が worklog 748 と driver l.1308 を確認) | 採用 | 内 (brief 是正) |
| B-2 | `_validate_schema` は本番で呼ばれるが、現行 official 受理集合は空なので現在値を一件も変えない | **real** | 採用 | 内 (記述を dormant gate へ限定) |
| B-3 | legacy consumer への波及は受理変更でなく拒否理由の順序変更だけ | **real (nit)** | 採用 | 内 (記述) |
| B-4 | holdout / ratified / pilot / report replay が name-mask 検査を迂回する | **real** | 不採用 | **scope 外** → 既裁定の [T-533]→[T-531] 受入条件へ |
| B-5 | `test_reflux_ir.py` の `test_frozen_gate_predicates_match_six_records_with_three_distinct_masks` が既に同性質を照合していた | **real** (親が逐語を確認) | 採用 | 内 (brief の既存被覆記述を是正) |

## 是正した brief 記述

### DW-G05 成果物影響 (B-1 / B-2 を反映して差し替え)

入れない場合、`entries.<workload>.system_gate.name` が実際に materialize される述語と食い違ったまま
受理される。D50 が選んだ `system_gate` の意図 (`g_rl` = readvali-locked だけを gate する) と、
実際にビルドされる binary・`src_token`・`variant_id`・S-1 直接比較の throughput が乖離し、
その乖離が inner entry の `entry_sha256` と selector の `binding_entry_sha256` に束縛される。
**ただし現行 official の受理集合は空 (`docs/phase3.md`) で、`name` は試行台帳にも判定 key にも
現れない (台帳は `configuration_id`、judge は `winner_configuration_id`)。**
したがって本検査は現在値を一件も変えず、[T-531] の世代移行で新世代 artifact を発行する時点で
実効化する **dormant gate** である。「現時点で誤 certification 経路を閉じた」とは書かない。

### 既存被覆 (B-5 を反映)

production の同性質検査は `s1_verify_extime_calibration.validated_target` の read-heavy 1 record のみ。
**test 層には既に `test_reflux_ir.test_frozen_gate_predicates_match_six_records_with_three_distinct_masks`
があり、現行 6 record の name→mask→述語を golden として照合している。** ただしこれは
`{"g_rt": 4, "g_rl": 8, "ident_all": 31}` をハードコードした test 専用 golden で、production gate ではなく、
新しい name が現れれば手で更新するまで機能しない。純増は **production gate の新設**である。

### 段 1 実測 (B) の限定 (A-6 を反映)

実走したのは次の 8 file である — `test_s1_known_axes_freeze.py`、`test_frozen_artifacts.py`、
`test_t080_freeze_migration.py`、`test_s8b_oracle_driver.py`、`test_s1_measurement_freeze.py`、
`test_reflux_ir.py`、`test_trigger_gate_binding.py`、`test_s8b_holdout_freeze.py`。
command は `python3 tools/run_tests.py <8 file> -q` (Pegasus 計算ノードへ dispatch、request 891654.nqsv)。
結論は「**この 8 file の範囲では generator の 1 行編集が追加の赤を出さない**」に限定する。
legacy `verify_document` は live generator sha を再計算して照合するため、その面が緑だとは主張しない。

## プラン v2 (v1 からの差分のみ)

v1 の骨格 (述語→mask→emitter 正引き、`trigger_gate_binding` に mask 導出、`s1_known_axes_freeze` の
生成層と schema 層の 2 点で検査) は維持する。次の 5 点を加える。

1. **(A-5)** `s1_known_axes_freeze` に **mask 0〜31 の name→mask index** を module 読み込み時に構築し、
   `s8a_trigger_sweep.subset_name` が同じ名を 2 つの mask へ与えたら **fail-closed** で停止する。
   `ident_all` は mask 31 の明示 alias として index へ加え、既存 name と衝突したら同じく停止する。
   照合はこの index を使う (逆文法パーサは作らない)。
2. **(A-2)** name の型契約を `type(name) is str` に固定し、membership の前に検査する。
   非 str・`None`・欠落・bytes・`str` subclass・`__eq__` 偽装をすべて拒否する。
   予測される受理集合の変化は「現行 6 record は plain `str` なので影響なし」。
3. **(A-4)** 受理集合を検査する負例は **例外型 (`FreezeError`) と安定 reason 断片のみ**を assert し、
   workload / configuration / mask / 期待名を含む完全診断文言に依存しない。
   完全診断は helper 直呼びの **診断専用テスト 1 本**へ分離し、変異 kill には数えない。
   `expected_names` は集合でなく **mask 昇順の固定 tuple** とする。
4. **(A-3)** helper を通す **mask 0〜31 の正例**を追加する。mask 31 は通常名と `ident_all` の双方、
   外側 whitespace 付き述語も含める。
5. **(B-3)** consumer への波及は「診断到達 (diagnostic reach)」と記述し、実効受理変更として数えない。

### gate の禁止 (署名) と通る正例

```python
def _require_trigger_name_mask_binding(
        name: object, predicate: object, *,
        workload: str, configuration: str) -> None:
    """禁止: type(name) is not str、または name が predicate の mask に束縛された
    正準名でないこと。前者・後者とも FreezeError を送出する。"""
```

通る正例 (これが赤になったら過剰拒否):

```python
predicate = s8a_trigger_sweep.predicate_for(("readvali-locked",))   # mask 8
_require_trigger_name_mask_binding(
    "g_rl", predicate, workload="balanced", configuration="system_gate")   # -> None
_require_trigger_name_mask_binding(
    "ident_all", s8a_trigger_sweep.predicate_for(T.GATEABLE_REASONS),
    workload="balanced", configuration="ident_all")                        # -> None
```

## 変異事前登録 (DW-M01)

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無いこと」を確認済み。

| ID | 変異位置 | 変異内容 | 期待 kill (赤になる node) | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | `_require_trigger_name_mask_binding` の型検査 | `type(name) is str` の検査を削除 | 比較偽装 name の負例 1 本 | membership は `__eq__` を使うため前段で落ちない。predicate 側検査は name に触れない |
| M2 | 同 helper の本体 | 先頭に `return` を挿入し恒真化 | 生成層負例 + schema 層負例 (計 2 node) | 述語は正準・flags 維持・main/remeasure 一致にするので既存の型/membership/equality では落ちない |
| M3 | `_validate_schema` の呼出し | 呼出し行を削除 | schema 層負例のみ | 生成層は同経路を通らない |
| M4 | `_trigger_entries` の呼出し | 呼出し行を削除 | 生成層負例のみ | schema 層は同経路を通らない |
| M5 | mask 31 の `ident_all` alias | alias 登録を削除 | 現行 6 record の正例 (過剰拒否検出) | `ident_all` を含む record は 3 件あり、他層は名を見ない |
| M6 | name→mask index の構築範囲 | `range(32)` を `(4, 8, 31)` に狭める | mask 0〜31 全点の正例 | 現行 6 record の正例だけでは生存する (A-3 の検出力そのもの) |
| M7 | `mask_for_canonical_predicate` の bit 順 | mask 列挙を逆順にする | 32 mask 復元テスト | binding 単体テストで完結 |

`M2`〜`M4` は 3 本まとめて「検査を消す」族で、M2 が両層、M3/M4 が片層の帰属を分離する。
非正準述語の負例は既存 membership が先に落とすため、**新検査の kill には数えない**。
T-080 の raw artifact 直接改竄も先行 hash 拒否が覆うため kill に数えず、`_validate_schema` 直呼びを根拠にする。

## 裁定パッケージ (scope 外の real 所見 — ユーザーへ返す)

### RP-1 (A-1 由来) — `assert_s1b_pairing` が述語を生文字列で比較するため、mask 31 alias と外側 whitespace で gate/ident の意味上の同一を受理できる

`s1_known_axes_freeze.py` l.612 は `gate.gate_predicate == ident.gate_predicate` を生文字列で比較し、
l.614 の期待表は文書自身から構築されるため自己無矛盾になる。両 record を `name="ident_all"` / mask 31 とし、
一方の述語にだけ外側空白を付けると、pairing の「gate と ident は別物」という要求を迂回できる。
S-1B の gate on/off 対比が同一構成同士の比較になりうる。
**本 wave では実装しない** — 閉じるには `assert_s1b_pairing` の比較意味論 (別性質: distinctness) を
変える必要があり、その consumer (`t080._verify_known_pairing`、measurement freeze の pairing 複製) へ
波及する。穴は本 wave 以前から存在し、本 wave が作るものではない。
**推奨**: 比較を復元 mask 同士に変え、gate と ident の mask 同一を拒否する。

### RP-2 (B-4 由来) — holdout / ratified / pilot / report replay が name-mask 束縛を迂回する

holdout 凍結は known 文書を直接読んで entry を複製し、検証も複製との equality だけである
(`s8b_holdout_freeze.py` l.487/524/809)。ratified と report は source / entry hash しか見ない。
非正準 producer 由来の known 文書を与えると、`holdouts.<id>.variant_binding.entries.system_gate` の
name と述語が食い違ったまま、selector basis hash・`binding_entry_sha256`・floor/oracle manifest の
`entry_sha256`・pilot 実測値がその文書へ束縛される。
**本 wave では実装しない** — これは既裁定の [T-533]「holdout 凍結の known 直接読み」と同一面であり、
[T-531] の世代移行統合へ同梱すると裁定済みである。
**推奨**: [T-531] の受入条件へ「canonical membership だけでなく [T-532] の name-mask 束縛も
holdout / ratified 境界で必須」と明記する。

## 分割方針

編集面は `trigger_gate_binding.py` + `s1_known_axes_freeze.py` + test 2 file で素集合にならないため
**単一実装単位**。Codex `role=author`、`reasoning=high`、`sandbox=workspace-write`。
