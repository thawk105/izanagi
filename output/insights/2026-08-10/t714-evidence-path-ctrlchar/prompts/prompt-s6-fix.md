あなたは izanagi プロジェクトの dev-wave 段 6 fix 実装子 (Codex `role=author`) である。日本語で報告せよ。

## 読むもの (読めなければ即停止し、その旨だけを出力せよ)

- 段 4 裁定 (scope の正本):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s4-adjudication.md`
- 段 6 レビュー A: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s6-revA.md`
- 段 6 レビュー B: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s6-revB.md`
- 現在の実装: wave worktree の HEAD commit (`git show HEAD`)

cwd は wave worktree、sandbox は workspace-write である。

## 権限境界 (違反したら停止して報告せよ)

- 編集してよいのは次の 4 ファイルだけである。
  - `orchestrator/campaign/s8c_preregistration.py`
  - `orchestrator/campaign/s8c_preregistration_evidence.py`
  - `orchestrator/tests/test_s8c_preregistration_core.py`
  - `orchestrator/tests/test_s8c_preregistration_predicates.py`
- **docs を編集するな。commit・stage するな。** git 状態を変えるな。
- **既存テスト (HEAD に入っている tracked なテスト) の期待値・assert を変更・反転・緩和・skip・
  削除するな。** 赤になったら実装側が誤りである。期待値が誤りだと判断したら、実装を変えずに
  報告して止めよ。
- **production を fail-open へ緩めて辻褄を合わせるな。** テスト側で代役 (fixture・helper・
  test double) を足すのは許す。
- 受理集合を CR/LF 以外で変えるな。NUL・tab・その他制御文字・`./` 正規化・非文字列そのものの
  拒否は**実装しない** (裁定範囲外)。

## 直すもの (3 件。これ以外は直すな)

### F1 (must-fix) — `str` サブクラス経由の guard 迂回

`read_blob_at` は `text` を検査した後、`spec = f"{resolved}:{text}"` を作る。f-string は
`__str__` ではなく **`__format__`** を呼ぶため、`__format__` を上書きした `str` サブクラスは
「検査時は安全な値、git へ渡すときだけ CR/LF 入り」を実現できる。

**不変条件:** 検査した文字そのものが git へ渡る。`__str__` / `__format__` / `__radd__` などを
上書きした `str` サブクラスでも破れない形にせよ。

- 実現手段は任せる。例えば `"".join([...])` は exact `str` を返し、subclass hook を経由しない。
- CR/LF を含まない通常の `str` / `Path` の受理集合と返り値は**変えるな**。
- `__format__` で CR を注入する `str` サブクラスの回帰テストを追加せよ。

### F2 (should-fix) — 単独の埋め込み CR テストが無い

現在の `embedded-cr` parameter の実値は `"\r\n"` であり、単独の埋め込み `"\r"` を検査していない。
「末尾 CR と LF は拒否するが埋め込み CR は通す」退行が現在のテストを全て通ってしまう。

- 単独の埋め込み `"\r"` を独立 case として追加せよ。
- 単独埋め込み CR で git が alias しない (別 blob を返さない) 場合は、alias の主張を無理に置かず、
  **policy として拒否する**ことを固定するテストにせよ。どちらであるかを報告に書け。

### F3 (nit、ついでに直す) — fixture が意図 path の実在を直接確かめていない

埋め込み CR/LF の fixture は、意図した controlled path が実際に tree へ入っていることを
直接確認していない。`git ls-tree -rz` などで candidate path の実在と intended blob を
直接 assert し、fixture が黙って空振りしないようにせよ。

## 直さないもの (裁定済み。手を出すな)

- NUL・tab・その他制御文字の拒否 (裁定 (a) の範囲外)
- 例外 message へ path locator や fingerprint を足す診断強化 (nit、別 wave)
- `_legacy_unframed_blob` の存在自体 (レビュー A/B とも「恒真化していない」と判定済み)
- `./` 正規化、非文字列そのものの拒否

## 検査と報告

- 緑を主張するなら走らせた nodeid と結果を併記せよ。実走できなければ「実装済み・未実走」と書け。
- 所見ごとに `closed` / `partial` / `regressed` の対応表を必ず出せ (F1、F2、F3 の 3 行)。
- 変更ハンク (file:line と意図)、受理集合の差、所有外への波及を報告に含めよ。
- 最後に `## 総括` 節を置き、5 行以内でまとめよ。
