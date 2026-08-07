# 段 4 裁定 — [T-624] activation record の no-op 拒否

基準 commit `bb824d8b`。段 2 は **GO**、段 3 レンズ A・レンズ B はともに **NO-GO** で、
根拠は独立している (A = 裁定境界と規律、B = 述語の意味と検出力)。親が裏取りして裁定する。

## 親が独立に裏取りした実測 (すべて本 worktree)

| # | 実測 | 手段 |
|---|---|---|
| P | `env_contract.py` の source sha256 は凍結成果物 2 種に pin されている — silo evidence が path+sha 隣接 field (`silo_ladder_rung1.json`)、t419 probe manifest が role 名 key `env_contract_sha256` (`0_888740.nqsv/manifest.json`)。値はいずれも `88d557ba…` | `sed` で直接確認 |
| Q | 現行 bytes の sha256 は `8d529822…` であり、上記 pin 値と**既に不一致**。すなわち両 pin は歴史記録であって現行 bytes との一致を要求する live pin ではない (実測 B の 136 passed と整合) | `hashlib` probe |
| R | `is_valid_successor` は `_validate_generations_without_bootstrap_fuse` → `validate_generations(GENERATIONS)` の module 初期化経路に**結線済み**。ただし世代列長が 1 のため `zip(sequence, sequence[1:])` が空で、body は現状**一度も実行されない** | `env_contract.py` の 308/316/344 行 |
| S | 段 2 の 20 行表は、レンズ B が提示した総和判定の誤実装を **1 行も落とせない** (全行が期待値と一致)。同誤実装は `(+2, −1)` の record を受理する | 下記 probe (repo 外の job dir で実行) |

実測 S の probe 本体 (判定部のみ。表の 20 行は `s2-plan.md` の逐語と同値、
shape / type gate は段 2 案どおり正しく置いた上で最終判定だけを差し替えた)。

```python
    return 1 <= sum(after[k] - before[k] for k in kb) <= len(kb)
```

出力は次のとおりだった。

```text
段 2 の 20 行を誤実装が全通過するか: YES (表に検出力なし)
反例 (+2,-1) を誤実装が受理するか: True
```

## 所見の裁定

### real (採用)

- **[A-M5] / [B-M5]。親の前提実測 C 「bytes を literal で pin する台帳・test は 0 件」は偽。**
  実測 P のとおり 2 種の凍結成果物が pin している。原因は 2 つ重なっている —
  (i) `grep -rln "env_contract" --include=*.json output/` を **`| head` で 10 件に切って**
  全件を見なかった (silo artifact は切られた側にいた)、(ii) role 名 key の pin は path 検索に
  掛からないという `DW-O09` の明記事項を、本文を読んだ上で適用しなかった。
  **F30 の 4 度目の再発** (3 度目 2026-08-06 と同型)。**採用。段 7 で failures へ再発追記する。**
  ただし実測 Q より、両 pin は歴史記録であり本 wave の編集で赤にはならない。
  正しい書き方は「pin 0 件」ではなく「**歴史 pin 2 件・live pin 0 件**」である。
- **[A-M1]。`DW-G04` を満たしていない。** 本述語の発火条件を満たす artifact path も計測 ID も
  今日書けない (親の実測 A と一致)。前 wave が発掘した `94a4…` / `892707.nqsv` は calibration 素材であり、
  env→generation mapping を持つ activation artifact ではない。裁定 B(a) が T-529 限定であることは、
  T-624 が `DW-G04` から免除されることを意味しない。**採用。**
- **[B-M1]。世代番号の delta だけでは、裁定 D が塞ごうとした失敗を塞がない。** 裁定 D の元の懸念は
  「serial が増えているのに新規 run の contract hash が旧較正へ戻る受理が通る」である。
  番号 mapping しか見ない述語は、g3 が旧較正 A を指す再束縛を `True` で通す。
  D176 自身が「逆引き index は module 属性として再束縛可能であり authority として扱ってはならない」と
  明記しており、番号射影はその再束縛に対して無力である。**採用。これが決定的。**
- **[B-M4]。段 2 の表に検出力がない。** 実測 S のとおり総和判定の誤実装が 20 行を全通過し、
  `(+2, −1)` を受理する。`DW-M03` の単独理由性も 6 か所で不足する。**採用。**
- **[A-M2]。D176 の先例と同型でない。** 実測 R のとおり `is_valid_successor` は
  module 初期化の call chain に結線済み (発火は 2 世代目登録の瞬間) であるのに対し、
  新述語は consumer が 1 つもない。「結線済み・未発火」と「結線なし」は別物である。
  親の (P1) はこの差を潰していた。**採用。**
