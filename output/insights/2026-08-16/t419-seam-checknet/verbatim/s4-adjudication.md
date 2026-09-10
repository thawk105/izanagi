# 段 4 裁定 — [T-419] 択 (c) seam + 検査網

2026-08-16 19:40 JST / wave `t419-seam-checknet` / base main `98df871b`

## 0. 裁定の骨子

段 3 は 2 レンズとも NO-GO を返した。**親は両方を real と認め、プラン v1 を採らない。**
ただし「実装しない」ではない。両レンズが独立に示した構造は次の 1 文に要約できる。

> 択 (c) が禁じた活性化を行わない限り、**受理集合を狭める production gate を置ける位置は
> 「次の世代を active にしてよいか」の 1 箇所しかない。** そこ以外に置くと、
> 今日の経路を壊すか (A-04/B-02)、他層に覆われるか (A-03)、今日の受理集合を変える (B-03)。

したがって裁定は「gate は活性化の後継判定へ集約し、それ以外は検査網 (テスト層) へ置く」である。
これは裁定文の語そのものにも合う — 前 wave の択一 §6 (c) は
「seam と **test-net** の hardening」と書いている。

## 1. 所見の裁定

| ID | 判定 | 扱い |
|---|---|---|
| A-01 名指しできる実在入力が無い | **real** | 採用。gate を活性化の後継判定へ集約し、そこで実在 g1/g2 を正負例にする |
| A-02 resolver の複数候補拒否は上流で到達不能 | **real** | 採用。この分岐を変異事前登録から外す。テストも書かない |
| A-03 S2/S3 が S4 catalog audit に覆われる | **real** | 採用。catalog audit を production から外し検査網 (テスト層) へ置く。これで mask が消える |
| A-04 g1 grandfather は規律 2 に反し恒久化する | **real** | 採用。**g1 例外を作らない。** 歴史 resolver に自己整合 gate を置かない |
| A-05 例外鍵 (contract, calibration) は過剰決定 | **real** | 採用。例外自体を作らないので消滅 |
| A-06 seam が bytes 束縛を失う | **real** | 採用。resolver は `IndexedFloorProtocol` を返し、admission は再読 bytes を SHA で再照合する |
| A-07 acquisition receipt は自己申告の内部整合 | **real** | 採用。ただし scope 内。「外部証明ではない」ことを worklog へ明記し、外部束縛は T-657 上位束へ残す |
| A-08 (i) の第 3 の形 | **real** | **採用。これが本裁定の中核。** 下記 §2 |
| A-09 編集面に source closure pin が実在 | **real** | 採用。M-G を訂正。影響は §4 |
| B-01 floor 実投入 shell と 5 module が scope 外 | **real** | **部分採用。** Python 側は seam と一致検査で閉じ、shell の rewire は裁定パッケージへ返す |
| B-02 resolver 6 consumer と g1 例外 | **real** | A-04 と同一。g1 例外を作らないことで解消。(ii) の後ろ向き半分は裁定へ返す |
| B-03 catalog audit は受理集合を変える | **real** | 採用。A-03 と同じ処置 (テスト層へ) |
| B-04 通常 loader の callback 配線漏れ | **real** | 採用。`env_contract.py:524` の loader 呼出しも composite へ寄せる。3 経路すべて |
| B-05 P3 は path の一意性を authority と取り違え | **部分 real** | 一意性が承認を意味しない点は正しい。ただし本 wave は**新しい選択面を作らない**ので受理は広がらない。上位束が来たとき resolver 1 箇所を差し替えれば済む形にする |
| B-06 method gate を外すのは裁定と矛盾 | **real** | 採用。A-08 の形で実装する。§2 |
| B-07 M-E の全文検索 0 件は反証済み | **refuted** | 検索対象は 8/16 の裁定パッケージ側であり、本 wave が書いた brief/plan/handoff は母集合ではない。ただし §2 のとおり M-E の一般化自体は縮小する |
| B-08 M-G は source commit trust を見落とし | **部分 real** | A-09 の方が鋭い。A-09 で置き換える |
| B-09 新規テストの自己参照と過剰決定 | **real** | 採用。負例は 1 面 1 理由に分ける。§3 |
| B-10 strict cache の TOCTOU 主張が未証明 | **real** | 採用。strict cache を作らないので消滅 (歴史 resolver を触らない) |

