### 所見 1 — M4 は到達証明ではなく、qsub の実環境伝播も未検証

主張: driver flag は存在するが、現行 job argv には届いていない。`qsub -v` は一つの comma-separated operand で、shell の引用は qsub 内部の comma 解釈を止めない。

一次証拠 (file:line): `tools/pegasus/floor_campaign.sh:961-965` は `--mode pilot` と `--protocol` だけ。driver の拒否は `orchestrator/campaign/s8b_floor_campaign.py:5255-5263`、flag 定義は同 `:6192-6200`。env seam は `tools/pegasus/submit_floor.sh:282-289,411-423`。qsub stub は argv を記録するだけで、環境へ設定しない `orchestrator/tests/test_pegasus_floor_tools.py:358-365`。

成立条件: 承認値を任意文字列にする、comma を含む値を許す、または qsub stub の argv 検査だけで「job に届いた」と判定する場合。

成果物への影響: exact `1` を生成しない限り、承認投入後も driver は拒否する。実 scheduler への env 到達は未証明のまま残る。

推奨: zero-arity flag、env 値 exact `1`、`-v` への単一 operand を固定する。実 qsub を走らせないなら、到達未検証と明記する。

### 所見 2 — P2 の confirmed receipt は certified writer の bootstrap で先に落ちる

主張: shell 側の `top_keys` を拡張しても不十分。job は `floor_campaign.sh:54-95` で certified writer preflight を先に実行し、`certified_writer_admission.py` が別の exact closed set を検査する。

一次証拠 (file:line): `orchestrator/campaign/certified_writer_admission.py:27-31,52-55,184-204`。preflight の import と `admit` 呼出しは `orchestrator/campaign/certified_writer_preflight.py:160-176`。shell 側の receipt 検査は後段の `tools/pegasus/floor_campaign.sh:405-494`。

成立条件: producer が `confirm_irreversible_pilot_holdout` を追加し、`certified_writer_admission.py` を未変更のままにする場合。

成果物への影響: confirmed job は driver 起動前に `floor receipt key set mismatch` で rc=4/3 相当となる。段 2 の validator fragment テストだけでは発見できない。

推奨: P2 を採るなら admission 本体、直接 admission テスト、fixture を編集面へ追加する。編集面を増やせないなら、receipt field を採らず env-only の P1 に戻す。

### 所見 3 — `v1` 維持は自動的な後方互換ではない

主張: 現行 `v1` は optional field を許す schema ではなく、複数 consumer が exact key set として実装している。

一次証拠 (file:line): job 側は `tools/pegasus/floor_campaign.sh:428-443`、certified writer は `orchestrator/campaign/certified_writer_admission.py:27-31,184`、テスト定数は `orchestrator/tests/test_pegasus_floor_tools.py:36-58,1123-1126`。説明文も exact keys として `output/insights/2026-07-25_t088-floor-wrapper-verbatim.md:315-342,1401-1407` に残る。`v2` にする場合は `orchestrator/campaign/floor_liveness.py:65-83` の `v1` literal も更新対象になる。

成立条件: `/v1` のまま confirmed field を足す、または confirmed receipt だけ `/v2` にする場合。

成果物への影響: 前者は strict consumer が confirmed receipt だけ拒否する。後者は旧 v1 receipt、liveness、既存 fixture と互換しない。

推奨: 親が「v1 の後方互換拡張」と「v2 + v1/v2 dual reader」を裁定する。I4 を守る最小形は、base と base+exact Boolean `true` の双方を全 strict consumer が受理する v1 拡張である。

### 所見 4 — 既存テストの影響は「0件」ではなく、互換形に依存する

主張: 未承認時の field 省略を厳守すれば既存テストは維持できるが、変更形を誤ると次が赤になる。

一次証拠 (file:line): interpreter 回数 pin は `orchestrator/tests/test_pegasus_floor_tools.py:686-699`。未承認 driver argv は同 `:987-1052`。初期 `export_spec` と qsub 形は同 `:1065-1074`。default receipt の exact keys/schema は同 `:1098-1126`、default qsub argv は同 `:1211-1236`。receipt validator の未設定 env 前提は同 `:1839-1879`、driver tail は同 `:1882-1884`。certified writer の default fixture は `orchestrator/tests/certified_writer_fixtures.py:129-149`、実 admission は `orchestrator/tests/test_campaign.py:4950-4977`。

成立条件: field を未承認時にも書く、driver flag を無条件 append する、未設定 env を `${VAR-}` なしで展開する、または certified writer 側で field を必須化する場合。

成果物への影響: I4 の receipt bytes、default qsub argv、`set -u` 下の fragment、既存 admission fixture が壊れる。

`test_hooks.py` は `tools/pegasus/submit_floor.sh` の path/class と sanctioned spelling だけを pin しており、`orchestrator/tests/test_hooks.py:2572-2604,2660-2664,2798-2800,2927-2931,3808-3815` に receipt/schema/approval argv の pin はない。ここは今回の赤箇所ではない。

推奨: default base schema を保持し、certified writer の legacy receipt と confirmed receipt を直接検査するテストを追加する。fragment だけで全 consumer を代表させない。

