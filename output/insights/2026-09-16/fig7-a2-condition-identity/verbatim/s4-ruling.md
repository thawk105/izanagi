# 段 4 裁定 — 図 5 identity 訂正 / プラン v2 / 変異事前登録

## 1. 所見の裁定 (real / refuted、採否)

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| R1 | sol 1 | 本 wave の活動そのものを止める後続裁定は無い | refuted (疑い) | — |
| R2 | sol 2 / luna 1 | 親の「caption 訂正と凍結 bytes 保持は両立しない」は一般化しすぎ。新 prefix 限定訂正で両立する | **real (親の誤り)** | **採用** |
| R3 | sol 2 | in-place 上書きは現在の授権では実施できない (D1645・D1753・README 追補) | real | **採用 = (P1) 維持** |
| R4 | sol 3 | 新図は歴史説明に限定。採用静的 backoff の結論へ転用しない | real | **採用** |
| R5 | sol 6 / luna 2 | 目盛 `fixed 10 us` を残す段 2 案は依頼未達。目盛訂正は本題の内側 | **real** | **採用 (プランを覆す)** |
| R6 | sol 5 / luna 4 | `tracked_inputs` への `caption_source` 追加は成立。ただし「機構上の必然」ではない | real | **採用 (根拠を訂正)** |
| R7 | luna 2 | `make_figure(data)` は prefix を受け取らないので、caption 分岐だけでは目盛へ届かない | real | **採用** |
| R8 | luna 5 | プランの行参照 2 箇所がずれ (`:862`–`:880` → 作図/publish は `:881`/`:882`、README は 610 行) | real | **採用** |
| R9 | luna 3 | caption だけ変えた図は絵が旧図の複製になる | real | R5 で解消 |
| R10 | luna 4 | 改訂稿を tracked_input にすると `.md` 1 byte 変更で着地図が赤になる | real | **受容** (同稿は自ら「凍結物・更新しない」と宣言済み) |
| R11 | luna 2 | 目盛の文字幅変更で `check_figure_layout` が落ちうる | real | **採用 (親が実走で確認)** |
| R12 | sol 7 | 着地テストの追加を独立した検査層へ膨らませない | real | **採用** |

**ユーザー裁定へ返す択一はない。** sol が明示的に「なし」と判定した。凍結解除も用途制限の撤回も
求めずに、依頼の目的を満たす経路が選べる。

## 2. 親 brief の訂正 (追記による訂正)

- **新事実 4 を訂正する。** 「caption の訂正と凍結 bytes の保持は両立しない」は、legacy caption を
  **一律**変更する場合にだけ正しい。新 prefix にだけ訂正版を返す分岐なら両立する。
- **(P4) を覆す。** 「caption の条件記述だけ」に限る、という制限は誤り。**x 軸目盛も条件記述である。**
  ユーザーの依頼は「**図が支持する命題**と caption を改訂稿の表現へ合わせる」であり、絵が
  `fixed 10 us` と表示し続ける成果物はこれを満たさない。目盛の訂正は本題の図 1 枚の内側とする。
- (P1)(P2)(P3) は維持する。(P3) の根拠だけ差し替える — closure が certification 行の保持を
  必須にしているのではなく、**実際に使った測定権威の出所記録を落とさない**ために 2 行を残す。

## 3. プラン v2 (確定)

### 3.1 図の identity と命題

- 新図の名前: **`fig7_a2_builtin_backoff_onoff_reject`** (figures/ に fig1〜fig6 が在り、fig7 は未使用)。
  図番号は `_figure_number` が prefix から導くので、名前の決定がそのまま caption の番号になる。
- 支持する命題: **attempt `t2022-20260828c` の記録された条件では、CCBench 内蔵の適応 backoff を
  有効にした群の median throughput が、無効にした対照より write-heavy (rr5) で −46.3902%、
  balanced (rr50) で −65.9080% 低く、当時の外側 protocol status は `reject` だった。**
