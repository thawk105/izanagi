## 総括

S1 は protocol SHA-256 と freeze SHA-256だけから identity を導出し、専用 leaf が再検算してから claim を取得する設計を採る。  
P1・P4・P5 は採用し、`ClaimRecord` の field 集合と `_fresh_run_id` の run 単位 consumer は変えない。P2 は結論を採るが、現行登録 contract に resume 可能な required-mode は存在しない。  
S2 は host の現実側 source だけが現行 scope 内で実在する。script SHA と nonce は独立 authority が Python leaf まで届かず、恒真な env 同士の比較は退ける。  
P3 を採用するため、script SHA・nonce を同一 wave で実装するには段 4 で scope 再裁定が必要である。静的検査のみで、pytest は未実走。

## S1 実装プラン

- `orchestrator/campaign/campaign_claim.py:5-10`

  `hashlib` と SHA-256 形状検査を追加する。identity preimage は次の固定 field のみにする。

  ```python
  {
      "schema": "izanagi-protocol-claim/v1",
      "freeze_sha256": freeze_sha256,
      "protocol_sha256": protocol_sha256,
  }
  ```

  `started_at`、PID、UUID、mode、`resume_dir` は入れない。

- `orchestrator/campaign/campaign_claim.py:28-32` 後

  次を新設する。

  ```python
  def derive_protocol_claim_identity(
      *,
      protocol_sha256: str,
      freeze_sha256: str,
  ) -> str:
  ```

  両入力を64桁小文字 hex として検査し、canonical JSONの SHA-256 を返す。不正入力は `ClaimError` とし、filename を作らない。

- `orchestrator/campaign/campaign_claim.py:228` 後

  leaf 強制用に次を新設する。

  ```python
  def acquire_protocol_claim(
      claim_root: Path,
      record: ClaimRecord,
      *,
      protocol_sha256: str,
      freeze_sha256: str,
  ) -> AcquiredClaim:
  ```

  `derive_protocol_claim_identity(...)` を leaf 内で再計算し、`record.campaign_identity` と完全一致しなければ filesystem 操作前に `ClaimError`。一致時だけ既存 `acquire_claim()` へ委譲する。これにより call site が `_fresh_run_id` へ戻っても専用 leaf が拒否する。

- `orchestrator/campaign/s8b_floor_campaign.py:4716-4719`

  現行 `claim_identity` を削除し、`single_process=True` の枝でのみ、意味を限定した名前 `protocol_claim_identity` を上記 helper から得る。

  入力の出所は次のとおり。

  - `protocol_sha256`: `s8b_floor_campaign.py:4679` の `_canonical_sha256(protocol)`
  - `freeze_sha256`: verified freeze の byte hashである `s8b_floor_campaign.py:4664-4669`
  - freeze hash は同時に `protocol["freeze"]["sha256"]` と照合済み

- `orchestrator/campaign/s8b_floor_campaign.py:4733-4742`

  `ClaimRecord.campaign_identity` に `protocol_claim_identity` を設定し、`acquire_claim` を `acquire_protocol_claim` に置換する。protocol/freeze SHAも専用 leafへ渡す。

- `orchestrator/campaign/s8b_floor_campaign.py:4759` と `:5104-5113`

  変更しない。`campaign_run_id` と run directory 名は引き続き `_fresh_run_id(protocol_sha256, started_at)` であり、run identity の意味だけを持つ。

- `single_process=False`

  `s8b_floor_campaign.py:4720` の発火条件は保持する。reservation/claim の取得は増やさず、`linux-baremetal` の contract を変更しない。

- provisional 裁定

  - P1: 採用。固定 domain、protocol SHA、freeze SHAのみ。
  - P2: 結論は採用し resume でも同じ protocol identity とする。ただし現行登録 contract は `env_contract.py:245-303` の `(True, False)` と `(False, True)` だけで、`single_process=True / allow_resume=True` は実在しない。
  - P4: 採用。`ClaimRecord` field は追加しない。
  - P5: 採用。identity の導出だけでなく専用 acquisition leaf でも再検算する。

## S2 実装プラン

- host

  - 現実側 source: kernel hostname。`socket.gethostname()` に対応する OS 状態は `/proc/sys/kernel/hostname`。FQDN形も床値 wrapper が観測しているため、`socket.getfqdn()` も取得し、いずれかとの完全一致だけを認める。wrapper の同型観測は `tools/pegasus/floor_campaign.sh:576-579,716-722`。
  - `orchestrator/campaign/reservation.py:5-10` に `socket` を追加し、`:178-188` 後へ次を新設する。

    ```python
    def _read_current_hostnames() -> tuple[str, ...]:
    ```

  - `reservation.py:218-227` の `check_reservation` にテスト用の厳格な reader seamを追加する。

    ```python
    hostnames_read_fn: Callable[[], tuple[str, ...]] = _read_current_hostnames
    ```

  - `reservation.py:237-251` で `PBS_JOBID` 照合後、boot ID照合前に検査する。reader が非 callable、例外、空、非文字列を返す、または `binding.host` がどの観測値とも完全一致しない場合は `ReservationError`。小文字化、short-name 切り詰め、警告化はしない。

