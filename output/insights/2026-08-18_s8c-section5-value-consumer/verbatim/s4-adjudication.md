# 段 4 裁定 (plan v2) — 8c §5 判定パラメータ欄の値 validator

作成 2026-08-18 19:30 JST。入力は段 2 プラン、段 3 レンズ B、親の一次資料確認。
段 3 レンズ A は wall-clock 3600 秒で SIGTERM (`codex_exit_code=-15`、`output_bytes=0`、
model call 26)。**成果物ゼロで未完了**。同レンズ (fail-open / 恒真化) は本裁定の plan v2 を
対象に再投入し、さらに段 6 の敵対レビュー 1 本へ引き継ぐ。

## 0. 裁定の核 — 設計を (A) から (E) へ変える

段 2 プランと親 brief は、制約違反値を `_classify_section5_value` で `FieldStatus.INVALID` に
倒す形 (以下 A) を前提にしていた。**親は A を不採用とする。** 根拠は一次資料 2 点。

1. `docs/phase3-8c-preregistration.md`「発効の判定と条件契約の凍結」は**凍結範囲**であり、
   「記入済みとは、値が単一の code span 内の canonical JSON であり、placeholder・`null`・
   空文字列・空 container のいずれでもないことをいう。**欄ごとの型・単位・範囲の検証は
   本手続きの対象外である**」と定義している。A は記入済み判定に型・範囲を持ち込むため、
   凍結本文と直接矛盾する。凍結本文の改訂は docs 編集 + 新世代であり scope 外。
2. 同節 (D458): 判定器の**受理集合・拒否理由**を変える変更は bytes 差の有無に関わらず
   `DECIDER_VERSION` の bump と新世代 record の発行を要求する。A は受理集合を狭め拒否理由を
   増やすため必須発動する。しかし新世代 record の `ruling_reference` は
   **その commit 時点の** `docs/decisions.md` に `## D<N>.` 見出しの実在を要求し
   (`_assert_rulings_exist`)、D 番号は land の fold でしか採番されない。加えて並行 8c wave が
   複数走っており、世代番号の衝突は merge で解けない。ユーザーは凍結 record の更新を
   明示的に scope 外と指定している。

したがって**採用する設計 (E)** は次である。

- `記入済み` 判定 (`_classify_section5_value` の FILLED/UNFILLED/INVALID) と
  `ActivationReport.effective` の連言式を**一切変えない**。受理集合は不変であり、
  `DECIDER_VERSION` の bump も新世代 record も発生しない。
- §5 値制約の validator を**新設**し、production の parse 経路から到達可能にする
  (8c §6 前提条件 7 が名指しで要求する「validator が production 経路から到達可能」の実体)。
- 違反は**構造化して報告する** (`Section5ValueViolation`)。理由コードは違反軸ごとに分ける
  (規律 3: なぜ壊れたかを返す)。
- **実効的な閂は repo 不変検査に置く。** 生きた `docs/phase3-8c-preregistration.md` の §5 に
  制約違反値が入った瞬間に受入全走が赤になるテストを足す。これにより
  「機械検証する consumer が実在するときに限り記入してよい」が実際に強制される。

**この裁定で達成されないこと (裁定パッケージへ回す。§6 参照)**: 判定器の内部で違反値が
`effective` を偽へ倒す形。これはユーザーが scope 外と指定した 3 項目 (machine_checkable 反転・
凍結 record 更新・§5 実値記入) のうち 2 つに正確に一致するため、親は実装せずユーザー裁定へ返す。

## 1. 段 3 レンズ B 所見の裁定

