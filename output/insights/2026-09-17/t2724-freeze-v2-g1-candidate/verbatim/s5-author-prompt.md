単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-v2-g1-candidate/s4-adjudication-addendum.md` — 親の裁定 (must-fix C-1、変更面、変異事前登録 M0〜M5)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-v2-g1-candidate/rv-d2077-d2078.txt` — D2077 / D2078 の逐語 (背景)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/campaign/s8b_holdout_freeze.py` — 約 97 KB / 2,270 行。編集対象。読むのは import 部 (10〜62)、`_run_git` / `_blob_at_head` (293〜340)、`_validate_floor_inputs` (1375〜1665)、`_measurement_closure` (1978〜2010)、`build_v2_g1_candidate` (2026〜2112) だけでよい
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/campaign/s8b_floor_campaign.py` — 約 300 KB。読むのは `IndexedFloorProtocol` (688〜705)、`_scan_floor_protocol_index_at_commit` (910〜1000)、`resolve_current_floor_protocol` (1032〜1075)、`_head_blob_100644` (grep で位置を出す) だけでよい。**編集しない**
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/campaign/s8b_holdout_admission.py` — 読むのは `_head_blob` (759〜785) と `_authority` (810〜870) だけでよい。**編集しない**
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/tests/s8b_v2_freeze_fixture.py` — 編集対象。`candidate_repository` (738〜920) を中心に読む
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/tests/test_s8b_holdout_freeze.py` — 編集対象。読むのは `test_v2_candidate_rejects_worktree_only_floor_protocol_master_seed_mutation` (1810〜1836)、`test_v2_candidate_build_and_generate_synthetic_g1` (1838〜1900)、末尾の `enforce_held_functions` (pytest 専用 file であること) だけでよい
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/tests/test_s8b_protocol_builder.py` — 読むのは `test_floor_protocol_historical_anchors_remain_legacy` (1228〜1249) だけ。**編集しない**

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl` とする。**大きい file を全文 `cat` しない。** `grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む。

## 背景 (親の実測)

freeze v2 g1 candidate の producer `s8b_holdout_freeze.py generate-v2-candidate` は、official 床値 result (protocol_sha256 = `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`、path の proto8 `2c8cf9be`) に対し `fails-closed: floor result.protocol_sha256 が固定 protocol hash と不一致` で止まる。producer は `FLOOR_PROTOCOL_REL` (= `output/s8b-freeze/floor_protocol.json`、ccbench_pin `d706650c…`、canonical sha `261cec1c…`) を literal で読むが、official 走行は index authority (`s8b_floor_campaign.resolve_current_floor_protocol`) が解決した版付き protocol `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json` (ccbench_pin `511c9538…` = HEAD の gitlink) を使った。2 文書の差は `ccbench_pin` 1 行。解決器は固定 path を anchor として index に含め、同一契約の候補が複数なら HEAD の ccbench gitlink と exact 一致する 1 件を返す (`resolve_current_floor_protocol` 1032〜1075)。admission 側 `_authority` (810〜870) も同じ解決器を使い、producer が渡す `protocol` 文書と解決 record の bytes 一致を要求する (851〜856)。

設計方向は既裁定 (D460: caller に選ばせず index authority で解決。D589: この箇所を D460 型変換の対象と名指しし、発火条件が揃うまで deferred)。

## 仕事 (所有 path のみ)

所有: `orchestrator/campaign/s8b_holdout_freeze.py`、`orchestrator/tests/s8b_v2_freeze_fixture.py`、`orchestrator/tests/test_s8b_holdout_freeze.py`。これ以外の file を編集しない。docs を編集しない。commit しない。

1. **`_validate_floor_inputs` の protocol 取得を index authority 経由へ置換する。**
   - `s8b_floor_campaign` は module 先頭で `s8b_holdout_freeze` を import している (循環) ので、`_validate_floor_inputs` 内の既存 local import 群と同じ場所で `from . import s8b_floor_campaign as _floor_campaign` する。
   - `record = _floor_campaign.resolve_current_floor_protocol(root=root)`。`FloorCampaignError` は `FreezeError("floor protocol を index authority で解決できない: …")` に包む。
   - `record.commit_oid == head` (captured HEAD) を要求し、`record.path` の worktree bytes (`_capture_regular_nofollow`) と `_blob_at_head(head, record.path, root)` の一致を要求する (既存の「floor protocol が captured HEAD と worktree で不一致」の文言と reason は**そのまま残す** — 既存 test が match する)。`record.raw_bytes` とも一致を要求する。
   - 以後の `validate_protocol` / `canonical_protocol_sha256` / raw==canonical / `protocol.freeze` 固定検査 / result との `protocol_sha256` 比較 / `proto8` 比較 / header field 比較は**変えない**。
   - 返り値 tuple に protocol の相対 path (`record.path`) を足し、`build_v2_g1_candidate` の `document["floor_protocol"]` を `{"path": <record.path>, "sha256": sha256(protocol_raw)}` にする。
   - `_measurement_closure` の専用 path 集合に解決 path を足す (引数で渡す)。`FLOOR_PROTOCOL_REL` の定数と代入行は**削らない** (`test_floor_protocol_historical_anchors_remain_legacy` が `^FLOOR_PROTOCOL_REL = "…"$` を exact 1 件で pin する)。専用集合に `FLOOR_PROTOCOL_REL` も残してよい。
   - 新しい subprocess 起動点を作らない (`test_ccbench_spawn_sites.py` が `_run_git` / `_run_git_bytes` / `_run_git_z` を各 1 件で台帳固定)。`_validate_floor_inputs` 内の `use_perf_from_receipt` / `result_keys_for_mode` / `validate_manifest_v3` の呼出しは残す (`test_official_perf_closure.py` の AST 述語)。
   - docstring / comment に「D460 型: caller に選ばせず index authority で解決する。固定 path は index の anchor として残る」を 1〜2 行で書く。三軸の値を書かない。