- **この図は採用静的 backoff についての結果ではない** (D1936 項21 / D1993 決定 5)。

### 3.2 訂正を新図へ閉じ込める seam — 既定を正しい側に置く

段 2 は「新 prefix なら訂正版を返す」という allow-list を提案したが、**裁定は逆向きに採る。**

```
FROZEN_LEGACY_CAPTION_PREFIXES = ("fig5_a2_certification_reject",)
```

- legacy profile の**既定は訂正後の条件記述**とし、この列挙に載る prefix のときだけ、凍結済みの
  旧文言をそのまま返す。列挙は「この 1 成果物の caption は訂正前の文言で凍結されている」という
  **凍結の記録**であって、機能の台帳ではない。
- **理由:** allow-list 側だと、将来 legacy 権威から別の図を作った人が黙って誤った条件記述を得る。
  既定を正しい側に置けば、誤りを持つのは明示的に凍結した 1 件だけになる。列挙の長さは同じで、
  新しい gate も検査層も増えない。
- caller は「どの成果物か」だけを選び、caption 文字列を注入できない (D1752 / D1753 の形を踏襲)。

### 3.3 変更する 3 箇所 (実装面 = Codex author)

`tools/plotting/plot_a2_certification.py`

1. **`_caption` の legacy 分岐** (`:653` 以降)。`prefix.name` が上の列挙に無いとき、条件記述を
   訂正した文言を返す。訂正するのは次の 2 点だけで、値・status・限定・abort 率の扱い・
   `gray dashed line` の説明は 1 文字も変えない。
   - `Median effects copied from certification are rr5 fixed 10 us …% and rr50 fixed 5 us …%`
     → 効果の主語を「内蔵適応 backoff の有効 vs 無効」にする。数値は既存の
       `100*data['effects'][workload]:.4f` 式をそのまま使い、定数へ焼き込まない。
   - 「cell ID と `fixed 10 us` / `fixed 5 us` は**要求された genome の名**であって効いた条件では
     ない。`BACKOFF_FIXED` は build に効かなかった。`BACK_OFF=1` が有効にするのは CCBench 内蔵の
     **適応**制御であり指数 backoff ではない」旨を 1〜2 文で足す。
2. **`make_figure` の目盛** (`:726`)。訂正対象の図では
   - x 目盛を `("BACK_OFF=0", "BACK_OFF=1")` にする。
   - x 軸 label を `"performance arm"` から `"CCBench built-in adaptive backoff"` にする。
   - **理由:** 目盛の文字数を旧 (`no backoff` 10 / `fixed 10 us` 11) と同程度 (10) に保ち、
     `check_figure_layout` の重なり判定への影響を最小にする (R11)。機構名は余白のある軸 label 側へ置く。
   - seam は `make_figure(data, *, frozen_legacy_caption: bool = False)` とし、既定は現行挙動。
     `main` (`:881`) が prefix から決めて渡す。**既存の `make_figure(data)` 呼び出しは無改造で通る。**
3. **`build_provenance`** (`:775`)。訂正対象の図のときだけ `tracked_inputs` へ 1 行足す。
   - `kind: "caption_source"`、`path: "docs/paper-story/results/2026-09-07-a2-certification-reject.md"`
     (生成器所有の固定値、caller から受け取らない)、`sha256` は生成時に `_sha256` で取得、
     `authority_scope: "condition description only; not measurement values or protocol status"`。
   - certification / raw_manifest の 2 行は保持する。`raw_manifest` は 1 行のまま。

### 3.4 テスト (実装面 = Codex author、同 file 内)

`orchestrator/tests/test_plot_a2_certification.py` に**既存の枠内で**足す。新しい検査層は作らない。

- 旧 fig5 の caption が凍結文言のままであること (既存 `test_landed_fig5_…` が守るので、
  **列挙から fig5 を外すと赤になる**ことを確かめる負例を 1 件)。