| 所見 | 判定 | 処置 |
|---|---|---|
| C07 の実体を値セル validator と同一視している | **real / 採用** | §0 のとおり設計を E へ変更。worklog と裁定パッケージに「本 wave は必要条件のみ、C07 は未充足のまま」と明記する |
| DECIDER_VERSION と generation record の scope 外指定が矛盾 | **real / 採用** | E では受理集合を変えないため矛盾自体が消える。bump は不要になる |
| `sd_max=-0.0` の拒否は過剰 | **real / 採用** | `sd_max` は `-0.0` を非負として**受理**する。`delta_min` は `> 0` 判定により `-0.0` を自然に拒否する (符号 bit の特別扱いを書かない) |
| unit/direction を非空文字列だけでは検証できない | **partial / 一部採用** | 固定語彙の強制は **refuted** — 8b §10.2 は語彙を凍結しておらず、勝手な語彙は過剰拒否になる。採るのは「両方が存在し、空白のみでない文字列であること」= 単位と向きの同時固定の構文的担保。実値の意味整合 (judge が引く向きと一致するか) は judge の責務であり scope 外として明記する |
| (P4) の見出し「fail-open」が本文と逆 | **real / 採用** | 用語を fail-closed に統一。E では欄名消失時に `PreregistrationError` を送出せず、**violation として報告**する (欄名集合の変更は §5 欄名 hash が凍結 chain で捕まえる)。加えて validator key が生き doc の欄名集合に実在することを meta-test で pin する |
| 欄消失の reason が ActivationReport から消える | **real だが scope 外** | E は `ActivationReport` を変更しない (digest を変えないため)。違反の可視化は parse 経路と不変検査が担う。report への搭載は裁定パッケージ項目 3 に含める |
| 非有限 reason は現行順序では到達しない | **real / 採用** | `1e309` / `NaN` は既存の `_strict_json` と `_canonical_bytes(allow_nan=False)` が先に落とす。validator 側の有限性検査は**冗長 gate**と明記し (DW-M03)、単独変異の証拠から外す。テストは既存層が落とすことを確認する形で書く |
| M9 の変異 literal が現コードと不一致 (`any` vs `all`) | **real / 採用** | 変異事前登録から M9 を外す (E では `all_filled` を触らないため対象外) |
| 並行 wave の merge 面が衝突する | **real / 採用** | validator table は**単一 dict に entry を並べる形**とし、entry 追加が行単位で衝突しないよう 1 欄 1 行 + 独立関数にする。親は受入直前に main を再取り込みする |
| 親の実測値の一般化には境界がある | **real / 採用** | worklog には「現行 executable pin は無い」「filled fixture の変更点は 1 箇所」「現存する 8c 実測成果物は無い」と限定して書く |
| (P1) exact schema は 8b が凍結していない | **partial** | exact schema は**採用**する (fail-closed 既定、規律 2)。ただし「8b が凍結した制約ではなく 8c 側の表現裁定である」と docstring と worklog に明記し、将来の表現変更は 8c 側の改訂で行うと書く |

## 2. plan v2 — 実装仕様 (段 5 実装子への指示の正本)

編集面は `orchestrator/campaign/s8c_preregistration.py` と
`orchestrator/tests/test_s8c_preregistration_core.py`、
`orchestrator/tests/test_s8c_preregistration_invariant.py` の 3 file だけ。

### 2.1 production 側 (`s8c_preregistration.py`)

1. 新 dataclass `Section5ValueViolation`: `field_name: str`, `path: str`, `code: str` を持つ
   frozen dataclass。`path` は `"H1.n"` のような違反位置。
2. 対象欄名の定数と validator table:
   - `SECTION5_ITERATION_CONTRAST_FIELD = "反復単位対比の判定パラメータ (H1 / H2: n・平均差の下限・差の標本 SD の上限)"`
     (`_normalize_inline` 後の形と exact 一致すること)
   - `_SECTION5_VALUE_VALIDATORS: dict[str, Callable[[Any], tuple[Section5ValueViolation, ...]]]`
     — 1 欄 1 entry。他の 8 欄は entry を持たない (= 検査しない。現行挙動のまま)。
3. `_validate_iteration_contrast_parameters(value)`:
   - root は `type(value) is dict` かつ key 集合が exact `{"H1","H2"}`。違反は
     `root-type` / `root-keys`。
   - 各 block は `type(block) is dict` かつ key 集合が exact
     `{"delta_min","direction","n","sd_max","unit"}`。違反は `block-type` / `block-keys`。
   - `n`: `type(n) is int` (bool を弾くため `isinstance` を使わない) かつ `n >= 2`。
     違反は `n-type` / `n-range`。
   - `delta_min`: `type(v) is int or type(v) is float` かつ `math.isfinite(v)` かつ `v > 0`。
     違反は `delta-min-type` / `delta-min-range`。`-0.0` は `> 0` により range 違反になる。
   - `sd_max`: `type(v) is int or type(v) is float` かつ `math.isfinite(v)` かつ `v >= 0`。
     **`-0.0` は受理する** (8b は有限の非負としか要求していない)。違反は
     `sd-max-type` / `sd-max-range`。
   - `unit` / `direction`: `type(v) is str` かつ `v.strip() != ""`。違反は
     `unit-type` / `unit-empty` / `direction-type` / `direction-empty`。
   - 検査順は root → H1 → H2、block 内は key 名の昇順で決定論的にする。
   - **違反は最初の 1 件で打ち切らず、見つかった順に全件返す** (診断のため)。
