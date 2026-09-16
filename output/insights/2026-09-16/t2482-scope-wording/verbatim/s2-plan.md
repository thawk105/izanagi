## 文言案

変更は production 2 定数と test の live literal 2 か所に限定する。以下の行番号は修正前のもの。

`orchestrator/campaign/artifact_admission.py:73–83` を次の全文へ置き換える。隣接文字列の連結後が実際の値となる。

```python
CAMPAIGN_VERIFIER_EPOCH_SCOPE = (
    "enforcement source closure (curated exact 63 path; "
    "2026-09-16 (e667c8c13) の実測では、収載 tuple 起点で静的 import を辿った"
    "発見集合 162 module のうち 63 を収載; source-import 推移閉包ではない)"
)
CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE = (
    "同実測の発見集合の未収載 99 module、orchestrator/verifier/__main__.py、"
    "orchestrator/verifier/cli.py、package 外の orchestrator/verify.py、および "
    "data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 "
    "import を含む非 import 委譲は本 map の外であり、完全性を主張しない。"
    "同発見集合は収載 tuple 起点であり、そこから静的 import で辿れない "
    "module は含まないため、認証成果物の発行器全体を網羅する集合ではない"
)
```

測定日・commit は発見集合とその収載・未収載数に係る。発見集合を認証経路全体や実行到達集合と同一視する説明は加えない。

## (P1)(P2)(P3) の採否

| 案 | 判断 | 理由 |
|---|---|---|
| P1：日付・commit 付き snapshot | 採用 | 162／99 を特定 commit の測定事実として示せる。実行時計算は不要。ただし冒頭の `curated exact 63 path` は現行 tuple の説明なので、将来の tuple 変更まで自動的に正しくなるわけではない。 |
| P2：tuple 起点の発見限界 | 採用、表現を限定 | 発見集合の意味を明確にする文言修正であり、対象拡大や機構追加ではない。「発行器を含まない」では発行器すべてが集合外と誤読されうるため、「発行器全体を網羅する集合ではない」とする。 |
| P3：24／36／2＋1 の内訳維持 | 不採用 | 24／36／2 は T-733 当時の追加根拠であり、現在の直接 import 被覆の内訳と読ませるべきではない。履歴と明記して残す案も可能だが、現行被覆の説明には不要。63 本目の由来は下記照合に残し、歴史 insight は維持する。D1651 は内訳維持を要求していない。 |

## D1651 要素照合表

| 必須要素 | 新文言の該当箇所 | 判定 |
|---|---|---|
| 収載 path 数 | `curated exact 63 path`、`63 を収載` | 維持 |
| 推移閉包ではない | `source-import 推移閉包ではない` | 逐語維持 |
| 未収載 module 数 | `同実測の発見集合の未収載 99 module` | 実測へ更新 |
| 非 import 委譲の除外 | `data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外` | 例示と一般形を維持 |
| 完全性を主張しない | `完全性を主張しない` | 逐語維持 |
| docstring を第二の正本にしない | `artifact_admission.py:173–177` などの参照方式を維持 | docstring は変更しない |

## D1884 強さ点検

| 句・変更 | 方向 | 点検結果 |
|---|---|---|
| `enforcement source closure`／`curated exact` | 同等 | 既存名称を維持。直後の非推移閉包という限定も維持する。 |
| `62 path` → `63 path` | 数字だけなら強める方向 | 収載済みの実物への訂正。`campaign_lock.py:49–113` の tuple は既に 63 本であり、この修正による被覆拡大ではない。これを単純に「弱めるだけ」と説明しない。 |
| 発見集合 `131` → `162`、そのうち `63` | 限定を明確にする方向 | 発見と収載を明確に区別する。162 module が束縛済みとは読ませない。 |
| 日付・commit・tuple 起点の明示 | 弱める方向 | 時点と探索起点を限定し、普遍的な被覆説明として読まれる余地を減らす。 |
| 24／36／2 の削除 | 同等、誤読抑制 | 現在も直接 import 先を網羅しているという含意を避ける。収載数と保証の限定は残る。 |
| `source-import 推移閉包ではない` | 同等 | 保証上限を維持。 |
| 未収載 `69` → `99` | 弱める方向 | 発見集合内の未束縛部分を実測どおり示す。 |
| verifier 3 path の個別除外 | 同等 | 既存の除外を維持。99 の内数とは書かない。 |
| 非 import 委譲の除外・完全性非主張 | 同等 | 限定を削除しない。 |
| 発行器全体を網羅しない | 弱める方向 | 発見集合の外側にも欠落があることを明示する。 |

