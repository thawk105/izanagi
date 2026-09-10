あなたは izanagi プロジェクトの dev-wave 段 5 実装子 (Codex `role=author`) である。日本語で報告せよ。

## 読むもの (読めなければ即停止し、その旨だけを出力せよ)

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/brief.md`
- 段 2 プラン: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s2-plan.md`
- **段 4 裁定 (これが正本。プランと食い違う箇所は裁定が勝つ):**
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s4-adjudication.md`

cwd は wave worktree (`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar`)、
sandbox は workspace-write である。repo の外へは書けない。

## 権限境界 (違反したら停止して報告せよ)

- 編集してよいのは次の 4 ファイルだけである。
  - `orchestrator/campaign/s8c_preregistration.py`
  - `orchestrator/campaign/s8c_preregistration_evidence.py`
  - `orchestrator/tests/test_s8c_preregistration_core.py`
  - `orchestrator/tests/test_s8c_preregistration_predicates.py`
- **docs を編集するな。commit するな。** git 状態を変えるな (`git add` / `git commit` / `git stash` 禁止)。
- 契約 JSON、freeze record、prereg markdown、他のテスト、他の module を編集するな。
- **既存テストの期待値・assert を変更・反転・緩和・skip・削除するな。** 既存テストが赤になったら、
  実装側が誤りである。期待値が誤りだと判断した場合は、実装を変えずに報告して止めよ。
- **production を fail-open へ緩めて辻褄を合わせるな。**

## 実装すること

段 4 裁定「plan v2」の 1〜5 と、段 2 プランの編集ハンク 1〜4、テスト計画、
変異事前登録 M01〜M14 が殺せる形を実装せよ。要点だけ再掲する。

1. `read_blob_at` — git へ渡す値を一度だけ文字列化し、**その同じ値**に CR/LF 検査を掛けてから
   spec を組む。reason は `path-control-char`。例外 message に生 path を入れない。
2. `_safe_path` — `_nonempty_string` の**呼出しより前**に CR/LF を明示拒否する。
   reason は `contract-path-control-char`。`_nonempty_string` 自体は変更しない
   (path 以外の field まで拒否が広がるため)。
3. テスト — 段 2 プランのテスト計画に、裁定 plan v2 の 2 (埋め込み CR/LF は
   「guard 不在なら**別 path の blob が返る**」ことを実証する fixture) を反映する。
   正常 path の正例を core / loader の両方に置く (M13/M14 の検出器になる)。
   末尾 CR/LF のテストは、既存の付随的拒否 (`_nonempty_string` の `value != value.strip()`) では
   なく**新しい明示検査**が発火していることを reason で区別できる形にする。
   埋め込みケースでは `candidate == candidate.strip()` を事前 assert し、付随的拒否では
   通らないことを固定する。
4. **受理集合を CR/LF 以外で変えるな。** NUL・tab・その他制御文字・`./` 正規化・非文字列拒否は
   **実装しない** (裁定範囲外)。現行の受理・拒否挙動を変更前に確認し、報告に書け。

## 検査と報告 (すべて満たすこと)

- 緑を主張するなら、走らせた nodeid と範囲を併記せよ。実走できなければ「実装済み・未実走」と書け。
  子の実走は親の全走を代替しない。
- テストを新設・改名したので、それを制約する meta-test も走らせよ。
- fixture へ現行 hash を差し込む等、テストを甘くして緑にするな。
- 期待値に working tree の hash など揮発する診断 payload を焼き込むな。
- 完了報告に次を必ず含めよ。
  - 変更ハンクの一覧 (file:line と意図)
  - **`read_blob_at` / `_safe_path` の caller 閉包**。`campaign.*` と `orchestrator.campaign.*` の
    両 namespace、`load_contract_bytes` / `semantic_contract_sha256` / module 直下の公開経路を
    含めて列挙し、新拒否が発火しうる経路と発火しない根拠を書け。
  - 所有外の caller、共有 fixture、consumer test への波及可能性の静的列挙
  - 変更前後の受理・拒否挙動の差 (CR/LF 以外が変わっていないことの根拠)
  - 走らせた pytest の nodeid と結果 (rc、passed/failed 件数)

## 出力形式

Markdown。最後に `## 総括` 節を置き、5 行以内でまとめよ。
