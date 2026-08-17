# 段 6 fix 裁定 (第 1 巡) — [T-1202] / [T-1197]

親裁定 / 2026-08-17 02:21 JST / 対象 commit `ccb9ee65`

段 6 の敵対レビュー 2 レンズが**独立に NO-GO** で一致した。所見を real/refuted と採否へ裁定し、
fix の scope を確定する。親は中核所見を独立に実測して裏取りした。

---

## 0. 親裁定 §1 の改訂 — dict carrier を限定許可する

**新事実 (裁定時に見えていなかった)**: production chain は `**dict` を 2 回通る。
親が実測して確認した:

```
run_trial:3162  finish_arguments = dict(..., drive=drive, ...)
        :3193  finish_arguments["origin_runtime"] = origin_runtime   # subscript 更新
        :3194  report = _finish_trial(**finish_arguments)
_finish_trial:2109  workload_arguments = dict(..., drive=drive, ...)
             :2128  workload_arguments["origin_runtime"] = origin_runtime  # subscript 更新
             :2130  cell = _run_workload(**workload_arguments)
```

親裁定 §1 は「`*args` / `**kwargs` 経由は到達と数えない」と書いた。**字義どおり適用すると
C12 に届かず、本 wave は目的を達しない。** 実装子はこれを静的 `dict(k=v)` carrier の追跡で
橋渡ししたが、それは未裁定の意味拡張である (レンズ A の A-01、レンズ B の B-01 が正しく指摘)。

**改訂裁定: 厳密に限定した不変 dict carrier だけを許可する。** 次を**すべて**満たす場合に限る。

1. carrier 名が当該関数内でちょうど 1 回だけ `Assign` で束縛される。
2. その RHS が `dict(...)` 呼び出しで、**keyword 引数のみ**である
   (`**` merge、位置引数、dict comprehension、dict literal 以外の式はいずれも不可)。
3. carrier への subscript 代入は、**key が str literal かつ target key と異なる**場合だけ許す。
   target key への subscript 代入、非 literal key、`del`、`.update(...)`、`.pop(...)`、
   `|=` などの再構成が 1 つでもあれば **carrier 全体を使用不能**とし、
   その target parameter を fail-closed で blocked にする。
4. carrier は `**carrier` として**ちょうど 1 回**splat される。
5. `**{...}` の literal dict splat、`**` 変数以外の式、`*args` は**引き続き全面禁止**。

この規則は実 production chain (subscript 更新は `origin_runtime` = target と別 key) を通し、
`drive` を subscript で差し替える攻撃を塞ぐ。

---

## 1. must-fix (実装する)

