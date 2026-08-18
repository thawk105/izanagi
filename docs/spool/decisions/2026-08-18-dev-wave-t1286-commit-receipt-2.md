---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1286-commit-receipt
seq: 2
---

## {{D:commit-receipt-issued-inside-verifier}}. COMMIT receipt は verifier 実走行の内側でだけ発行する

**決定:** COMMIT receipt を発行する capability は、実 verifier entrypoint が trace を検証した
その呼び出しの内側でだけ生成する。呼び手が構築した `VerifyResult` や、呼び手が組み立てた
serialized dict / hash を authority にしない。capability は operation・variant・workload・sink・
lock context を焼き込み、receipt 発行時に完全一致と一回消費を要求する。

**理由:**
- 「receipt を要求する検査を足す」ことと「receipt が verifier 由来である」ことは別である。
  前者だけを実装すると、テストも同じ呼び手側の経路で receipt を作るため全緑になり、
  検査は恒真になる。本 wave では焦点走 1388 passed の状態で、trace を一度も読まずに
  live receipt を発行できた。
- 呼び手が立てる真偽値は非権威である。最適化圧力は必ず正しさの門を攻撃しに来るという前提
  (規律 2) に立てば、門の入力は門自身が生成しなければならない。
- capability を operation へ束縛しないと、正常な trace を 1 回検証するだけで任意の
  variant / payload 向けの receipt を量産できる。単発の検証を無制限の発行権に変えてはならない。

**却下した選択肢:**
- 既成 `VerifyResult` を受け取る issuer を残し、呼び手の規律で運用する — 規律で守る門は
  門ではない。実装子は実際にこの経路を作った。
- receipt を producer 側だけで要求する — 低層 writer を直接呼べば素通りするため支配点にならない。
- 一回限りを in-memory object の消費だけで表す — durable な根拠にならない。
  ledger 内の消費済み集合を flock 下で走査する。

## {{D:enforcement-source-ratification}}. 新 certified lock は批准済み closure digest とだけ突き合わせる

**決定:** 新しい certified lock を作るとき、enforcement source closure の path→blob map 全体の
canonical hash を、`hooks/` 配下の read-only 台帳が持つ批准済み digest 集合と比較する。
一致しなければ lock を作らない。台帳は 0 行で land し、追記 API・CLI・自動更新処理を作らない。
台帳データ自身は自己参照を避けるため closure から除外する。
**この機構を「人間が批准したことの機械的証明」と記述してはならない。**

**理由:**
- 従来の live 検査は disk bytes が HEAD blob と一致するかという自己整合しか見ておらず、
  verifier を弱化して commit すればその bytes が新しい正規として記録できた。
  規律 2 が名指しする reward hacking の経路である。
- 批准単位を path ごとにすると、個別には批准済みでも組合せとして未審査の closure を作れる。
  map 全体の hash 1 本にする。Git commit SHA は含めない — 同一 bytes が別 commit へ
  移っただけで批准を失わせない。
- `hooks/` 配下は Write でも Bash リダイレクトでも書き込みが機械的に拒否される。
  規律 2 の脅威主体は AI 実装者なので、この配置は実効的な障壁である。
- ただし hook 側の障壁は暗号学的証明ではない。謳える性質は「AI 実装者が追記できない集合との
  比較」までであり、それを超える主張をすると恒真な保証を新設したことになる。
- 比較処理と receipt 実装面を closure の外に置くと、比較を改変して迂回でき、
  弱化しても批准対象 digest が変わらない。どちらも closure へ収載する。

**却下した選択肢:**
- 実装を見送りユーザー裁定へ戻す — 裁定は実害の観測を待たないと明記しており、
  fail-closed の既定は live 影響ゼロ (v2 lock が 1 件も存在しない) で実現できる。
- 批准値を持つ台帳を wave 側で作って land する — 弱化した本人が批准する形になる。
- 外部 trust root と署名を本 wave で新設する — 粗い provenance 方針に触れるため裁定へ返す。

## {{D:ident-activation-wrapper-two-contracts}}. activation の検証済み wrapper は head 用と prefix 用で契約を分ける

**決定:** `env_contract` が公開する検証済み activation wrapper を 2 つに分ける。
current head 全体を検証するものと、`(activation_serial, activation_state_sha256)` を取って
前置部分列へ同じ検査を適用するものである。identity 側はこの 2 つだけを使い、
activation の leaf 関数を直接呼ばない。

**理由:**
- 記録済み activation tuple の検証は、current chain head 全体の健全性と、記録 serial までの
  前置部分列の健全性という**別々の 2 つ**を要求する。head 用 wrapper を prefix にそのまま
  流用すると正当な過去 lock を誤拒否し、prefix 用だけに置換すると現在の head の破損を見逃す。
- 直接呼びは wrapper が足す 4 検査 (行ごとの calibration 検証・registry 交差検査・
  verified hash 集合の更新・fork 安全 cache) をすべて素通りする。
- 経由化を AST 検査だけで固定すると恒真になる。runtime の負の対照が要る。ただし
  successor callback が実行される serial では直接 validator も同じ拒否をするため、
  差が出るのは callback が呼ばれない初期 serial である。負の対照はそこへ置く。

**却下した選択肢:**
- 単一 wrapper で両用途を賄う — 上記のとおりどちらかの意味が壊れる。
- AST 検査だけで直接呼びを禁じる — 呼び出し形は縛れても検査内容の回復を示せない。
