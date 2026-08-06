---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t574-historical-resolver
seq: 1
---

## {{D:historical-reverify-entry-split}}. 履歴契約での再検証は live admission と別入口にする

**決定:** artifact に記録された `contract_sha256` から契約世代を解決する経路は、
`reverify_published_freeze` という **read-only 専用の新入口**に置く。
`launch_validate` は current 契約束縛のまま受理集合を変えず、live 実走 admission に残す。
新入口の戻り値は `LaunchValidatedFreeze` と別型の `ReverifiedFreeze` とし、oracle driver の
exact type 検査が historical token を受け取らないようにする。
記録 hash の解決は artifact 1 件につき一度だけ行い、同一 contract object を journal 検証・
run_cmd 再導出・result 検証・occurrence 検証の全 edge へ必須引数で渡す。
oracle report の manifest 再検証も同じ規律で resolver 必須にし、解決は manifest 単位で一度だけ行う。

**理由:**
- `launch_validate` は read-only の report 経路と live 実走 admission の共用入口である。
  oracle driver が `run_block` の中でこれを呼び、通過後に marker・WAL・予算を書く。
  同関数を履歴解決へ切り替えると、旧世代の floor 証拠と現世代の実行 receipt を混成した
  新規実走が受理されうる。拡大してよいのは publish 済み成果物の再検証だけである。
- 記録 hash を複数回解決すると、同じ artifact の各行が単一の契約・calibration snapshot へ
  束縛されない。一度だけ解決して同じ object を配ることが、proof chain の前提である。
- 型分離は偽造耐性を与えない。検証結果 token は封印されていない frozen dataclass であり、
  手で構築できる。効くのは自分たちの consumer が黙って広がらないことだけであり、
  本当の防壁は「live 経路が履歴 resolver をそもそも呼ばない」ことにある。
  この限界を型の docstring に明記する。

**却下した選択肢:**
- `launch_validate` 自身を履歴解決へ切り替える — live 実走の受理集合まで広がる。
- 各述語が記録 hash を個別に解決する — 同じ artifact 内で解決結果が割れうる。
- 検証結果 token の型分離だけで live 経路を守る — token は偽造可能で、権限 gate にならない。

## {{D:generation-guarantee-scope-limit}}. 世代解決の保証は calibration 選択までとし、述語の世代分岐を名乗らない

**決定:** 記録 hash からの世代解決を配線する段階で保証するのは
**「記録 hash から世代を解決すること」と「解決した世代の calibration を選ぶこと」**に限る。
`versioned predicate dispatch` という語をコード・docstring・テスト名・台帳で使わない。
世代番号別の述語表も作らない。契約由来の値を解決世代から取る配線は行うが、
それが観測可能な保証だとは主張せず、専用の構造 pin テストで「引数が効いている」ことだけを固定し、
そのテストの docstring に受理正例ではない旨を書く。

**理由:**
- 正当な後継世代が変更できるのは calibration 参照の path と sha256 だけである。したがって
  clock 値・numactl・attestation mode は世代間で必ず同値になり、解決世代の値を使う実装と
  current を引く実装は、正当な世代では観測的に区別できない。
- 区別できない実装を「世代別の述語検証済み」と台帳に書くと、後続の読み手が実在しない保証を
  前提に設計する。名ばかりの保証を作らないという既存規律の直接の帰結である。
- 変異検査でもこれを裏取りした。解決世代の値を使う配線を current 参照へ戻す変異は、
  専用の構造 pin でしか殺せず、正当な世代を使う統合正例では殺せない。

**却下した選択肢:**
- 世代番号を key とする述語 dispatch 表を置く — 登録世代が 1 本しかない間は
  「常に同じ述語を選ぶ表」であり、無条件分岐と観測的に区別できない。
- 構造 pin テストを受理正例として数える — 正当な世代では作れない値差を人工的に作っており、
  世代解決が効いた証拠ではない。