| # | 所見 | 裁定 | 内容 |
|---|---|---|---|
| F1 | lensA A-01 / lensB B-01 | **real・採用** | 上記 §0 の限定 carrier 規則へ厳格化する。`**{literal}` splat と `*args` は block。負例: target key への subscript 代入、`.update()`、`**{"drive": custom}` splat、carrier 再束縛。 |
| F2 | lensA A-02 | **real・採用** | **支配関係を要求する。** 代入が call より前にあり、同一の無条件経路で call を支配することを最低条件にする。現状は `relay(drive=drive)` の後に `drive = trigger...` を置くだけで到達と数え、実行時は `UnboundLocalError` になる。負例: 使用後代入。 |
| F3 | lensB B-02 | **real・採用** | **位置引数を fail-closed で block する。** target parameter に位置引数または `*args` が見えたら blocked。負例: `run_trial(custom_drive)` の位置引数 override。 |
| F4 | lensB B-03 | **real・採用** | sentinel 解決の形を厳格化する。代入が sentinel `if` の**直下 body に唯一存在**し、`else` 節も追加の入れ子条件も無いことを要求する。負例: `else` 配置、入れ子 conditional。 |
| F5 | lensA A-03 / lensB B-04 | **real・採用** | **binding count == 1 を import にも課す。** `from . import X` の後に `X = decoy` があれば解決しない。local 束縛形を保守的に列挙する (local import、`for`、`with`、`except as`、walrus、`global` / `nonlocal`)。1 つでもあれば解決不能へ倒す。package initializer は top-level の確実に実行される複合文も読み、解釈不能なら曖昧として閉じる。負例: module rebind、local import shadow、`if True:` 下の package shadow。 |
| F6 | lensA A-04 / lensB B-06 | **real・採用 (親が canonical を裁定)** | **target 定義の path は契約が宣言する evidence path 集合 (全条件の和、14 path) の中でなければならない。** 中継 module は宣言外でよいが、**終端 target の定義**は宣言内に限る。実測でこの規則は全条件の実 target を通す (`lookup`→env_contract.py、`attest_and_build_receipt`→execution_guard.py、`single_process_required`→reservation.py、`load_ratified_freeze`→s8b_ratified_freeze.py、`forbid_trial_restart`→trial_registry.py、`assert_campaign_layer3_chain`→autonomous_trial_completeness.py、いずれも宣言済み)。C09 の bare name 比較を廃し、これで production decoy も未宣言 path も塞ぐ。負例: production decoy (宣言外 path の同名定義)。 |
| F7 | lensA T-01 | **real・採用** | 上限テストが production default を検査していない。`MODULE_LIMIT == 512` の exact assert と、**default limits のまま 65 module 以上を探索する fixture** を追加し、`512 -> 64` 変異 (M11) が確実に kill されるようにする。 |
| F8 | lensA M-03 | **real・採用** | **単一理由性を回復する。** 各負例 fixture は 1 つの target だけを壊し、他 target は正しく直接配線する。allocation も (定義不在 / call edge 不在 / 属性不在) を独立負例へ分割する。過剰決定 fixture は DW-M03 違反。 |
| F9 | lensA T-02 | **real・採用** | 不在型 matrix を C01 / C04 / C09 / C12 の 4 条件へ展開する。適用不能な組合せは**理由を明記して**除外する (黙って落とさない)。 |
| F10 | lensB B-05 | **real・採用** | 1 回の `evaluate_all` 内で resolved commit / raw blob / AST / binding / 同一 root graph を**条件間で共有**する。EvidenceRef は条件別に再投影する。テストは module-scoped の snapshot / result fixture か batch Git 読取で重複走査を除く。現状 C04/C09/C12 で 26.4 秒 = 受入全走の約 22%。 |
| F11 | lensA H-01 | **採用 (記述の是正)** | snapshot-vs-HEAD exact test は同じ evaluator を両側に使うため補助検査である。**その旨を docstring に明記**し、mutation kill の根拠に数えない。`DECIDER_VERSION` exact assert は恒真でないことを両レンズが確認したので維持。 |

## 2. refuted / 現状維持

| 所見 | 裁定 | 理由 |
|---|---|---|
| lensA F-OK | **防御成立** | module 不在・曖昧解決は edge 不在、parse 失敗は ERROR、cycle は visited で停止、4 上限超過は ERROR。fail-open は静的に見つからない。 |
| lensA D-OK | **防御成立** | EvidenceRef は path 順、frontier / state は canonical 順。ただし F7 の強化でテスト側を補う。 |
| lensB A-01 / A-02 / A-03 | **適合** | 所有 4 file、許可済み期待値変更のみ、consumer 到達、pytest 収集、scope 外非混入。 |

## 3. 118 対 56 の差 (lensA T-01 が指摘) — 親の説明

矛盾ではない。親が段 3 待機中に測った 118 は **repo 内 module の transitive import 閉包の全体**で
ある。評価器の traversal は需要駆動で、target が見つかれば打ち切り、無関係な枝は開かない。
実測 56 はその需要駆動の結果である。**上限 512 の妥当性は「実 tree がどの上限にも触れない」ことで
担保するのであって、118 や 56 という個別値で担保するのではない。** ただし T-01 が正しく指摘した
とおり、その担保を**production default で**検査していなかった。F7 で是正する。

## 4. scope 外 = 裁定パッケージへ (実装しない)

| 項目 | 理由 |
|---|---|
| lensA S-01: 属性名の存在は enforcement の証明でない | 現 gate の設計 (親裁定 §4 どおり) であり、cross-module 化で偶然一致の範囲が広がっただけ。属性検査を「拒否方向と契約との対応まで見る」形へ変えるのは条件の再定式化であり [T-1167] 系の所有。**裁定パッケージへ残件として明記する。** |
| 段 4 §9 の 7 件 | 変更なし。混入していないことを lensB A-03 が確認済み。 |

## 5. fix の投入

- 所有は単位 A の 2 file (`s8c_preregistration_evidence.py`,
  `test_s8c_preregistration_predicates.py`) に閉じる。単位 B の 2 file は所見なし (H-01 は防御成立)。
  **一枚岩のため fix 子は 1 本**とする。
- 段 5 実装子契約 (`DW-S05-A` / `DW-S05-B` / `DW-S05-C`) を全文継承する。
- **既存テストの期待値を変更しない。** 実 tree の 12 条件 golden は
  `C12 = UNSATISFIED / allocation-enforcement-consumer-absent` を含む現行値のまま維持する。
  これが変わったら実装側が誤りである。
- fix 後に親が焦点走・変異 matrix・受入全走を再実施する。
