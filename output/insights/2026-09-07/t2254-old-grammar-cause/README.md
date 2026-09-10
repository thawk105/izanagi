# [T-2254] 旧 grammar が受入全走の失敗原因であることの実測と、裁定の食い違い

対象 HEAD: `542bfadb86b14625a99cca1bdef3583ea09a95ca`
実測日: 2026-09-07 (JST 22:28〜22:50)
実行場所: Pegasus。`tools/run_tests.py` が計算ノードへ dispatch した
(request `981664.nqsv` / `981687.nqsv` / `981713.nqsv` 相当の 3 走)。
測定 root: `/work/1/SFC/tanab/b10-backoff-grid-runs5`。
`IZANAGI_B10_MEASUREMENT_ROOT` は未設定 (`env | grep` が rc=1) なので、
`orchestrator/tests/test_plot_b10_extended_backoff.py` の既定値がそのまま使われた。

いずれも trace-disabled でない通常の repo テストであり、性能計測ではない。

## 1. 何を測ったか

主張は「旧 grammar (pre-T733 の exact-24 contract loader map) が、受入全走で図の生成経路を
落としていた原因である」である。これを、既存の受入経路そのものを使った**対**で測った。

| 走行 | 木の状態 | 結果 |
|---|---|---|
| baseline | 現行 main のまま | `10 passed in 5.40s` (child rc=0) |
| 対照 1 (広い) | `_decode_campaign_lock_for_purpose` の `HISTORICAL_RAW` 枝を無効化 | `1 failed, 9 passed in 5.93s` |
| 対照 2 (狭い) | `_inspect_campaign` の decode 呼び出しを `_decode_campaign_lock` へ戻す | `1 failed, 9 passed in 4.96s` |

対照 2 は段 3 のレンズ B の指摘で追加した。対照 1 の `if False and ...` は共有 helper 全体を
変えるため、helper の別の呼び手 (`artifact_admission.py:1144`) と、現行 exact-62 lock を
読む場合の返却型まで一緒に変えてしまう。対照 2 は焦点の呼び出し 1 箇所だけを
`da44dc7b1^` (D1653 実装 commit の直前) と byte 一致させたもので、
同版の当該行は `decoded = _decode_campaign_lock(lock_raw)` だった。

一時変異はいずれも 1 行で、`git diff --stat` が `1 file changed, 1 insertion(+), 1 deletion(-)`。
走行後ただちに `git checkout --` で復元し、`git status --porcelain` が空、
`sha256sum orchestrator/campaign/artifact_admission.py` =
`f9a74c41ba92e974e495a978a291d2dbfc361a3e0e287641b9027c8023d708c5` が
`git show HEAD:` の同 file と一致することを両回とも確認した。

## 2. 赤の中身

両対照とも赤は 1 件だけで、
`orchestrator/tests/test_plot_b10_extended_backoff.py::test_throughput_ci_is_wal_t95_and_abort_has_no_ci_in_canonical_data`
である。**2026-09-05 の受入全走 (`1 failed / 19869 passed / 92 skipped`) で唯一赤だった
test と同一**である (一次記録は `docs/archive/worklog-phase3-0905-1279.md`)。

対照 2 の例外連鎖 (`-rA` 付きで取得):

- 落ちた場所は `orchestrator/campaign/campaign_lock.py:337` の `_validate_authority`。
  条件は `tuple(sorted(blob_sha256s)) != tuple(sorted(CONTRACT_LOADER_RELATIVE_PATHS))`。
- 例外は `CampaignLockCodecError: authority.contract_loader_blob_sha256s の exact key 集合が不正`。
- これが `The above exception was the direct cause of` として
  `plot_b10_extended_backoff.py:754` → `test_plot_b10_extended_backoff.py:197` へ伝わる。

対照 1 では同じ内因が `artifact_admission.py:971` で
`ArtifactAdmissionError: campaign.lock codec validation failed: ...` に包み直されていた。
traceback の `lock_raw` は `campaign-lock/v2` で payload に
`static-backoff grid; workload=write-heavy` と `"trial":"b10-backoff-grid"` を含む。

対照 2 では残り 9 件が `-rA` の `PASSED` 行で個別に確認できている。
すなわち baseline の `10 passed` は skip による空振りではない。