4. `_parse_section5` は欄名を validator table へ引き当て、`FILLED` と判定された値だけを
   validator へ渡し、返った violation を集約する。**`FieldStatus` は書き換えない。**
   - 未登録欄は violation ゼロ (現行挙動のまま)。
   - validator table の key が §5 欄名集合に無い場合は、その key について
     `code="validator-field-missing"`、`path=""` の violation を 1 件足す (fail-closed の報告)。
     例外を投げない (parse を落とすと受理集合が変わるため)。
5. `MarkdownContract` に `section5_value_violations: tuple[Section5ValueViolation, ...]` を足す。
   **`ActivationReport` と `Section5Finding` は変更しない** (`_activation_report_digest` は
   `_jsonable(report)` を全 field 走査するため、report を変えると digest が動く)。
6. 公開経路: `parse_preregistration_markdown` / `parse_preregistration_at` /
   `parse_preregistration_worktree` の戻り値経由で到達できること。
   **CLI の subcommand を増やさない** (`test_actual_cli_has_no_approval_or_activation_commands`
   が `{"check","prepare-revision"}` を exact pin している)。
7. `DECIDER_VERSION` は `s8c-decider/v3` のまま。世代 record を作らない。docs を編集しない。
8. subprocess を増やさない (`test_ccbench_spawn_sites.py` が `_git` 1 件を exact pin)。

### 2.2 テスト側

`test_s8c_preregistration_core.py`:

- 正例 (canonical、key 昇順):
  `{"H1":{"delta_min":1,"direction":"on-minus-off","n":2,"sd_max":0,"unit":"ops_per_second"},"H2":{"delta_min":1,"direction":"on-minus-off","n":2,"sd_max":0,"unit":"ops_per_second"}}`
  → violation 0 件、`FieldStatus.FILLED` (既存判定は不変であることも同時に assert)。
- 負例は正例から**1 軸だけ**変える形で、violation の `code` と `path` を exact に assert する:
  root 非 dict / root key 欠落 / root 余剰 key / block 非 dict / block key 欠落 /
  block 余剰 key / `n` が bool / `n` が float / `n` が 1 / `delta_min` が文字列 /
  `delta_min` が 0 / `delta_min` が `-0.0` / `sd_max` が文字列 / `sd_max` が `-1` /
  `unit` が数値 / `unit` が空白のみ / `direction` が list / `direction` が空白のみ。
- **`sd_max` の `-0.0` は受理される**ことを正の対照として書く (過剰拒否の負の対照)。
- 非有限 (`1e309`) と `NaN` は既存層が `INVALID` で落とし violator へ届かないことを、
  現行 reason code (`invalid-json` 等) の exact 一致で書く (冗長 gate の明示)。
- 既存判定が緩んでいないことの対照: 制約違反値でも `FieldStatus` は `FILLED` のままであり、
  placeholder / 空 container / 非 code span の既存 reason code が変わらないこと。
- production 経路: `parse_preregistration_at` (git blob 経由) が violation を返すこと。
- `_markdown(filled=True)` の fixture は**変更しない** (E では FILLED 判定を変えないため
  `{"v":1}` のままで全欄 FILLED が成立する)。既存 16 テストの期待値は 1 つも動かない。

`test_s8c_preregistration_invariant.py`:

- **生き doc の閂**: `parse_preregistration_worktree(ROOT)` の
  `section5_value_violations` が空であることを assert する。これが「違反値を land できない」
  実効的な gate である。
- validator table の key が生き doc の `section5_field_names` に実在することを assert する。
- 現在の当該欄が未記入 (`UNFILLED`) であり violation ゼロであることを併記する
  (恒真でないことを示すため、上の負例群が別途 violation を出すことと対で読む)。
- 新規 test file を作らないため `WAVE_REQUIRED_PATHS` は変更しない。

### 2.3 変異事前登録 (DW-M01。段 6 の fix 後に最終 anchor で再検証してから本走)

