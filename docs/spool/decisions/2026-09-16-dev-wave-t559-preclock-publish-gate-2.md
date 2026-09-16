---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t559-preclock-publish-gate
seq: 2
---

## {{D:pre-post-clock-publish-gate}}. 較正 publish の直前に、凍結 pre profile と benchmark 後の観測 clock を canonical 述語で照合する

**決定:**

1. 較正取得 CLI の `_certify_main` に、既存の late 自己整合検査の直後・`status` 決定の直前で、
   凍結した pre profile の実効クロックと benchmark 直後に取得済みの post profile のクロックを
   照合する gate を置く。判定は canonical 述語 `effective_clock_comparison_passes` の
   **戻り値だけ**で行い、帯計算を再実装せず、診断値を受理判断に使わない (D191 決定 1・決定 6)。
2. 比較の expected 側は**凍結した dynamic pre profile** とし、最初の static probe でも post でも
   置き換えない。tolerance は attempt 開始時に policy 定数から焼いた凍結値を使う。
3. post 側の供給源は既に取得している post profile とし、新しい probe を足さない。
4. 失敗は既存の reason list の末尾へ足し、既存 reason を消さず・上書きせず・統合しない。
   `status` が `rejected` になることで publish より前に止まる。**publish transaction の位置と
   順序は変えない。** 拒否時に published artifact を削除しない (D191 が既に却下している)。
5. 失敗時だけ attempt staging へ診断 sidecar を 1 つ残す。凍結 attestation profile 全体と
   その SHA-256、canonicalization 識別子、canonical へ渡した実入力、診断値、および
   **照合時点の policy 値**を含める。
6. **gate を通った attempt の published artifact の bytes を変えない。** calibration artifact に
   新しい field を足さず、既存 field にも post 情報を混入させない。

**理由:**

- D191 の「射程」節が、benchmark 中および benchmark 後のクロックは依然として検査されないと
  自ら記録していた。外側の post probe は CLI 終了後に走り、canonical 述語を一度も通らず、
  publish を取り消さない。凍結した事前状態と事後の観測値の照合を公表前に課すのが
  ユーザー裁定 (択 (a)) である。
- publish transaction 自体を後ろへ移す案は影響範囲が広く、裁定が採らないと定めた。
  受理判定へ reason を足す形なら、publish の位置・順序・公開後再読を 1 行も動かさずに
  「公表前に止める」を満たせる。
- 照合時の policy 値を sidecar に残すのは、benchmark 中に policy 定数が変わった場合に
  帯内の標本でも canonical が False を返すためである。この値が無いと、後日 policy が戻った
  環境で sidecar を再計算すると判定が反転し、成果物だけからの再計算が成立しない。
- 判定を canonical の戻り値に固定するのは、診断の `band_pass` で分岐する実装が
  policy 不一致を見逃すからである。policy 変更時に帯内でも拒否することを要求する負例で、
  この違いを実際に撃てる。
- published bytes を変えない制約は、凍結 pin の保全に不可欠だからではない。artifact schema の
  exact keys 検証に触れず、登録済み較正を束縛する既存の参照と digest をこの wave の射程外に
  保つための、保守的な自己制約である。

**射程 (この決定が保証しないこと):**

- benchmark **中**に帯外へ振れて post 観測までに戻った変動は検出しない。
  post 観測は `calibrate_fn` の返却直後の 1 回だけである。
- CLI 終了後に外側 job wrapper が撮る post attestation は本 gate の検査対象外であり、
  それを評価して publish を取り消す経路は依然として無い。
- probe の観測者効果 (F108) は是正しない。D155 決定 (4) がユーザー再裁定へ返した項である。
- **成功した照合の証拠は成果物に残らない。** sidecar は失敗時だけ書くため、成功時の
  pre→post 判定を成果物から再計算できない。受理集合・published bytes・参照を変えないので
  本 wave の must-fix にはせず、裁定パッケージへ返した。
- 本 gate が守るのは CLI publish 経路だけである。git 直接追加・旧 worktree からの持ち込み・
  attempt からの複製・pin 更新は、D155 決定 (3) のとおり本 gate も loader も拒否しない。

**却下した選択肢:**

- **publish transaction を後ろへ移す** — 裁定が影響範囲の広さを理由に採らないと定めた。
- **calibration artifact に post 標本や比較結果の field を足す** — top-level・profile・quality は
  exact keys 検証であり、schema を広げれば accepted artifact の bytes と digest が変わる。
  登録済み較正を束縛する既存の参照へ波及する。
- **判定に診断値 (`band_pass`) を使う** — policy 不一致を見逃す。D191 決定 6 が
  3 者の連言を canonical 述語に限ると定めている。
- **拒否時に published artifact を削除する** — content-addressed で immutable な公開領域を
  事後に壊し、並行 publish との race も生む (D191 が却下済み)。
