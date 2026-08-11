---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-module-fixture-cost
seq: 2
---

## {{D:session-meta-candidate-scan}}. rollout の session 解決は候補行だけを parse し、同一性の錨は SHA pin に置く

**決定:** `tools/codex_reasoning_ab.py` の `_find_rollout` は、`_json_lines` による全行 parse を
やめ、専用 scanner `_session_meta_rows` が供給する `session_meta` 行だけを見る。候補判定は

    b'"session_meta"' in line          # UTF-8 literal
    or b"\\u00" in line                # ASCII 文字の JSON Unicode escape
    or b"\x00" in line                 # json.loads が受理する UTF-16 / UTF-32

の論理和とする。`_json_lines` 本体、`len(matches) != 1` の 5 行と rc、
`payload.id` / `payload.session_id` の OR 条件、`sorted(rglob(...))` の全ファイル走査、
`path.resolve()`、ファイルごとの `break` は不変に保つ。

**決定 (2): 候補外行の非捕捉例外が消えることを認める。** 現行は全行を parse するため、
`payload` に巨大整数を含む**非対象行**で `ValueError` (int 変換上限) が伝播して停止する。
候補行だけを parse するとこの偶発停止を失う。**候補行側の例外境界は現行と同一に保つ**
(`JSONDecodeError` と `UnicodeDecodeError` だけを握り潰し、`except Exception` へ広げない)。

**理由:**
- 遅さの主因がここにあることを一次資料と profile で確定した。構築 1 回 111.63s のうち
  `_find_rollout` が 74.62s (67%)、`json.loads` は 3,030,525 回で 51.04s。
  606,027 行 × 5 走査 = 3,030,135 が profile 実測とほぼ一致し、機序の同定が数値で成立した。
- 対象行抽出の同一性を独立 2 経路で実証した。実 corpus 全 2,799 ファイル / 606,027 行の
  突き合わせで不一致 0 (`json.loads` は 99.54% 削減)。敵対レンズの符号化網羅解析
  (literal / `\u00XX` / BOM / CR / UTF-16LE,BE / UTF-32LE,BE / surrogate / `\/` / 大文字 `\U`) は
  「正常 decode される対象行の false negative は構成不能」と結論した。DW-G03 の独立 2 例が成立する。
- **失われるのは設計された検査ではない。** 停止していたのは無関係な行の病的 bytes による
  偶発例外であり、返す path は 1 bit も変わらない。同一性の錨は `ROLLOUT_SHA256` であり、
  `_find_rollout` の 5 呼出はいずれも直後に `_verify_rollout_sha` を走らせる。
- 効果は実装前に paired で確定した。順序 ACB / BCA の 2 走で構築 1 回 87.58 / 86.94s →
  52.74 / 52.94s = **39.1〜39.8%**。走間変動 1.75s の 1 桁上。
  受入全走では同 fixture が 14 worker で構築されるため約 475s の work が消える。
- 変異 9 件が全件 KILLED (MISMATCH 0 / SURVIVED 0)。述語の各分岐の削除・特定 escape 値への
  縮小・例外捕捉の拡大・ID の OR 縮約・ファイル内 `break` の早期化・malformed 行での打切り・
  `OSError` 捕捉の削除が、いずれも機械的に検出される。

**却下した選択肢:**
- **走査結果の memo 化** — root 単位 index は path 一覧を signature にしても
  同一 path の書換・追記を検出できない。実際に本 wave の作業中だけで rollout が
  2799 → 2806 → 2813 と増え、対象 root を不変と扱えないことが実測された。
  追加効果は 17% にとどまり、stale の穴と釣り合わない。
- **利用テストの xdist group 化** — 構築回数そのものを 14 → 1 にできるが、
  過去のユーザー裁定と衝突するため再裁定を要する。鎖長の見積りも未確立である。
- **POS/NEG fixture の遅延分割** — 片側だけを使うのは利用 17 本中 5 本で、効果が小さい。
- **本番 clone の軽量化** (`--no-hardlinks` の除去、object closure 封印の省略) —
  これらは検証している安全性質そのものであり、速度のために触らない。

**残る比例コスト:** 本決定は走査の係数を下げるが、**比例そのものは消さない**。
`~/.codex/sessions` は codex を使うほど増え、実測増加率は約 106 files/day、約 26 日で倍である。
比例除去は別タスクとしてユーザー裁定へ返した。

## {{D:supersession-pin-derivation}}. 生きた台帳に対する検査は、伸びる集合を literal で固定せず fail-closed 方向だけを釘付けする

**決定:** `orchestrator/tests/test_t793_report.py` のうち**実 HEAD の `docs/decisions.md` を読む
2 node** は、D291 supersession 走査が返す decision ID 集合の**完全一致を検査しない**。
代わりに次を検査する。

- `status == "possible_supersession"` (gate が fail-closed に発火すること)
- `"D292" in decision_ids` (既知の実参照を取りこぼさないことの positive control)
- `decision_ids` が非空・重複なし・全要素が `D<数字>` の形であること

**凍結 blob を使う 5 node (合成 `D999` を足すもの) は完全一致のまま変更しない。**
これらは実 HEAD に依存しないので腐らず、集合の完全一致という検出力の本体はここに残る。

**理由:**
- `_scan_d291_supersession` は自然言語から supersession と単なる参照を区別できないため、
  「D291 より後の decision section に `D291` が一度でも現れたら承認済みと断言しない」という
  **意図的に保守的な fail-closed 走査**である。よって返る ID 集合は、D291 に言及する決定が
  増えれば必ず増える**生きた量**であり、literal で固定すると書いた瞬間から腐る。
- 実害が出た。無関係な wave が D305 を land しただけで当該 2 node が赤になり、
  **受入全走を経由する全 wave の land が止まった**。テストは production の欠陥を捕らえたのではなく、
  台帳が正常に伸びたことを赤としていた。
- **緩めた方向が安全である。** ID が増える方向は gate をより保守的にするだけで承認を緩めない。
  危険なのは ID が減る / 空になる方向で、それは `status` と `"D292" in ...` が捕まえる。
- 期待値を `("D292", "D305")` へ書き換える案は採らない。次に D291 を参照する決定が入った時点で
  同じ停止が再発し、**修正のたびに全 wave を止める構造が残る**ため。

**却下した選択肢:**
- **既知赤 waiver (W1 形式) の新設** — 起草まで行ったがユーザー裁定で取り下げた。
  waiver は赤を残したまま迂回する形であり、恒久ルール「テストがおかしければテストを直す」に反する。
  しかも本件の集合は今後も伸び続けるので、waiver は事実上恒久化する。
- **期待集合をテスト側で再導出する** — production の走査を再実装することになり、恒真な検査になる。

**残る検出力の欠落:** 実 HEAD に対しては「余計な ID が増えていないこと」を検査しなくなる。
これは gate を厳しくする方向の変化しか見逃さないので受理する。
厳密な集合検査が要る場合は、凍結 blob 側 5 node に合成 decision を足して固定する。