2. **fixture に版付き protocol の option を足す。** `candidate_repository(...)` に keyword (例 `versioned_protocol: bool = False`) を足し、True のとき (a) 固定 `FLOOR_PROTOCOL_REL` はそのまま置き、(b) その protocol の `ccbench_pin` を fixture ccbench repo の HEAD commit sha に替えた版付き文書を `s8b_floor_campaign._derived_reseal_protocol_relpath(contract_sha256, ccbench_pin)` の path へ canonical bytes で置き、(c) 親 repo の gitlink (`external/ccbench`) がその commit を指す状態で commit し、(d) result / manifest / journal / launch certificate / admission evidence は**版付き protocol** で作る (run_dir の proto8 も版付きの canonical sha)。既存呼出し (既定 False) の挙動は 1 bit も変えない。fixture の ccbench が nested `git init` repo であることを利用する (gitlink は `git add external/ccbench` で入る。`_scan_floor_protocol_index_at_commit` が要求する commit 済み条件を満たす)。

3. **test を足す (`test_s8b_holdout_freeze.py`)。**
   - 正例: `versioned_protocol=True` で `build_v2_g1_candidate` が成功し、`document["floor_protocol"] == {"path": <版付き path>, "sha256": <版付き raw sha>}`、`document["floor_source"]["path"]` の proto8 == 版付き canonical sha[:8]、`generate_v2_g1_candidate` が固定 candidate path へ書く。
   - 負例 1: `versioned_protocol=True` の fixture で result の `protocol_sha256` を固定 protocol の canonical sha に書き換えると `floor result.protocol_sha256 が固定 protocol hash と不一致` で拒否 (現行の拒否文言は変えない。必要なら文言の「固定」を「解決した」に改めてよいが、その場合は既存 test の match も同時に直す)。
   - 負例 2: `versioned_protocol=True` で版付き protocol の worktree bytes だけを変える (canonical を保つ改変ではなく、master_seed を変えて再 canonical 化) と `floor protocol が captured HEAD と worktree で不一致` で拒否。既存 `test_v2_candidate_rejects_worktree_only_floor_protocol_master_seed_mutation` は固定 path 1 件の fixture で同じ経路を通るので残す。
   - 既存の test の期待値を変えない (F27)。fixture への現行 hash 差し込みで緑にしない。期待値に揮発 payload を焼き込まない。

4. **変異事前登録 M0〜M5 (addendum の表) の単一理由性を実装後に確認する。** 各変異について「どの test のどの assert が最初に赤になるか」と「同じ入力を拒否する層が前後・内側に無いか」を書く。殺せない登録は理由を書いて再照準案を出す (親が登録し直す)。

## 検査

- 焦点走: `PYTHONPATH=. python3 -m pytest -q orchestrator/tests/test_s8b_holdout_freeze.py orchestrator/tests/test_s8b_protocol_builder.py -k "protocol or v2_candidate or historical_anchors" -p no:cacheprovider`。全体: `PYTHONPATH=. python3 -m pytest -q orchestrator/tests/test_s8b_holdout_freeze.py -p no:cacheprovider`。pytest が sandbox で起動できなければ `python3 -c "import pytest,sys; sys.exit(pytest.main([...]))"` を試し、それも不可なら「実装済み・未実走」と書く (走らせていない結果を緑と書かない)。
- 緑には実走 nodeid と件数を併記する。子の実走は親の全走を代替しない。
- 所有外 caller・共有 fixture・consumer test の波及可能性を静的に列挙する (`candidate_repository` の呼び手、`_validate_floor_inputs` の呼び手、`FLOOR_PROTOCOL_REL` を読む test)。
- 指示外の受理集合変更をしない。scope 前の受理・拒否挙動 (固定 protocol と一致する result だけ受理) と、scope 後 (index authority が解決した現行 protocol と一致する result だけ受理) を報告に明記する。
- 親 docs は未 land だが、それに依存して赤になる test は無い見込み。赤が出たら回帰として nodeid と本文を報告する。

## 禁止

- 所有外 file の編集、docs 編集、commit、`git` の状態変更 (add は可)。
- 走査除外 (`EXCLUDED_PATHS`)・freeze allowlist・admission・批准側 (`s8b_ratified_freeze.py`)・campaign 側 (`s8b_floor_campaign.py`) の変更。
- `output/s8b-freeze/` 配下・`output/` 配下の実 artifact への書込み (tmp fixture だけを使う)。
- 三軸の値 (holdout の workload 定義) を source・test・報告に逐語で書かない。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## 変更点 (file:line と要旨)
## 受理集合の前後
## 実走した検査と結果 (nodeid・件数・rc)
## 変異 M0〜M5 の単一理由性
## 波及の静的列挙
## 未実装・未実走・懸念
## 総括
