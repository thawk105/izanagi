# 段 1 brief — [T-329] 「次の一手」保存則の拡張

## scope

`tools/check_docs.py` の「次の一手」保存則 (D70) を、ID の存在・遷移検査から次の 2 つへ広げる。

- **(i) carry 参照先の実在**: carry 行 `- [T-NNN] (N)` と旧書式 `- [T-NNN] 変わらず ((N) 参照)` の
  `N` が、現行 worklog + archive に実在するエントリ番号を指すこと。
- **(ii) archive の主張と実体の一致**: `docs/archive/worklog-*.md` のファイル名が名乗る entry 範囲、
  および `docs/archive/README.md` 「現在の収容物」行が名乗る範囲が、ファイル実体の entry 集合と
  一致すること (min/max だけでなく範囲内の欠番も赤)。

scope 外: ID 採番規則そのもの、見送り台帳の構造、worklog 以外の archive 収容物 (`audit-*` 等)、
`docs/worklog.md` 冒頭 D70 節の文面改訂。

## 確定済みユーザー裁定

裁定 (115) (`docs/archive/worklog-phase3-0802-113-116.md`) で択 **(a)** 採用。(i)(ii) の**両方**を入れる。
理由は F79 の実害 (裁定 5 件の消失 + 宙吊り参照 675) を機械で止めること。再裁定不要。

## 純増検出力 (性質で検索した既存被覆)

- 「ID が後続エントリか見送り台帳のトップレベルに現れるか」= 既存 (`check_transition`)。
- 「carry 行の参照先エントリが実在するか」= **被覆ゼロ**。現行は `(N)` を一切解決していない。
- 「archive の実在物が README 索引から辿れるか」= 既存 (名前↔ファイル実在の到達性のみ)。
- 「archive の名前 / README が名乗る entry 範囲と実体が一致するか」= **被覆ゼロ**。

## 成果物影響 (DW-G05)

実装しない場合、F79 型 (ローテーションや競合解消でエントリ本文が丸ごと消えるが、名前も ID 存在検査も
通る) の再発を機械が緑で通す。失われる値 = carry が指すユーザー裁定の逐語と持ち越し理由。
受理集合は「参照先が実在し、archive の主張範囲と実体が一致する台帳だけ受理」へ狭まる。

## 不変条件

1. **既存 canonical 台帳・archive は緑のまま**。親の brief 前実測 = 名前が範囲を名乗る archive 全件で
   min/max・件数が一致 (不一致 0、欠番 0)、全域番号期の carry 参照 504 種すべて実在 (宙吊り 0)。
   赤が出たら内容側の欠落として報告し、検査を緩めて通さない。
2. 番号採番前の archive (日付だけの名前、ファイル内ローカル番号 `(1)`〜`(17)`) は対象外。除外は
   「名前が entry 番号を名乗らない」という**構文条件**で書き、ファイル名 allowlist にしない。
3. **新規 I/O を増やさない**。既存の archive 走査と既存の README 読取の中で完結させ、履歴比例コストを
   純増させない。
4. 検査対象は `docs/worklog.md` と `docs/archive/worklog-*.md` と `docs/archive/README.md` のみ。
5. pin 閉包 (DW-O09): `tools/codex_reasoning_ab.py` は `git show BASE_COMMIT:path` 経由の凍結参照で
   live bytes を見ない。`tools/spool_fold.py` は fold 時に動的算出。**live pin は無し**。
6. 実装面 (check_docs.py・テスト) は Codex `role=author` が書く。親は docs 本文と spool fragment のみ。

## 攻撃対象の provisional 裁定

- **(P1)** ファイル名の解釈: `-` 区切り token のうち 4 桁は日付、それ以外を entry 番号とみなす。
  番号 token が 0 個なら「範囲を名乗っていない」として (ii) を免除し、その中の carry 参照も (i) から
  免除する。
- **(P2)** README 行の書式は `` - `<name>` — worklog の <日付> (<lo>)〜<日付> (<hi>) 分 `` と
  `(N) 分` の 2 形。`〜` 前後の空白は揺れる。書式外の行 (`audit-*`、墓標行) は対象外。
- **(P3)** (i) の解決先は「全域番号 universe」= 番号を名乗る archive + 現行 worklog のエントリ番号集合。
  同一番号が 2 か所に実在したら別種の赤にする。

## 成果物の形

`tools/check_docs.py` の新検査 + `orchestrator/tests/test_check_docs.py` の positive / negative テスト。
受理集合を変えるので段 4 で変異を事前登録し、段 6 で dispatch recipe + `--force-dispatch` の
runner (変異 spec は repo 外) により実発火を実証する。

## 並列分割

check_docs.py と test file はカップリングが強いので実装子は 1 本。段 2 プラン 1 本、段 3 敵対相談 2 本
(sol / luna)、段 6 敵対レビュー 2 本 + fix。受入は本 worktree で lease を取って全走。