結論として、数値上の収載数は増えるが、実装済み 63 本を超える保証は追加しない。D1884 の段階実装方針を撤回したり、「現行 63 で終端」と裁定したりする文言でもない。

## test 更新計画

| 箇所 | 更新 |
|---|---|
| `orchestrator/tests/test_artifact_admission.py:1160–1170` | `test_real_e0_is_rejected_only_by_certified_epoch_gate` の `identity_scope`／`excluded_scope` 期待 literal を上記全文へ置換する。 |
| `orchestrator/tests/test_s1_9pair_figure_provenance.py:74–89` | `CURRENT_E0_EPOCH` の同 2 field だけを上記全文へ置換する。E0、state、reason_code は維持する。 |

独立 literal は残す。production 定数参照に置き換えると、production の誤った数値や限定句の削除に期待値も追随し、文言変異を検出できなくなる。oracle report の定数参照テストは伝播の確認には有効だが、この独立照合の代わりにはならない。

以下は変更しない。

- `test_s1_9pair_figure_provenance.py:90–103` の `FROZEN_E0_EPOCH`：生成時の receipt。`:736–744` が凍結文言との一致を検査している。一方、現行値は `:383–385` で別に検査される。
- `artifact_admission.py:84–92` の `PRE_T733_*`：exact-24 歴史 grammar 固有の説明。`:220–235` が歴史診断へ適用し、`test_artifact_admission.py:1772–1782` が独立 literal と現行値との差を検査している。
- 凍結 validator hash、記録済み成果物、歴史 insight、tuple、decode、受理述語、E1 preimage、一致検査。

## brief 実測の照合

射影ファイルはすべて読取可能だった。JSON は標準ライブラリで読み取り、配列長・集合差・現行 tuple との対応を確認した。import 探索 probe 自体は再実行していない。

| 項目 | 照合結果 |
|---|---|
| 現行 63／162／99 | 一致。HEAD JSON の配列長もそれぞれ 63／162／99、`discovered − enrolled` は 99。現行 tuple と JSON の `enrolled` は順序込みで一致。 |
| 正例対照 63／140／77 | 一致。control JSON の配列長と集合差、および T-2344 README の記録が一致。 |
| 発見集合の増分 | HEAD と control の差は追加 22、削除 0。収載数は双方 63。 |
| 1 段展開 | JSON の HEAD は 83／未収載 20、control は 81／未収載 18。brief と一致。 |
| verifier 3 path | `orchestrator/verifier/__main__.py`、`orchestrator/verifier/cli.py`、`orchestrator/verify.py` は双方の JSON の `discovered` に無い。`enrolled` にも無い。99 とは別記できる。 |
| 63 本目 | `campaign_lock.py:112` は `orchestrator/campaign/verify_fanout_worker.py`。HEAD JSON の収載・発見集合双方に存在。T-2344 README `:40–41` は T-2429 による追加と記録しており、由来の説明と一致。追加 commit の履歴監査はしていない。 |
| 24／36／2 の由来 | T-733 README の「何をしたか」「閉包の寸法」と一致。T-2344 README `:59–67` は、その後すでに直接委譲の未収載が生じたと記録している。現在の網羅性の根拠には使えない。 |
| E1 preimage | `artifact_admission.py:1061–1065` は domain と、tuple 順の `UTF-8(path) + NUL + blob digest bytes` の連結。scope 文字列を直接連結していない。 |
| 読取時の scope | `:183–184` が定数を既定値とし、`:1044–1048`、`:1074–1078` の診断生成は scope 引数を渡さない。記録 map から scope を復元する処理ではない。 |
| `__post_init__` | `:187–190` が両定数との完全一致を検査し、不一致で `TypeError`。維持する。 |

brief には次の限定・修正が必要。