- script SHA-256

  - 現実の値自体は shell wrapper に存在する。床値は実行中 `$0` を hash する `floor_campaign.sh:508-520` と committed blob の hash `:540-555`、T126 は `t126_qualification.sh:674-681,708-716`。
  - しかし Python側の `sys.argv[0]` は PBS script ではない。床値は `floor_campaign.sh:962-965` で Python driver、T126 は `t126_qualification.sh:788-797` で別 driver を起動する。したがって Python executable の hash との比較案は退ける。
  - 現行 edit scopeでは実行中 shell script の bytesまたは FD が `check_reservation` に渡らないため、正しい照合を実装できない。段 4 で wrapperから read-only FDまたは厳格に検証した evidence を渡す scope 拡張を採った場合だけ、`check_reservation` に必須 `script_sha256_read_fn` を追加する。
  - reader 不在、読取不能、64桁小文字 hexでない、または不一致なら時刻検査前に `ReservationError`。省略可能な `None`、環境変数による免除、警告継続は設けない。

- nonce

  - `IZANAGI_SUBMISSION_NONCE` は `submit_floor.sh:411-423` で `qsub -v` に渡されるが、同じ job script が `IZANAGI_RESERVATION_NONCE` も設定するため、env 同士の比較では trust boundary を越えない。
  - create-only receipt は実在するが scheduler 所有ではない。床値 receipt は login-side wrapper が `submit_floor.sh:466-495` で `"x"` 作成し、T126 receipt も submitter が `submit_t126_qualification.sh:730-791` で publishする。
  - よって P3 を採用し、nonce 照合は設計メモに留める。scheduler 所有の receipt または live scheduler応答に nonce が束縛された実 artifact path が得られるまで実装しない。
  - source が実在した後は、receipt の読取不能、duplicate key、schema不一致、job ID不一致、nonce不一致をすべて `ReservationError` にする。

- `single_process=False`

  `check_reservation` の caller 条件である `s8b_floor_campaign.py:4685` と `s8b_oracle_driver.py:915-925`、および `reservation.py:273-277` は変えない。したがって host照合を含む新検査は required reservation 経路以外では発火しない。

## 変更するテスト

- `orchestrator/tests/test_campaign_claim.py:17-22`

  新しい identity helper と専用 acquisition leaf を importするだけで、既存 generic claim の期待値は変更しない。

- `orchestrator/tests/test_s8b_floor_campaign.py:3785-3811`

  既存 owner-report test の事前 claim を `_fresh_run_id` ではなく `derive_protocol_claim_identity` で作る。既存 claim の `created_utc` と実行側 `now_fn` を別の秒にし、同一秒衝突から「別 run・同一 protocol」の衝突へ期待を強める。

- `orchestrator/tests/test_reservation.py:37-47`

  positive fixture に一致する `hostnames_read_fn` を明示する。現実側観測をテスト seam で供給するだけで、検査の省略ではない。

- `orchestrator/tests/test_reservation.py:125-133`

  記録済み Pegasus positive control に `("bnode011",)` を返す hostname readerを追加する。literal binding の期待は維持する。

- `orchestrator/tests/test_s8b_floor_campaign.py:1258-1302`

  required-mode integration fixture の live hostname readerを `"fixture-host"` に固定する。fake bindingだけを差し替えて実機 hostname に依存しないようにするもので、host mismatch の期待を弱めない。

- `orchestrator/tests/test_s8b_oracle_driver.py:1927-1940,2195-2219`

  oracle側の required fixtureにも一致する hostname observationを供給する。`check_reservation` の第2 production consumerを取り残さない。

- `orchestrator/tests/test_s8b_floor_campaign.py:3949-3952`

  P4 採用により変更しない。exact field set pinを維持する。

- `orchestrator/tests/test_s8b_floor_campaign.py:6408-6413`

  値の期待は変更しない。hostが現実照合済みになっても claim record の値は同じである。

## 新設するテスト

- `test_campaign_claim.py`

  `test_protocol_claim_identity_changes_for_each_bound_digest`: protocol SHAだけ、freeze SHAだけをそれぞれ変更し identity が変わることを別 caseで固定する。対象 fieldが identityから抜けた場合だけ赤になる。

- `test_campaign_claim.py`

  `test_protocol_claim_leaf_rejects_run_identity_before_write`: validな protocol/freeze SHAに対して timestamp形式の `record.campaign_identity` を渡し、`ClaimError` と directory無変更を要求する。leaf再検算が無い場合だけ赤になる。

