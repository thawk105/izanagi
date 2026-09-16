# 段 6 裁定 — レビュー 2 本の所見と変異事前登録の訂正

## 1. must-fix の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A-1 | review A | 新 caption が改訂稿に無い精密日時 (`created_utc`) を持つ | **refuted (must-fix としては)** | 不採用。理由は §2 |
| B-1 | review B | 凍結 prefix への差替えで**既定 legacy 経路の CLI 被覆**が失われた。`main` が常に `frozen_legacy_caption=True` を渡す欠陥を、現行のどの assertion も捕まえられない | **real** | **採用 → fix 1 巡** |

## 2. A-1 を不採用にする理由

- caption の精密日時は `measurement_conditions.workloads[].created_utc` であり、その権威は
  `tracked_inputs` の `certification` / `raw_manifest` 2 行 (権威 bytes) である。
  改訂稿ではない。
- 成果物自身が `caption_source` 行の `authority_scope` を
  `condition description only; not measurement values or protocol status` と**明示的に限定**している。
  測定条件の権威を改訂稿に求めるのは、成果物が宣言していない読み方である。
- レビュー A 自身が「日時の捏造・数値誤りという判定ではない」「出所のある値ではある」と書いている。
  削れば、出所のある provenance 情報を caption から**減らす**ことになる。
- 改訂稿は「それぞれ別時刻に実行した」と述べ、caption の `at distinct recorded times` はこれと一致する。
  精密値はその主張を支える証拠であり、主張の追加ではない。
- ユーザーは「本題の図 1 枚と caption だけ」と scope を切った。identity 訂正と無関係な文の変更で
  旧 caption との差を広げない。
- **親の prompt が「改訂稿を唯一の照合先」と読める書き方をしたことが、この所見を生んだ。**
  レンズの誤りではなく親の指示の誤りである。段 8 の改善候補へ回す。

## 3. B-1 の fix 範囲 (これだけ)

失われた被覆を**同じテスト枠内で**復元する。新しい検査層・helper 群・fixture 一式は作らない。

- 既定 (非凍結) legacy prefix で `main` を通す CLI テストを 1 本持つこと。仮 repo に
  `docs/paper-story/results/2026-09-07-a2-certification-reject.md` を置いて成立させる。
- そのテストが次を同時に検査すること。
  - repo 相対 argv と完全 provenance (top-level key 全集合、`tracked_inputs` が 3 行)。
  - **`main` から描画へ渡る分岐** — 生成された図の x 目盛が `BACK_OFF=0` / `BACK_OFF=1` で、
    x 軸 label が `CCBench built-in adaptive backoff` であること。
    これにより `main` が常に凍結側を渡す欠陥が殺される。
- 凍結 prefix の CLI テストは現状のまま残す (凍結経路の被覆)。
- **既存テストの期待値を反転・緩和・skip・削除しない。**

## 4. 変異事前登録の訂正 (DW-M07。本走前に anchor と期待 node を再検証する)

両レンズが一致して、親の M1 / M2 / M5 の期待 node と赤理由が誤りだと指摘した。**採用する。**

| # | 訂正 |
|---|---|
| M1 | 共有列挙 `FROZEN_LEGACY_CAPTION_PREFIXES` は `_caption` と `build_provenance` の**両方**が読む。空にすると caption 不一致と入力集合の 2 系統で落ち、単一理由にならない。**`_caption` 内だけで凍結名を訂正側へ送る変異へ再照準する** (`build_provenance` の参照は触らない) |
| M2 | KILLED は成立するが期待 node は 2 件ではない。訂正 caption テストは 2 parameter、加えて旧図着地・凍結負例の正常確認・新図着地 closure も同じ caption 投影理由で落ちる。**期待 node を実測で確定する** |
| M3 | 妥当 (両レンズ一致)。変更なし |
| M4 | 妥当。ただし **tick だけに注入し xlabel を巻き込まない**ことで理由を限定する |
| M5 | README 逐語一致は変異で変わらないので赤理由にならない。`_assert_named_landed_bundle` は closure で先に止まる。**期待理由を「caption 全文比較 + 着地 caption の再投影不一致」へ訂正する** |

**期待 node は probe 走で実測して確定し、推測で登録しない。** 親が fix 後の最終 commit に対して
`--plan-only` と probe を回してから本走する。

## 5. 親裁定の誤り (受け入れ、訂正する)

- `s4-ruling.md` §3.3 の「既定は現行挙動」は不正確。**引数を省略した呼び出しの互換性**は保つが、
  legacy データの既定目盛と軸 label は訂正後へ変わる。§3.2 の方針とは整合しており、説明の誤り。
- §5 の変異事前登録は上表のとおり訂正する。
- §4 の「既存テストの期待値を甘くしない」は assertion の文面だけでは満たせない。
  検査対象を狭める prefix 差替えも弱体化に当たる。**B-1 の fix で復元する。**

## 6. refuted として記録する疑い (レビューが自ら否定したもの)

- 凍結破壊 — 旧 fig5 の 3 file は記録された SHA-256 と byte 一致。README の fig5 節・Erratum・
  追補も起点 `9d52ef145` と byte 一致。fig6 の 3 file も一致。
- 凍結 caption の再現 — 現物 JSON と UTF-8 **1788 bytes 完全一致**、空白差もなし。
- fig6 / current-full への波及 — 判定の全分岐で current-full は常に旧 tick / 旧 xlabel、
  caption は早期 return、provenance は追加行なし。保存 caption は **1995 bytes 完全一致**。
- layout 検査の恒真性 — 実 renderer の文字 bbox を比較しており恒真ではない。
- `tracked_inputs` の「差し替え」未達 — 権威 2 行は現在も使う測定値・判定・入力束縛の出所であり、
  改訂稿を条件記述の出所として足す現物は依頼の目的を満たす。
- 用途制限の迂回 — 成果物と docs の現状に、採用静的 backoff の結論へ戻す導線は無い。
- 改訂稿が無い環境での非凍結 legacy 生成は **fail-closed** (rc=2、不完全 bundle を publish しない)。
