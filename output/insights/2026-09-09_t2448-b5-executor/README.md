# 2026-09-09/10 — [T-2448] 軸 B5 の実行器 (leaf 実行器 + 2 つの preflight)

- wave: `dev-wave-t2448-b5-executor` / branch `worktree-dev-wave-t2448-b5-executor`
- 起点 main: `7f17e1c63` / 受入時の main: `8150cb882` / 受入した tip: `99b40a7fa`
- 依頼: 軸 B5 の実行器 (parser・fixture・schema・runner) を作り、部分登録 §5.3 の
  registration preflight で catalog と実行器の bytes を束縛し、live preflight では 3 索引すべての
  member について ID lookup を再実施する。走行前に検索語彙・除外規則を緩めない (D1895)。

## 0. この wave が作ったものと、作っていないもの

**作った:** 軸 B5 の **leaf 実行器**と 2 つの preflight。

| 成果物 | 行数 |
|---|---:|
| `orchestrator/axis_b5_search/parsers.py` | 519 |
| `orchestrator/axis_b5_search/preflight.py` (registration + live) | 934 → fix 後 |
| `orchestrator/axis_b5_search/runner.py` (leaf 実行と 6 条件の評価) | 1033 → fix 後 |
| `orchestrator/axis_b5_search/anchor_registry.json` (16 anchor、30 member) | — |
| `orchestrator/schemas/axis_b5_search_{page_evidence,live_preflight,registration_seal}.schema.json` | 3 本 |
| `orchestrator/tests/fixtures/axis_b5_search/` | 実応答 10 + 合成 15 file |
| `orchestrator/tests/test_axis_b5_search_{parsers,executor}.py` | 20 + 34 node |

**作っていない (限界として明記する):**

- 軸全体の完走述語 (部分登録 §5.2 の論理積) を評価する軸集約器。**実行器は `完走` / `RW3` /
  軸の成熟度を返す API を持たない。**
- 演算子 control (§4.1) の集合関係と anchor 包含 control (§4.3) の評価。実行器は control の
  「発火」を返さない。request の完走値だけを持つ。
- 登録全体を索引順・query ID 辞書順で走らせる production 入口。
- checkpoint / resume と、複数窓にまたがる枝の独立 2 走 digest 一致。
- anchor に依存する補助 61 stream (凍結 catalog の外なので後継凍結物での登録が要る)。

**したがって本 wave の registration seal は暫定である。** seal record の `seal_scope` に
`leaf-executor-provisional` と除外層 (`checkpoint` / `resume` / `axis-aggregate` /
`control-firing` / `supplemental-anchor-stream-execution`) を機械可読に書いた。
checkpoint を後から runner へ足すと runner の bytes が変わるので、seal は取り直しになる。

**軸 B5 は `RW0` のままである。** 本 wave は世界の不在を支持せず、検索の実行も認可しない。
**外部 request は 1 本も出していない** (名前解決の probe を除く。§6)。

## 1. registration preflight を親が実データで通した

閉包記録 §0 が残した (a) registration preflight は「実行器が未実装」だけを理由に閉じていなかった。
本 wave の実行器に対して、親が実 repo で `verify_registration(HEAD, repo_root=".")` を走らせた。

- 結果: `passed=True`、**38 file を seal**。
- 束縛対象: 凍結 3 文書 + 凍結 catalog JSON + `orchestrator/axis_b5_search/` 配下の全 file +
  B5 schema 3 本 + fixture root 配下の全 file。**directory は exact file set で照合し、
  余分な path を拒否する。**
- catalog は固定 SHA-256 `7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f` と
  `render_catalog_json()` の両方に対して byte 一致を要求する。

**この実走が本物の欠陥を 1 件出した。** 下記 §3 の F1。

## 2. live preflight は「作ったが走らせていない」

閉包登録 §2.4 (b) の 3 形だけから 30 member (OpenAlex 16 / arXiv 1 / DBLP 13) の ID lookup を
組み立て、`収録` / `非収録` / `不達` / `unclassified` を判定する経路を実装した。
**本 wave では 1 本も発行していない。** 実行は人間の認可事項である (閉包記録 §0 (c))。

