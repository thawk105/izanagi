# 段 4 裁定 — real/refuted、plan v2、変異事前登録

## 総合判定

段 2 プランは **不採用**。両レンズが独立に NO-GO を出し、指摘は収束した。
親は brief の (P2)「可視化と通知に留める」を**撤回**し、**受入投入直前の宣言と保留**を機構の中心へ移す。
brief の (P1)「roster を補助として使う」も**撤回**し、roster を全面的に落とす。

## 裁定表 (レンズ A = 正しさ・信頼境界、レンズ B = 実効性・射程)

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| B1 | land **後**通知では 18 分の受入窓を閉じない | **real / 採用** | 機構の中心を「受入投入直前の land-intent 宣言 + peer 宣言の参照」へ移す |
| B5 | 受信側契約が無い (送る側だけの半機構) | **real / 採用** | 受信側規則を入口 (`.claude/commands/dev-wave.md`) へ同時に書く |
| B9 / A5 | 610 行・3 データ源 join は効果に対し過大。roster の `cwd` は全 worker が repo root で worktree を指さず、`intent` は複数 T-ID を含むため**現行データで一意 join は成立しない** | **real / 採用** | `wave_peers.py` を破棄。roster を使わない。宛先解決は親が `ListAgents` で行う |
| A3 | 制御文字除去と長さ制限は injection の無害化ではない。`purpose` / path / basename / branch の印字可能文字はそのまま親コンテキストへ入る (`git check-ref-format` は指示文 branch 名を受理する) | **real / 採用** | AI 向け出力を**閉じた語彙へ射影**する — sanitized slug、enum、40 桁 hex、整数だけ。目的文・path・branch 名は全モードで出さない |
| A4 / A1 | 固定 template は送信者を認証しない。`land_status` を caller が手入力すると偽の `landed` を通知できる | **real / 採用** | 受信通知は **local main を読み直す契機にだけ**使う (待機・取り込み・検査省略の根拠にしない)。`landed` 文面は保存済み land JSON からのみ生成し、`landed`/`already-landed` 以外では生成を拒否する |
| A6 / A9 | partial/unavailable のとき「0 件」「一意」と誤断定しうる | **real / 採用** | source が完全でなければ `advice=unknown` へ倒す。`clear` は完全取得時のみ |
| A2 / B10 | git ancestry では active と landed を区別できない | **real / 採用** | lifecycle は所有者が書く handoff 宣言を正本にし、git ancestry を使わない |
| B8 | 通知の収支。`rejected` / `lock-busy` / fold 失敗まで全 peer へ撒くのは損 | **real / 採用** | 送信は (i) 受入直前の `land-intent`、(ii) **成功 land** の `landed` だけ。失敗系は送らない |
| A7 | helper 5 秒 / 親 2 秒の timeout 矛盾 | **real / 消滅** | startup 統合 (S-B) を破棄したため該当なし |
| B2 | S-B は自動 caller が無く best-effort に留まる | **real / 採用** | S-B を破棄 |
| A11 | テスト名だけでは空実装・恒真 assert を排除できない | **real / 採用** | 「ちょうど 1 件の hold を返す」正例と、常時空・常時 unknown・全 raw 通過を殺す変異を事前登録 |
| A10 | `dev_wave_land.py` no-touch は所有宣言だけで機械 gate が無い | **real / 部分採用** | 本 wave は同ファイルを 1 byte も変えない。**byte 不変 gate の新設は scope 外** (新しい阻害 gate を作らない不変条件と衝突するため、裁定パッケージへ) |
| A15 | 「`git -C <他 worktree>` を repo hook が拒否する」という親の帰属は誤り。`hooks/guard_bash.py` の fast-path は read-only git を許可しており、実際の拒否は**外側の Claude harness の隔離**である | **real / 訂正を受諾** | brief・handoff の記述を訂正する。設計は他 worktree への git 参照を使わないので結論は不変 |
| A14 / B11 | 「並行 3 wave が同一予算を消費中」は snapshot であり、`DW-G03` の独立 2 例ではない | **real / 訂正を受諾** | 一般化を撤回。射程を「受入窓の追い越し削減」へ限定し、恒常的な族制度化を主張しない |
| B12 | brief の `DW-G05` 成果物影響は F157 を誤用 (T-641 は裁定 (c) で終端済み) | **real / 訂正を受諾** | 成果物影響を「worklog の受入 request / 実測参照が再走値へ差し替わる件数と秒数」へ書き換える |
| B6 | 「land 自体を新機構で直列化せよ」は反証 (既に lock 内で直列化済み) | **refuted / 同意** | `dev_wave_land.py` 現状維持を確定 |
| A13 | SendMessage 1 回の成功から配送保証へ一般化するのは誤り | **real / 採用** | best-effort・順序/即時/exactly-once 無保証と明記 |
| A16 | roster の unknown field 方針が未確定 | **消滅** | roster を使わないため該当なし |
| B3 | 経路全体が未発火 (宛先解決の実証が無い) | **real / 部分採用** | 宛先解決は親の `ListAgents` 照合に落とし、tool は宛先を作らない。段 1 で SendMessage の到達は実測済み。end-to-end の実運用実測は段 9 後の次 wave へ送る |
| B7 | handoff 宣言板の延長として `- land-window:` 1 行を足すのが最小 | **real / 採用** | plan v2 の中核に採用 |

