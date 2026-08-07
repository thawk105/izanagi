---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t614-provenance-ledger
seq: 2
---

## {{D:known-violation-ledger}}. provenance の既知違反を固定台帳で分離し、rc は新規だけで決める

**決定:** 共有済み履歴に残り規約内で緑に戻せない provenance 違反を、`check_ai_provenance.py` 内の
frozen 定数 `KNOWN_PROVENANCE_VIOLATIONS` に置く。各 entry は
`(full 40-hex SHA, expected_finding_kind, ruling)` の 3 つ組で、`ruling` はユーザー裁定の出典を指す。
監査は次の連言だけで既知へ移す — **full SHA の完全一致**、**finding 種別の一致**、**entry あたり 1 件**。
同種の 2 件目以降、別種 finding、別 SHA、短縮 SHA は新規に残す。

- **正常完了時の rc は新規違反だけで決める。** 新規 0 なら既知があっても rc=0。
- **既知は rc に関わらず stdout の末尾側へ公開する。** 公開が唯一の抑止であるため沈黙させない。
  既知 0 件のときの逐語出力は完全に不変とし、既存の消費者を壊さない。
- **台帳の破損と stale は rc=2 とする。** stale = 台帳 SHA が監査範囲内にあるのに期待種別の
  finding が 0 件。これは provenance 違反ではなく監査機構自身の破綻なので、新規違反には数えない。
  診断は `expected-finding-missing` (checker の退行疑い) と `policy-epoch-not-visible`
  (非権威な invocation) に分ける。
- **台帳の妥当性検査は import 時ではなく history 分岐内の既存 `try` の内側**で lazy に行う。
- **code は docs を parse しない。** 台帳の実体はコードだけに置く。
- `--message-file`、forward correction、waiver の判定は変えない。

**理由:**
- 赤が常態化すると新しい違反が既存分に紛れる。実際に既存 6 件の隣へ 7 件目が入り、
  「手で帰属して赤を跨ぐ」運用で見逃されかけた。既知と新規を機械的に分離すれば、
  新規 1 件は 1 件として見える。
- 抑止条件を SHA と種別の連言に限り、entry あたり 1 件に絞ることで、台帳が「その commit の
  すべての finding を飲む緩衝材」になる経路を塞ぐ。
- stale を rc=2 にすると、gate を弱める改変 (期待 finding を生む検査を壊す変更) が台帳側から
  検出できる。rc=1 に混ぜないのは、rc semantics を「新規のみ」と定めた裁定を超えないためである。
- 台帳の内容を docs でなくコードに置くのは、新しい信頼経路 (docs を parse する) を作らないため。
  entry の `ruling` field は「どの裁定で 1 件増えたか」を可視化するが、**これは片側 drift を
  検出する tripwire であって、ユーザー裁定を機械的に強制する機構ではない**。

**却下した選択肢:**
- **finding と種別を平行 tuple で持つ** — 長さ不一致で新規違反が黙って落ちる。単一構造にした。
- **epoch が見えない entry を stale 判定から外す** — 偽赤は消えるが、期待 finding の生成が壊れた
  ときに rc=0 で通る fail-open になる。規律 2 に反するので、非権威な invocation での過剰拒否
  (rc=2) を受け入れる側へ倒した。権威ある範囲の定義は既存の forward correction 契約が既に
  「既定 full 監査か両 commit を含む range」に限定している。
- **未裁定の違反を台帳へ足して緑にする** — 台帳追加は防壁の恒久的な緩和であり、ユーザー裁定の
  領分である。既定監査が赤のまま残ることを受け入れ、処置は裁定へ返す。
- **既定監査の範囲計算 (`--ancestry-path`) を同時に直す** — 実測では現に no-op で、裁定外の
  scope 拡張になる。所見として裁定へ返す。

## {{D:nonacceptance-run-warning}}. 受入形でない走行の警告は親側で出し、正規 marker のある子だけ抑止する

**決定:** `tools/run_tests.py` の `main()` の最初期 — site 判定・dispatch・bounded 再実行・
3 つの acceptance-only preflight のいずれよりも前 — で、受入形でなければ stderr へ 1 行警告を出す。
bounded 子では、親が生成した**正規形式**の marker pair (正の PID・16 桁 lower-hex・正の
canonical decimal cap) を確認したときだけ抑止する。空・malformed・形式不一致では警告を維持する。
一意な marker を持たない dispatch 子では抑止せず、親と子の各 1 行を許容する。
`_is_acceptance_run()` の判定、pytest argv、3 gate の順序と rc、終了 rc、suite fingerprint は変えない。

**理由:**
- 受入全走のつもりで受入形でない走行を行い、事前検査が黙って不発のまま結果を記録した事故が
  独立 2 例あった。警告は受理集合を変えずにその誤記録だけを塞ぐ。
- **実行子側に置くと dispatch 成功時に手元から消える** — 親へ戻る子 stderr は末尾 4 KiB だけなので、
  pytest の出力に押し出される。警告の目的は人間が打った端末に出ることなので親側に置く。
- marker の存在だけで抑止すると、環境変数がたまたま在る直接走行で警告が消える。形式まで見る。
- 二重表示は不可視より害が小さい。dispatch 子を一意に識別する共通 marker が無い以上、
  1 行の重複を許して不可視を避ける。

**却下した選択肢:**
- **実行子側 (`use_xdist` 直前) に置く** — 上記のとおり dispatch 成功時に消える。
- **警告を receipt へ構造化して収集後に親が表示する** — 受理集合を変えない 1 行の目的に対して
  機構が重い。dispatch receipt の stderr tail が変わることは影響として記録すれば足りる。
- **marker の名前だけを見る** — 偽装・偶発一致で警告が消える。
