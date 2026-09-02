# [T-2148] 排他権の世代の意味論 — 候補の列挙と consumer 挙動の実測

D1449 が「候補と consumer 挙動の実測なしには裁定できない」として保留した件の材料である。
本 wave は裁定しない。schema、受理集合、lease payload、`lease_generation` の slot は
1 byte も変えていない (D1449 が現状維持を命じている)。

- 測定日: 2026-09-02
- 基準 commit: `6ff06800de0e2a0a8ac261d2e20320e68db8ebb3`
- 測定機: Pegasus login node。使い捨ての lease directory に対する read-only 相当の probe だけ。
  **本番の lease directory には触れていない。**
- probe は repo 外 (`dev-wave-jobs/dev-wave-t2148-lease-generation-probe/artifacts/`) に置いた。
  逐語は `verbatim/probe*-script.md` にある。

---

## 1. 一番大きい発見 — 保留の根拠になっていた機序が実体と逆向きだった

D1400 項目 11 は、世代を lease payload へ足せない理由をこう書いている。

> 排他権の payload は field 集合を厳密一致で検査し、解釈できない payload を
> **「誰も保持していない」へ縮退させる**。したがって世代を payload へ足すと、旧い実装で
> 稼働中の wave が保持中の排他権を空きと読み、受入の排他が壊れる。

**実体は逆である。** `state=free` を返すのは `acceptance.lease` が directory に存在しないときだけで
(`tools/wave_land_window.py:567-568`)、解釈できない payload は `unavailable` になる
(`:245-247` -> `:66-68` -> `:383-384`)。

実測 (`probe1-placement.jsonl`)。世代 field を 1 つ足した fresh な payload に対して:

| 操作 | 観測 |
|---|---|
| 他 wave の claim | `unavailable` / `lease-unavailable` |
| **保持者自身の release** | `unavailable` / `lease-unavailable` |
| status | `unavailable` / `lease-unavailable` |
| renew | `unavailable` / `lease-unavailable` |

現行の受入は `unavailable` を受理集合にも非ブロッキング集合にも入れていないので
(`tools/dev_wave_wait.py:373-374`)、旧実装は**止まる**。production 入口で実走して確認した
(`probe3-acceptance.txt`): `rc=70`、`classification=claim-state`、`reason=terminal-claim-state`、
受領証も log も作られず、lease の bytes は不変だった。

`orchestrator/tests/test_wave_land_window.py:332-350` が「解釈できない fresh payload は
`unavailable` を返し、bytes と mtime を変えない」を pin しているので、これは偶発ではなく設計である。

**訂正の射程を広げてはいけない。** 言えるのは「基準 commit の現行 helper の fresh 経路では
排他が開かない」までである。混在しうる過去版の reader と着地ツールは測っていない。
着地ツールは renew の失敗では止まらない (5 節)。

---

## 2. しかし「排他が実際に開く」置き方は別に実在した

固定名 `acceptance.lease` 自体を世代付きの名前や世代 directory へ動かす案では、旧 reader が
固定名を見つけられず、**2 本目の lease を取る**。実測 (`probe1-placement.jsonl`):

| 置き方 | 他 wave の claim |
|---|---|
| `acceptance.<世代>.lease` へ改名 | **`acquired`** |
| `generation.<世代>/acceptance.lease` へ移動 | **`acquired`** |

これは規律 2 (正しさゲートを緩めない) に触れる唯一の型である。D1400 項目 11 が警戒していた
「排他が空きと読まれる」形は、payload への追加ではなく**この置き方に存在する**。

---

## 3. 裁定の第一階層は候補ではなく「粒度」である

計画は「同じ wave・同じ main でも再取得ごとに別値になる」を判定基準の先頭に置いていた。
しかし D906 は署名対象に世代を含めることを求めるだけで、**粒度は決めていない**。
粒度を先に固定すると、その粒度に合わない候補が自動的に落ちる。

