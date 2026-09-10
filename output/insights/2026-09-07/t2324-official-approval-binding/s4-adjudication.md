# [T-2324] 段 4 裁定 — 床値 official の §8 承認束縛

base main = d19d2182f (段 4 直前に `--ff-only` で取り込み。f486ff13c..d19d2182f は本 wave の編集面に
1 file も触れていない)。裁定 inbox 再走査で wave 開始後の新規更新はなし。

## 0. 方式の再裁定はしない

D926 が方式を確定している。段 2 / 段 3 のいずれも方式そのものへの反証を出していないので、
実装方向は D926 のまま進める。

## 1. 親 brief の自己訂正 (段 3 が反証した親の記述)

- **(訂正 1) 不変条件 1 の「副作用より前」は誤り。** `_run_campaign_core` の入口
  (`orchestrator/campaign/s8b_floor_campaign.py:7256-7258`) で
  `floor_job_checkpoint.take_checkpoint_environment(os.environ)` が `os.environ.pop` を行い、
  これは現在の gate (`:7304`) より前にある。正しい不変条件は
  **「build 呼出し・driver 子 process 起動・cell claim 予約・一回性 key の消費・
  filesystem 書き込みより前」**である。
- **(訂正 2) 成果物影響の書き方。** 正しくは
  「**起動と API の受理集合はこの commit で変わる。測定値と freeze / certified の選択結果は
  実投入まで変わらない。nonce 束縛の保証が及ぶのは標準投入経路だけ**」。
  「標準投入経路でだけ起動可能になる」は raw `qsub` / CLI 直呼び / Python API 直呼びまで
  塞ぐ意味に読めるので使わない (D926 が明示的に保証範囲外としている)。
- **(訂正 3) N4 の DW-G04 witness から `output/s8b-freeze-budget-approvals/g1.json` を外す。**
  g1 は投入器・job・driver のどこからも読まれず、official result 後の v2 candidate 生成
  (`orchestrator/campaign/s8b_holdout_freeze.py:2014` 付近) で初めて読まれる。
  正しい witness は既存 `output/s8b-freeze/floor_protocol.json`、既存 hydrate 経路
  (`tools/pegasus/fetch_third_party.py`)、D1628 の reservation 束縛既定 transport、
  実装後の新しい source commit と job script blob である。
- **(訂正 4) 変更面表は 13 行ではなく 14 行。** 位置の訂正は §4 の表に反映した。
- **(訂正 5) (P1) の根拠。** `between_run_noise_*.json` 3 件の実在だけからは producer を
  同定できない (JSON に producer identity が無い)。結論を支えるのは
  `orchestrator/campaign/between_run_floor.py` が独立の入口として存在することと、
  production の `.sh` / `.py` に `submit_floor.sh` を起動する consumer が 0 件であること。

## 2. 所見の裁定

### real・採用 (実装する)

| ID | 内容 | 裁定 |
|---|---|---|
| A-1 / B-2 | 固定 official + 「承認 env 未設定なら flag を渡さない」で、承認なし通常投入が staging・qsub・receipt・予約・依存 build を消費してから driver で拒否される | **real。§3 の分割裁定で解く** |
| A-2 | 同投入の failure stage が `floor_driver` と誤分類される | **real。§3 で標準経路は解消。非標準経路は保証外として機構を足さない** |
| A-3 | 未設定・空文字・不一致を 1 文言にまとめると failure artifact から判別できない | **real・採用。空文字と不一致を別文言にする** |
| A-4 | public gate の独立した歯が変異で帰属できない (先段 authority と private core が隠す) | **real・採用。§5 の M-3 / M-4 で正例の被験体を名指しする** |
| A-5 | 空文字用 `-z` に独立した歯が無い (nonce が hex 検証済みなので `!=` でも必ず拒否) | **real・採用。A-3 の文言分離で歯を作る** |
| A-6 / B-7 | 親の producer 根拠と g1 witness の誤り | **real・採用。§1 の訂正 3 / 5** |
| A-7 / B-6 | 変更面表の件数と位置のずれ | **real・採用。§4 の表** |
| B-1 | `$NONCE` の `,` / 改行 guard は到達不能で、変異も帰属しない | **real・採用。guard と専用テストを plan から外す** |
| B-3 | `orchestrator/tests/test_ccbench_spawn_sites.py` が `s8b_floor_campaign.py` の sink を 4705 / 8625 行で厳密固定し、自己 golden も同値を要求する | **real・採用。同じ変更単位で 2 lineno を両所更新する** |
| B-4 | docs の更新帯が計画より広い (README 260 行、restart runbook 165-260 / 448-449) | **real・採用 (一部)。§6 参照** |
| B-5 | 成果物影響の記述 | **real・採用。§1 の訂正 2** |

