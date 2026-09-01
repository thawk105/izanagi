# 段 4 裁定 — [T-1984] D906 の外部署名主体

親が段 2 プランと段 3 の 2 レンズ (所見 11 + 11 件) を裁定した結果。

## 0. 親自身の実測 (レンズが出していない、本裁定で最も重い制約)

`tools/wave_land_window.py:135` は lease payload を
`set(value) != {"holder", "main_sha", "ttl"}` で **exact field set 検査**している。
そして `236-251` は、parse に失敗した lease を例外にせず
**`holder, main_sha = None, None` = 「誰も保持していない」へ縮退**させる。

**含意:** lease payload へ `lease_generation` を足すと、旧 `wave_land_window.py` を持つ
稼働中 wave は、**保持中の lease を空き lease と読む。** lease directory は
`/work/1/SFC/tanab/dev-wave-jobs/land-lease/` の共有 1 本であり、現在 6 本以上の wave が使っている。
これは受入の排他を壊す。**したがって本 wave では lease payload の形式を変更しない。**

この制約はレンズ A・B のいずれも指摘していない。親の独立実測である。

## 1. 所見の裁定 (real / refuted と採否)

### 採用する real 所見

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| R1 | A-4 | 旧 land consumer による迂回が残る。`dev_wave_land.py` の root は `__file__` 由来で、検査は cwd == wave worktree だけ。pre-v6 の land blob を wave 側から起動すれば新 verifier を通らない | **real・採用。** 必須化しても関門は不可避にならない。段 7 で「閉じた」と書かない根拠 |
| R2 | A-10 | AI が鍵を生成してから hook で以後の書込みを拒否しても D906 を満たさない。生成時点で AI が秘密を支配した事実は後付け hook で消えない | **real・採用。** 鍵儀式は人手の手番。AI が代行しない |
| R3 | A-8 / B-9 | 親 brief の (P5)「既存 schema 版上げと同じ範囲」は **refuted**。停止するのは過去 v5 receipt だけでなく、legacy lease・非保持走行・旧 waiter の稼働 wave・鍵未配置期間を含む | **real・採用。親の前提を撤回する** |
| R4 | B-10 | `held` / legacy `queued` の `unclaimed=True` receipt 廃止は **D662 と衝突**する。D662 は「`held` でも待たず疑似 holder で投入」を定めている | **real・採用。実装しない。裁定パッケージへ** |
| R5 | A-3 / B-2 | 再送防止は別 wave / main / tip / lease acquisition 間だけを閉じる。同一 context の exact single-use は閉じない | **real・採用。** 逐語を限定して記録 |
| R6 | B-5 | repo 内 reference と repo 外 operational issuer の bytes 同一性・実行実在を land が束縛する field が無い。issuer に自己申告させれば F385 と同型の自己証明 | **real・採用。未閉鎖へ明記** |
| R7 | B-1 | 署名が証明するのは「設定済み公開鍵に対応する秘密鍵による承認と署名後の非改変」まで。特定 issuer の実行は証明しない | **real・採用。親の言い方を訂正する** |
| R8 | A-2 | production positive control は人手 issuer 実在まで作れない。test key の後付け署名を production control と呼ぶのは D431 違反 | **real・採用。** 部分充足に留め unmet を明記 |
| R9 | B-6 | D906 の「検査器」は `tools/check_acceptance_reds.py` と読むのが妥当 (receipt vocabulary が根拠)。ただし `checker_content_sha256` は期待 content hash であって実行 bytes の証明ではない | **real・採用。** 語義はこれで確定し、限界を明記 |
| R10 | B-7 | 「受理追加なし」は raw byte 集合としては不正確。v5 → signed-v6 は縮小でなく置換 | **real・採用。** 変異台帳の書き方を訂正 |
| R11 | A-9 / B-8 | `test_dev_wave_land.py` の無署名 v5 正例と署名必須化は両立しない。ただし fixture 更新自体は正当な契約更新であり弱体化ではない | **real・採用。** 本 wave では編集不可のため必須化を送る |
| R12 | 親 | (第 0 節) lease payload 変更は稼働中 wave の排他を壊す | **real・採用。実装しない** |

### refuted と裁定した所見

- A-1 (恒真化は段 2 設計に無い)、A-5 (issuer 通過時の単純差替えは残らない)、A-7 (回避策は関門を弱めない)、
  B-3 (判定の未閉鎖は落ちていない)、B-8 (fixture 更新は弱体化ではない) — いずれも refuted に同意する。

### 親 brief の撤回

- **(P4) の因果を訂正する。** 「issuer へ起動権を移せば本 wave tip の署名実装が走るので回避できる」は誤り。
  正しくは「repo 外の operational issuer が、旧 main launcher の v5 出力を後段で署名するから成立する」。
  issuer 本体は tip の copy ではない。
- **(P5) を撤回する。** R3 のとおり。
- **parent-findings.md の「receipt は issuer を通らないと作れない」を撤回する。** R7 のとおり、
  検証できるのは configured key による署名であって、特定 issuer process の通過ではない。