`probe2-derivation.jsonl` で、payload を 1 byte も変えない導出値の粒度を実測した。

| 導出元 | renew 間で不変 | 再取得で変化 | どの粒度を表すか |
|---|---|---|---|
| 現行 payload bytes の hash | ○ | **×** | wave + main |
| holder と main_sha の hash | ○ | **×** | wave + main |
| wave 名からの導出 | ○ | **×** | wave |
| main_sha からの導出 | ○ | **×** | main の進み |
| lease directory の inode | ○ | **×** | lease directory |
| **lease file の inode** | ○ | **○** | **取得ごと** |
| lease file の mtime | **×** | ○ | (renew で変わるため使えない) |

**取得ごとの粒度を選ぶと、payload を変えずに実現できるのは lease file の inode だけである。**
一方、wave 単位・main 単位・directory 単位を選ぶなら、上の 5 つはいずれも正しい表現になる。
「恒真」と切り捨てられるかどうかは粒度の裁定で決まる。

観測値は `144118389621765871 -> 144118389621765871 -> 144118389621765872` だった。
**この filesystem では `st_birthtime` が取得できない** (`None`)。したがって inode の再利用を
区別する手段が無く、番号は連番で振られている。

---

## 4. 取得ごとの粒度を選ぶと、非保持走行の世代が定義できない

これが今まで欠けていた中身である。D662 は受入 lease の待ち行列を廃止したので、他 wave が
lease を保持していても受入は進む。その走行には**取得が無い**。

**本 wave 自身の受入全走が、たまたまこの経路だった。** 走行は
`acceptance succeeded; lease was not acquired` を出力し、排他権を 1 度も取得しないまま
受領証を発行した。その受領証を保存した (`nonholding-run-receipt.json`)。中身は次のとおり。

- lease に関する field は **`lease_holder` の 1 つだけ**である。
- その値 `65a08fd3d486` は `sha256("dev-wave-t2148-lease-generation-probe")[:12]` と
  **完全に一致する**。

着地ツールは同じ関数を独立に計算して等しいかだけを見るので、**排他権を保持しなかった走行の
受領証は、保持した走行の受領証と lease の証拠において区別できない。** これはコード読解ではなく
本番経路の観測である。

現行コードの構造は次のようになっている (以下は**コード読解**)。

- 保持している走行は、受領証を出す前に `held-self` を再確認し、holder と main の一致と
  最小 TTL 残量を要求する (`tools/dev_wave_wait.py:3906-3960`)。live な取得への束縛が実在する。
- **保持していない走行は、その確認が丸ごと飛ぶ** (`:3907` の `if not claim_context.unclaimed:`)。
- しかも holder は lease から読むのではなく `sha256(wave 名)[:12]` として**その場で合成される**
  (`:2903-2911`)。
- 着地ツールも同じ `sha256(acceptance_wave)[:12]` を独立に計算し、受領証の `lease_holder` が
  それと等しいかだけを見る (`tools/dev_wave_land.py:792-800`)。

つまり `lease_holder` は **wave 名の純関数**であり、排他権を保持したかどうかの情報を
1 bit も運んでいない。着地側の照合は lease の保持に関して恒真である。

**世代を受領証へ足しても、wave が手元で合成できる値である限り同じ構造が再生産される。**
D906 が却下欄で名指しした「署名だけを足して鍵の置き場を決めない = 恒真になる」形にそのまま当たる。

D1449 は非保持走行を着地不可にする方向を明示的に不採用としている。したがって、
**取得ごとの粒度を採るなら「取得が無い走行の世代」を別に定めなければ意味論は完成しない。**

---

## 5. 移行窓の費用 — 「2400 秒で回復する」は誤り

`probe5-ttl.jsonl` の実測。世代 field 入りの payload に対して:

| 経過 | status | 保持者の release | 他 wave の claim |
|---|---|---|---|
| 0 秒 | unavailable | unavailable | unavailable |
| 2399 秒 | unavailable | unavailable | unavailable |
| 2401 秒 | stale | **unavailable** | **acquired** |
| 2401 秒後に新実装が renew | unavailable | unavailable | unavailable |