### real・採用しない (scope 外。報告する)

| ID | 内容 | 裁定 |
|---|---|---|
| B-4 の一部 | `docs/phase3-8b-restart-runbook.md:262-272` の W-3 が「candidate producer 不在」と書くが `generate-v2-candidate` は実在する | **real だが本 wave の変更が原因ではない。scope 外。§6 と worklog へ次の一手として起票する** |
| A-2 の非標準経路 | raw `qsub` で承認 env を省いた job は build を消費してから driver で拒否され、stage も誤る | **real だが D461 / D926 が保証範囲外と明言した経路。機構を足さない (DW-G05)** |

### refuted (実装しない)

- **A-8** 承認 gate の恒真化経路は無い。
- **A-9** 標準 job 内で approval nonce と検証済み receipt nonce がすり替わる経路は構成できない。
  よって検査を receipt validation の後へ動かす必要はなく、早い位置 (fail-closed の向き) を採る。
- **A-10** CLI / API / resume / sub-command / mode 省略記法から承認値なしで core へ到達する経路は無い。
- **A-11 / B-11** N1・N2・N3・N5 は成立する。
- **A-12 / B-8 / B-9** D926 が不変とした 4 面への間接変更は無く、却下肢も復活していない。
- **B-10** (P2) は支持される。`s8b_holdout_freeze.py` は文言だけ直し挙動は変えない。
- **B-12 / B-13** `test_official_perf_closure.py`・`conftest.py`・`admission_registry.json`・
  `hooks/` の登録更新は不要。
- **B-14** production 層の取り残しは無い。
- **B-15** DW-G04 を理由に設計メモへ戻す必要は無い。
- **B-16** delimiter guard を除く主要変異は専用テストへ帰属できる。

### 親が段 3 の合意を反証した 1 件

- **(P4) 承認 gate を `take_checkpoint_environment` より前へ動かさない。**
  plan が前倒しを提案し、段 3 の 2 レンズがどちらもそれを妥当と認めた。**親は必要性を反証する。**
  - 前倒しが解決するのは「未承認 official の直接 API 呼出しで `os.environ` が pop されること」だけで、
    artifact も一回性 key も filesystem も動かない。拒否後は process が終わる。
  - `take_checkpoint_environment` の docstring が言うとおり、この pop は
    **計測される子 process に診断用 env を継承させない**ための無条件の隔離である。
    `orchestrator/tests/test_pegasus_floor_tools.py:1337-1375` はその保証を
    `_validate_mode` を番人にした 1 本の無条件テストで押さえている。gate を前倒しすると
    このテストを承認状態で条件分岐する 2 本に割る必要があり、無条件の保証が条件付きへ弱まる。
  - D926 が要求するのは「承認検証を claim 予約より後へ置かないこと」であり、現在位置 (`:7304`) は
    `campaign_claim.acquire_claim` (`:7482`) と holdout observation reservation (`:7879`) の
    両方より前で、既存テスト
    `orchestrator/tests/test_s8b_floor_campaign.py:7285-7300` が
    `not out_root.exists()` (書き込み 0 回) を既に固定している。
  - 段 3 の 2 レンズは、親 brief の**誤った不変条件 (訂正 1)** を基準に妥当性を判定していた。
    直すべきは不変条件の書き方であって gate の位置ではない。
  - よって `_assert_official_permitted` の呼出し位置は `:7208` と `:7304` のまま動かさない。
    `orchestrator/tests/test_pegasus_floor_tools.py:1337-1375` は**変更しない**。

## 3. A-1 / B-2 の分割裁定 (本 wave の主要な設計判断)

alpha は「未設定も早期拒否へ強めろ」、beta は「brief を D926 の形へ弱めろ」と逆を主張した。
**両者を層で分ける。**

