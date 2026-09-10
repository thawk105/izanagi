# [T-2118][T-2119] 条件 9 の判定器が呼出しの生死を見るようにした

- 日付: 2026-09-02
- branch: `worktree-dev-wave-t2118-t2119-c09-liveness`
- 実装 commit: `8b58a10ef80b8342b7195fc7e944a0fc26329482`
- 変異走の対象 commit: `8e6ad2fbdb080d3f75c61cc32c91dc245512781b` (上記に local main 取り込みを重ねた merge)
- 一次資料: `output/insights/2026-09-01_t2075-layer3-bypass-hard-failure/README.md`、D1456、D1459

## 何が問題だったか

事前登録の条件 9 の判定器は、受入関数 `assert_trial_registry_acceptance` の本体に
`assert_campaign_layer3_chain` の呼出しがあることを要求していた。その走査に使っていた
`_called_names` は `ast.walk` で木を全部たどるため、**`if False:` の下に置いた呼出しも
「呼んでいる」と数えた**。判定を恒真化できる形である。

同じ module には既に生死判定つきの走査 `_live_called_names` があり、条件 9 の producer 側は
そちらを使っていた。受入側だけが取り残されていた。

## 何をしたか

1. 受入側の走査を `_live_called_names` へ替えた (D1456)。
2. 証拠契約の条件 9 の文言を実装へ合わせた (D1459)。「全 build report」を
   「受領証発行へ到達する全 build report」へ、`reachable_from` の `registry append` を
   `acceptance receipt issuance` へ直した。受入が永続化するのは受領証だけで、registry append は
   この関数の中に存在しない。
3. 凍結の改訂手続きに従い `DECIDER_VERSION` を v9 へ上げ、世代記録 g15 を `prepare-revision` で
   発行した。契約 bytes に追随する hash pin 4 件と条件 9 の token pin も同じ commit で同期した。
4. 受入側だけを死枝化する負例テストを足した。既存の生死テストは producer 側しか見ていなかった。

## 機構が必要だったことの実測 (反実仮想)

変異 probe で、修正を戻す変異 (`_live_called_names` を `_called_names` へ) が落とすテストを数えた。

**落ちたのは 1 件だけで、それは本 wave が追加したテストである。** 既存の 619 件は、受入側の呼出しが
死んだ枝の下へ移っても 1 件も落ちなかった。この機構は既存の被覆と重複していない。

## 変異 matrix (本走 rc=0)

baseline PASSED、5 変異すべて KILLED、SURVIVED 0・MISMATCH 0。期待 node は probe の観測から
完全集合として登録し、本走で完全一致した。

| ID | 変異 | 期待 node 数 | 位置づけ |
|---|---|---|---|
| m1-revert-liveness | 受入側の走査を生死不問へ戻す | 1 | **機構本体**。単一理由性が成立する |
| m2-acceptance-gate-always-fires | 呼出し検査を恒真成立へ倒す | 14 | **過剰拒否の正例**。受理集合を縮小する wave の承認外拒否を検出する |
| m3-revert-contract-proof | 契約の proof を旧文言へ | 5 | 冗長 gate (hash pin + snapshot が同時に落ちる) |
| m4-revert-decider-version | 版を v8 へ戻す | 3 | 冗長 gate (版 pin が落ちる) |
| m5-revert-contract-reachable-from | 契約の token を旧値へ | 7 | 冗長 gate (hash pin + exclusion pin + snapshot) |

m3〜m5 は事前登録の時点で冗長 gate と明記しており、機構の証拠は m1 と m2 で立てている。

m1 の単一理由性は、合成 fixture の `policy = {"no-build": False, "certifying": False}` が別行で
生きているため後段の文字列検査が落ちないこと、producer を変異させないため前段の到達性検査も
通ることをコードで確かめたうえで、本走の観測 node 1 件で裏取りした。

## 敵対相談・レビューで出て、実装しなかった所見 (裁定パッケージ候補)

段 3 のレンズ A が挙げた 4 件はいずれもコード上正しいが、本 wave では実装していない。
**C09 を充足可能集合へ入れる前の blocker として扱う。**

1. **生死判定に入らない死んだ形がある。** `IfExp`、短絡 `BoolOp`、`raise` や `try/finally` の
   完了伝播は現行の除外列挙に無い。比較式と関数呼出しは `docs/decisions.md:20104-20109` が
   「不明」として両枝を残すと定めており、これは裁定どおりの挙動である。列挙を広げるのは
   同じ helper を共有する 20 箇所以上の判定器の受理意味を同時に変える改訂であり、D1456 の
   射程外である。
2. **呼出し先の実体同一性を見ていない。** 宣言済みの別 path に同名の decoy を置く、属性呼出しに
   すり替える、といった形が通る。終端 target の定義 path が契約の宣言する集合に含まれればよい、
   という設計は同 decisions の項 7 として landed である。条件ごとの exact tuple を要求する形へ
   変えるのは別の設計判断である。
3. **policy marker は文字列の存在検査である。** `do_build=False` から受領証までのデータフローを
   保証しない。レンズ A は「生きた文字列に替えても、無用途の `("no-build", "certifying")` を
   置けば通る」と示した。**半端な生死化はかえって恒真な保証を増やすので採らなかった。**
4. **受領証発行経路の支配関係を見ていない。** 呼出しが生きていても、受領証を出す枝では
   実行されない形が作れる。

段 6 のレビュー B が出した must-fix 1 件は **refuted** である。「親が担当する g15 が既に差分へ
入っているので `prepare-revision` を実行できない」という所見だったが、g15 は実際に親が
`prepare-revision` で生成 (rc=0) してから commit したものである。レビューへ渡した差分が commit 後の
ものだったため、生成前の状態と読まれた。

レンズ A の nit 1 件 (新文言の `build report` を「受入関数へ渡る全 report」と読むと `do_build=False`
が残る) は記録に留める。契約の同じ文の後半が「missing または no-build の鎖を certify してはならない」と
no-build を別に扱っており、D1459 が指定した文言をそのまま採った。

## 検査

- 焦点走 (`test_s8c_preregistration_predicates.py` / `_core.py` / `_invariant.py`): 619 passed, 0 failed, 5 skipped
- consumer 走 (`test_t671_source_binding.py` / `test_campaign_lock_codec.py` / `test_artifact_admission.py` / `test_s8c_gate_report.py`): 342 passed, 0 failed
- `python3 tools/check_ai_provenance.py`: rc=0、7816 件、新規違反なし
- 変異本走: rc=0、baseline PASSED、KILLED 5 / SURVIVED 0 / MISMATCH 0

## 落とし穴

- 変異走の 1 回目は共有木の事後検査で rc=125 になった。並行 wave が共有 checkout の未追跡ファイルを
  書き換えるためで、worklog 1127 に同型が記録されている。独立 clone を `--source-repo` へ渡して
  構造的に断った。
- 契約 JSON の bytes を変えると、全体 hash pin・制御文字を足した派生 hash pin 3 件・条件 9 の
  token exclusion pin・世代記録・実 repo snapshot の 5 系統が動く。段 2 プランと段 3 の 2 レンズは
  いずれも派生 hash pin 3 件を拾えず、親の焦点走が初めて実測で出した。
- 実 repo snapshot テストは全条件の evidence に契約 blob の sha を含むため、契約を変えた作業ツリーが
  未 commit のうちは必ず赤になる。commit すると解消する。実装の回帰と読み違えない。