親が裁定した実装上の要点は 4 つ。

1. **判定順序。** OpenAlex は status を先に見る。404 は content type を見ずに `非収録` とする。
   前 wave が保存した実応答では OpenAlex の 404 が `text/html` を返すので、順序を逆にすると
   **登録どおりなら `非収録` になる応答が `不達` に化ける。**
2. **3 値に入らない応答を丸めない。** DBLP が 200・`application/json`・`@total > 0` で当該 DOI が
   無い形は `unclassified` として観測した形のまま記録し、走行を開始しない。
3. **未登録の運用値を発明しない。** timeout・User-Agent・request 間隔は既定値を持たず、
   呼び手が明示した値を記録へ逐語で残す。
4. **登録に無い阻止条件を足さない。** 観測 work ID が登録値と食い違っても記録するだけで、
   走行開始を阻止しない。登録された述語は 3 値だけである。

## 3. 凍結文が定めていない運用値と、本走発行の fail-closed

期待 content type の exact 集合・timeout・User-Agent・request 間隔・retry 対象の失敗集合・
redirect の扱いは、軸 B5 の事前登録が**定めていない**。実装子の便宜値で埋めると、凍結後に
実装者が選んだ実行契約になる。

そこで **本走の request 発行は `UnregisteredRunPolicyError` で fail-closed** とし、未登録の
6 項目 (`expected_content_types` / `timeout_s` / `user_agent` / `request_interval_s` /
`retryable_failures` / `redirect_policy`) を機械可読に列挙して返す。
6 条件の評価そのものは保存済み応答に対して完全に実装しており、そこが本 wave の実体である。

**走行の認可はユーザーの手番であり、そのときにこれらの値が決まる。**

## 4. 段 3・段 6 の敵対検証が出した所見

段 3 (プランへの攻撃) 2 本、段 6 (実装への攻撃) 2 本。親は現物で裏を取ったものだけを real とした。

**production の欠陥 7 件 (すべて修正済み):**

| # | 欠陥 | 出所 |
|---|---|---|
| F1 | directory exact set 検査が `.gitignore` の `__pycache__/*.pyc` を余分な path と数え、**一度でも import した実 repo では必ず落ちる gate** だった | 親の実走 |
| F2 | arXiv の日付 delimiter 正規化が `[...` と `..."` の混在形も正規形へ丸め、受理集合を広げていた | 段 6 A |
| F3 | 条件 1 の OpenAlex 期待 AST の形が実応答の形と一致しない | 段 6 B |
| F4 | `B5-CTL-AND2023@openalex` の期待 AST が catalog 共通の 2026 cutoff を使い、凍結文が固定する 2023-12-31 と食い違っていた | 段 6 A |
| F5 | live preflight の集約器が公開 seam で、呼び手が作った record から走行可を作れた | 段 6 A |
| F6 | seal が任意の `repo_root` を束縛するだけで、実際に import された module がその root 配下かを見ていなかった | 段 6 A |
| F7 | live schema に複製された `registration_seal` 定義が standalone schema より弱かった | 段 6 B |

**F3 の修正方向は親が正本で確かめてから決めた。** 段 6 B は「正常な OpenAlex 応答が条件 1 で落ちる」と
指摘したが、条件 1 の OpenAlex 節は `2026-09-02-axis1-search-amendment.md` §3 を軸 B5 へそのまま
当てる規則で、その登録構造は `{"get_rows": ..., "filter_rows": [{"column_id": ..., "value": ...}, ...]}`
である (`orchestrator/axis1_search/catalog.py:325-353` が同じ形を作る)。
**実装の builder は正しく、誤っていたのは合成 fixture の側だった。** 指示を誤れば正しいコードを
壊すところだった。`get_rows` は軸 B5 の登録どおり文字列 `"200"` のままにしている (軸 1 は `"works"`)。

