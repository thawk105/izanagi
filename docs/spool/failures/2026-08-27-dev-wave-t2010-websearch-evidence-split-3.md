---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t2010-websearch-evidence-split
seq: 3
---

## 新規

### {{F:nonnfc-fixture-kills-readers}}. repo 内の意図的な非 NFC fixture を読むだけで codex 子の成果物が全損する [コンテキスト浪費] [手順漏れ]

- 事象: 段 3 の敵対レンズ 1 本が `codex_exit_code=0` / `validator_rc=0` /
  成果物 7,543 bytes 健在のまま `evidence_status=invalid` で捨てられた。
  728 秒を空費した。同じ prompt を地雷回避文つきで再投入すると rc=0 で通った。
- 根本原因: `orchestrator/tests/test_check_docs.py` の 2 行 (NFC 検査自身の fixture) が
  **意図的に非 NFC** である。子がその範囲を読むと、Codex CLI が tool 出力を
  `custom_tool_call_output` として rollout へ**非 NFC のまま記録**し、
  `tools/codex_worker_launch.py` の rollout NFC 検査が落として attempt ごと捨てられる。
  **子が引用を選んだのではなく、読んだ時点で死ぬ。** 引用の禁止では防げない。
  結合記号は **U+309A** (KATAKANA-HIRAGANA SEMI-VOICED SOUND MARK) で、
  F260 が名指しする U+0300-U+036F の**範囲外**である。既存の対策文言は 1 文字も防げない。
- 地雷の所在は完全に特定した。親が tracked 16,077 file を全走査し、
  **非 NFC はこの 1 file 2 行だけ**であることを実測した。
- 恒久対応: 現時点では**運用回避だけ**である。親が段 3・5・6 の全子 prompt へ
  「当該 2 行を含む範囲を読むな。行番号で避けろ」を入れ、再投入と後続の子 4 本が
  すべて rc=0 で通ることを実測した。**恒久対処は
  {{T:nonnfc-landmine-permanent-fix}} でユーザー裁定へ返す** — 候補は
  (a) fixture を実行時合成へ変え repo 内 bytes を NFC に保つ (親の推奨)、
  (b) rollout の NFC 検査を tool 出力の記録に限って緩める (規律 2 の面に触れるため推奨しない)、
  (c) 恒久的に prompt へ回避を書き続ける。
- 再発検知: 不受理時は receipt の `attempts[].evidence_status` を読む。
  `invalid` かつ `codex_exit_code=0` なら stdout と rollout の各行を
  `unicodedata.normalize('NFC', s) == s` で走査する。非 NFC 行が
  `custom_tool_call_output` なら本型である (子の作文由来の F260 と区別できる)。
  repo 側の全走査は `git ls-files` 全件に同じ述語を当てれば取れる。

## 再発

### F259

- **再発: 2026-08-27** — 本 wave が {{D:stdout-duplicate-key-admission}} で恒久対処するまでの間に、
  親が F259 を出した実物の走行 (99 行中 22 行が `web_search` item の `id` 重複) を
  現行コードで再生し、因果を確定した。同 attempt の rollout 259 行に重複 key は無く、
  反実仮想 (`stdout_invalid=False`) で `evidence_status=complete` になる。
  **stdout 経路だけを直せば足りる**ことの実測根拠である。
  F259 の恒久対応欄が挙げていた「検証側を緩めない」は維持した — 緩めたのは拒否の**定義域**であり、
  成果物側の重複 key 拒否は 1 bit も変えていない。

## supersede 追記

- F259 **supersede: 2026-08-27** — 恒久対応欄の「子 prompt に Web 検索の禁止を絶対制約として書く」は D1149 のユーザー裁定で撤回された。Web 検索は許可され、拒否の定義域を成果物側へ限る形で {{D:stdout-duplicate-key-admission}} が実装した。`DW-C01` の無条件禁止の文言も既裁定 [T-981] と整合する形へ改めた。
- F263 **supersede: 2026-08-27** — 恒久対応欄が挙げた 3 案のうち「`evidence_status=invalid` の理由を receipt へ書く」と「stdout event の重複キー扱いを分離する」は本 wave で実装した ({{D:evidence-status-complete-means-no-fatal}} と {{D:stdout-duplicate-key-admission}})。残る「consult / review 段で web_search を既定無効にする」は D1149 が却下しており、[T-981] の残件として {{T:websearch-default-off-wiring}} でユーザー裁定へ返す。