- 新 prefix の caption が訂正文言を持ち、`fixed 10 us` の語を効いた条件としては述べないこと。
- 新 prefix の図の x 目盛が `BACK_OFF=0` / `BACK_OFF=1` で、旧 prefix では従来どおりであること。
- 新 prefix の provenance の `tracked_inputs` が 3 行 (certification / raw_manifest / caption_source)
  で、`raw_manifest` が 1 行であること。旧 prefix では 2 行のままであること。
- 新図が着地したときの `_assert_named_landed_bundle` を呼ぶテスト 1 本 (helper は単独で収集されない)。
  着地前は既存 fig5 テストと同型の skip 条件にする。

### 3.5 親の担当

図 3 file の生成 (login node、計測機の外)、`docs/paper-story/figures/README.md` の編集、
worklog / insights fragment、commit、受入全走、変異走行、land。

## 4. 不変条件 (段 5・6 で破ってはならない)

- 旧 `fig5_a2_certification_reject.{png,pdf,provenance.json}` の bytes を変えない。
- `fig6_*` の bytes を変えない。
- 権威 bytes (`certification.json` / `raw-manifest.json`) と外部 WAL / raw cell を変えない。
- 値・median・効果・outer status・`cells`・`genome`・`_artist_series` の内部 identity を変えない。
- caption へ caller 由来の任意文字列を注入する経路を作らない (D1753)。
- `CANONICAL_SHA256` に entry を足さない (legacy entry が既に在る)。
- 新しい gate・検査層・台帳・一般化を足さない。既存テストの期待値を甘くしない。
- provenance の top-level key 集合を変えない (既存の完全集合 assertion がある)。

## 5. 変異事前登録 (DW-M01。段 5 の実装前に確定)

実装面の差分があるので変異 matrix は免除されない。次の 5 件を事前登録する。
各件は「位置 / 変異 / 期待赤 node / 単一理由性の確認点」を持つ。

| # | 位置 | 変異 | 期待 KILLED node | 単一理由性 |
|---|---|---|---|---|
| M1 | `FROZEN_LEGACY_CAPTION_PREFIXES` | 列挙を空にする | 旧 fig5 の着地 closure テスト | 旧 provenance の caption と再生成文字列の不一致だけで落ちる。他層に旧文言を守る gate は無い |
| M2 | `_caption` の凍結分岐条件 | 条件を反転 (凍結側と訂正側を入れ替え) | 旧 fig5 着地テスト **と** 新図 caption テストの両方 | 2 node が落ちることを事前に期待値として登録する |
| M3 | `build_provenance` の `caption_source` 追加 | 追加行を落とす | 新図 `tracked_inputs` 3 行テスト | closure は行数を検査しないので、この 1 node でだけ落ちる |
| M4 | `make_figure` の目盛分岐 | 訂正対象でも旧目盛を使う | 新図 x 目盛テスト | 目盛文字列を検査する node は他に無い |
| M5 | `_caption` の訂正文言 | 「要求 genome であって効いた条件ではない」の 1 文を削る | 新図 caption テスト + README 逐語一致 | README 収録は親が着地させる。着地前は caption テストのみを期待 node とする |

**baseline 緑が前提。** 変異前に対象 file 集合の焦点走が緑であることを親が実測する。
SURVIVED は `DW-M04` に従い mutated 内容の diff で注入実在を確認するまで equivalent としない。
`tools/mutation_harness.py` を使う (`DW-M05`)。変異中は親の編集と worktree へ書く子の起動を止める。

## 6. 段 5 の分割

実装子 1 本 (`role=author`、`sandbox=workspace-write`)。編集所有は
`tools/plotting/plot_a2_certification.py` と `orchestrator/tests/test_plot_a2_certification.py` の 2 file。
docs・図の生成・commit は親。分割の単位が 1 つなので別 worktree は 1 つで足りる。