- **投入器 `tools/pegasus/submit_floor.sh` は、実投入 (非 dry-run) で承認引数が無ければ拒否する。**
  位置は argv 検証の直後、submission staging root の検査・`mkdir "$SUBMISSION_DIR"`・
  payload staging・claim root 作成・`qsub` のいずれよりも前。`--dry-run` は承認引数なしでも通す
  (PBS を消費せず、投入 interface の点検に要る)。
  - 理由: wrapper が official 固定になった以上、承認なしの実投入は**必ず** driver 拒否で終わる。
    早期拒否は新しい gate の新設ではなく、確定した無駄と誤分類された failure artifact を
    作らないことである。D926 は失敗文言と guard を同じ変更単位で直すことを明示している。
  - D461 が却下した「wrapper で無条件に承認 flag を渡す」には当たらない。人間が引数を渡さない限り
    投入が成立しないだけで、flag の付与は job 側の nonce 一致に依然として従属する。
- **job script `tools/pegasus/floor_campaign.sh` は D926 の形を literal に保つ。**
  - 承認 env が未設定 → flag を渡さない (driver が拒否する)。
  - 設定済みかつ空文字 → `write_failure 2 submit_binding` で build と driver より前に停止。**専用文言。**
  - 設定済みかつ不一致 → `write_failure 2 submit_binding` で同様に停止。**別の専用文言。**
  - 一致 → driver argv の末尾へ承認 flag を 1 個 append。
  - 理由: ここで未設定も停止させると、標準経路では append が実質無条件になり、
    D926 が却下した「固定 official wrapper が承認を無条件 append する」と静的検査で
    見分けが付かなくなる。条件付き append を条件付きのまま保つ。

## 4. 変更面 (訂正済み・14 行)

| # | file:line | やること |
|---|---|---|
| A1 | `orchestrator/campaign/s8b_floor_campaign.py:465-475` | `_assert_official_permitted(mode, confirm_official_floor_run)` へ。`is not True` で exact bool を要求 |
| A2 | 同 `:7207-7208` | public wrapper から承認を渡す。`_nondefault_campaign_seams` へは渡さない |
| A3 | 同 `:7304` | private core も同じ gate。**位置は動かさない** |
| A4 | 同 `:8393-8406` (`_parser`) | zero-arity `--confirm-official-floor-run` を追加。`:8435` の `--confirm-user-freeze` は別 parser・別目的なので触らない |
| A5 | 同 `:8599-8608` (CLI 拒否) と `:8625-8630` (`run_campaign` 呼出し) | 承認なし official だけ refuse。文言から `§8` を外す。CLI flag を bool で下流へ渡す |
| A6 | 同 `:42-45` と `:5163-5168` | module 説明と launch コメントを新しい gate の意味へ |
| B1 | `tools/pegasus/submit_floor.sh:7-11` (usage)、`:31-34` (初期値)、`:36-70` (parser)、argv 検証直後 (新設)、`:621` (export spec) | 承認引数、実投入時の必須化、nonce 値の承認 env |
| B2 | `tools/pegasus/floor_campaign.sh:545-552` | 承認 env の 3 分岐 (未設定 / 空 / 不一致) と `export -n` |
| B3 | 同 `:1200-1206` | 固定 official argv + 一致時のみ 1 個 append |
| B4 | 同 `:1329`, `:1360`, `:1377` | 失敗文言と job-result の mode を official へ |
| C1 | `orchestrator/campaign/s8b_holdout_freeze.py:932-941` | 拒否は残し、理由を「この v1 経路は世代別承認を検証しない」へ |
| C2 | 同 `:944-957` | docstring の理由を v2 側 authority (`s8b_ratified_freeze.load_ratified_freeze`) の責務分担へ |
| D1 | `orchestrator/tests/test_s8b_floor_campaign.py:775-825`, `:6347-6355`, `:6491-6493`, `:7081-7131`, `:7273-7300`, `:7547-7567`, `:7786-7809`, `:11068`, `:11508`, `:11788`, `:12636`, `:12776` | 正例・負例の対、非 seam 除外集合、call-order pin の逐語 |
| D2 | `orchestrator/tests/test_pegasus_floor_tools.py:2196-2219`, `:2222-2309`, `:2322-2340`, `:2533-2558`, `:2597-2628`, `:2709-2752`, `:2928-2999`, `:3898-3931`, `:4026-4143`, `:4208-4309` | 承認輸送、実 argv と token の二層、job-result / failure golden。**`:1337-1375` は変更しない** |
| D3 | `orchestrator/tests/test_ccbench_spawn_sites.py` の `_DEFERRED_GATE_MEMBERS` と `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink` | `s8b_floor_campaign.py` の 4705 / 8625 を実装確定後の lineno へ両所更新 (B-3) |
| D4 | `orchestrator/tests/test_s8b_holdout_freeze.py:1285-1301`、`orchestrator/tests/test_s8b_ratified_freeze.py:940-963` | 拒否継続と新理由、gate monkeypatch を実引数へ |
| E1 | `tools/pegasus/README.md:217-260`、`docs/phase3-8b-restart-runbook.md:49`, `:165-260`, `:448-449`、`docs/pegasus-runbook.md:1641-1645`、`docs/phase3.md:112-126` 付近 | 親が書く (D95) |

