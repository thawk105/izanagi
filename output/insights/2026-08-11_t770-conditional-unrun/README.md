# 「条件付き未実走」を依存物不在から切り離した — 実測と変異台帳

wave: `dev-wave-t770-conditional-unrun` / 実装 commit `4f2c72cb`。
裁定は [T-770] R1 (b) + R2 (a) (worklog エントリ 403、正本パッケージは
`output/insights/2026-08-11_known-red-exceptions/package.md`)。

`authority: none` / `default_effect: no-state-change`。可変状態の正本は worklog 末尾と現行 phase doc。

## 何を変えたか

受入全走の 20 skipped のうち 4 件は「template patch 未適用」で恒久 skip する。これを
`orchestrator/tests/README.md` は「依存物不在」に数えていたが、実体は repo 内で満たせる前提で
あり、census を読む側が「外部依存だから仕方ない」と誤読する面だった。

裁定に従い patch 窓は開けず、分類だけを正した。**受入 suite の挙動・受理集合・skip 件数 (20) は
変えていない。production コードは 1 byte も変えていない。**

- `skiputil` に `CONDITIONAL_UNRUN` と `skip_conditional_unrun()` を足し、依存物不在 (`skip`) と
  条件付き未実走を別経路にした。理由文の先頭に分類語、末尾に正本 doc への pointer が必ず載る。
- 対象 4 node を新 helper へ差し替えた。skip 条件式は 4 本とも逐語で不変。
- テスト README に「条件付き未実走 (repo 内で満たせるが開けていない)」節を立てた。
- `test_skip_classification.py` が分類の結線を機械で固定する。

## 段 1 の前提実測 (裁定の前提が今も成立するかの確認)

wave 前 HEAD `0c0fbf25` のこの worktree、計算ノード request `901500.nqsv`、
`python3 tools/run_tests.py --force-dispatch <4 node> -rs -q`。
**4 skipped / 2.75 秒 / rc=0。** 理由文は 4 本とも「template patch 未適用 …」であり、
裁定パッケージの事実 1 は成立している。`test_source_digest_fixed_variant_distinct` に
`_require_g13()` が無いこと (事実 4) も静的に確認した。窓を開けないので guard は足していない。

## 分類変更後の skip 理由文 (実測)

計算ノード request `901504.nqsv`、焦点走。4 node の理由文は次の形になった。

```
条件付き未実走: template patch 未適用: Options.cmake に BACKOFF_FIXED 既定なし
  — repo 内の前提で満たせるが受入 suite では窓を開けない — 分類と理由は `orchestrator/tests/README.md`
```

機構名「template patch 未適用」は 4 本とも残してある。worklog・failures・裁定パッケージの
census はすべてこの語でこの 4 件を数えており、受入出力からこの語が消えると census 側の
grep が 1 件も当たらなくなるためである (段 6 の親所見、fix 1 巡で closed)。

## 焦点走で出た赤 2 件 — 差分に帰属しない

同じ request `901504.nqsv` で `test_real_repo_serialization.py` の 2 node が
`ModuleNotFoundError: No module named 'tests'` で赤になった。

- `test_ratified_memo_has_a_real_resolution_payer`
- `test_protocol_builder_repo_tree_guard_is_wired_to_real_root`

**機序は選択走の import path である (DW-O18)。** 両 node は `from tests import ...` を使い、
これは `orchestrator/` が `sys.path` に載っていないと解決しない。載せているのは
`test_reflux_ir.py:122` の module import 時の副作用だけで、焦点走ではそのファイルを
収集していない。本 wave の差分は `from tests import` 経路に到達できない。受入全走では
`test_reflux_ir.py` が収集されるため緑になる (下記)。

この隠れ結合自体は実在する所見だが本 wave の scope 外であり、修正せず起票した。

## 変異 matrix