**test の検出力の穴 8 件 (すべて塞いだ):** 期待 AST の正例が production builder の出力同士を
比べていて恒真だった件、registration の正例が実行器本体を含まない fake root を通していた件、
production 入口 `run_leaf` を通る test が無かった件、成功側 `run_live_preflight` が未実走だった件、
cursor 終端と `非収録` の負例が無かった件、部分最終 page の正例が条件 2 で落ちる fixture を
使っていた件など。

**不採用にしたもの:** 段 2 プランが推奨した「観測 work ID の drift で走行を阻止する」は、
登録に無い阻止条件を足すことになるので採らず、記録のみとした。

## 5. 変異 matrix

`tools/mutation_harness.py --runner-mode dispatch`、runner =
`python3 tools/run_tests.py orchestrator/tests/test_axis_b5_search_executor.py orchestrator/tests/test_axis_b5_search_parsers.py -q -rf`。
probe 先行方式 (全件 SURVIVED 期待で観測 node を集め、本走で期待へ写す) を採った。

**本走 2 回目 (HEAD `61f7813ec`、spec sha256 `fad64f426de611670e492aa25bde57446f825eac547511ab46ece06418e7d3a6`):
baseline 緑 (赤 0)、KILLED 12 / SURVIVED 0 / MISMATCH 0、期待 node 29 件が完全一致。**

| id | 変異 | 期待 node 数 |
|---|---|---:|
| m01 | OpenAlex の初回 cursor を literal `*` から `%2A` へ | 2 |
| m02 | 期待 AST の children を set 化 (多重度を落とす) | 2 |
| m03 | live preflight の `all(収録)` を `any` へ | 3 |
| m05 | 条件 3 の実要素数を `capacity_echo` に差し替え | 4 |
| m06 | 本走発行の fail-closed を外す | 2 |
| m07 | seal の directory exact set を部分集合検査へ緩める | 2 |
| m08 | DBLP の cutoff 判定を落とす | 3 |
| m09 | 3 値に入らない応答を `収録` へ丸める | 2 |
| m10 | OpenAlex の判定順序を content type 先行へ入れ替える | 2 |
| m11 | `G2-08` の主キーを arXiv ID にする (registry と自己検査 literal の 2 層同時) | 3 |
| m12 | retry delay の `6.0` を `7.0` へ | 2 |
| m13 | `__pycache__` の除外を外す (F1 の回帰) | 2 |

**m04 (総件数 drift を最終 page の値で受理) は登録しなかった。** 単一理由になる 3 page 構成の
fixture が無く、条件 3 と同時に赤になるためである (DW-M01 の「帰属が絞れなければ登録しない」)。

**期待 node に `test_registration_accepts_exact_commit_tree_and_returns_schema_valid_seal` が
全 12 件で入っている。** これは fix2 でこの test が実 HEAD と実 git で照合する形になったためで、
**registration seal が実行器の bytes 改変を実際に検出している**ことの証拠である。
各変異の帰属は、この共通の検出に加えて変異固有の test が別に赤になることで保たれている。

**m12 は受理集合を変えない定数の凍結検査である** (DW-M08 の diagnostic sensitivity pin)。
retry の consumer は本走発行が fail-closed のため現時点で存在しない。

### 変異走行が暴いた test の欠陥

**本走 1 回目は 11 KILLED / 1 MISMATCH だった。** MISMATCH は m13 で、probe では赤 1 件、
本走では赤 2 件になった。原因は、`__pycache__` の正例 test が**実 repo の共有 tree へ
`.pyc` を書いて消す**作りだったことである。xdist の別 worker が同じ実 repo を読む test
(`test_live_preflight_accepts_exact_30_and_wid_drift_is_evidence_only`) が、その `.pyc` が
存在する瞬間に落ちていた。**赤 node 集合が走行ごとに変わる状態で、受入の全走でもランダムに
赤を出す形だった。** 変異走行を 2 回まわしたからこそ出た差である。

fix2 で検査を 2 つに分けた。除外の意味論は `tmp_path` の一時 tree に対して決定的に検査し、
実 repo に対しては読み取りだけで gate が通ることを確かめる。実 repo 側に `__pycache__` の
存在を前提にした assert は置いていない (`PYTHONDONTWRITEBYTECODE` の環境で偽の赤になるため)。