- **[A-M3]。identity 副作用を成果物影響として scope の正当化に使えない。** T-126 `code_identity` と
  silo `runtime_modules_sha256` はコメント 1 行でも動く provenance 値であり、これを
  `DW-G05` の充足に数えると同 gate が恒真になる。**採用。**
- **[B-M2] [B-M3] [A-M4]。命名 (`is_valid_*` が state 全体の検証と読める)、generic `Mapping` の
  snapshot 依存、env 集合変化の永久拒否を未裁定のまま決定へ昇格させること。** いずれも real。
  **採用。ただし単位 2 を land しないため実装面には効かず、裁定パッケージと決定の射程へ残す。**

### refuted / 補正

- **[A-M2] の「registry 未登録 env・存在しない generation さえ受理する」を単独の NO-GO 根拠にはしない。**
  それは純 data-layer 述語であることの当然の帰結であり、D176 が既に許した形と同じである。
  NO-GO の重みは [A-M1] と [B-M1] にある。
- **[A-M5] の「実測 C は事実として偽」は正しいが、「歴史 artifact が壊れる」ではない。**
  実測 Q のとおり現行 bytes は既に pin 値と異なる。レンズ B [M5] の「live runtime 再計算 +
  歴史 pin は保持」という分類が正しい表現である。
- **[A-N1] は nit のまま。** 実測 B から「全受入が緑」を導くつもりは無く、brief にもそう書いていない。

## 親の provisional 裁定の帰趨

| | 判定 |
|---|---|
| (P1) 単位 2 (述語実装) を今日 land してよい | **誤り。** `DW-G04` の発火材料が無く (A-M1)、番号射影の述語は裁定 D の狙った失敗を塞がない (B-M1) |
| (P2) 成果物影響ゼロでも実装してよい | **誤り。** identity 副作用は `DW-G05` の充足に数えられない (A-M3) |
| (P3) env 集合変化は拒否 | **未裁定へ戻す。** 決定へ昇格させない (A-M4 / A-S2) |

親の一般化が段 3 で覆るのは **5 wave 連続**である。段 8 の改善候補へ記録する。

## 裁定 — 本 wave の scope

**実装する (単位 1 のみ、docs):** ユーザー裁定 (a) の遷移規則を decisions へ明文化する。
決定本文には裁定 (a) の逐語規則と射程 (何を保証しないか) だけを書き、
未裁定の要素 (env 集合変化の扱い、述語の署名、exact-int 等の型規約) を含めない。

**実装しない (単位 2):** 純 data-layer 述語と表駆動テストは land しない。
`DW-S04` に従い段 5・6 を飛ばし `4→7→8→9` とする。**実装差分がないため変異 matrix と
受入全走は本 wave の対象外**である (docs 変更に対する `check_docs.py` と関連テストは走らせる)。

これはユーザー裁定 (a) を止めるものではない。(a) が命じたのは**規則の明文化**であり、
コード述語はその実現手段として親が (P1) で暫定選択したものにすぎない。明文化は本 wave で完了する。

## ユーザーへ返す択一 (scope 外の real 所見)

| # | 択一 | 親の推奨 | 決めないと何が起きるか |
|---|---|---|---|
| α | **述語の入力粒度。** (a) env→generation の数値 mapping / (b) generation と contract hash (`GenerationEntry`) を同一入力で束縛し `is_valid_successor` と合成 / (c) 実 activation record schema が決まるまで置かない | (c)。次点 (b)。(a) は B-M1 のとおり狙った失敗を塞がない | 番号だけの gate を「no-op を拒否する保証」と誤読した consumer が、旧較正へ戻る record を受理する |
| β | **env membership migration。** (a) activation transition では env 集合変化を永久に拒否し別機構へ回す / (b) 追加は許し削除は拒否 / (c) 未定義のまま置く | (a)。ただし別機構の裁定が要る | 新 env を足した最初の activation record が一律拒否され、例外経路の後付けか受理集合の再変更になる |
| γ | **`DW-G04` の適用。** (a) 適用し、activation record の実 artifact が出るまで述語を設計メモに留める / (b) T-624 に限り上書きし、合成 fixture を発火証拠と認める | (a) | (b) を採ると、永久 fuse と観測的に区別できない実装が「no-op を拒否する gate」として台帳に残る |

## 変異事前登録 (`DW-M01`)

**実装差分が無いため変異は登録しない。** `DW-M01` は実装前の登録を求めるが、本 wave の成果物は
docs だけであり、無効化して赤にできる gate を新設しない。段 7 の worklog へ同じ射程を明記する。