### 所見 5 — runbook 未更新では、人間は承認経路を実行できない

主張: 投入手順書には承認引数が一箇所もなく、現行手順を忠実に実行すると承認 flag は渡らない。

一次証拠 (file:line): `docs/phase3-8b-restart-runbook.md:165-169` は `--mode pilot` 固定だけで blocker 解消と記載するが、実装はなお driver gate を持つ。投入手順は同 `:229-234` の dry-run と同 script 実行だけ。`docs/pegasus-runbook.md:1406-1409` も sanctioned な `qsub -v` 再利用だけを述べる。指定語の `confirm-irreversible-pilot-holdout` と `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT` は両 runbook に存在しない。

成立条件: shell だけ land し、親が段 7 の docs 変更を行わない場合。

成果物への影響: 人間は文書どおりに投入して driver 拒否を受け、pilot 実測は得られない。

推奨: scope 外として親の裁定パッケージへ返す。承認付き dry-run、実投入、receipt 確認、不可逆消費の警告、投入後の marker/qstat/accounting 確認を runbook に追加する。

### 所見 6 — M8 は誤記であり、既存の bytes 束縛と承認束縛を混同している

主張: brief の「path 束縛のみ、bytes 束縛なし」は事実と異なる。job script bytes は既に複数箇所で束縛されている。ただし receipt 全体や承認 field の bytes は束縛されていない。

一次証拠 (file:line): brief の M8 は `/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/brief.md:28`。source blob hash は `orchestrator/campaign/certified_writer_admission.py:122-128,196-204`、実行中 `$0` と repo blob の比較は `tools/pegasus/floor_campaign.sh:508-521,540-556`。receipt の create-only copy は同 `:380-399` だが、そこで receipt 全体の hash は取っていない。

成立条件: M8 を P2 の根拠として「既存 bytes 保護が無い」と説明する、または receipt field を人間承認の強い認証と説明する場合。

成果物への影響: 不存在の bytes pin を追加する方向へ scope が逸れる。一方、P2 は env と receipt の整合を検査するだけで、receipt field の人間起源を暗号学的には証明しない。

推奨: brief を「job script bytes は既存束縛済み、承認 env と receipt の意味束縛が未実装」と訂正する。P2 の field は consistency evidence とだけ記述する。

### 所見 7 — M10 の「実績 0 件だから実害ゼロ」は成立しない

主張: floor run が 0 件なのは観測された実害が無いことを示すだけで、経路が安全または実効的である証拠ではない。

一次証拠 (file:line): brief の M10 は `brief.md:30`。runbook は `docs/phase3-8b-restart-runbook.md:185-190` で、qsub は scheduler に受理され、失敗は計算ノード側で起き、キュー資源を消費しうると明記する。さらに `:201-204,223-228` は実投入の停止点と rc だけでは成功判定できないことを記録する。

成立条件: 実 qsub と計算ノード上の job をまだ一度も通していない状態。

成果物への影響: env 到達、certified writer、build、driver gate、床値実体化のどこで止まるか未確認のまま、将来の投入時に資源消費と再試行を発生させる。

推奨: 「実害ゼロ」ではなく「floor 成功実績なし、実効性未検証」と記録する。実走をしない本 wave では、親が残余リスクとして引き取る。

### 所見 8 — `docs/failures.md` の過去型が少なくとも五つ再発する

主張: 本プランは説明と実装の不一致、consumer 取り残し、恒真な保証の過去型を同時に踏む構造である。

一次証拠 (file:line):

- F22 は rc=0 だけを検収し、consumer との突合を忘れた型 `docs/failures.md:352-364`。今回の qsub stub の argv 成功だけで到達を主張すると同型。
- F30 は consumer/pin の閉包を取り落とした型 `docs/failures.md:736-763`。今回の certified writer admission と docs の取り残しが同型。
- F332 は producer と下流5面の順序・schema差分を見落とした型 `docs/failures.md:8153-8188`。`v1` のまま field を足す判断が同型。
- F334 は producer 不在と stub テストで本走ゼロのまま land した型 `docs/failures.md:8217-8240`。M10 の一般化が同型。
- F341 は契約 flag と負の対照が同じ入力を共有して恒真化した型 `docs/failures.md:8364-8382`。承認時だけ flag を足すテストは、独立した未承認負例を持たないと同型。

成立条件: shell fragment と qsub stub だけを検査し、certified writer・runbook・実環境到達を検査対象から外す場合。

成果物への影響: 全テスト緑でも、confirmed receipt が bootstrap で落ちる、または実投入で初めて停止する状態を land する。

推奨: 親は P2 の scope 拡張、runbook 更新、certified admission の confirmed/legacy 直接テスト、実 qsub 到達未検証の明記を一括で裁定する。

## 総括

- 最も危険なのは、P2 receipt が certified writer の exact set で driver 前に拒否される点。
- M4 は flag の存在であり、M8 は job script bytes の既存束縛を見落としている。
- 親の択一は「P2を採り scopeを admission・docs・直接テストまで拡張」か「今回の2 shellはenv-onlyにし receipt拡張を別裁定へ送る」かである。
- 静的検査のみ実施し、編集と pytest は行っていない。