- **parent-findings.md の「repo の外の別主体」を撤回する。** repo 外 path は別の OS 主体を意味しない。
  同一 uid のままである。書けるのは「repo 外 path に operational copy と鍵を配置した」までである。

## 2. 択一の裁定

**(b) を採る — 機構を実装し、production の必須化は行わず、間を未閉鎖と明記する。**

両レンズが独立に (b) を推奨し、親の独立実測 (第 0 節) も (a) を否定する。ただし
**(b) の意味を厳密に固定する。**

- v6 を optional にしない。v5 fallback を新設しない。trust root が無いときに通す形にしない。
  test module 名による bypass を作らない。**これらはすべて発行権限の迂回路であり採らない (規律 2)。**
- production の現行 v5 経路は **1 bit も変更しない。** 必須化は後続の activation wave が
  waiter と land を同時に v6-only へ切り替える形で行う。

**(a) を採らない理由 (「安全側だから」ではない):**
1. 鍵儀式は人手の手番であり (R2)、AI が代行すると D906 の却下選択肢「署名だけを足し鍵の置き場を
   決めない = 恒真になる」に落ちる。
2. 必須化は稼働中 6 本以上の land を鍵配置まで止める (R3)。
3. `test_dev_wave_land.py` を編集できないため全走が緑にならない (R11)。
4. 必須化しても R1 の旧 land 迂回が残るため、「閉じた」とは書けない。

**(c) を採らない理由:** 実装可能な部分まで止めるのは D1197 の実装命令に反する。

## 3. 本 wave の scope (実装する)

| 単位 | 専有 path | 内容 |
|---|---|---|
| U1 | `tools/acceptance_receipt_signature.py` (新規)、`orchestrator/tests/test_external_acceptance_signing.py` (新規) | canonical v6 payload の構築と Ed25519 署名検証。固定 trust root loader。production land へは配線しない |
| U2 | `tools/acceptance_issuer_reference.py` (新規) | reviewed reference issuer。tested_main の launcher blob を自ら選択・実行し、git 由来 field を再導出して署名する。production waiter からは呼ばない |
| U3 | `hooks/guard_write.py`、`hooks/guard_bash.py`、`hooks/README.md`、`orchestrator/tests/test_external_authority_hooks.py` (新規) | 外部 authority root を防護対象へ追加する。**誤操作抑止であって認証防壁ではないと明記する** |

**不変条件 (実装子へ渡す):**

- `orchestrator/tests/test_dev_wave_land.py` を編集しない (稼働中の別 wave 2 単位が未 commit で編集中)。
- `orchestrator/campaign/artifact_admission.py` / `campaign_lock.py` / `contract_loader_binding.py` に触れない。
- **`tools/wave_land_window.py` の lease payload 形式を変更しない (第 0 節)。**
- `tools/dev_wave_land.py` / `tools/dev_wave_wait.py` / `tools/acceptance_launcher.py` の
  production 受理集合を変更しない。
- 新規 test file には自走 harness を持たせる (`orchestrator/tests/test_plain_runner_coverage.py` が発火する)。
- 鍵の bytes を出力のどこにも書かない。

## 4. 実装しない (裁定パッケージとしてユーザーへ返す)

1. **鍵儀式 (人手の手番)。** 外部 issuer と Ed25519 鍵を repo 外の固定 subtree へ人が配置する。
   AI が生成すると D906 を満たさない (R2)。
2. **production の署名必須化。** 1 の完了後、かつ `test_dev_wave_land.py` の競合解消後に
   activation wave で行う。
3. **`lease_generation` の production 配線。** lease payload 形式を変えると稼働中 wave の排他が壊れる
   (第 0 節)。D906 の「排他権の世代」は canonical schema に slot を置くに留め、production 値の
   生成源は activation wave で決める。DW-O13 の実測ができないため、本 wave では述語として採用しない。
4. **`held` / legacy `queued` の receipt 廃止。** D662 と衝突する (R4)。
   「D662 を改訂して非保持走行を land 不可とする」か「D906 を満たす別の世代意味論を採る」かの裁定が要る。
5. **exact single-use の再送防止 (外部 consume ledger)。** D906 の「再送防止」が
   lease acquisition 間までか exact single-use までかが未確定 (R5)。
6. **旧 land consumer の迂回 (R1) の封鎖。** main 起点で consumer bytes を固定する設計は scope 拡張。

## 5. 変異事前登録 (DW-M01)

実装前に登録する。各変異は、同じ入力を拒否する層が前後に無いことをコードで確認してから登録する。
確認できないものは登録せず実効 gate へ再照準する。

