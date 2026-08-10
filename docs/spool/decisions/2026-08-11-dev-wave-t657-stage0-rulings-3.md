---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t657-stage0-rulings
seq: 3
---

## {{D:design-literal-binding-rejects-html-comments}}. 設計文書と検査値を束縛する gate は、comment を除去せず存在を拒否する

**決定:** 設計正本から literal を抽出して検査側の値と exact 照合する gate は、対象文書に
HTML comment (`<!--` / `-->`) が 1 つでもあれば fail-closed で拒否する。comment を除去して
可視部分だけを読む実装にしない。

**理由:**

- 除去は「どこまでが comment か」を Markdown の文脈なしに決めることになり、その判定自体が
  攻撃面になる。実際に、code fence 内の開始と fence 外の終了が対になって**可視の差分行ごと
  消える**構成が成立し、除去を入れる前には拒否されていた文書が受理された。
- 存在の拒否なら判定が 1 つの述語に閉じ、隠し場所が無くなる。抽出器を増やしても攻撃面は増えない。
- 設計正本に comment を置けない制約は実質的な損失にならない。書きたい注記は本文に書けばよく、
  「読者に見えない正本」は正本の定義に反する。

**却下した選択肢:**

- comment 除去 + 未閉鎖 comment の拒否 — 上記の code fence 経路で破れた。
- Markdown parser の導入 — 検査のために parser の正しさを新しい信頼境界として抱えることになる。
- 抽出器ごとに個別対処 — 抽出器が増えるたびに同じ穴を作り直す。

## {{D:dev-wave-waiter-pid-and-codex-coldstart}}. 背景 job の待ち手は detach 後の実体 pid を使い、codex の cold start 失敗は新 artifact 名で再投入する

**決定:** `nohup setsid` で detach した子の完了待ちでは、`$!` を producer pid として使わない。
起動後に `ps` で実体 (`dev_wave_codex.py --wave <slug>`) の pid を引き、それを死亡判定に使う。
codex 子が `evidence_status=missing` / `stdout_bytes=0` / 短い `wall_clock_s` で not_accepted に
なった場合は、認証や prompt でなく起動遅延を疑い、**既存 `.done` を消さず新しい artifact 名**で
1 度だけ再投入する。

**理由:**

- `nohup setsid bash -c '...' &` の `$!` は中継 process の pid であり、setsid が新しい session を
  作った直後に消える。pid 死判定の待ち手は、実体が稼働中でも即座に「producer 死」と誤報する。
  本 wave で実測した (実体は 1 分以上稼働していた)。
- codex の launcher は既定 5 秒の evidence grace 内に起動イベントが出ないと SIGTERM で止める。
  本 wave の初回はこれで `wall_clock_s=8.59` の not_accepted になり、直後の手動 probe は
  同 model・同 effort で 4.88 秒完走した。差は binary の page cache の温度だけで、
  prompt にも認証にも帰属しない。

**却下した選択肢:**

- `pgrep -f <pattern>` で待つ — 待ち手自身の argv に pattern が載って自己マッチする既知事故。
- grace を延ばす caller flag を足す — 起動導線は caller 指定不可の設計であり、
  独立 2 例目が出るまで族一般化しない。
- 同じ artifact 名で再投入する — 既存 attempt artifact と衝突し、launcher が fail-closed で止まる。