- `test_s8b_floor_campaign.py`

  `test_required_same_protocol_different_run_time_collides`:1秒違う owner claimを先に置き、同じ protocol の campaignを起動して既存 owner付き拒否と tree不変を要求する。run時刻が identity に残った場合だけ赤になる。

- `test_reservation.py`

  `test_check_reservation_rejects_live_hostname_mismatch`: binding=`node-a`、live observation=`node-b` とし、host不一致だけで赤にする。

- `test_reservation.py`

  `test_check_reservation_rejects_unreadable_hostname`: reader例外を `ReservationError` に変換することを要求する。例外の握り潰しまたは host検査省略だけを検出する。

- script SHA の authority が裁定・実装された場合

  - 一致する receipt/script positive control
  - script bytesを1 byte変えた mismatch
  - reader不能

  の3件を分離する。mismatch test は他 fieldをすべて正しく保ち、script照合欠落だけで赤にする。

- nonce authority が実在した場合

  - receipt nonceだけを変更した mismatch
  - receipt欠落
  - receipt job ID不一致

  を分離する。現時点では発火 artifact が無いため、実装済み検出力として数えない。

## 親 brief の誤り

- `brief.md:66-69`

  現行 registered contract で resume が拒否される直接理由は、元 run の claim残存ではなく `s8b_floor_campaign.py:4658-4662` の `allow_resume=False` である。`env_contract.py:245-303` に `single_process=True / allow_resume=True` は無い。一方、`IsolationPolicy.__post_init__` は `env_contract.py:67-69` で bool形状しか検査しないため、将来または注入 contractとしては組合せ自体が可能である。

- `brief.md:46-48`

  `ReservationBinding` に fieldが存在することと、独立した現実側 sourceが存在することを同一視している。host sourceはあるが、script SHAは shell内で止まり、nonceの scheduler-owned receiptは存在しないため、3件すべてについて DW-O13充足とは言えない。

- `brief.md:102-106`

  Unit Bを `reservation.py` と `test_reservation.py` だけで閉じる pin閉包は不完全。host検査だけでも `test_s8b_oracle_driver.py:1927-1940,2215-2219` に波及する。script/nonceの必須 evidenceを導入するなら両 production callerとPBS wrapperにも波及する。

- `brief.md:47,49`

  現行位置は `check_reservation=reservation.py:218-270`、`acquire_claim=campaign_claim.py:167-228`。記載の終端行はそれぞれずれている。

## 実装単位の分割

現行 briefの列挙集合そのものは `Unit A ∩ Unit B = ∅` だが、Unit Bのconsumer閉包が不足している。

- Unit A

  `campaign_claim.py`、`s8b_floor_campaign.py:4716-4742`、`test_campaign_claim.py`、`test_s8b_floor_campaign.py`。floor integration fixtureへの host reader seamも、同一 test fileの所有衝突を避けるためUnit Aが持つ。

- Unit B

  `reservation.py`、`test_reservation.py`、`test_s8b_oracle_driver.py`。host照合だけなら production oracle callerの変更は不要。

この修正版でもファイル集合は素集合である。ただしUnit Bの APIを先に確定し、Unit Aが後から integration fixtureを合わせる依存順があるため、完全並列ではない。

script/nonce evidenceを同一 waveへ入れる裁定なら、Unit Bへ `s8b_oracle_driver.py` とPBS wrapper群を追加し、floor callerの変更はUnit Aへ寄せる必要がある。しかし `s8b_floor_campaign.py:4693-4699` は許可編集面外なので、現行制約のままでは分割不能である。

## 未解決・裁定が要る点

- S2の完了条件を次から択一する必要がある。

  1. script SHA・nonceの独立 authorityが無いので、S1とhostだけへ明示的に再裁定し、残りを別 taskへ送る。
  2. PBS wrapper、両 Python caller、編集面を拡張し、実行 script bytesとauthority receiptを必須 evidenceとして渡す。ただし nonceについては scheduler-owned artifactを先に実測する必要がある。
  3. submitter-owned receiptまたは env同士の比較を authority とみなす。

  推奨は1。3は恒真 gateを残すため退ける。2は現時点でnonceの DW-G04 artifactが無く、直ちには実装へ進めない。

- 将来 `single_process=True / allow_resume=True` を登録する場合、protocol claimが残っている限り resumeを拒否する one-shot semanticsを採るか、contract組合せ自体を禁止するかを裁定する。今回の推奨は前者で、受理集合は強める方向にだけ狭まる。

- ユーザーの「host/script/nonceを同じ waveで」という既裁定を維持するなら、上記authority不足は段 4 の停止条件であり、部分実装を既成事実として landしてはならない。