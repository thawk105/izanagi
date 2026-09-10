# 段 1 brief v2 — [T-1302] 非帰属 checker のユーザー裁定 R2 を実効化する

wave `dev-wave-t1302-r2-nonattrib` / 2026-08-17 / base main `699c9cae`

**v2 の位置づけ:** 初版 brief で `DW-O13` (gate 入力の実在) を段 2 前に読んでいなかった。
gate 新設の可能性が段 4 で判明したため、入口の巻き戻し規則に従い段 2 成果物を invalidate し、
`DW-O13` を読了したうえで段 2 からやり直す。本 v2 の「実測」節は**親が一次資料で直接確認した
事実だけ**で構成する。

## scope

ユーザー裁定 R2「確率的なフレークで受入全走を何度も無駄にする構造は全てのセッションに対して
許さない」を end-to-end で発効させる。
scope 内 = `tools/dev_wave_wait.py` の受領証消費述語と outer receipt schema、
`tools/dev_wave_land.py` の受理・結果 JSON、3 test file、`docs/pegasus-runbook.md`、
新 D (D371 / D389 の部分改訂 + 残余の明示受容)。
scope 外 = 裁定 #3 ([T-1283]) のうち待ち手・runner の**全経路**の main 側 blob 束縛
((P7) が flake 経路だけを先取りする)、`tools/check_acceptance_reds.py` の変更。

## 親が一次資料で確認した実測

1. checker は既に第 3 分類 `flake` を出す。実出力
   `output/insights/2026-08-17_t1116-nonattrib-checker/probe2-receipt.json` の node は
   `classification` / `main_rerun_rc` / `nodeid` / `rerun_rc` / `wave_rerun_rc` の 5 field で
   全 rc が 0、status は `non-attributable-only`。
2. 発効を止めているのは consumer。`tools/dev_wave_wait.py:2803-2812` は
   `set(node) == {"classification","nodeid","rerun_rc"}` かつ
   `classification == "non-attributable"` を exact に要求するので、5 field の flake node は
   必ず `_StageFailure` になり受領証が出ない (= 受入全走 1 本が丸ごと捨てられる)。F366 の構図。
3. checker の単独再走 rc は既に `{0,1}` へ限定済み (`tools/check_acceptance_reds.py:1264-1269`)。
   したがって `flake` は「main rc=0 かつ wave rc=0」に論理的に等しい。
   **初版 brief の「rc=2〜5 も flake になる fail-open」は偽である。**
4. land は wave 側 bytes で走る (`_REPO_ROOT = Path(__file__).resolve().parents[1]`、
   `docs/pegasus-runbook.md:1054` の cwd 相対起動、worklog (573) の実測)。
5. `verdict == "non-attributable-only"` の land は
   `tested_main:tools/check_acceptance_reds.py == tested_tip:同` を要求する
   (`tools/dev_wave_land.py:706-745`)。待ち手側にも同じ等値検査がある
   (`tools/dev_wave_wait.py:1975-2013`)。**checker を 1 byte でも変えると本 wave は
   非帰属/flake 受領証で land できない。**
6. **wave tip 側の単独再走は wave の runner が実行する。**
   `_default_node_runner` は `worktree / "tools" / "run_tests.py"` を起動する
   (`tools/check_acceptance_reds.py:956-994`)。rc=1 のときだけ FAILED/ERROR の証明を要求し、
   **rc=0 には対象 node が実行された証明を要求しない**。
   land は tip の runner の**存在**しか見ない (`tools/dev_wave_land.py:700-705`)。
7. outer receipt の runtime consumer は `tools/dev_wave_land.py` の 1 file だが**入口は 2 本**ある。
   land 本検証 (`:608-753`) と release-authority (`_release_authority_digest`, `:575-589`、
   呼出は `:3391`, `:3423`)。両方が共有 exact parser `_receipt_object` (`:562-572`) を通る。
8. `docs/pegasus-runbook.md:878-882` は「台帳へ『全テスト緑』と書く前に receipt の
   `verdict` と `red_nodeids` を読むこと」と指示している。`flake_nodeids` を読ませていない。
9. `dev-wave-acceptance-receipt/v3` の生きた閉包は 4 hit
   (`tools/dev_wave_wait.py:231`、`tools/dev_wave_land.py:70`、
   `orchestrator/tests/test_dev_wave_wait.py:1758`、`:8224`)。ほかに `docs/decisions.md:16631`
   (D393 の記述) と archive / output の履歴。
10. baseline 焦点走 (この worktree、main `699c9cae` と同一 tree):
    `test_check_acceptance_reds.py` 80 passed。
    `test_dev_wave_wait.py` + `test_dev_wave_land.py` は 503 passed / 2 failed。
    赤 2 件は `test_exploration_external_root_keeps_wave_clean` と
    `test_real_git_production_provenance_rejects_malformed_merge_message` で、
    **変更前から赤**であり login ノードで dispatch 経路を叩くことによる環境赤。
11. `check_docs.py` rc=0 (baseline)。`docs/pegasus-runbook.md` は byte 予算の登録対象外。
    `docs/dev-wave/**` に `non-attributable` の出現は 0 件なので、L1/L2 本文追加は生じない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 裁定パッケージ #2 の択 (c)。** flake を通すが `red_nodeids` とは別集合
  (`flake_nodeids`) として outer receipt・land 結果 JSON・台帳へ記録する。