## 6. 親が実測したこと

**新しい外部 request は 1 本も出していない。** 出所は前 wave が保存した生応答と、名前解決 probe だけ。

- 名前解決 (2026-09-09、login node `pegasus02`): 3 索引とも解決した。HTTP 層の可用性は
  2026-09-07 の観測が最後の実測である。
- 保存済み生応答の header: arXiv は `application/atom+xml; charset=utf-8`、OpenAlex は 200 が
  `application/json` で **404 が `text/html`**、DBLP は challenge の `text/html`。
  詳細と裁定への効き方は `parent-measurements.md`。
- **anchor registry の転記を凍結記録の表から独立に抽出して照合した。** 16 anchor の DOI と
  OpenAlex work ID は全件一致、member 集合も OpenAlex 16 / arXiv 1 / DBLP 13 で完全一致、
  `G2-08` の主キーは DOI で arXiv ID は別 field。

### DBLP について brief の誤りを訂正した

段 1 brief は「DBLP 13 member は `不達`」「要求値は 2026-09-07 の実測では到達不能」と書いたが、
これは実測を超えた一般化だった。**閉包記録 §2 は anchor 固有 request を 1 本も送っておらず、
`不達` は共有 endpoint の環境 probe からの外挿だと明記している。13 member の個別 live 値は未観測である。**
live preflight で 13 本を実際に出すことには情報価値がある。段 3 のレビューが指摘し、親が現物で確認して直した。

## 7. 受入と検査

- **受入全走: child-green。** tested main `8150cb882` / tested tip `99b40a7fa`、
  **22413 passed / 68 skipped / 0 failed**。
- 焦点走 (変更 production を参照する consumer test を参照関係で列挙): 867 passed / 1 failed。
  この 1 件は `test_real_repo_serialization.py::test_real_repo_writers_do_not_materialize_oracle_environment_candidates` で、
  **焦点走の選択範囲による偽赤**だった。当該 test は他の test module を import する形で、
  狭い file 選択では前提が確立せず落ちる (DW-O18 の「file 選択走は import path 確立後に限り偽赤」)。
  **main tip に本 wave の変更を一切含まない木を作って同じ test を単独で走らせても同じく落ち、
  受入全走では緑だった。** 本 wave に帰属しない。hold 登録も裁定送りも要らない。
- `tools/check_docs.py` rc=0、`tools/spool_fold.py --dry-run` 成立、
  `tools/check_ai_provenance.py` 全数監査で新規違反なし。

## 8. 生証拠の所在

| dir / file | 内容 |
|---|---|
| `brief.md` | 親の段 1 brief (DW-O13 の値域実測を含む) |
| `parent-measurements.md` | 親の実測 (名前解決、保存済み応答の header と裁定への効き方) |
| `rulings-stage4.md` | 段 4 裁定 (成果物の名乗り、未登録運用値、所見ごとの採否、変異の事前登録) |
| `mutation/spec-probe.json`、`probe-ledger-1.json`、`probe-ledger-2.json` | 変異 probe の spec と台帳 |
| `mutation/spec-final.json`、`final-ledger-1.json`、`final-ledger-2.json` | 本走の spec と台帳 |
| `codex/` | 段 2 plan、段 3 相談 A / B、段 5 author A / B、段 6 レビュー A / B、fix、fix2、台帳 fix の逐語と prompt |

## 9. 次 wave の出発点

閉包記録 §0 の 3 点のうち、**(a) registration preflight は実装が揃い、親が実データで rc=0 を得た。**
残るのは (b) live preflight の実施と (c) 人間の実行認可である。加えて本 wave が scope 外とした
5 つ (軸集約器、control の集合関係と包含 control、実行証拠の exact-set manifest と offline 再評価、
全走入口、checkpoint / resume) と、補助 61 stream の後継凍結物での登録が残る。

**走行の認可の前に、未登録の 6 運用値をユーザーが決める必要がある。** 実行器はそれまで
本走 request を 1 本も出せない。