## 5. 変異事前登録 (DW-M01。実装前に登録し、実装後に単一理由性を確認する)

| ID | 位置 | 変異 | 赤にする専用テスト | 単一理由性の確認 |
|---|---|---|---|---|
| M-1 | `floor_campaign.sh` の一致時 append | `if` を外して無条件 append | 「未設定時の実 argv に承認 flag が無い」 | 未設定経路は他の gate を通らない |
| M-2 | 同 | append を 2 回にする | 「一致時の実 argv 完全一致」と `count == 1` | 同上 |
| M-3 | `s8b_floor_campaign.py:7208` | public gate の呼出しを削除 | public 未承認負例。**protocol authority を通る有効な protocol/freeze を渡し、private core を sentinel 化して「private core へ到達したこと」自体を赤にする** (A-4) | 先段 authority が拒否しない入力を使い、private core を被験体として名指しする |
| M-4 | 同 `:7304` | private core の呼出しを削除 | private core 直呼びの未承認負例。**downstream 未到達 sentinel と exact 拒否文言を要求する** | CLI / public を経由しないので先段の拒否が隠せない |
| M-5 | `_assert_official_permitted` の `is not True` | `if not confirm` へ緩める | `False` / `None` / `1` を拒否し exact `True` だけ受理する負例 | `1` は truthy なのでこの変異だけが赤にする |
| M-6 | `floor_campaign.sh` の空文字分岐 | 空文字分岐を削除 | 「設定済み空文字を空文字専用文言で拒否する」 | A-3 の文言分離により不一致分岐では拾えない |
| M-7 | 同の不一致分岐 | `!=` 比較を削除 | 「別 nonce を不一致専用文言で拒否する」 | 空文字分岐では拾えない |
| M-8 | `floor_campaign.sh:1202` | `--mode official` を `pilot` へ戻す | token inventory (`--mode` は 1 個、直後は `official`) と実 argv 完全一致 | mode 受け口が無いので他の層は発火しない |
| M-9 | `submit_floor.sh` の実投入必須化 | 必須化の条件を削除 | 「非 dry-run で承認引数なしなら submission dir 作成と qsub より前に rc=2」 | dry-run 経路は別条件なので隠さない |
| M-10 | `s8b_floor_campaign.py` CLI 拒否 | CLI 拒否を削除 | CLI 未承認 official が rc=2 / `status=refused` で protocol loader 未呼出し | core 拒否は例外を投げるので rc と出力形が違い、区別できる |
| M-11 | `s8b_holdout_freeze.py:932-941` | 世代 document 拒否を削除 | 既存の `test_verify_rejects_unratified_generation_documents` | 挙動不変の裁定に対する回帰検査 |

`-z` 単独削除 (旧 A-5) は M-6 として登録する。文言分離をしなければ同値変異になるため、
文言分離は M-6 成立の前提である。

## 6. docs (親が書く)

- `tools/pegasus/README.md:217-260` — 投入 command を承認引数付きへ。旧 failure 文言 (260 行) も直す。
- `docs/phase3-8b-restart-runbook.md`
  - `:49` と `:165-197` — 固定 pilot / official 空集合の現行運用記述を、固定 official + 明示承認へ。
  - `:229-241` — 投入手順を承認引数付きへ。
  - `:244-252` — 走行後の退避手順。**official result は repo 相対 path から
    `_validate_floor_inputs` が読むので、pilot と同じ即時退避を official へ引き継がせない。**
  - `:448-449` — 「固定 pilot 経路で走らせる」の決着文を現況へ。
  - pilot の完走実績は dated history として分離して残す (規律 7)。