回復は「TTL 超過かつ誰も renew していない」ときに、**他 wave が剥奪する形でだけ**起きる。
保持者自身の release は TTL 後も回復しない。新実装が renew を続ける限り、旧実装の停止は
無期限に延びる。

なお着地ツールは、renew が `unavailable` でも `land(request)` を実行する
(`tools/dev_wave_land.py:5628-5650`)。renew と release の結果は stderr へ印字されるだけで
着地の結果を左右しない (`:5712-5720`)。**これはコード読解であり、実走していない。**
着地を測定目的で起動していない (main を進める操作だから)。

---

## 6. 定常費用 — 残留と掃除主体

`probe1-placement.jsonl` の release 後の directory の中身。

| 置き方 | 旧 reader への影響 | release 後に残るもの | 掃除主体 |
|---|---|---|---|
| 別 file を併置 (3 種いずれも) | **無し** (baseline と完全同値) | その file | **未定義** |
| hardlink を併置 | 無し | hardlink 名 | 未定義 |
| companion directory | 無し | directory | 未定義 |
| **xattr** | 無し | **何も残らない** | **不要** |
| lease dir の外の台帳 | 無し | 台帳 | 未定義 |

`release` が消すのは `acceptance.lease` と `ticket.` 接頭辞の file だけである。
**xattr だけが lease の unlink と同時に消えるため掃除を要しない。**
xattr はこの filesystem で読み書きできることを実測した (`user.izanagi_lease_generation` を
書いて読み戻せた)。ただしこれは使い捨て directory での観測であり、本番の directory の
権限・filesystem・並行条件は測っていない。

---

## 7. 候補の分類 (裁定用)

粒度を「取得ごと」と置いた場合の分類である。粒度が変われば分類も変わる (3 節)。

**規律 2 に触れるので採れない**
- 固定名 `acceptance.lease` を世代付き名へ置換
- 固定 lease を世代 directory の下へ移動

**移行が壊れるので現行のままでは採れない**
- lease payload への field 追加 (乱数・時刻・単調計数のいずれも同じ)

**取得ごとの粒度では恒真 (別の粒度なら正しい表現になる)**
- 現行 payload bytes の hash / holder と main の hash / wave 単位 / main 単位 / lease dir 単位
- 呼び手が `--lease-generation` で issuer へ渡す現行の形。issuer は値を live lease から
  導出せず、期待値も同じ呼び手由来なら「渡した値と渡した値が等しい」だけになる
  (`tools/acceptance_issuer_reference.py:15,442-464,513-527`)

**shortlist (移行互換で、取得ごとに変わりうる)**
- lease file の inode (payload 不変。ただし birth time が取れず再利用を区別できない)
- xattr (掃除不要。ただし値を書く主体が現行の producer なら、同じ主体が値を選べる)
- 保護された sidecar / 外部台帳 (D906 に最も直接対応する。ただし現行 consumer は読まない)

**shortlist のうち、値を書く主体が現行の producer である版はすべて再送に弱い。**
同じ主体が値を選べるなら、旧受領証の世代を新しい lease へ書き直せば照合は再び一致する。
再送防止には「同一 context の再取得で旧値を再利用できない」ことが要り、
「再取得で別値になり得る」だけでは足りない。

---

## 8. この材料でできること・できないこと

**できる:** 規律 2 に触れる候補の棄却、移行が壊れる候補の棄却、恒真な候補の識別、
shortlist の確定、そして**粒度の裁定**。

**できない:** shortlist からの最終採用。理由は 3 つある。

1. 現行の着地ツールは signed-v6 の検証器を呼ばず v5 を受理する。世代を強制する
   production consumer が存在しない (`tools/dev_wave_land.py:94-130`、reference issuer は
   production から未接続)。