**注意:** 生成器は workload を write-heavy から順に処理して最初の失敗で止まるので、
この走行が実際に通常 decoder へ拒否させたのは B10 格子 write-heavy の lock 1 件である。
残り 2 件が拒否されることは §3 の grammar 分類から従うが、この走行では実行していない。

## 3. lock 側の grammar (strict 分類)

現行閉包 `CONTRACT_LOADER_RELATIVE_PATHS` は 62 path、
`PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS` は 24 path
(`orchestrator/campaign/campaign_lock.py` の literal を実測)。

走査した 2 root にある `campaign.lock` 15 件それぞれについて、
`authority.contract_loader_blob_sha256s` の **key を並び順のまま** 取り出し、
`PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS` を sorted した列と完全一致するかを判定した。
key の個数だけの分類ではない。

- **13 件が exact ordered 一致 (= 旧 grammar)。** 内訳は B10 格子 3 件
  (write-heavy / read-heavy / balanced) と paper-story A-2 認証 10 件
  (`t2022-20260827` / `t2022-20260828` / `t2022-20260828b` / `t2022-20260828c` の
  rr5・rr50 各 2 件、`t2228-20260904a` の rr5・rr50 2 件)。
- **2 件が不一致 (key 62)。** `t2364-20260907b` の rr5 と rr50 で、いずれも 2026-09-07 に
  現行コードで作られた新しい測定である。**旧 lock の発行し直しではない。**

範囲の限定: 走査したのは `/work/1/SFC/tanab/b10-backoff-grid-runs5` と
`/work/1/SFC/tanab/izanagi-measurements` の 2 root だけである。
「13 件」はこの 2 root での file path 数であって、保管領域全体の網羅ではない。
D1563 が書いた 11 件は 2026-09-03 時点の数で、その後 A-2 が 2 件増えている。

## 4. 主張の格

この対から言えるのは次の 1 文である。

> HEAD `542bfadb86b14625a99cca1bdef3583ea09a95ca` の焦点 test では、同一の SHA-256 で
> 束縛された B10 入力に対し、現行の `HISTORICAL_RAW` decoder がある baseline は通過し、
> その入口を通常 decoder へ戻した対照は
> `authority.contract_loader_blob_sha256s` の現行 exact key 集合検査で失敗した。

言えないことを明記する。

- 「今の受入全走に他の赤が無い」は、この焦点走の対からは言えない。別に全走で測る。
- 「2026-09-05 の全走で赤が 1 件だけだった」は本 wave の測定ではなく、
  `docs/archive/worklog-phase3-0905-1279.md` の一次記録である。
- 一時変異は正しさゲートそのものを触っているが、受理集合を**狭める**向きであり、
  反証用の対照だけに使い、認証・性能評価に使わず即時復元した。規律 2 の禁止線は越えていない
  (段 3 レンズ B の判定も同じ)。

## 5. 裁定の食い違い (本 wave の主要な発見)

[T-2254] は「実測して確定したら 3 案を再提示し、選択はユーザー裁定に委ねる」という項だった。
実測は上記で確定したが、**3 案の提示と選択は既に 2026-09-03 に済んでいた**。

| 裁定 | 日付 | 性格 | 内容 |
|---|---|---|---|
| D1511 | 2026-09-02 | ユーザー裁定 | 版付き decoder を作らない。再訪条件 = admission API 経由で読み直す必要が生じたとき |
| D1550 | 2026-09-03 | ユーザー裁定 | まず実測。確定したら 3 案を再提示、選択はユーザー → [T-2254] |
| **D1563** | **2026-09-03** | **ユーザー裁定** | **実測完了として 3 案から「新閉包で発行し直す」を選択。版付き decoder を明示的に却下** |
| D1653 | 2026-09-05 | **親裁定** | 歴史閲覧限定 decoder を採用。再発行案を規律 7 違反として却下 |

D1653 の実装 `da44dc7b1` は `refs/heads/main` の祖先である。すなわち **main に着地しているのは
D1563 が却下した側の案**である。D1653 は本文中で D1563 を一度も引用していない。
D1563 が命じた「発行し直し」は、§3 のとおり実施されていない。

D1563 を明示的に撤回・上書き・棚上げした後続裁定は不在である。
`docs/decisions.md` 全体に対し `D1563`、`D1653`、`旧 grammar`、`旧閉包`、`HISTORICAL_RAW`、
`pre-T733`、`exact-24`、`新閉包`、`発行し直`、`版付き decoder`、`歴史 decoder`、`別の束縛`、
`撤回`、`上書`、`supersed`、`棚上げ` で検索した (段 3 レンズ A が実施、親が再確認)。
`D1563` の文字列は見出し自身にしか現れない。

