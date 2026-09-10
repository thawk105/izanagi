# [T-419] 択 (c) — seam と検査網の補強 (2026-08-16)

wave `dev-wave-t419-seam-checknet` / branch `worktree-dev-wave-t419-seam-checknet`

## この wave が何をしたか

2026-08-16 /rulings 全件 第 2 回 #3 (authority=ユーザー) の択 (c) を実装した。
上位の較正・凍結権限束の完成を待たず、seam と検査網の補強だけを land する。
環境契約の active 世代は変えていない (activation serial は 1 のまま)。

## 中心にある構造的事実

択 (c) が活性化を禁じている以上、**受理集合を狭める production gate を置ける位置は
「次の世代を active にしてよいか」の 1 箇所しかない。** 段 3 の敵対 2 レンズが独立に、
それ以外の位置は (a) 今日動いている経路を止める、(b) 他層に覆われて帰属が成立しない、
(c) 今日の受理集合を変える、のいずれかになることを示した。

したがって gate は活性化の後継判定へ集約し、走査の拡張は検査網 (テスト層) へ置いた。
これは択一の原文 (「seam と test-net の hardening」) の語とも一致する。

## 従属 3 問の確定

- **(i) 方式名の実体一致** — 実行時 attestation ではなく**活性化の後継判定**に置いた。
  実行時の判定を変えることは D329 (2026-08-12 のユーザー裁定) の反転であり、
  pegasus の全 attestation が即座に落ちる。裁定へ返した。
- **(ii) 自己不整合な旧較正** — 「新たに ever-active になる較正を止める」という前向きの半分だけを
  実装した。既に ever-active な第 1 世代の扱いは裁定へ返した (実測で、歴史 resolver は
  歴史成果物専用ではなく live campaign の COMMIT 監査を含む 6 consumer に載っている)。
- **(iii) 活性化の根拠** — `quality.status=accepted` に加えて、自己整合・content-addressed path・
  acquisition receipt の内部束縛を要求する形にした。

## 親の実測 (すべて本 worktree の HEAD で取得)

| # | 内容 |
|---|---|
| M-A | pegasus の active は第 1 世代 (`contract e576e9cd…`、`calibration 753f535a…`、`attestation_mode=required`)。登録は 2 世代、ever-active は第 1 世代のみ |
| M-B | 自己整合の再計算: 第 1 世代 = 48 標本中 1 本が帯外 (3080.935、帯 [2058.98, 2143.02])、第 2 世代 = 0 本。両者とも `quality.status=accepted` |
| M-C | `_verify_entry_calibration` は active 経路と歴史 resolver の共有。ここを狭めると active 側も落ちる |
| M-D | 歴史 resolver の非テスト consumer は 6 件。うち `wal.py` の COMMIT 監査は live campaign 経路 |
| M-E | (i) は D329 の反転。8/16 の裁定パッケージは D329 に一度も言及していない (全文検索 0 件)。ただし F339 は実害の中身 (方式改訂で全 attestation が落ちる) を記録済み |
| M-F | 自己整合の既知例外つき検査は test 層に既存。ただし走査は active view の 2 件だけで、登録済み・未 active の第 2 世代は 1 件も見ていない |
| M-I | activation record は genesis 1 本のみ。遷移検査は `previous_rows is not None` のときだけ呼ばれるので、後継判定を厳しくしても今日の読み込みは 1 bit も変わらない |
| M-J | floor protocol index は exact 1 件で、key の ccbench pin は HEAD の gitlink と**一致しない**。resolver の選択条件に pin を入れると今日 0 件になり床値の受理経路が壊れる |
| M-L | `effective_clock.method` を現行 probe 定数と exact 比較すると、第 2 世代は True、第 1 世代は False。実在バイトで正例と負例が揃う唯一の位置 |
| M-M | `campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` は編集対象 3 file を含む exact 12 path の source closure。該当形式の campaign.lock は 32 件中 0 件なので既存再開は壊れない |

**M-G は誤りだった。** 「編集面に source pin は 0 件」と書いたが、上記 M-M のとおり実在する。
段 3 のレンズ A が反証し、親が独立に確認して訂正した。

## 逐語成果物

- `verbatim/s2-plan.md` — 段 2 プラン
- `verbatim/s3-lensA.md` / `verbatim/s3-lensB.md` — 段 3 敵対 2 レンズ (ともに NO-GO)
- `verbatim/s4-adjudication.md` — 段 4 裁定
- `verbatim/s5-unitA.md` / `verbatim/s5-unitB.md` — 段 5 実装子の報告
- `verbatim/s6-revA.md` / `verbatim/s6-revB.md` — 段 6 敵対レビュー (ともに NO-GO)
- `verbatim/s6-fix.md` / `verbatim/s6-fix2.md` — 段 6 fix 2 巡
- `verbatim/merge-audit.md` — main 取り込みの合成監査
- `ruling-package.md` — ユーザーへ返す 3 件の裁定パッケージ
- `mutation-spec.json` / `mutation-ledger.json` — 変異事前登録と台帳 (権威)
- `mutation-spec-probe.json` / `mutation-ledger-probe.json` — 1 回目 (probe、erratum つき)

## 変異検査

commit `29da0425` に対して 2 回走らせた。**合計 13 変異、SURVIVED 0。**

| 走行 | spec | 件数 | 結果 |
|---|---|---:|---|
| 1 回目 (probe) | `195c626a…` | 13 | KILLED 3 / MISMATCH 10 / SURVIVED 0 / baseline PASSED |
| 2 回目 (権威) | `ac326497…` | 10 | **KILLED 10 / MISMATCH 0 / SURVIVED 0 / baseline PASSED** |

**1 回目の MISMATCH 10 件は、期待より多く落ちた側である。殺せなかった変異はゼロだった。**
原因は、enforcement source closure の 12 path を変異させると、その注入自体が
`contract-loader-drift` を起こして `test_campaign.py` の約 25 件を巻き込むことである。
これでは狙った検出が過剰決定になるため、2 回目は対象集合からその file を外し、
1 回目に実測した node 集合をそのまま期待値として再登録した。

`test_campaign.py` を必要とする 3 件 (M9 床値 resolver の contract 一致 /
M10 admission の bytes 再照合 / M11 検査網の走査範囲) は、1 回目で**期待値と完全一致の KILLED**
であり、そちらが権威である。2 回目の 10 件と合わせて 13/13 が KILLED になる。

登録した変異の内訳。

- 新設 4 面をそれぞれ 1 面だけ無効化 (自己整合 / 方式名 / content-address / 取得記録)
- 配線 4 経路をそれぞれ元の構造判定へ戻す (通常 loader / ident の 2 箇所 / 発行 tool)
- 床値 seam の 2 面 (resolver の contract 一致条件 / admission の bytes 再照合)
- 検査網の走査範囲を active view へ戻す
- **過剰拒否の正例 2 本** — 方式名の判定を再生経路へ効かせる変異と、
  既に ever-active な世代へも効かせる変異。どちらも今日の経路を壊すので検出されなければならず、
  実測でどちらも KILLED になった

## この wave が保証しないこと

- 床値 protocol の seam は preflight admission までである。shell wrapper と 5 module は
  literal path を持ったままで、配線そのものは裁定へ返した。
  literal が resolver の結果と一致することを固定する検査だけを置いた。
- acquisition receipt の検査は artifact 内部の自己整合であり、外部の取得証明ではない。
- 活性化の後継判定は今日 production で一度も呼ばれない。発火するのは次の世代交代からである。
