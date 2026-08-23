---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1477-d58-ablation
seq: 2
---

## 新規

### {{F:backoff-sweep-official-ratification-gap}}. backoff_sweep.pyのofficial新規campaign初期化が2026-08-18以降おそらく未実行のまま批准台帳gapで塞がっていた [ドリフト] [テスト代表性]

- 事象: [T-1477] D58 ablationでPegasus上`backoff_sweep.py read-heavy`(screening無し、
  `declared_use_class="official"`固定)を実行したところ、brand-new campaign初期化
  (既存lock無し・既存WAL無し) 経路で`IdentityMismatch: contract-loader-drift:
  enforcement-source-ratification: enforcement-source-closure-unratified: closure digest
  is absent from the read-only ledger`が発火し、実行開始2〜3秒でfail-closedした
  (`orchestrator/campaign/ident.py:242 _capture_current_loader_binding` →
  `contract_loader_binding.py:400 verify_ratified_contract_loader_binding`)。
- 根本原因: `hooks/enforcement-source-closure-ratifications.v1.jsonl`(enforcement-source
  批准台帳、`CONTRACT_LOADER_RELATIVE_PATHS`の25 pathのclosure digestを記録) はD526
  (2026-08-18、worklog entry 660) で「批准台帳のhooks/配置はAI実装者の追記を機械的に塞ぐ...
  0行のままlandするため新certified lock生成はfail-closedになる」と明記のうえ**意図的に0行**で
  land済みだった。当時は「v2 lockが存在しないためlive影響はゼロ」と判断されていたが、
  `backoff_sweep.py`は3箇所全てで`declared_use_class="official"`固定であり、`ident.py`の
  new-campaign初期化経路は既定`require_environment_contract=True`でこの検査を必ず通る。
  worklog全文検索でD526land以降の追記実績は無く(2026-08-22現在も0行)、2026-07-15の
  positive control (insight `2026-07-14_bench-first-screening-design.md` §5 item6) は
  D526land より1か月前の実行だったため抵触しなかったと推定される。すなわち**D526land
  (2026-08-18) 以降、環境を問わずbackoff_sweep.pyのofficial新規campaign初期化を
  完走させた実行が存在しない可能性が高い**——他wave/他人格による日常的なsweep実行は
  既存lockの再利用 (resume) か`declared_use_class="exploration"`系の別経路を使っており、
  この特定の組合せ (official + brand-new campaign) を通していなかったと考えられる。
- 恒久対応: D526は意図した設計 (AIによる自己批准を防ぐfail-closed) であり、本waveはこれを
  緩めない。恒久対応は「人間が`hooks/enforcement-source-closure-ratifications.v1.jsonl`へ
  現行closure digestの批准entryを追記する」ことに限られる (D526自身が定めた唯一の解除経路)。
  AIからの追記手段は存在しない。本F エントリはこの経路が塞がっていた事実の記録であり、
  再開判断はユーザー裁定 (2026-08-22、[T-1477] wave内でwave区切りを選択) に委ねた。
- 再発検知: `declared_use_class="official"`かつ`is_reservation_required`または
  brand-new campaign初期化 (既存lock無し) を新たに実行しようとするあらゆるwaveが、
  同じ`contract-loader-drift`エラーで即座に検知する (fail-closedのため実害は最小)。
  批准台帳が埋まっていない間は、この経路を前提にした受入・実測計画を段1briefで
  事前に検出できるよう、`hooks/enforcement-source-closure-ratifications.v1.jsonl`が
  0行のままかを着手前に確認する運用を検討する (段8改善候補、docs予算逼迫のため本wave未実装)。
- 2026-08-23 追試 (再開 wave、推定を実測へ格上げ): 上の「おそらく未実行」という推定を、現行
  local main (`b89ea755` 取り込み時点。closure 25 file は 2026-08-21 以降不変) に対する直接
  呼出しで実測へ格上げした。`contract_loader_binding.capture_contract_loader_binding()` と
  `verify_live_contract_loader_binding()` は成功し、`verify_ratified_contract_loader_binding()`
  だけが `enforcement-source-closure-unratified: closure digest is absent from the read-only
  ledger` で落ちる。批准台帳 file は working tree にも git 履歴にも存在しない (0 行ですらなく
  未作成で、`git cat-file -e main:hooks/enforcement-source-closure-ratifications.v1.jsonl` が
  `Not a valid object name` を返す)。よって本 gap は T-1477 固有でも Pegasus 固有でもなく、
  現行 main そのものの状態である。
- 迂回路の不在も実測した: `declared_use_class` を `official` から `exploration` へ変えても
  迂回できない。`ident.ensure_campaign_identity` の批准検査は `require_environment_contract`
  にだけ従い、この引数は use class と独立である (`loop.py` は既定 `True` のまま呼ぶ)。
  `False` を渡す呼出しは `orchestrator/campaign/guided.py` の guided 免除経路だけで、
  `verify_against_lock` は `not require_environment_contract` かつ v2 lock の組合せを
  `v2-lock-requires-authority` で拒否する。既存 lock の resume 経路は批准検査を通らないが、
  ablation の off/on はどちらも brand-new campaign なので該当しない。規律 2 により、
  免除経路への付け替えは採らない。
- 運用上の含意 (批准は closure 版ごとにしか効かない): `CONTRACT_LOADER_RELATIVE_PATHS` の
  25 file は直近 30 日で 163 commit が触れている (最新の変更は 2026-08-21)。D526 は台帳データ
  自身を closure から除いているので追記行そのものは digest を動かさないが、25 file のどれかが
  動けば digest が変わり新しい行が要る。したがって批准と official 新規 campaign の起動は
  近接させる必要があり、間に 25 file を触る wave が着地すると再び塞がる。