- `docs/pegasus-runbook.md:1641-1645` — sanctioned な投入は承認引数付き `submit_floor.sh` だけであり、
  raw `qsub` を組み立てないこと、raw 経路は nonce 束縛の保証外であることを追記。
- `docs/phase3.md:112-126` 付近 — dated history は残し、T-2324 による supersede と
  起動受理集合の変更を現況として追記。
- `docs/decisions.md` の D323 / D324 / D461 / D926、`docs/failures.md`、dated paper-story、
  archive worklog、既存 insight は書き換えない。
- **W-3 (`docs/phase3-8b-restart-runbook.md:262-272`) の「candidate producer 不在」は本 wave の
  変更が原因ではないので直さない。** 次の一手として起票する。

## 7. scope 外 (実装しない)

- `$NONCE` の delimiter guard とその構造テスト (B-1)。
- raw `qsub` 経路のための failure stage 精密化 (A-2 の非標準経路)。
- W-3 の producer 不在記述の是正 (B-4 の一部)。
- `REFREEZE_DISQUALIFYING_SEAM_NAMES`、`_derive_refreeze_eligibility`、
  submission receipt schema、admission claim key 6 項目、
  `test_official_perf_closure.py`、`conftest.py`、`admission_registry.json`、`hooks/` の変更。
- 承認 gate の位置変更と `test_pegasus_floor_tools.py:1337-1375` の分割 (P4)。

## 8. 段 5 の分割 — 1 単位にする

brief は U1 / U2 の 2 単位を予定していたが、**1 単位へ改める。** 理由は次の 3 点である。

- U2 は U1 が確定する signature・flag 名・lineno を前提にするので、2 単位は**並列にならない**。
  素集合分割は並列投入のためにあり、直列な依存では patch 移植の手番だけが増える。
- D3 (`test_ccbench_spawn_sites.py` の 4705 / 8625) は U1 の編集で行がずれた後にしか確定しない。
  分割すると「U1 の確定を待って U2 が入れる」という単位間 handshake になる。
- テスト層は shell の実 argv と Python の parser を同じテストで突き合わせる (D324 の二層) ので、
  実装と検査を単位で割ると片側だけ緑の状態が生じる。

したがって編集 path 所有は 1 単位が全部持つ。

- 所有 path: `orchestrator/campaign/s8b_floor_campaign.py`、
  `orchestrator/campaign/s8b_holdout_freeze.py`、`tools/pegasus/submit_floor.sh`、
  `tools/pegasus/floor_campaign.sh`、`orchestrator/tests/test_s8b_floor_campaign.py`、
  `orchestrator/tests/test_pegasus_floor_tools.py`、
  `orchestrator/tests/test_ccbench_spawn_sites.py`、
  `orchestrator/tests/test_s8b_holdout_freeze.py`、
  `orchestrator/tests/test_s8b_ratified_freeze.py`。
- 名前は親が固定する: CLI `--confirm-official-floor-run`、env
  `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN`、Python keyword `confirm_official_floor_run`。
- docs (E1) は親が段 7 で書く。実装子は docs を触らない。

## 9. 通る正例 (DW-S04: gate の禁止は署名で書き、通る正例を 1 つ添える)

```
tools/pegasus/submit_floor.sh --confirm-official-floor-run
  → qsub -v IZANAGI_SUBMISSION_NONCE=<n>,IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=<n>
  → floor_campaign.sh が <n> == <n> を確認し driver argv 末尾へ --confirm-official-floor-run を 1 個
  → s8b_floor_campaign.py --mode official --protocol <p> --confirm-official-floor-run
  → CLI gate 通過 → run_campaign(confirm_official_floor_run=True) → core gate 通過 → campaign 実行
```

禁止側の署名:

- `_assert_official_permitted(mode: str, confirm_official_floor_run: bool) -> None`
  — `mode == "official" and confirm_official_floor_run is not True` を拒否する。
- `submit_floor.sh` — 非 dry-run かつ承認引数なしを、submission dir 作成前に rc=2 で拒否する。
- `floor_campaign.sh` — 承認 env が設定済みで submission nonce と exact 一致しないとき
  (空文字を含む) を、build と driver より前に `write_failure 2 submit_binding` で拒否する。