## 2. 従属 3 問の確定 — (i) は「活性化の後継判定」で実装する

前報告の「(i) を丸ごと差し戻す」は**取り下げる。** レンズ A の A-08 が正しい。

- M-E の一般化は縮小する。`docs/failures.md` の F339 は
  「値の一致を要求すると方式改訂で全 attestation が落ちる」「是正は活性化と対で行う必要がある」
  まで記録しており、**実害の中身は裁定時に記録されていた**。伏せられていたのは
  「これは D329 という**ユーザー裁定**である」という一点だけである。
- **実測 (親、本 worktree HEAD)**: `effective_clock.method` を現行 probe 定数
  `EFFECTIVE_CLOCK_METHOD` と exact 比較すると、**g2 は True、g1 は False** である。
- **実測 (親、M-I)**: `env_contract_activation.py:395` は `previous_rows is not None` の
  ときだけ後継判定を呼ぶ。活性化記録は genesis 1 本 (serial=1) なので、
  **後継判定はいま production で一度も呼ばれない。**

したがって後継判定に置く実体一致は、**今日の受理集合を 1 bit も変えず、未来の世代交代だけを狭める。**
D329 の理由 (「probe を改良すると過去の登録が構造的に attestation を通れなくなる」) とも
衝突しない — 遡って過去の登録を落とすのではなく、**これから active にする世代へ
「現行 probe と同じ方式で取られたこと」を要求する**だけだからである。

確定:

- **(i)** = 活性化の後継判定で `successor.calibration.effective_clock.method` と
  現行 probe 定数の exact 一致を要求する。**実行時 attestation (`_recorded_verdict`) は触らない。**
  その残余 (実行時も実体一致にするか = D329 の可否) だけを裁定へ返す。
- **(ii)** = 同じ後継判定で自己整合 (帯外 0 件) を要求する。これで
  「自己不整合な較正が新たに ever-active になる」経路は閉じる。
  **既に ever-active な g1 の扱い**は実装せず裁定へ返す — 8/16 の裁定パッケージは
  「g1 期成果物の**歴史**検証が落ちる」と書いたが、実測では歴史専用ではなく
  **live campaign の COMMIT 監査 (`wal.py:1064`)・floor admission・reflux closure を含む
  6 consumer** が止まる。これは裁定時に記載されていない事実である (`DW-S04`)。
- **(iii)** = 同じ後継判定で content-addressed path と acquisition receipt の内部束縛を要求する。
  根拠は `quality.status=accepted` だけでなくなる。**外部取得証明ではない**ことを明記する (A-07)。

## 3. プラン v2 (確定 scope)

**単位 A — 活性化の後継判定 (S2 前向き + S3 + (i))**

- `env_contract.py` に composite activation admission を追加する。構造判定
  `_is_valid_activation_successor` は無変更で残し、その後段に artifact 判定を足す。
- 要求 4 面: (1) 自己整合 = 帯外 0 件、(2) `effective_clock.method` が現行 probe 定数と exact 一致、
  (3) calibration path が content-addressed、(4) acquisition receipt の内部束縛が成立。
- 配線は **3 経路すべて** — 通常 loader (`env_contract.py:524`)、`ident.py`、
  `tools/issue_env_contract_activation.py` (B-04)。
- `_verify_entry_calibration`、歴史 resolver、strict cache、g1 例外は**作らない・触らない**。

**単位 B — floor protocol seam (S1)**

- `s8b_floor_campaign.py` に、index から current contract hash 一致の record を exact 1 件返す
  resolver を足す。引数は root だけ。**選択条件に ccbench pin を入れない** (M-J: 今日 0 件になる)。
- resolver は `IndexedFloorProtocol` を返し、`certified_writer_admission.py` は
  **再読した bytes の SHA を record と再照合してから** `validate_protocol_against_current` する (A-06)。
- 複数候補拒否の分岐は追加しない (A-02)。

**単位 C — 検査網 (S4、テスト層のみ)**

- 自己整合・policy 同一性の走査を `ec.REGISTRY` (2 件) から
  **registered catalog ∪ ever-active (3 件)** へ広げ、exact 件数を固定する。
