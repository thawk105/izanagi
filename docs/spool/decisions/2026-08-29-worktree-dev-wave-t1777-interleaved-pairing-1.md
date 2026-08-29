---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: worktree-dev-wave-t1777-interleaved-pairing
seq: 1
---

## {{D:a1-fixed-ab-interleave-rejected}}. A-1 の対は固定 AB の完全交互にしない

**決定:** A-1 対測定の配置を「adaptive → static10 の固定順で rep 単位の完全交互」へ改める案は
**採らない。** 配置の択一 (ブロック交互 + 対内順序の均衡 / rep 単位 ABBA / 均衡無作為) は
ユーザー裁定へ返し、裁定が出るまで実装しない。

**理由:**

- 固定 AB の完全交互は、消そうとしている交絡を別の完全交絡へ置き換える。static10 が常に対の
  2 番目になるため、差に arm 効果と対内順序効果 (直前 arm の残留・周波数・熱) が常に同じ向きで
  乗り、両者を分離できない。時間隔だけを縮めても識別性は改善しない。
- 消そうとしている時間隔の交絡が効いている証拠が無い。既存の探索走は固定順の 1 走だけで、
  時間ドリフト・偶然・arm 固有挙動を分離できない。逆順走が存在しない。
- 実測すると、現行の位置対応は分散を減らしていない。3 workload すべてで対応差の標本 SD が
  独立近似より 25〜33% 大きく、位置を揃えた arm 間の相関は負である
  (−0.591 / −0.563 / −0.765)。ただし各系列 n=5 であり、この相関推定自体が粗い。
  一次資料と計算定義は本 wave の insight に置いた。
- 大型機構の本格実装前に最安の生死確認を行うという計画 gate に該当する。
  配置を凍結する前に専用機構を作ると、作るものを間違える。

**却下した選択肢:**

- **固定 AB の完全交互を実装する** — 上記のとおり新しい完全交絡を導入する。
- **reps=1 の campaign を反復数だけ並べる** — verify が campaign × arm ごとに走るため、
  balanced では 2 回から 410 回になる。verifier capability は PID・variant・operation へ
  束縛され一度消費すると再利用できないので、証明書の使い回しでは避けられない。
  ただし費用の増加は反復数倍ではなく、単純合計で約 30% 増である。
- **配置を親の判断で凍結して実装まで進める** — 配置は estimand の意味を決めるため、
  A-1 study の構造に関する既往の裁定と同じくユーザーの手番である。

## {{D:a1-arrangement-change-requires-two-closure-literals}}. A-1 の配置変更は閉包 2 か所の literal 更新を必ず要求する

**決定:** A-1 非認証 lane の入口が study ID と配置名を literal で二重に固定している事実を、
配置変更を扱う全ての後続 wave の前提として記録する。どの配置案を採っても
`orchestrator/campaign/ident.py` と `orchestrator/campaign/wal.py` の更新は避けられない。
両者は enforcement source closure の member である。

**理由:**

- `ident.py` の `is_a1_non_certifying_config()` は study ID と
  `pairing_design == "arm-grouped-positional-v1"` の exact 一致を要求する。
- `wal.py` の A-1 marker 判定が同じ 2 条件を独立に再び要求し、不一致なら build 前に拒否する。
- したがって新しい study ID または新しい配置名を使う実行は、片方だけを直しても入口で止まる。
  投入経路と job script も旧 study ID に固定されており、端まで繋ぐには併せて分岐が要る。
- 「実装は campaign loop か pipeline を要求する」という従来の理解は不正確である。
  loop と pipeline が必要になるのは rep 単位の完全交互を採る場合だけで、
  driver 層のブロック配置なら不要である。一方 ident と wal はどの案でも必要である。

**却下した選択肢:**

- **片方の marker だけを緩める** — もう片方が build 前に拒否するため実行できない。
- **配置名を据え置いて新しい配置を走らせる** — 同一性が分かれず、配置変更の前後が
  同じ campaign へ混ざる。混在防止は配置名が同一性に入ることで成立しているため、
  この経路を壊してはならない。