`tools/mutation_harness.py`、runner-mode=dispatch、固定 HEAD `4f2c72cb`。
対象コマンドは
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_skip_classification.py orchestrator/tests/test_hooks.py -q -rf`。
spec = `mutation-spec.json` (生成器が anchor の一意性を assert する)、台帳 = `mutation-ledger.json`。

| ID | 変異 | 期待 | 実測 |
|---|---|---|---|
| M1 | `test_hooks.py` の hook node を wave 前の素の `skip(...)` 逐語へ巻き戻す | KILLED / 1 node | KILLED / 同一 1 node |
| M2 | `test_campaign.py` の Options 既定 node を同じく wave 前の逐語へ巻き戻す | KILLED / 1 node | KILLED / 同一 1 node |
| M3 | helper が分類語と pointer を付けずに素の `skip` へ委譲する形へ落とす | KILLED / 1 node | KILLED / 同一 1 node |
| M4 | README の分類節から nodeid を 1 件削る | KILLED / 1 node | KILLED / 同一 1 node |

baseline PASSED。**SURVIVED / TIMEOUT / MISMATCH / PARSE_ERROR はゼロ (4/4 KILLED)。**

M1 / M2 は「wave 前の実コードの形」をそのまま変異として登録したものである。分類が素の `skip` へ
戻る退行が、新設検査 1 本だけで撃たれることの実証になる。M3 は helper 側の骨抜き、M4 は README
census 側の欠落を撃つ。3 種の赤理由はすべて単一 node へ落ちる。

**runner の範囲は 2 ファイルに絞ってある** (`test_skip_classification.py` と `test_hooks.py`)。
M2 が変異させる `test_campaign.py` は範囲外だが、新設検査は対象ファイルを収集ではなく path から
AST で読むため期待 node は範囲内で成立する。全走で撃つ設計にしていないことをここに明記する。

### 新旧両走 (`DW-M08`) を走らせていない理由

M1 / M2 の「旧側」= wave 前 HEAD は、**変異後の状態そのもの**である (4 node が素の `skip` を呼ぶ)。
その状態で段 1 の実測が 4 skipped / rc=0 の緑だったこと、および直前 land の受入全走が
rc=0 だったことが、「旧テストはこの退行を検出しなかった」という差分の直接の証拠になる。
同じ spec を旧 HEAD へ当てても新設検査も helper も存在せず、走行そのものが成立しない。

## 親検査

- `python3 tools/check_docs.py` rc=0
- `python3 tools/check_ai_provenance.py` (全史) rc=0 — 実装 commit 後と main 取り込み後の 2 回
- `python3 tools/spool_fold.py --dry-run` rc=0

## 受入全走

2 走した。どちらも緑で、赤は 1 件も出ていない。受入形のまま (`python3 tools/run_tests.py` を
裸で投入) 、lease は 1 走目から通して保持している。

| 走 | tip | 実測 |
|---|---|---|
| 1 | `d256c501` | rc=0 / 8,487 passed / 20 skipped / 564.30 秒 |
| 2 (採用) | `2f680772` | rc=0 / 8,487 passed / 20 skipped / 498.68 秒 |

1 走目の走行中に local main が 5 commit 進み、land の ff-only が成立しなくなったため 2 走目を
走らせた (runbook §7.3 が明記する残余 race)。

**skip 件数は両走とも 20 で、wave 前の診断走行と同じである。** 本 wave は分類だけを変えて
skip を増やしても減らしてもいない、という不変条件の実測確認になる。

**land tip は受入 tip より 1 commit 進む。** 差分は worklog fragment と本節への受入結果の
追記だけで、コード・テスト・reference・入口を含まない。

## 焦点走の赤 2 件は受入では出ない (裏取り)

上記「焦点走で出た赤 2 件」で示した機序どおり、`test_reflux_ir.py` が収集される受入全走では
当該 2 node は緑である (両走とも failed = 0)。選択走 import path の偽赤という帰属が実測で
裏付けられた。

## 裁定に対して実装していない部分

R1 (c) の「隔離 checkout での境界テスト」は裁定文が別途起票と定めているため本 wave では
実装していない。[T-747] の pinned compiler blocker が解けた場合の (a) 窓開け再検討も同じく
起票側へ送った。どちらも同じ問い (この 4 node を実際に走らせる経路) の 2 ルートなので
1 件へまとめてある。