### 5.1 ただし、ユーザーは後日 2 度 D1653 に依拠している

親の初期の読み (「親裁定がユーザー裁定を覆したまま」) は、次の 2 件を欠いていた。
段 3 のレンズ A が指摘し、親が一次資料で裏を取った。

- **D1669 (2026-09-07、ユーザー裁定)** は `execution-provenance` v1 の歴史 decoder について、
  「歴史 decoder は D1653 が『収載する grammar は実在 corpus が確認できたものだけ』と定めた面と
  同型である」を理由に挙げ、D1653 の条件を先例として使っている。
- **D1680 (2026-09-07、ユーザー裁定)** は「旧 grammar の追加収載は D1653 の
  『実在 corpus が確認できたものだけ』で決まる」として、当該項を /rulings の索引から外している。

どちらも **D1563 との衝突を認識したうえで exact-24 decoder を選んだ記録ではない**。
したがって暗黙の全面追認とも D1563 の supersede とも読めないが、
D1653 が現に台帳上で機能している事実は伏せてはならない。

### 5.2 技術的にはどちらが正しいか

段 3 のレンズ A は、D1563 の理由づけのほうが不十分だと判定した。親も同意する。

- D1563 は「束縛は内容ハッシュに掛かっており、新しい lock は同じ内容に対する新しい束縛である」
  と書く。しかし lock が表すのは blob の内容だけではない。lock は WAL より前に live capture
  されるので、**測定後に不足 path の blob hash を計算しても「測定時に disk bytes と blob が
  一致した」という時間付きの事実は復元できない**。これは D1653 の指摘であり、正しい。
- さらに lock hash は completion / receipt / manifest の digest 鎖へ伝播している。
- 一方、D1653 の「旧記録を新閉包で発行し直すのは規律 7 に反する」という表現は広すぎる。
  旧 bytes を残したまま「後日作った派生記録」と明示して新 artifact を発行すること自体は
  規律 7 が禁じていない。**正確な境界は「その新 lock は当時の測定時 lock の代替にはならない」**である。

## 6. ユーザーへ返す 3 案 (選択はユーザーの手番)

依頼の指示どおり 3 案をそのまま再提示する。ただし現在の main を出発点として書き直してある。
**親はどれも選ばない。**

### 案 1 — 版付き (歴史閲覧限定) decoder を採る

- 今からすること: すでに着地している D1653 の実装を維持し、**D1563 との衝突を新しい
  ユーザー裁定で解消する**。新規実装は不要。
- 規律 2: certified 経路は通常 decoder の現行 exact-62 のまま。旧 exact-24 を受けるのは
  exact enum の `HISTORICAL_RAW` のときだけで、返却型も別である。現行 certified の受理集合は変わらない。
- 規律 7: 歴史 view は当時の verifier epoch を判定根拠にし、現行適合を `unknown` と表示する。
  旧記録を現行 certified へ遡及昇格しない。
- 撤回費用: 将来撤回するなら、旧 literal・歴史 decoder・purpose 分岐・歴史 epoch・別返却型を
  除去し、B10 図と他の旧 lock 読み手に別解を与える必要がある。
- 補足: D1511 (版付き decoder を作らない) と D1563 (版付き decoder を却下) の 2 件を
  明示的に覆す裁定になる。

### 案 2 — 該当 lock を新閉包で発行し直す (D1563 が選んだ案)

- 今からすること: D1653 を撤回して D1563 を再確認し、§3 の 13 件について、旧 bytes を残したまま
  現行 exact-62 の新 lock と、それを参照する下流束縛を発行する。三択を排他に扱うなら
  現在の歴史 decoder を撤回する。
- 規律 2: decoder も certified 判定式も広げない。corpus 側を現行述語へ移す。
- 規律 7: **ここが争点である。** §5.2 のとおり、新 lock は当時の測定時 lock の代替にならない。
  D1563 はこの時間的束縛と下流 digest 鎖を考慮していない。
- 撤回費用: 3 案中で最も大きい。図の生成器は lock を含む外部入力を固定 hash で束縛しており、
  新 lock と下流 digest 鎖を発行すると「発行しなかった状態」へは戻せない。

