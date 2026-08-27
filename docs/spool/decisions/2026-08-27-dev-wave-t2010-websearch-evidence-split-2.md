---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t2010-websearch-evidence-split
seq: 2
---

## {{D:stdout-duplicate-key-admission}}. Codex CLI stdout の重複 key を許容する条件を 4 つの述語で閉じる

**決定:** D1149 が要求した「Codex CLI 自身が吐く stdout event 行の重複 key を異常として記録し
attempt を落とさない」を、`orchestrator/codex_roles/events.py` の**名前で opt-in する別入口**
(`parse_jsonl_allowing_duplicate_keys`) として実装する。既存の `strict_json_loads` と
`parse_jsonl` は署名も挙動も変えない。

許容するのは次の T1〜T4 を**すべて**満たす行に限る。1 つでも欠ければ従来どおり拒否する。

- **T1**: event object の top-level key が一意であること。重複は top-level より下でだけ許す。
- **T2**: その event の `type` が `STDOUT_CONSUMED_EVENT_TYPES` に含まれないこと。
  この定数は 1 箇所だけに置き、許容述語と `_consume_stdout_event` の**両方が参照する**。
- **T3**: last-wins で捨てられる側を含む元 tree 全体が、既存の domain 検査
  (UTF-8 / NFC / 有限数 / 深さ / key 型) を通ること。
- **T4**: 重複 key 以外の拒否理由が 1 つも無いこと。

許容した行は評価に一切寄与させず読み飛ばし、行番号を issue として記録する。

**理由:**

- **T1 と T2 が無いと D68 (4) の隠蔽が成立する。** last-wins 正規化だけでは
  `{"type":"thread.started","thread_id":"不正","thread_id":"正当"}` のように
  **先の値の不正を後の値で隠せる**。同型で `turn.completed` の `usage` も騙せ、
  `{"type":"error","type":"thread.started",...}` は event 種そのものを化けさせられる。
  段 3 の敵対レンズが 3 反例を構成し、親が経路で確認した。
- **境界を key 名や `web_search` に結び付けない。** `id` を名指しで許すと CLI の次版で
  別 key が重複したとき同じ全損が再発し、逆に「重複なら何でも許す」と T4 が崩れる。
  境界は producer 固有入口と**意味射影**で閉じる。
- **T2 を定数の共有で書く。** `_consume_stdout_event` が消費する型と許容述語が参照する型が
  ずれると、将来 consume 対象が増えたときに隠蔽経路が開く。片方だけ拡張すると壊れる形にした。
- **T3 は捨てられる側も検査する。** last-wins で消える値に domain 違反を置けば、
  検査を通り抜けた不正値が「あったこと」自体が記録から消える。
- 成果物側 (外側 event、最終 agent message、内側 `result_json`、rollout の 3 経路) の
  重複 key 拒否は 1 bit も緩めない。規律 2 の面である。

**却下した選択肢:**

- **既存入口へ `allow_duplicates` 引数を足す** — 既定値の取り違えで全 consumer が緩む。
  `strict_json_loads` は probe / launcher / run_codex_role の consumer を持つ。
- **許容を `id` の重複だけに限る** — CLI の版に依存し、次版の別 key で再発する。
- **重複 key の拒否そのものを外す** — D1149 が却下済み。成果物側の健全性検査に触れる。
- **rollout 側も同じ入口へ寄せる** — 実測した attempt の rollout に重複 key は無く、
  緩める必要が無い。evidence payload 境界の内側である。

## {{D:evidence-status-complete-means-no-fatal}}. evidence_status の complete は「致命的異常なし」であって「異常なし」ではない

**決定:** codex worker receipt を schema v5 へ上げ、attempt へ `evidence_issues` を追加する。
`evidence_status` の 3 値 (`complete` / `missing` / `invalid`) は変えないが、
**`complete` の意味を「致命的異常が無い」へ改める。** 異常ゼロを要求する読み手は
`evidence_issues` を読む。この規約を `_evidence_status` の docstring に書く。

`missing` と `invalid` の判定順序は**従来どおり `missing` を先に置く**。

v1〜v4 の receipt は従来の field 集合で読み、`evidence_issues` を要求しない。
再計算時の照合も v5 のときだけ `evidence_issues` を比較する。

**理由:**

- D1149 と既裁定 [T-981] が「`evidence_status=invalid` の理由を receipt へ記録する」を要求する。
  理由を残す場所が要り、既存 field は流用できない — `failure_class` は accepted 時に
  `None` 必須で束縛されており、意味を壊す。
- **前方非互換は version を上げても上げなくても避けられない。** attempt の field 集合は
  `_closed_object` が完全一致 (`set(value) != fields`) を要求するので、field を 1 つ足せば
  旧 reader は必ず拒否する。version を上げない利点が無いため上げる (診断が正確になる)。
  この限界は主張せず記録する。
- **判定順序を変えてはならない。** 致命的 issue を `missing` より先に判定すると、
  session 欠落と stdout 異常を同時に持つ既存 v1〜v4 receipt が `missing` から `invalid` へ
  再計算され、`check-receipt` が過去の正当な receipt を拒否する。
  親が旧実装と新実装へ同一状態を与えて実測した。`missing` は既に fail-closed であり、
  順序を戻しても受理集合は広がらない。
- 理由の記録が無ければ、同じ `invalid` が重複 key 由来か非 NFC 由来かを次の走行が
  推定でしか辿れない。本 wave 自身がその 2 種を 1 日で両方踏んだ。

**却下した選択肢:**

- **receipt へ新 field を足さず既存 field を流用する** (親の当初案) — 段 3 の 2 レンズが
  独立に反対した。accepted な attempt の異常を意味を壊さずに書ける既存 field が無い。
- **`evidence_status` に第 4 の値を足す** — 値を読む全 consumer の分岐が増え、
  旧 receipt との意味互換も壊れる。
- **schema を上げず optional field にする** — `_closed_object` の完全一致により
  旧 reader の拒否は同じで、拒否理由の診断だけが不正確になる。