| # | 位置 | 変異 | 期待 | 単一理由性の確認事項 |
|---|---|---|---|---|
| M1 | 署名検証の等値比較 | 署名不一致でも真を返す | KILLED | 他層に署名検査が無いこと |
| M2 | trust root loader | receipt 内の値を鍵として採用する | KILLED | 固定 trust record 以外から鍵を取らないこと |
| M3 | canonical payload 構築 | 署名対象から 1 field を落とす | KILLED | 落とした field の改竄負例が赤になること |
| M4 | canonical payload 構築 | field 順序を非決定にする | KILLED | 正規化が署名の前提であること |
| M5 | context 束縛比較 | `tested_tip` の比較を省く | KILLED | 再送負例が赤になること |
| M6 | hook の subtree 判定 | component 境界を部分文字列一致へ緩める | KILLED | `/authority-x` を `/authority` と誤認する負例 |
| M7 | hook の外部 root 追加 | 追加した root を集合から外す | KILLED | 直接書込み負例が赤になること |

登録時に冗長 gate であることが判明した変異は、単独変異の証拠から外し理由を台帳へ書く (DW-M03)。

## 6. positive control (D431) の充足状態

- **充足させる:** 実在の production v5 受領証 (repo 外 job dir の実物) を tracked fixture として
  取り込み、canonical projection 述語へ通す。期待値は test source 内の独立 literal とし、
  `os.environ`・production 定数・戻り値自身・loader から作らない。
- **unmet と記録する:** 署名検証述語そのものの production positive control。
  production signed-v6 receipt は人手 issuer が実在するまで発行できないため (R8)。
  **test key の後付け署名を production control と呼ばない。skip / xfail / 期待反転で緑に見せない。**
- 負例は 4 方向すべて置く: 署名なし / 鍵違い / field 改竄 / 別 context への再送。

## 7. 段 7 で使う言い方 (D1197 の明記義務)

**書いてよい:** 署名検証 module・reference issuer・外部 authority の hook 防護を追加した。
**書いてはならない:** 「外部署名主体を実装し、着地受領証の真正性が閉じた」。

段 7 の冒頭は次の逐語を使う (レンズ B の案を採用)。

> 【機構追加・未強制】署名検証・issuer reference・外部 authority hook 防護の実装部品を追加したが、
> production land の署名必須化と operational issuer / 鍵の配置は完了していない。
> これらの部品は現在の着地関門では効いておらず、unsigned-v5 receipt による既存受理を置換していない。
> D906 の enforcement 完了とは数えず、着地受領証を根拠にした正しさ主張は D1197 に従い未閉鎖である。

未閉鎖の一覧はレンズ B の「未閉鎖の確定版」を正本とし、これに R1 (旧 land consumer の迂回) と
第 0 節 (lease payload を変更できない理由) を加える。

---

## 8. erratum (段 6 レビュー後の訂正 — 初回の記載は上に残す)

段 6 の敵対レビュー 2 本が、段 4 の記載のうち次を訂正した。**初回の記載は消さない。**

### 8.1 第 3 節の単位 U3 は成立しない

第 3 節は U3 として guard の 2 file の編集を挙げたが、**guard 自身が自分の subtree への
書き込みを拒否する** (同 subtree の README 以外)。Claude と Codex の双方へ配線済みであるため、
**どの AI 作業者も編集できない。** したがって U3 は本 wave では実装せず、
外部 authority の書込み防護は**鍵儀式と同じく人手の手番**として第 4 節へ移す。

段 7 で「外部 authority の書込み防護を追加した」と書いてはならない。

### 8.2 変異 M6・M7 は対象を失っていた

M6・M7 は U3 を前提に登録したため、U3 が消えた時点で**対象実装も負例も存在しない。**
そのまま KILLED と記録すれば、実在しない防護を充足済みと誤記することになる。
レビュー A の再照準に従い、次へ差し替える。

| # | 差し替え後の位置 | 変異 | 期待 |
|---|---|---|---|
| M1 | 署名検証 | 署名不一致の例外を握り潰して成功扱いにする | KILLED |
| M2 | 固定公開鍵 loader | 固定定数でなく環境変数指定の鍵を採用する | KILLED |
| M3 | canonical payload 構築 | 署名対象から 1 root field を落とす | KILLED |
| M4 | canonical payload 構築 | key の正規化順序を挿入順へ倒す | KILLED |
| M5 | context 束縛比較 | 検査した tip の比較を省く | KILLED |
| M6 | 高水準 API | 固定 loader と低水準署名検証を迂回して payload を返す | KILLED |
| M7 | context 束縛比較 | wave 名の比較を省く | KILLED |

**M2 は段 6 レビュー時点で SURVIVES だった。** fix がその境界を通る control を追加して閉じた。
この初回結果は消さず、変異台帳へ erratum として残す。

### 8.3 「署名なし」負例は M1 の証拠に数えない

署名 field を落とす負例は、署名検証へ届く前に exact-schema の検査が先に赤にする
**冗長 gate** である。単一理由性が成り立たないため、M1 の証拠から外す (DW-M03)。
Ed25519 層の実効負例は鍵違いと field 改竄の 2 件である。

### 8.4 段 7 の逐語はレビュー B の一覧を正本とする

「書いてよいこと」「書いてはならないこと」の逐語は、段 6 レビュー B が返した一覧を正本とする。
とくに **fixture は最終 commit で追跡されるまで D431 の充足に数えない。**