- **「E1 値不変」は同じ記録済み map に対して成立する。** `artifact_admission.py` 自身が `campaign_lock.py:57` の収載 path なので、文言修正後の blob を記録する新規 lock の E1 まで不変とはいえない。preimage の形式と既存記録からの再導出値を変えない、という条件にする。
- **「数値更新は未束縛部分を大きく見せる方向だけ」は不正確。** 62→63 の訂正もある。既存被覆への追随である点を明示する。
- 外部 root 23 directory の検索結果、producer 11 箇所すべて、bytes pin の網羅調査、並行 wave の状態は今回独立に再確認していない。親の証拠として扱い、自分の実測済みとは記さない。

## 変異の事前登録案

更新後の正常系を基準に、以下を一件ずつ適用して復元する。新規 gate や恒久検査は追加せず、既存テストで確認する。

略号：

- **A**：`orchestrator/tests/test_artifact_admission.py`
- **S**：`orchestrator/tests/test_s1_9pair_figure_provenance.py`

| ID | 単独変異 | 落ちるはずの test と照合点 |
|---|---|---|
| M1 | production SCOPE の `curated exact 63 path` を `curated exact 62 path` にする | A `test_real_e0_is_rejected_only_by_certified_epoch_gate`、`:1160` の `assert identity_scope == literal` |
| M2 | production SCOPE から `; source-import 推移閉包ではない` を削除 | 同 test、A `:1160` |
| M3 | production EXCLUDED_SCOPE の `未収載 99 module` を `未収載 69 module` にする | 同 test、A `:1165` の `assert excluded_scope == literal` |
| M4 | production EXCLUDED_SCOPE から `、完全性を主張しない` を削除 | 同 test、A `:1165` |
| M5 | A 側だけ、SCOPE 期待 literal の `発見集合 162 module` を `発見集合 161 module` にする | 同 test、A `:1160`。production は正常値のまま。 |
| M6 | S の `CURRENT_E0_EPOCH` 側だけ、EXCLUDED_SCOPE の末文を削除 | S `test_p1_independent_real_wal_projection_matches_frozen_report`（`:826`）から `:828` の `_real_inputs()` を通り、`:383–385` の epoch 完全一致検査で失敗。 |

M6 の照合点は Python の `assert` 文ではなく、`if epoch != CURRENT_E0_EPOCH` → `_reject()` → `ProvenanceError`（S `:153–154`）である。無関係な後続 assert の失敗とは記録しない。

production 変異は import 前に適用する想定。import 後に定数だけ monkeypatch すると dataclass 既定値との不一致で別経路の `TypeError` になり、狙った literal 照合を実証できない。各結果は予定した照合点への到達で判定し、dirty closure による失敗を検出成功へ数えない。

## 焦点走の対象

次の検索を実施した。

```text
rg -n 'CAMPAIGN_VERIFIER_EPOCH_(EXCLUDED_)?SCOPE' --glob '*test*.py'
```

直接の定数参照は以下の 2 file。

| file | 検出位置・役割 |
|---|---|
| `orchestrator/tests/test_artifact_admission.py` | `:1782`。歴史文言と現行定数が異なることの確認。加えて `:1160`／`:1165` に今回更新する独立 literal がある。 |
| `orchestrator/tests/test_s8b_oracle_report.py` | `:1007–1008`。`test_report_projects_e1_epoch_from_resolved_campaign_layout` の `:1002` の assert が両 field の report への伝播を確認。 |

独立 literal は定数名検索だけでは拾えないため、`CURRENT_E0_EPOCH` と旧文言でも検索した。その結果を加えた焦点走の対象集合は、次の **3 file** とする。

```text
orchestrator/tests/test_artifact_admission.py
orchestrator/tests/test_s8b_oracle_report.py
orchestrator/tests/test_s1_9pair_figure_provenance.py
```

親が commit 後の正常系で `tools/run_tests.py` を通して焦点走を実施し、変異確認後に brief 指定の `tools/dev_wave_wait.py acceptance` 既定経路で受入を行う。ここではテストを実走しておらず、緑とは判定していない。

## 総括

P1・P2 を採用し、P3 の履歴内訳は現行保証文言から落とす。実装差分は **3 file・4 か所**で、63／162／99 の測定時点と発見集合の限界を明示する。

tuple、受理述語、E1 preimage、一致検査、歴史定数・凍結成果物を維持する。ファイル変更・テスト実走は行っていない。