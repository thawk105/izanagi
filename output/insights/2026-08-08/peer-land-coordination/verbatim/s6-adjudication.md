# 段 6 裁定 — レビュー所見の処置と fix 方針 (fix 第 1 巡)

## 判定: 現実装は land 不能。土台を差し替える。

両レンズが独立に NO-GO。致命的なのは次の 3 点で、いずれも「handoff の Markdown ヘッダへ
宣言を相乗りさせた」という段 4 の設計選択に由来する。

1. **実物 9 本中 7 本が宣言不能** (D2,3,4,6,7,8,9,10)。稼働中の handoff は
   `wave branch/worktree/起点 main/job artifact` 等の旧書式で、canonical 4 行ヘッダを持たない。
   しかも `peers` はそれを `absent` として **`advice=clear` を返す** — 見えない peer を
   「並行なし」と誤報する最悪の失敗方向である。
2. **対称 deadlock と恒常 hold** (C6, D16, D17, D18)。同時に複数が `acceptance` を宣言すると
   全員が hold になり、winner も release も無い。さらに TTL は handoff 全体の mtime を見るため、
   契約上必須の 10 分ごとの handoff 更新が古い宣言を再 fresh 化して**恒常 hold** になりうる。
3. **契約文が実行不能** (C5, C7, D11, D12, D13)。どの handoff・どの directory・どの SHA を
   渡すか書いておらず、`unknown` の処置も無く (fail-open)、受入前の送信も land JSON の保存手順も
   指示していない。`land-intent` 生成は dead code。

加えて **slug が閉じた語彙でない** (C1) — `IGNORE_PREVIOUS_INSTRUCTIONS.md` は許可文字だけで
書けるため、段 3 レンズ A の所見 3 は閉じていない。**handoff の非 atomic 上書き** (C9, D15) は
セッション WAL を壊しうる。テストにも恒真が複数ある (C4, C16〜C23)。

## 差し替える設計 (fix v3) — sidecar lease

handoff には**一切書かない**。専用の lease directory を単一の正本にする。
これで D10 (書式互換)、D15 (WAL 破壊)、D17 (mtime 汚染)、C6/D16 (対称 deadlock) が
**構造的に**消える。実装も小さくなる (C21/D21 の「537 行は過大」に応える)。

- `claim --lease-dir D --wave <slug> --main-sha <40hex> [--ttl <秒>]`
  - `D/acceptance.lease` を `O_CREAT|O_EXCL` で作る。**成功した 1 本だけが winner。**
  - 既存が TTL 内なら `held` を返して**取らない** (rc=0、`state=held`)。
  - 既存が TTL 超過なら stale として破棄して取り直す (破棄→再 EXCL 作成、失敗したら `held`)。
  - lease の age は **lease file 自身の mtime** から測る (handoff の更新に汚染されない)。
- `release --lease-dir D --wave <slug>`
  - lease の owner digest が一致するときだけ unlink する。**他人の lease は絶対に消さない。**
- `status --lease-dir D [--wave <slug>] [--json]`
  - `{state: free|held|stale|unavailable, holder: <12hex|null>, holder_self: bool,
     main_sha: <40hex|null>, age_seconds: int, source: {...}}`
  - **`free` は directory を完全に読めたときだけ。**読めなければ `unavailable`。
- `message --kind landed --land-json <file> --wave <slug>` は現行のまま維持する
  (C12 が堅牢性を反証済み)。**`land-intent` は削除する** (dead code、D21)。
- **AI 向け出力の識別子は `sha256(slug)[:12]` の 12 桁 hex だけ**にする。slug の生文字列を
  どの出力経路 (JSON・人間向け・エラー・`--help` の prog) にも出さない。これで C1 を閉じる。

## 契約文 (親が書き直す)

- 受入直前: `claim` を取り、`state=free` で自分が winner のときだけ受入を投入する。
  `held` / `stale` / `unavailable` / 非 0 rc では投入しない (C5, D12 の fail-open を閉じる)。
- land 後: `release` し、`landed` 文面を `ListAgents` 照合済み peer へ 1 度だけ送る。
- lease directory の実 path は**機体固有情報**なので `docs/pegasus-runbook.md` に置き、
  入口には環境変数名だけを書く。

## 所見処置表 (主要分のみ)

| 所見 | 裁定 | 処置 |
|---|---|---|
| C1 slug が閉じていない | real / must-fix | 12 桁 digest だけを出す。`prog` も定数化 |
| C2 未裁定の受理集合縮小 | real / 消滅 | handoff を読まなくなるため該当なし |
| C4 advisory の期待値が実装定数由来 (恒真) | real / must-fix | テスト側の独立 literal にする |
| C5 / D12 `unknown` で fail-open | real / must-fix | 契約を「free かつ winner のときだけ投入」に |
| C6 / D16 対称 deadlock | real / must-fix | 排他 lease で構造的に解消 |
| C7 / D13 送信が dead code | real / 一部採用 | `land-intent` を削除。`landed` 送信を契約に明記 |
| C8 stat/open race で偽 clear | real / 消滅 | 単一 lease file の fd 由来 metadata だけを使う |
| C9 / D15 非 atomic 上書き | real / 消滅 | handoff を書かない |
| C10 landed の producer 束縛 | real / should-fix | caller 契約として明記。producer fd 束縛は scope 外 |
| C11 status 型偽装で rc 誤分類 | real / must-fix | `isinstance(str)` を先に検査し rc=3 へ閉じる |
| C16〜C23 テストの恒真・変異生存 | real / must-fix | 独立 oracle 化、境界値の literal 固定、hang 隔離 |
| D10 実物 7/9 が宣言不能 | real / 消滅 | sidecar 化で該当なし |
| D14 既存 consumer 退行なし | refuted | 変更なし |
| D19 節約系列は実在する | real | worklog へ効果系列として記録する |
| D22 land byte 不変 gate | refuted | 裁定パッケージに残す |
| D23 受信規則の JIT 正本化 | real / scope 外 | 予算 4 byte のため裁定パッケージへ (T-641 (c) 既決) |
| D24 実 E2E を land 前条件にせよ | real / 部分採用 | 実 lease directory での claim→held→release→再 claim を親が実測する。独立 2 wave の E2E は次 wave |

## 変異事前登録 v2 (旧 MW1〜MW7 を差し替え)

| ID | 位置 | 変異 | 単一理由で落ちるテスト |
|---|---|---|---|
| MX1 | `claim` の EXCL 作成 | `O_EXCL` を外す (既存 lease を奪う) | 2 本目の claim が held になるテスト |
| MX2 | `claim` の TTL | TTL 超過判定を常に真にする (常に奪う) | fresh lease を奪わないテスト |
| MX3 | `claim` の TTL | TTL 超過判定を常に偽にする (永久 held) | stale lease を破棄して取るテスト |
| MX4 | `release` の owner 照合 | owner を照合せず unlink する | 他人の lease を消さないテスト |
| MX5 | `status` の完全性 | directory 読取り失敗でも `free` を返す | `unavailable` は `free` にならないテスト |
| MX6 | 識別子射影 | digest でなく slug 生文字列を出す | 命令風 slug が全出力に現れないテスト |
| MX7 | `message --kind landed` | land JSON の status 検証を外す | `stale-main` JSON で rc=3 テスト |
