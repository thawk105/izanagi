# 親 brief v2 — F37 の機械強制化 (land 関門) + DW-S01 への既存被覆検索の追加

**v1 (`parent-brief.md`) は invalidate 済み。流用禁止。** 段 1 の途中で `DW-STOP` の
「承認済み裁定の前提を覆す未見の新事実」が 2 件入ったため段 1 を再実行した (経緯は handoff)。

base commit `bcda1c02` / branch `worktree-dev-wave-t139-provenance-known-violation`
worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation`

## scope (確定済みユーザー裁定)

正本: `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-09-t659-provenance-and-f37-rulings.md`
(2026-08-09 ユーザー発話「推奨通りで」) の**項目 2 と項目 4**。

- **W1 (裁定 2)**: `tools/dev_wave_land.py` が provenance 検査を**自ら走らせて rc を確認**し、
  既知違反以外の赤があれば land を拒否する。「検査 rc をパイプへ通せない形」への移行 = F37 の機械強制化。
- **W2 (裁定 4)**: 「書く前に既存被覆を検索する」を前提実測の手順へ足す
  (置き場は `docs/dev-wave/core.md` の `DW-S01`)。docs のみ、親が書く。

### scope 外 (並行 wave が所有)

`tools/check_ai_provenance.py` への known-violation 登録 (`2c192953` 1 件 + [T-139] 22 件) と
probe の `.md` 逐語移行は、**ユーザーが 08:43 に起動した並行 wave**
(branch `worktree-dev-wave-t682-provenance-known-violations`) が所有する。**本 wave は
`tools/check_ai_provenance.py` を 1 byte も触らない。** 親のユーザー指示「重複を避けよ」に従った
分割で、相手へ通知済み。

## 実測 (段 1 で取得。裁定の前提を覆す事実はない)

- `python3 tools/check_ai_provenance.py` → **rc=1 / 1947 件中 23 新規違反**、所要 **38.3 秒**
  (`prov-baseline.txt`、rc は単独取得)。23 件はすべて上記並行 wave が登録する対象。
- `python3 tools/check_docs.py` → **rc=0**。`docs/dev-wave/core.md` は 8655 / 予算 9600 bytes
  (余白 945)。W2 の追記はこの余白に収める。**予算値は上げない。**
- **既存被覆 (性質での検索)**: `dev_wave_land.py` は既に子検査を
  `subprocess.run([sys.executable, checker, ...], shell=False)` + `returncode != 0` で判定する型を
  2 本持つ — `_validate_generated_docs` (:1363、`check_docs.py`) と
  `_preflight_fold_message` (:1387、`check_ai_provenance.py --message-file`)。
  **shell を介さないので rc は構造的に pipe へ乗らない。W1 はこの型の 3 本目である。**
  一方 **全史 provenance 監査の自走は存在しない** → W1 の純増検出力は 100%。
- `hooks/`・`tools/`・`orchestrator/tests/` に「rc が pipe で失われる綴りを止める」機構は無い
  (`pipefail`・「パイプ」で hit ゼロ)。
- **DW-O09 pin 閉包**: `tools/dev_wave_land.py` と `docs/dev-wave/core.md` を bytes で pin する
  台帳・`FROZEN_MANIFEST`・generator source hash pin は `--include=*.py` / `--include=*.md` の
  双方で存在しない。凍結成果物の bytes は変わらず `DW-O10` は不成立。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 監査対象は wave tip の全史、実行体は tip 側の `check_ai_provenance.py`。**
  意味論を「この land 後の main で全史監査が緑であること」に揃える。
  main 側の実行体を使うと、**known-violation を新規登録する wave が永久に land できない**
  (main の古い実行体はその登録を知らない) という deadlock が生じる。
  ただし tip 側実行体を使うことは「wave が自分の関門を弱められる」余地を作る — ここが最大の争点。
- **(P2) 関門は lock 内・ff-only の前に置く。** 事後に走らせて赤なら rollback、より単純で、
  部分適用状態を作らない。
- **(P3) 赤の定義は `returncode != 0` そのもの。** 「既知違反以外の赤」は checker 自身が
  known-violation を除外した上で rc へ畳んでいるので、land 側で finding を再解釈しない
  (再解釈は受理集合の二重管理になり、緩める方向の穴になる)。
- **(P4) 新しい reject rc を 1 つ足す** (`RC_AUDIT` の再利用はしない — 監査失敗の原因が
  切り分けられなくなる)。
- **(P5) 逃がし道 (`--skip-provenance` 等) は作らない。** escape hatch を残した機械化は
  規律 2 が名指しする reward hack の形であり、D95 と同型。
- **(P6) 38 秒 × land lock 保持を受け入れる。** `--range` で軽くする案は `DW-O17`
  「range は補助で、full 監査だけが権威」と衝突するため採らない。

## 不変条件 (緩めてはいけない)

1. `tools/check_ai_provenance.py` を触らない (並行 wave の所有)。
2. 既存の land 受理集合を**狭める方向にだけ**変える。緑だった land を通し続ける正例を必ず 1 つ持つ。
3. 逃がし道・環境変数による無効化・「赤でも警告だけ」を作らない。
4. `_validate_generated_docs` / `_preflight_fold_message` の既存挙動と rc を変えない。
5. 本 wave の全検査は rc をパイプへ通さず単独で取る。
6. docs 予算値を上げない。

## 成果物影響 (DW-G05)

- **W1 未実装**: F37 が 4 例目を生む。3 例の実測実害は「22 commit を赤のまま land」
  「1 commit を赤のまま land」「偶然の grep hit でのみ検出」。台帳 (commit 履歴の provenance) の
  受理集合が親の習慣次第で恒真化し、**本物の著者偽装を検出できなくなる**。
  実装すれば「land 後の main で全史監査が緑」が機械的に保証される。
- **W2 未実装**: 親が前提実測のために不要な probe を書き続ける。実例 = [T-659] の
  `probe_split_window.py` は不適切であるだけでなく**不要**だった (既存テスト 3 本が production
  経路でより強く同じことを断言していた)。成果物側の影響は、裁定パッケージの中核証拠が
  「親が書いた弱い証拠」に置き換わり、**推奨の根拠が実際より弱くなる**こと。

## 成果物の形

- `tools/dev_wave_land.py`: 新関数 1 (全史 provenance 監査の自走 + rc 判定)、`land()` 内の
  呼び出し 1 箇所、新 reject rc 定数 1。
- `orchestrator/tests/test_dev_wave_land.py` (または既存の land テスト): 赤で拒否する負例、
  緑で通す正例、逃がし道が無いこと、rc が pipe を経ずに取得されること。
- `docs/dev-wave/core.md` の `DW-S01` へ W2 の 1 文 (**親が docs として書く**)。
- `docs/failures.md` の F37 へ「再発 3 例 + 恒久対応を機械強制へ移した」旨 (段 7、spool fragment)。

## 並列分割方針

実装面は **単位 A のみ** (`tools/dev_wave_land.py` + その test)。W2 は docs で親が書く。
段 5 は 1 単位なので並列化しない。段 3 の敵対相談は 2 レンズ並列。

## 順序制約 (段 9 で効く)

現状 23 新規違反があるため、**並行 wave の登録が local main へ land する前に本 wave の関門を
land すると、関門が自分自身の land を fail-closed で拒否する。** 段 9 の直前に単独 rc で
`check_ai_provenance.py` の緑を実測し、緑でなければ `DW-STOP` に従い待つ。逃がし道は作らない。