E では受理集合を変えないため、変異の多くは **DW-M08 の「diagnostic sensitivity pin」**枠に入る。
kill 判定に使うのは「repo 不変検査が違反値を止める」挙動である。事前登録は次のとおり
(逐語は段 5 の実装確定後に anchor を取り直す)。

| # | 変異位置 | 期待 | 枠 |
|---|---|---|---|
| M1 | validator table を空 dict にする | 生き doc 不変検査 + key 実在 meta-test が赤 | kill |
| M2 | `_parse_section5` から validator 呼び出しを外す | 全 violation テストが赤 | kill |
| M3 | `n` の型検査を `isinstance(n, int)` にする | bool 負例が赤 | kill |
| M4 | `n >= 2` を `n >= 1` にする | `n=1` 負例が赤 | kill |
| M5 | root key の exact 検査を部分集合検査にする | 余剰 key 負例が赤 | kill |
| M6 | block key の exact 検査を落とす | block key 欠落・余剰負例が赤 | kill |
| M7 | `delta_min > 0` を `>= 0` にする | `0` と `-0.0` 負例が赤 | kill |
| M8 | `sd_max >= 0` を `> 0` にする | `-0.0` 受理の正の対照が赤 (過剰拒否の検出) | kill |
| M9 | `unit`/`direction` の空白検査を落とす | 空白のみ負例が赤 | kill |
| M10 | validator key 不在時の violation 生成を落とす | 欄名改変テストが赤 | kill |
| M11 | 有限性検査 (`math.isfinite`) を落とす | **赤にならない見込み** — 既存 canonical 層が mask する | 冗長 gate (単独証拠から外す) |

M11 は DW-M03 に従い冗長 gate と事前に明記する。SURVIVED でも equivalent 扱いにせず、
「前段の canonical 層が同じ入力を拒否している」ことを台帳へ書く。

## 3. 不変条件 (段 5 実装子への禁止事項)

- `docs/**` を編集しない。凍結 record を作らない。`DECIDER_VERSION` を変えない。
- `FieldStatus` の返り値、`_classify_section5_value` の既存分岐順と reason code、
  `ActivationReport` の field 集合、`_activation_report_digest`、CLI subcommand 集合を変えない。
- 既存テストの期待値を 1 つも変えない (E ではその必要がない)。
- テストを甘くしない。負例は 1 軸 1 件で単一理由にする。
- subprocess を増やさない。新規 test file を作らない。

## 4. 成果物影響 (DW-G05)

- 本 wave 単独では certified 選択・レポート・台帳の値は 1 つも変わらない
  (8c は現在も未発効であり、実走成果物は存在しない)。
- 変わるのは repo の受理集合である: **§5 の当該欄に制約違反値を書いた変更が land できなくなる**。
  実装しなければ、8b §10.2 が言う「現在の担保は欄が空であることだけ」の状態が続き、
  当該欄は永久に記入不能のままになる。

## 5. 段 5 の分割

編集面が小さいため Codex author 1 単位 (並列分割なし)。所有パスは上記 3 file。

## 6. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **違反値を判定器の内部で `effective=False` へ倒すか。** 倒すなら (a) 凍結本文
   「欄ごとの型・単位・範囲の検証は本手続きの対象外である」の改訂、(b) `DECIDER_VERSION` の
   v4 bump、(c) 新世代 record の発行、(d) その record が引く D 番号の事前確保、が同時に要る。
   いずれも本 wave の scope 外指定に該当する。
2. **§6 条件 7 を `machine_checkable: true` へ倒し、evaluator が本 validator を消費する形。**
   条件 7 は judge・完全 block・n の exact 一致・3 表も同時に要求するため、単独では充足しない。
   別 wave (`t1352-c07-result-judge` 系) と一体で裁定するのが自然である。
   **この項目は D458 の世代移行を必ず伴う** (段 6 レビュー B の指摘) — 条件 7 を機械検査対象へ
   載せると `all_satisfied` と将来の受理集合が変わるため、`DECIDER_VERSION` の bump、
   新世代 record、その record が引く裁定参照が同時に要る。
3. **違反を `ActivationReport` へ載せるか。** 載せると report digest が動く。現在 capability を
   持つ artifact は存在しないため実害はないが、D458 の「射影された判定入力の意味」に触れる
   可能性があるため、親は裁定なしに実施しない。