2. 鍵と発行権限の配置は人間の手番であり (D906、D1400)、AI は代行しない。外部主体が
   実在するかを本 wave では測れない。
3. 使い捨て directory は本番 directory と同値でない。xattr・inode・保護された sidecar・
   外部台帳を積極採用する根拠には、本番と同じ filesystem・権限・並行条件での証拠が要る。

**測っていないもの:** 混在しうる過去版 reader、着地ツールの実走、外部署名主体、
移行窓で影響を受ける wave の絶対数 (rollout 時の旧版稼働数に依存するため測れない)。

---

## 9. consumer の閉包

`tools/wave_land_window.py` を import または subprocess 起動する実体は 6 件である。

| 種別 | consumer |
|---|---|
| production | `tools/dev_wave_wait.py:2722-2733` (CLI を subprocess 起動) |
| production | `tools/dev_wave_land.py:44,5634-5637,5696-5700` (import して renew/release を直接呼ぶ) |
| 直接テスト | `orchestrator/tests/test_wave_land_window.py` |
| 直接テスト | `orchestrator/tests/test_dev_wave_wait.py` |
| 推移テスト | `orchestrator/tests/test_dev_wave_land.py` |
| 推移テスト | `orchestrator/tests/test_resume_gate_acceptance_boundary.py` |

`tools/acceptance_receipt_signature.py` と `tools/acceptance_issuer_reference.py` は
世代の consumer ではあるが、`wave_land_window` を import しないのでこの閉包には入らない。

---

## 10. 測定と推論の区別

| 事項 | 出所 |
|---|---|
| 1 節の 4 操作すべて `unavailable` | **実走** (P1) |
| 受入が `rc=70` / `claim-state` で止まる | **実走** (P3、production 入口) |
| 2 節の排他が開く 2 例 | **実走** (P1) |
| 3 節の粒度表 | **実走** (P2) |
| 5 節の TTL 4 分岐 | **実走** (P5) |
| 6 節の残留と xattr の可否 | **実走** (P1) |
| 4 節の「非保持走行の受領証は保持した走行と区別できない」 | **実走** (本 wave 自身の受入全走。受領証を保存した) |
| 4 節の残り (確認が飛ぶ位置、識別子の合成位置) | **コード読解のみ** |
| 5 節の着地ツールが renew 失敗で止まらないこと | **コード読解のみ。実走していない** |
| 8 節の 1 と 2 | **コード読解と既裁定** |

4 節を専用 probe で実走しなかった理由: 受入は main に遅れているとき post-claim merge を
実行して wave branch に merge commit を作る (`tools/dev_wave_wait.py:3671-3690`)。
非保持走行を probe として起動すると、測定の副作用で branch が動く。所見自体は書く側と
読む側の 2 箇所の単純・無条件なコードで確定しており、実走が足す証拠は限界的だと判断した。

**結果として専用 probe は不要になった。** 本 wave の受入全走そのものが非保持走行になり、
その受領証が本番経路の観測を与えた (4 節)。判断の前提だった「実走が足す証拠は限界的」は
外れており、受領証の field 集合と値は読解だけでは確定できなかった。

---

## 11. 再現方法

probe は repo 外に置いた使い捨て script である。逐語は `verbatim/probe*-script.md`。
本番の lease directory を使わないこと。`--lease-dir` で使い捨て directory を明示すること。

```
python3 <job>/artifacts/probe1_placement.py     # 60 行の配置 matrix
python3 <job>/artifacts/probe2_derivation.py    # 導出値の粒度
python3 <job>/artifacts/probe3_acceptance.py    # production 入口の受入
python3 <job>/artifacts/probe5_ttl.py           # TTL 前後の分岐
```

段 2 の計画と段 3 の 2 レンズの逐語は `verbatim/s2-plan.md`、`verbatim/s3-lensA.md`、
`verbatim/s3-lensB.md`。段 4 の裁定は `verbatim/s4-adjudication.md`。
