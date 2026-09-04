---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-04
wave: worktree-dev-wave-t2262-floor-staged-transport
seq: 1
---

## {{D:floor-payload-authority-is-the-verified-binding}}. 床値の既定 payload は検証済み予約束縛から導き、環境変数を authority にしない

**決定:** 床値 campaign の既定 (production) FetchContent transport は、payload の所在を
**検証済みの `reservation_binding` の nonce** と canonical な submit receipt path 関数から導く。
生の環境変数 (`IZANAGI_SUBMISSION_NONCE` 等) を導出の authority にしない。
検証済み束縛が存在しない環境では fail-closed で拒否し、環境変数にも外部取得経路にも落ちない。

staging 先は repo 外の固定 leaf とし、repo 外であることをコピー前に確定させる。
固定 prefix から payload までの全 path component と 3 依存 source を no-follow で検査する。
複製は in-process で行い、新しい process 起動点を作らない。

`REFREEZE_DISQUALIFYING_SEAM_NAMES` の 18 名集合と `_derive_refreeze_eligibility` の判定式は
literal のまま変えない。既定経路は raw 引数が `None` のまま seam 分類を通り、導出は分類より後で
起きるため、「official・fresh・非既定 seam ゼロだけを適格にする」という意味は変わらない。

**理由:**

- D1562 が解消案 1 を裁定し、導出規則を明示的に固定して発見による暗黙の入力経路を作らないことを
  設計論点として名指ししている。
- 生の環境変数を authority にすると、core が検証する submit receipt を選ぶ nonce と、payload を
  選ぶ nonce を別々に設定できる。両者の等値を保証するのは正規 job script だけで、driver API 自身には
  等値検査がない。32 桁 hex の形式検査は traversal を防ぐだけで、両者が同じ submission を指すことを
  証明しない。段 3 の敵対レンズが独立に構成し、親がコードで裏を取った。
- 検証済み `reservation_binding` は submit receipt の `job_id` / `job_script_sha256` / `nonce` の
  一致検査を通っており、payload をその束縛から導けば追加の権威を新設せずに束縛できる。
  D1586 が「承認済み identity の権威が repo に無いなら記録に留める」と定めた状況とは異なり、
  本件は権威が repo 内に実在するため拒否できる。
- 束縛の確定は staging より前に起きる。順序は実測で確かめた。
- 固定 prefix の ancestor 検査は、正規 job script が全 path component について行っていた検査である。
  driver へ移す以上、移した先で再現しなければ検査そのものが消える。

**却下した選択肢:**

- **新しい環境変数を導入する** — 既存の検証済み束縛から導けるため不要であり、
  検証されない入力経路を 1 本増やすことになる。
- **生の環境変数をそのまま読む** — 上記のとおり submit receipt の束縛と切り離される。
- **directory 走査や候補探索で payload を見つける** — 発見による暗黙の入力経路であり D1562 に反する。
- **複製を `cp -a` の子 process で行う** — 意味は保てるが、審査済み process 起動点の台帳を
  変更することになり、同台帳を編集中の別 wave と編集面が交わる。in-process 複製で同じ意味
  (symlink の保存、mode bit、`.git` を含む木全体) を保てることを実測した。

## {{D:floor-claim-basis-change-needs-new-run-id-not-a-migration}}. seam basis を変える変更を跨ぐ resume は認めず、新しい世代 ID での再投入を既定とする

**決定:** 床値の測定世代 claim に記録される非既定 seam の集合が変わる変更について、
**移行機構・backfill 機構を新設しない。** 変更を跨いで既存の部分 claim を resume することは
できないものとし、運用は**新しい `campaign_run_id` での再投入**を既定とする。

**理由:**

- 既存 claim は旧い seam basis を保持し、変更後に補完される claim は新しい basis になる。
  混在は claim 由来の適格性検査が拒否する。これは fail-closed の正しい向きである。
- 実測時点で `measurement-generation-claims` は repo 内に存在せず、生きた部分 claim は 0 件だった。
  直す対象が存在しない機構を先に作ることになる。
- 回復機構を足すと、claim の内容を後から書き換える経路を作ることになる。
  create-only の記録に書き換え経路を持ち込むより、新しい世代として発行し直すほうが小さい。

**却下した選択肢:**

- **旧 basis を新 claim へ backfill する** — create-only の記録へ書き換え経路を持ち込む。
- **basis の混在を許容する述語へ緩める** — 正しさ防壁を緩める向きである。
- **移行機構を先に用意しておく** — 発火条件を満たす既存 artifact が無く、`DW-G04` に反する。
