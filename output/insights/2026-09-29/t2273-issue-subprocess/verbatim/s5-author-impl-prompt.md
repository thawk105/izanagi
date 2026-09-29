単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

作業木 (あなたが書いてよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl
所有 path (これ以外を編集しない): `orchestrator/campaign/s8b_holdout_freeze.py`、`orchestrator/tests/test_s8b_holdout_freeze.py`。
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s4-ruling.md — 親の段 4 裁定。**「plan v2」1〜5 が仕様の正本、「変異の事前登録」M1〜M6 が test の検出対象。**
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md — 段 2 plan (段 4 で MAXREPEAT の分岐・test は不採用にした。それ以外は plan v2 と矛盾しない範囲で参考)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s3-consult-a-out.md — 反例・境界・番人の指摘 (fixture の作り方の根拠)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/D512-D513.md、D350-D351.md、F264.md — 既裁定の逐語。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/pin-closure.md — 既存 test の一覧と source guard。
- 作業木の orchestrator/campaign/s8b_holdout_freeze.py (417〜700 行) と orchestrator/tests/test_s8b_holdout_freeze.py (380〜1200 行)。

## 目的

受入 shard-0 の律速 (T-080 発行 child の CPU の 99 % が `search_repository`、うち `_scan_one` の正規表現 search 行 54 %・共通 literal の `in` 行 19 %) を、report の canonical bytes を 1 bit も変えない係数削減で縮める。仕様は s4-ruling.md の plan v2 のとおり。

## 変える前の受理・拒否挙動 (保つもの)

- `search_repository` の列挙・正規化・open・read・decode・免除・例外の型と文言・report の全 field と canonical bytes は現行のまま。`_scan_one` の戻り値も現行と同一。
- 共通 literal だけを含み軸 literal を含まない text は regex に進まない。`_derive_required_literal` が None を返す式・非 exact `str` の式・str subclass の text の扱い (前置判定なしの全文 search) は現行のまま。
- `_ScanMemo` の identity 束縛と内容変化の fail-closed 拒否は現行のまま (新しい memo 内容はその検査の後でだけ再利用する)。memo は 1 回の `search_repository` に閉じる。
- 受理集合を変えない (規律 2)。production に最適化の無効化 knob・環境変数・新しい gate を足さない。

## 作ること

1. plan v2 の 1・2 を `orchestrator/campaign/s8b_holdout_freeze.py` に実装する (module private helper 2 つ: 共通判定 helper と局所化 search helper。名前は任意だが test から monkeypatch で差し替え・計数できる module 属性にする)。**ソースに軸 key と具体値を連続した literal として書かない** (repo 全文走査の自己汚染。現行の `"ycsb_" + "rratio"` のような分割を踏襲)。
2. plan v2 の 3・4 を `orchestrator/tests/test_s8b_holdout_freeze.py` に実装する。test の fixture 文字列にも実軸の key と具体値を連続で書かない (合成 key を使うか、既存 helper `concrete_axis_encodings` 等で実行時生成)。既存の番人は数える単位を「候補数」に移すだけで、数値 (5 / 0・5・9 / reference 3 回 / 導出 12 回 / memo hit 0 回) と意味を保つ。
3. 変異 M1〜M6 (s4-ruling.md) のそれぞれが、登録した番人で**単一理由で**赤になることを、作業木で一時的に変異を当てて該当 test を走らせて確かめ、必ず元に戻す (戻した後 `git diff` が意図した変更だけであることを確認)。P0 (docstring 1 語) が全緑であることも確かめる。結果は変異ごとに「赤になった nodeid と assert 行」を報告する。

## 検査 (実走したものは nodeid・範囲・件数を書く)

- 走らせ方: `tools/run_tests.py` と `python3 -m pytest` は使わない (sandbox で dispatch できない・guard が拒否する)。作業木の root で
  `PYTHONPATH=. python3 orchestrator/tests/test_s8b_holdout_freeze.py` (自走 harness) か、それが 0 件収集になる file では
  `PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['<file>','-q','-rf']))"` を使う。
  それも走らないなら、最低限 test module を import して対象 test 関数を直接呼び (`tmp_path` は `tempfile.mkdtemp()`、`monkeypatch` は `pytest.MonkeyPatch()` で代用)、fixture が成立することと、対象の最適化を実行時に外すと期待どおり赤になることを確かめる。
- まず `orchestrator/tests/test_s8b_holdout_freeze.py` 全体。
- `_scan_one`・`search_repository`・`_ScanMemo`・`_derive_required_literal` を使う他の test file を grep で洗い出し、あなたの sandbox で走らせられる範囲で走らせる (例: test_s8b_ratified_freeze.py、test_s8b_oracle_driver.py の holdout 関連 node、test_s8c_preregistration_invariant.py の非 hold node)。重くて走らせられないものは「実装済み・未実走」と書き、親が計算ノードで走らせる。
- test の新設・改名に伴う制約 meta-test (test file 列挙・node 数・所要台帳 `acceptance_duration_ledger.json`・real-repo access 登録など) を自分で洗い出し、要るなら所有 path の範囲で対応し、所有外の変更が要るなら変更せず報告する (F42)。
- 期待値に tree hash 等の揮発値を焼き込まない。test を甘くして緑にしない。依存先 (`re`・`_reference_scan_one`) を stub で置き換えて機構を通らない緑にしない。
- 自己汚染: 作業木で `python3 -c` を使い `s8b_holdout_freeze.search_repository(<作業木 root>, files=[変更 2 file])` の holdout conjunction が空であることを確かめる。

## 報告

見出し「## 実装」「## test」「## 変異の確認」「## 実走」「## 波及 (所有外 caller・共有 fixture・consumer test の静的列挙)」「## 未実走・懸念」「## 総括」。各項目に file:line。緑には実走 nodeid・範囲を併記し、走らせていないものを緑と書かない。「## 総括」は 5 行以内。
