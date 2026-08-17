# 段 4 裁定 — [T-1302] R2 実効化 (plan v2 + レンズ A/B の裁定)

wave `dev-wave-t1302-r2-nonattrib` / 2026-08-17 / 親裁定

裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox`) を段 4 直前に再走査した。
最新 2026-08-17 分を含め、[T-1302] に関する新しいユーザー裁定は無い。
本 wave のユーザー裁定は依頼文の「残余を明示受容する形にする / 検査を消して緑を買う形は採らない」である。

---

## 所見の裁定

| # | 所見 | 判定 | 措置 |
|---|---|---|---|
| A1 | P7 を `flake_nodeids` 非空で条件分岐させると、flake を red と偽った crafted receipt が gate を素通りする | **real** | **採用・設計変更**: P7 を `verdict == "non-attributable-only"` 全体へ無条件化する (下記 R-1) |
| A2 | 同じ runner blob でも main と tip の挙動は import 閉包・cwd・環境で異なりうる。gate の保証は狭い | **real** | **採用 (docs)**: 保証範囲を D と runbook へ正確に書く。「wave-controlled runner を束縛した」とは書かない。PASSED 証明 plugin は新機構なので**実装しない** (次の一手へ起票) |
| A3 | P5 は決定的な全走限定赤まで受容しており、[T-1278]「走行形で結果が変わるテストは正しさシグナルに使えない」と緊張する | **real (緊張は実在)** | **受容を維持**。代案「同一 tip で full-suite を再走し緑なら flake」は受入全走をもう 1 本消費し、R2 の目的 (窓を捨てない) と正面から矛盾するため**不採用**。緊張は D 本文とユーザー報告へ明記する |
| A4 | 「flake が wave 側 runner の rc=0 を証拠にする初の経路」は偽。child-green が既にそうである | **real (brief v2 の (P7) 根拠が誤り)** | **採用・根拠差し替え**: P7 は「本 wave が開ける窓の補償」ではなく、**既にユーザー裁定済みの [T-1283] (択 (a)) を `non-attributable-only` 経路へ部分実装する防御深度**と位置づける |
| A5 | 正当に runner を変えた wave は、受入全走と全再走を終えた後に高価に拒否される | **real** | **採用 (docs)**: runbook に「`tools/run_tests.py` を変更した wave は非帰属受理を使えない (完全緑で通す前提で計画せよ)」を明記。早期停止は child-green を巻き込むため**実装しない** |
| A6 | rc pin 以外の述語 (和集合非空・sorted/unique/disjoint・node exact field) も現 producer には発火しない | **real** | **採用 (docs)**: 新 D に述語ごとの表を置き「現 producer narrowing / crafted・drift 防御深度 / 将来 wave narrowing」を分離する |
| A7 | schema v3 を決めた D393 を明示改訂しないと、v3 と v4 の 2 正本が残る | **real** | **採用**: 新 D で D393 の schema 値部分を明示的に supersede する |
| B1 | 影響 helper (`_checker_receipt_bytes` / `_queue_checker` / `_red_check`) と全 `LandResult(...)` 呼出しの列挙が不足 | **real** | **採用**: 実装子 prompt の必須更新一覧へ入れる。`LandResult` の新 field は既定値付きにして全 call site の破壊を避ける |
| B2 | 相互 pin は producer と consumer が helper を共有すると偽緑 | **real** | **採用**: 実 producer が書いた bytes を `json.loads` して実 consumer 述語へ渡す。期待値は独立 literal |
| B3 | P7 は request の `tested_main` / `tested_tip` を使わないと merge 後に空洞化する | **real** | **採用**: 現在の `main` / `HEAD` を使わない。既存 checker blob 検査と同じ revision を使う |
| B4 | 40 桁 SHA だけでは runner が blob である証明にならない | **real** | **採用**: `cat-file -t` で `blob` を確認してから SHA を比較する (checker 側は既存契約のまま触らない) |
| B5 | red-only の受理集合を P7 で狭めないことを固定すべき | **refuted (A1 により方針反転)** | P7 は無条件化するので、red-only で runner blob が異なる受領証は**拒否**が正しい。過剰拒否の正例は child-green 側で登録する |
| B6 | fragment と runbook は同じ commit に入れ、`check_docs` と `spool_fold --dry-run` を両方通す | **real** | **採用** |
| B7 | 未実施の受入結果を fragment へ先に書くのは偽の完了 | **real** | **採用**: 実測後に fragment 本文を確定する |
| B8 | `base:` は land 時点で carry 解決後の実体から再計算する | **real** | **採用**: 段 7 で `spool_fold._task_item_digest` 相当の規則で算出し、受入直前に dry-run で確認 |
| B9 | 追加テストは固定 fixture に限り、履歴比例コストを持ち込まない | **real** | **採用** |
| B10 | 段 6〜9 の手順 (焦点走・docs commit 後の受入・同一 bytes での land・lock 内 fold) | **real** | **採用** |

---

## 確定した設計 (plan v2 からの差分)

- **R-1 (A1・A4・B5 由来):** P7 を **`verdict == "non-attributable-only"` の全受領証**に対して無条件で
  適用する。`flake_nodeids` の値で条件分岐しない。
  待ち手と land の両方で `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` の
  **object type が `blob`** であることを確認し、blob SHA の等値を要求する。
  child-green の受理集合は変えない。
- **R-2 (B3):** revision は request の `tested_main` / `tested_tip` を使う。現在の `main` / `HEAD` を使わない。
- **R-3 (B1):** `LandResult.acceptance_flake_nodeids` は既定値 `None` を持つ keyword field とし、
  既存の `LandResult(...)` 全 call site を壊さない。
- **R-4 (A2・A6):** docs は保証範囲を正確に書く。「blob 等値は同一 bytes の runner が両側で使われた
  ことだけを保証し、import 閉包・cwd・環境・pytest 選択の同一性は保証しない」と明記する。
- **R-5 (A7):** 新 D は D371・D389 に加えて **D393 の schema 値**も明示改訂する。

## gate の署名 (DW-S04)

**禁止 (署名):**

1. `verdict == "non-attributable-only"` かつ
   `blob(tested_main:tools/run_tests.py) != blob(tested_tip:tools/run_tests.py)` → 受領証を発行しない / land しない。
2. `verdict == "non-attributable-only"` かつ `type(tested_*:tools/run_tests.py) != "blob"` → 同上。
3. checker receipt の node が
   `{classification=non-attributable, nodeid, rerun_rc}` (rerun_rc==1) でも
   `{classification=flake, main_rerun_rc, nodeid, rerun_rc, wave_rerun_rc}` (3 rc すべて 0) でもない → `_StageFailure`。
4. `red_nodeids` と `flake_nodeids` が各々 sorted・unique でない、または互いに素でない → 拒否。
5. `verdict == "non-attributable-only"` かつ `red_nodeids ∪ flake_nodeids` が空 → 拒否。
6. `verdict == "child-green"` かつ `red_nodeids` または `flake_nodeids` が非空 → 拒否。
7. outer receipt の schema が `dev-wave-acceptance-receipt/v4` でない、または field 集合が exact でない → 拒否。

**通る正例 (承認外の過剰拒否を検出する):**

- 正例 1: `verdict == "child-green"`、両集合空、`tested_main` と `tested_tip` の
  `tools/run_tests.py` blob が**異なる** → **受理される**。
- 正例 2: `verdict == "non-attributable-only"`、runner blob と checker blob が両側同一、
  非帰属 node 1 件 (`rerun_rc == 1`) + flake node 1 件 (3 rc すべて 0)、
  2 集合が互いに素 → **受理され、`red_nodeids` と `flake_nodeids` に別々に出る**。

## 変異事前登録 (DW-M01)

| ID | 位置 | 変異 | 期待される赤 (単一理由) |
|---|---|---|---|
| M1 | 待ち手 node 述語 (flake 枝) | 5 field exact を落とす | crafted 6 field flake payload が受理される |
| M2 | 待ち手 node 述語 (flake 枝) | 3 rc == 0 の 1 つを落とす | `wave_rerun_rc == 1` の crafted node が flake として受理される |
| M3 | 待ち手 node 述語 (非帰属枝) | `rerun_rc == 1` pin を落とす | `rerun_rc == 0` の crafted 非帰属 node が受理される |
| M4 | 待ち手・land の disjoint 検査 | 互いに素の検査を落とす | 同一 nodeid が両集合にある receipt が受理される |
| M5 | 待ち手 verdict 条件 | 和集合でなく `red_nodeids` だけを見る | flake-only の正当な受領証が拒否される (過剰拒否 kill) |
| M6 | 待ち手 P7 | runner blob 等値検査を落とす | runner blob が異なる非帰属走で受領証が発行される |
| M7 | land P7 | `tested_main` の代わりに現在の `main` を使う | merge 済み main で gate が空洞化し crafted receipt が land する |
| M8 | land P7 | object type 検査を落とす | `tools/run_tests.py` が blob でない fixture で受理される |
| M9 | land exact field 集合 | `flake_nodeids` を任意にする (v3 fallback) | v3 receipt が land される |
| M10 | land 結果伝搬 | `LandResult.as_json()` から `acceptance_flake_nodeids` を落とす | 受理した flake が結果 JSON に残らない |

正例 (過剰拒否検出) は上記「通る正例 1・2」を変異走でも走らせる。

## 実装しない (scope 外・次の一手へ)

- 単独再走 rc=0 に「対象 node が call phase まで実行され PASSED した」証明を要求する仕組み (A2)。
  → 新機構であり `DW-G02` / `DW-G04` に従い設計メモに留める。[T-1283] 族として起票する。
- 待ち手・runner の**全経路** (child-green を含む) の main 側 blob 束縛 ([T-1283] 本体)。
- `tools/check_acceptance_reds.py` の変更。
- 初回全走と単独再走の argv・環境・scheduler の同形化 (A2)。→ 起票。