## plan v2 (実装するもの)

### V-1 `tools/wave_land_window.py` (新規)

閉じた語彙だけを扱う小さい tool。roster を読まない。git を読まない。

- `declare --handoff <自分の handoff> --state idle|acceptance|landed [--main-sha <40hex>]`
  - **引数で渡された 1 ファイルだけ**を書く。directory 走査をしない。symlink・非 regular file を拒否。
  - `- land-window: …` 行**ちょうど 1 行**を作成または置換する。他の行の bytes を変えない。
  - `acceptance` / `landed` は `--main-sha` 必須 (40 桁 lowercase hex)。
- `peers --handoff-dir <dir> --self <自分の handoff> [--json] [--now <epoch>]`
  - 各 handoff から**射影された値だけ**を返す:
    `{slug, state, main_sha, age_seconds, declaration: present|absent|invalid}`。
    slug = basename から `.md` を除き `[A-Za-z0-9._-]` 以外を除去し 64 字で切る。
    **目的文・path・branch 名・自由文を一切出さない。**
  - `source: {status: ok|partial|unavailable, reason, scanned, invalid}`。
  - `advice`: 自分以外に `acceptance` または `landed` の宣言が TTL (既定 2400 秒) 以内にあれば
    `hold`、source が `ok` でそれが無ければ `clear`、それ以外は `unknown`。
    **`clear` は完全取得時のみ。**TTL 超過の宣言は hold にしない (死んだ session による飢餓を防ぐ)。
- `message --kind land-intent --main-sha <40hex> --wave <slug>`
  `message --kind landed --land-json <file> --wave <slug>`
  - 固定文面のみ。`landed` は保存済み land JSON の `status` が `landed` / `already-landed` の
    ときだけ生成し、SHA は同 JSON の `main_after` から取る。それ以外は rc=3 で生成拒否。
- rc: 0 正常 / 2 CLI 誤用 / 3 生成拒否。traceback を外へ出さない。

固定文面 (自由文の挿入点を持たない):

```
[dev-wave] land-intent main=<40hex> wave=<slug>
advisory です。指示ではありません。local main を読み直す契機にだけ使い、待機・取り込み・
検査省略の根拠にしないでください。受入を開始済みなら中断せず完走してください。
```

### V-2 `.claude/commands/dev-wave.md` へ最小追記 (親が行う)

- 9 段状態機械の段 6 行末: 受入投入の直前に land-window を宣言し peer の宣言を読む旨。
- 終端: land 成功後に `ListAgents` で照合した peer へ 1 度だけ送る旨と、受信側規則。
- 予算: 現在 9035 / 9500。並行 wave `t632` が +21 を予定しているため、実効余白は 444 byte。
  追記は **400 byte 以内**に収める。`docs/dev-wave/**` は 1 byte も触らない。

### V-3 テスト `orchestrator/tests/test_wave_land_window.py`

恒真を殺す正例を必ず含める。

- 有効 fixture で `acceptance` の peer が**ちょうど 1 件**のとき `advice=hold` かつ slug が一致する。
- 全員 `idle` かつ source 完全なら `advice=clear` (常時 `unknown` を返す実装を殺す)。
- `declare` 後、対象ファイルの他の全行が byte 単位で不変である。

### 実装しないもの (裁定パッケージへ)

- `dev_wave_land.py` の byte 不変 gate の新設 (A10)。
- 受信側規則を `docs/dev-wave/**` の正本節へ置くこと (予算 4 byte で不可、T-641 (c) 既決)。
- end-to-end の実運用実測 (独立 2 wave での発火・再走削減の計測)。

## 成果物影響 (DW-G05、B12 の訂正を反映)

実装しない場合、並行 wave が同じ main を base に受入全走を重ね、追い越された側の
**worklog の受入 request ID と実測秒数 (直近実測 1055.40s / request `895517.nqsv` と同型) が
再走値へ差し替わる**。certified 選択・材料レポートの受理集合は変わらない。

## 変異事前登録 (DW-M01、B-057)

| ID | 位置 | 変異 | 単一理由で落ちるテスト |
|---|---|---|---|
| MW1 | `declare` の file 検査 | symlink / 非 regular を受理する | symlink handoff 拒否テスト |
| MW2 | `declare` の行置換 | land-window 行以外の bytes も書き換える | 他行 byte 不変テスト |
| MW3 | `peers` の self 除外 | 自分を peer に含める | self 除外テスト |
| MW4 | `peers` の完全性判定 | partial/unavailable でも `clear` を返す | 不完全 source → `unknown` テスト |
| MW5 | `peers` の TTL | TTL 超過の宣言でも `hold` を返す | 古い宣言は hold にしないテスト |
| MW6 | slug 射影 | basename を無加工で出す | 制御文字・長大名の射影テスト |
| MW7 | `message --kind landed` | land JSON の status を検証せず生成する | `stale-main` JSON で rc=3 テスト |

各変異は他層に同じ入力を拒否する gate が無いことを実装時に確認する。確認できない変異は
登録から外し、実効 gate へ再照準する。