### 案 3 — 図の生成経路を別の束縛へ移す

- 今からすること: B10 図だけを中央 admission から外し、既存の固定 file SHA-256 束縛を
  読み取り権威にする。排他に扱うなら現在の歴史 decoder も撤回する。
- 規律 2: certified admission は変わらない。ただし図の読み手が admission 内の検査
  (起動記録、記録 commit blob 照合、拒否 overlay、WAL topology) を失う。
- 規律 7: 旧 lock と測定 bytes をそのまま残す点では適合する。一方、
  「当時の epoch」と「現行適合 unknown」の区別は単なる file hash 束縛では表現できない。
- 撤回費用: 図だけなら変更面は小さいが、A-2 の 10 件を含む他の読み手の閉塞は解決しない。
- 補足: **D1563 と D1653 の両方がこの案を却下している。**

### 争点を 1 行にすると

> D1653 (歴史閲覧限定 decoder) を明示的に追認して D1563 を supersede するか、
> D1653 の技術的指摘を承知のうえで D1563 (発行し直し) を再確認するか。

案 3 は 2 つの裁定が独立に却下しており、本 wave の実測もこれを復活させる材料を出していない。

## 7. [T-2254] の終端

段 3 のレンズ A は「[T-2254] 自体は完了させてよい」と判定した。親はこれを採る。

- [T-2254] の要求は「原因の実測」と「3 案の再提示」である。実測は D1563 が認定し、
  本 wave が現行コードで独立に再現した。3 案の提示と選択も D1563 で行われている。
- 項が残ったのは未達だからではなく、D1563 を記録した同じ /rulings entry が
  [T-2254] を旧 entry への参照のまま持ち越し、以後も持ち越し続けたためと読める。
- D1563 と D1653 の権威の衝突は **[T-2254] とは別の新しい裁定事項**である。

## 8. carry 本文の訂正

[T-2254] の項文は「稼働 branch `worktree-dev-wave-t733-source-closure-transitive` の閉包拡張は
変異 5/5 KILLED まで通っているが、この件が理由で着地できていない」と書いている。
2026-09-07 の実測では同 branch は `refs/heads/main` の祖先で、
`git log --no-merges main..worktree-dev-wave-t733-source-closure-transitive` は空である。
取り残しは無い。

## 9. 段取りの誤り (自己記録)

段 2 の read-only 子 (22:21 起動) が読んでいる worktree を、22:29 に親が一時変異させた。
結果として子の出力に汚染は無かった (`if False` の語は子の出力に現れない) が、これは運任せである。
**背景の read-only 子と親の一時変異を同じ worktree で重ねてはいけない。**

## 10. 段 3 の所見と裁定

`verbatim/s3-lensA.md` と `verbatim/s3-lensB.md` が原文。親の裁定は次のとおり。

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 D1563 は有効なユーザー裁定 | real | 採用。§5 |
| A-2 D1653 は上書き権限を確認できない親裁定 | real | 採用。§5 |
| A-3 D1563 の技術的理由は不十分 | real (親 brief の暗黙の前提を訂正) | 採用。§5.2 |
| A-4 D1563 を撤回した後続 D は不在 | real | 採用。§5。親も再検索した |
| A-5 D1669 / D1680 が D1653 に依拠している | real (**親の見落とし**) | 採用。§5.1。親が一次資料で裏取り |
| A-6 三択を白紙で開き直すべきでない | 部分採用 | 依頼が「3 案を再提示」と明示しているので 3 案は載せる。ただし §6 末に争点を 1 行で示した |
| A-7 [T-2254] は完了させてよい | real | 採用。§7 |
| B-1 対照 1 は seam より広い | real | 採用。対照 2 を追加実測した。§1 |
| B-2 baseline の緑は空振りでない | refuted (疑いが成立しない) | 採用。`-rA` の PASSED 行と env 未設定を記録。§1〜2 |
| B-3 帰属には例外連鎖まで要る | real | 採用。§2 に連鎖と発生位置を記録 |
| B-4 主張の格に時点と範囲が要る | real | 採用。§4 の 1 文に限定 |
| B-5 この対照は規律 2 違反ではない | refuted (疑いが成立しない) | 採用。§4 |
| B-6 「13 件」は strict 分類が要る | real | 採用。15 件全部を exact ordered で分類し直した。§3 |