- **(P2) verdict 文字列は `non-attributable-only` のまま**とし、受理条件を
  「`red_nodeids ∪ flake_nodeids` が非空」へ変える。新 verdict 名は足さない。
- **(P3) `tools/check_acceptance_reds.py` は変更しない** (実測 5)。待ち手側の rc 値 pin は
  **現行 producer に対する narrowing ではなく、破損受領証と将来 drift への防御深度**である。
  そのように docs へ書く (恒真ゲートを「守っている」と書かない)。
- **(P4) 非帰属 node は `rerun_rc == 1`、flake node は 3 個の rc すべて `== 0` を exact に pin する。**
- **(P5) 残余は原因を問わず明示受容する。** `flake` は原因の分類ではなく**観測分類**
  (初回全走で赤、main 単独再走が緑、wave tip 単独再走が緑) と定義する。
  受容する残余には production code / `conftest.py` / 共有 fixture / pytest plugin だけでなく、
  test file 自身・`tools/run_tests.py` 以外の選択/build 設定・初回と再走の argv や環境差・
  負荷や外部汚染由来の全走限定赤を含む。**決定的な赤も通りうる**と明記する。
  差分到達可能性の完全な写像が無い限り閉じられない。
  **検査を消して緑を買う形は採らない (規律 2)。**
- **(P6) F366 の恒久対応 (受領証 schema と消費側述語の相互 pin) を本 wave で機械化する。**
  実 checker が出す 3 分類の実 receipt を実 consumer 述語へ通し、accept/reject を実測する。
  synthetic dict だけの pin にしない。期待集合は独立 literal で書き、
  producer AST や consumer helper から生成して循環比較にしない。
- **(P7) flake 経路に限り `tools/run_tests.py` の main/tip blob 等値を要求する** (新 gate)。
  実測 6 のとおり、flake は **wave が制御する runner が出した rc=0 を証拠として受理する初の経路**
  である。窓を開けるのが本 wave である以上、補償も本 wave の責任とする (worklog (573) の先例)。
  [T-1283] のユーザー裁定 (択 (a)、待ち手と runner も main 側 blob へ束縛する) と同方向の
  部分実装であり、受理集合を**狭める**変更なので規律 2 に整合する。
  適用は「`flake_nodeids` が非空のとき」に限り、child-green と red-only の受理集合は変えない。
  **`DW-O13` の gate 入力実在確認:** 入力は `{tested_main,tested_tip}:tools/run_tests.py` の
  blob sha。待ち手には revision 引数付きの `_red_gate_blob_sha` が既にあり
  (`tools/dev_wave_wait.py:1950-2012`)、land は既に `tested_tip:tools/run_tests.py` を
  git で解決している (`:700-705`)。**新しい識別子も新しい receipt field も導入しない**
  (両者とも git から直接再計算する) ので、同名識別子の二義化は生じない (D75)。
- **(P8) release-authority 経路 (`_release_authority_digest`) も v4 で通ることを test で pin する。**
- **(P9) `docs/pegasus-runbook.md:878-882` の台帳記録指示に `flake_nodeids` を足す。**
  受理した残余が段 7 の台帳まで届く経路を文書で閉じる。

## 不変条件 (緩めない)

- 受理集合が広がるのは「main 単独緑 かつ wave tip 単独緑」の node に限る。
  attributable (main 緑・wave 赤) は従来どおり checker rc=1 で停止。
- D389 の 3 条件 (`child_rc == 1` ちょうど、checker rc=0 かつ status、`log_sha256` 一致) と
  checker blob の main/tip 等値は 1 つも緩めない。bypass flag / 環境変数を作らない。
- outer receipt の field 集合と land の受理述語は同じ差分で変え、schema を v4 へ bump する。
  v3 fallback を作らない。
- `red_nodeids` と `flake_nodeids` は各々 sorted・unique、互いに素を producer と consumer の
  両方で検査する。
- 履歴・台帳・file 数に比例するコストをテスト経路へ入れない。

## 成果物影響 (DW-G05)

実装しないと flake 1 件で受入全走 1 本 (1055〜1273 秒 + queue 待ち) が捨てられ続け、R2 は
発効しない。`flake_nodeids` を別集合にしないと、証拠なしで通した残余がどの nodeid だったかを
受領証・land 結果・台帳のどこからも追跡できない。(P7) を入れないと、wave 側 runner が
「対象 node を走らせずに rc=0 を返す」だけで任意の赤を flake として land できる。

## 成果物の形

- 実装差分: `tools/dev_wave_wait.py`、`tools/dev_wave_land.py` (Codex author が書く)。
- テスト: `orchestrator/tests/test_dev_wave_wait.py`、`test_dev_wave_land.py`、
  `test_check_acceptance_reds.py`。
- docs: `docs/pegasus-runbook.md`、spool decisions fragment (新 D)、spool worklog fragment。

## 分割方針

exact 述語が producer/consumer で相互に絡むため実装は**単一の Codex author 子**。
段 3 の敵対相談は 2 lane、段 6 のレビューは 2 lane。
