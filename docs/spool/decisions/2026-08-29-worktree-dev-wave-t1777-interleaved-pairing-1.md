---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: worktree-dev-wave-t1777-interleaved-pairing
seq: 1
---

## {{D:a1-counterbalanced-block-pairing}}. A-1 の次の実走は単一 campaign の 5-rep ブロック交互 + AB/BA 均衡にする

**決定 (ユーザー指示による相談のうえ確定):** A-1 対測定の次の実走の配置を次に定める。
凍結済みの現行 study は書き換えず、別 study として起こす。

1. 1 workload = 1 campaign のまま、**両 arm の build と verify を bench より前に完了**する。
2. `bench_lock()` を全ブロックにわたり **1 回だけ**保持し、5 rep ずつの arm ブロックを交替させる。
3. 10 対を 1 組とし、組の中に `A^5 B^5` と `B^5 A^5` を 1 つずつ置く。組内の先後だけを凍結 seed で決める。
4. contrast は物理順によらず常に `static10 − adaptive` とする。
5. 推定対象は**「5-rep 均衡スケジュール下での差」**とし、残留効果の無い定常状態の直接効果と
   同一視しない。この限定を事前登録の本文に書く。
6. `bench_max_rounds = 1` とし CV 再測は使わない。静定と競合検査は残す。
7. 対ごとの同期追記台帳は置かない。全ブロック完了後に arm ごとの完了記録とスケジュール受領証を
   出し、途中中断と片側 commit は invalid に閉じる。

**理由:**

- 固定 AB の完全交互は、時間隔の交絡を対内順序の完全交絡へ置き換えるだけである。
  static10 が常に対の 2 番目になり、arm 効果と残留効果を分離できない。
- 5-rep ブロックなら同番号間の間隔は約 16.8 秒となり、現行の約 41 分の 1 になる。
  一方で arm 間の遷移回数は rep 単位交互の約 5 分の 1 で、残留効果の取り込みが小さい。
  周期 4 の固定 ABBA が環境変動と共振する型も避けられる。
- 単一 campaign なら verify は workload あたり 2 回のままである。
- 対ごとの同期追記は、それ自体が対の間の時間と状態を変える観測者効果になる。
- 消そうとしている時間隔の交絡が効いている証拠は無い。既存の探索走は固定順の 1 走だけで、
  時間ドリフト・偶然・arm 固有挙動を分離できない。したがって配置は「交絡を消した」と
  主張するためではなく、**識別可能性を上げるため**に選ぶ。

**却下した選択肢:**

- **固定 AB の rep 単位完全交互** — 新しい完全交絡を導入する。
- **rep 単位 ABBA** — 間隔は最短だが arm 間遷移が 5 倍になり、残留効果と周期 4 の
  環境変動を強く取り込む。
- **均衡無作為** — seed 固定は再現性を与えるだけで、実現した時間の偏りや長い連は除かない。
- **1 workload を K 本の campaign へ割る** — 配置の狙いは同じだが、campaign 境界・静定・
  build/verify・ロック解放を 62 回持ち込む。さらに `trial_registry.py` が A-1 の campaign 群を
  workload と同数の exact unique triple に固定しているため、driver だけでは成立せず
  registry と collector の変更も要する。
- **現行維持** — 長時間ドリフトと arm 順が完全交絡したままになる。

## {{D:a1-new-arrangement-needs-its-own-pilot-and-sizing}}. 新配置の反復数は同じ機構で走らせた pilot から取り直す

**決定:** 新配置の反復数は、旧配置の計画 sigma を流用せず、**本番用の機構をそのまま使った
pilot** から取り直す。pilot 専用の簡易実装は作らない。

手順は次のとおり。各 workload について同じ機構で 60 対を 1 度測り
(5 対/ブロック × 12 ブロック、A 先行 6・B 先行 6、組内順は凍結 seed)、
TPS・物理順・ブロック番号・ブロック内位置・時刻を記録する。
対 SD にカイ二乗上側係数を掛けて計画 sigma を作り、ブロック平均から実効 sigma も作り、
両者の大きい方で反復数を探索する。判定式・floor・3 条件と成功率は既存の sizing 手順に揃える。
pilot の観測値は最終推定へ混ぜない。

**理由:**

- 計画 sigma は対応差の標本 SD から導く量であり、配置を変えると共分散項が変わる。
  旧配置の値を流用すると、別配置の分散設計を旧配置の pilot で正当化することになる。
- pilot と本実装は実装面がほぼ完全に重なる。異なるのは study ID、policy と事前登録の hash、
  反復数、係数、sigma、出力先といった profile 値だけである。したがって pilot を挟む費用は
  「小さく 1 度測る」ぶんだけで、二重実装にはならない。
- 簡易版の pilot を sizing に使うと、build/verify とロック解放が対の間に入るため、
  本番とは異なる共分散を測ってしまう。

**却下した選択肢:**

- **旧 planned sigma と旧到達確率をそのまま新 policy へ写す** — 装置の意味が変わるのに
  分散設計だけ据え置くことになる。
- **pilot を挟まず配置を凍結して本走へ入る** — 反復数を決める情報が無い。
- **pilot 専用の簡易機構を作る** — 測る共分散が本番と違うため、sizing の入力にならない。

## {{D:a1-arrangement-change-requires-all-four-closure-members}}. A-1 の配置変更は閉包 4 member すべてに及ぶ

**決定:** 採用した配置を実装する wave の前提として、次を記録する。
enforcement source closure の member 4 つがすべて変更対象になる。

- `orchestrator/campaign/ident.py` — A-1 非認証 lane の判定が study ID と配置名を
  exact 一致で要求するので、新しい対を閉じた集合へ足す。
- `orchestrator/campaign/wal.py` — 同じ 2 条件を独立に再び要求するので、片方だけ直すと
  build 前に拒否される。
- `orchestrator/campaign/loop.py` — 現行は arm ごとに評価を完了してから次へ進むので、
  両 arm を先に準備する調整役が要る。
- `orchestrator/campaign/pipeline.py` — 現行は arm 単位で全反復を 1 つのロック内で測るので、
  build/verify と bench の分割とブロック実行器が要る。

非閉包側では driver の profile・スケジュール・collector・投入 selector と job script も
旧 study ID に固定されているため、同じ変更単位で分岐させる。

**理由:**

- 当初は「実装は campaign loop か pipeline を要求する」「driver 層のブロック配置なら
  loop と pipeline は不要」と理解していたが、どちらも不正確だった。前者は ident と wal を
  落としており、後者は両 arm の事前 verify がこの 2 file の分割を要求することを見落としていた。
- 閉包 member を編集する wave は、commit 前の焦点走で内容と無関係な偽赤が機械的に出る。
  変異 matrix でも同型の共通核が出るので、判定は共通核を引いた差分で行う。

**却下した選択肢:**

- **片方の marker だけを緩める** — もう片方が build 前に拒否するため実行できない。
- **配置名を据え置いて新しい配置を走らせる** — 同一性が分かれず、配置変更の前後が
  同じ campaign へ混ざる。混在防止は配置名が同一性に入ることで成立しているため、
  この経路を壊してはならない。