- 未 active g2 のみを壊す drift 負例を足す (今日 1 件も検査されていない面)。
- floor protocol path literal を持つ全 module と shell wrapper の値が resolver 結果と
  一致することを固定する meta-test を足す (B-01 の Python 側を閉じる)。
- **production の authority load へ catalog audit を入れない** (A-03/B-03)。

**裁定へ返す (実装しない)**

1. 実行時 attestation の method 実体一致 (D329 の可否)。
2. 既に ever-active な g1 の自己不整合の扱い (6 consumer が止まる実測つき)。
3. floor path の shell wrapper・driver 層の rewire (B-01 の残り)。

## 4. `DW-O09` の訂正 (A-09)

M-G は誤りだった。`campaign_lock.py:29-42` の `CONTRACT_LOADER_RELATIVE_PATHS` は
**exact 12 path の enforcement source closure** で、本 wave が編集する
`env_contract.py` / `env_contract_activation.py` / `ident.py` を含む。
`contract_loader_binding.py` が記録 commit blob と live bytes を照合し、
`ident.py:365` が不一致を `contract-loader-drift` で拒否する。

**親の実測**: 該当形式 (v2、`identity_preimage` を持つ) の campaign.lock は
`output/campaigns/` の 32 件中 **0 件**である。したがって既存 campaign の再開は壊れない。
新規 lock の `contract_loader_blob_sha256s` は変わるが、これは記録であって測定量ではない。
凍結成果物の bytes は 1 byte も変えない。

## 5. 変異事前登録 (`DW-M01`)

各変異は「同じ入力を拒否する層が前後に無い」ことを確認した上で登録する。
期待 node は fix 後の最終 commit で `--junitxml` から再導出する (`DW-M07`)。

| # | 位置 | 変異 | 単一理由性 |
|---|---|---|---|
| 1 | composite admission の自己整合検査 | 常に True を返す | 構造判定は帯外標本を読まない。catalog audit は production に無い |
| 2 | composite admission の method 検査 | 常に True を返す | 実行時 attestation は非空検査のままなので前後層に無い |
| 3 | composite admission の content-address 検査 | 常に True を返す | 構造判定は path/SHA が共に変われば通す |
| 4 | composite admission の receipt 束縛検査 | 常に True を返す | 同上 |
| 5 | 通常 loader の callback | composite から構造判定へ戻す | 配線 3 経路のうち loader だけを戻す |
| 6 | `ident.py` の callback | 同上 | |
| 7 | issue tool の callback | 同上 | |
| 8 | floor resolver の contract hash 一致条件 | 無条件に先頭 record を返す | index は複数 path を上流で拒否するが、**hash 一致条件は resolver にしか無い** |
| 9 | admission の bytes 再照合 | 削除 | 再照合は他にどこにも無い (A-06) |
| 10 | 検査網の走査集合 | catalog ∪ ever-active → `REGISTRY` | 3 件 → 2 件になり g2 が脱落する |

**過剰拒否の正例 (受理集合を縮小する wave の必須登録)**

| # | 内容 | 期待 |
|---|---|---|
| P1 | 実在 g2 を後継とする serial 2 の後継判定 | **通る** (4 面すべて満たす) |
| P2 | 今日の authority load (serial 1) | **通る** (後継判定を一度も呼ばない) |
| P3 | 今日の floor admission | **通る** (resolver は現行 path と同一 record を返す) |

**負例の単一理由性 (B-09)**: g1 は自己整合と method の**両方**で落ちるため、
単独の負例に使わない。4 面それぞれに、その 1 面だけを壊した合成 successor を用意する。
実在 artifact の負例は「g1 の method」を method 面**だけ**の証拠として別枠で記録する。

## 6. 停止しない根拠

`DW-S04` は「承認済み裁定は裁定時の未見事実でだけ止め、親は不採用にせず新事実を添えて返す」と
定める。本裁定は 3 件を返すが、**裁定の中核 (seam + 検査網 + 従属 3 問の実装可能な面) は
すべて実装する**。返す 3 件はいずれも、実測で「今日動いている経路が止まる」または
「実装したふりになる層が残る」ことを示せたものだけである。
