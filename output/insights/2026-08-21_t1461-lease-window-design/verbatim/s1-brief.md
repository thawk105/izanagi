# [T-1461] 段1 brief — 受入lease (D239) の排他区間を縮める設計

## scope
D239の排他lease (`tools/wave_land_window.py`) が現在 claim→(behind main なら merge)→受入テスト
実行 (compute dispatch queue待ち込み) →land投入 の全区間を排他保持している構造を、「重い処理は
claim前に先取りし、claim後は前提再確認+fast-forward+foldの短時間に抑える」方向へ再設計できるか
分析・検討する。D239の排他性 (並行landの直列化) 自体は維持する。成果物は設計提案、または段4で
安全に切り出せると判断した範囲があればその実装 (段4で確定、今は決め打たない)。T-870系列(h)(i)
(login_headroom peak履歴回復・queue-timeout overrideの受入launcherへの到達性) とは別軸で、
統合しない — あちらは「テスト実行を速くする/避ける」話、本waveは「lockの持ち方を変える」話。

## 確定済み前提事実 (今回コード調査で file:line 確認済み、段2で独立に裏取りすること)
- 実測根拠: `output/insights/2026-08-20_t870-congestion-nproc/README.md` 段9節。受入投入〜land完了
  7時間中、実テスト実行8分44秒・残り98%超がlease順番待ち (15+並行wave実測、queue congestion)。
- D239 (`docs/decisions.md:11172`): lease機構の原設計。目的は「無駄な受入投資の防止」であり、
  本文が「land の権威は変えない」と明記する通り正しさ機構ではない。既知の限界: fencing tokenなし
  (コード自身も `dev_wave_wait.py:4396` で明言)、release権限証明はwave slug digest
  (`sha256(wave)[:12]`) のみ。TTL=2400秒 (`wave_land_window.py:28`)。
- **lease機構の実体**: `claim()`(`wave_land_window.py:651-781`)はlease dir内の単一file
  `acceptance.lease`をO_EXCL+flockの二段で排他生成。metadataは`holder`/`main_sha`/`ttl`の3 field
  のみ (`:147-149`) — `tested_tip`相当の情報はlease側に無い。待ち行列は`ticket.<12hex>`による
  `queued_at_ns`順FIFO (`:592-648`)、TTL 300秒 (`:29`)。`renew()`(`:784-847`)はCLI未配線
  (Python importでのみ呼べる)。
- **D128 flock (`dev_wave_land.py:2018-2047`、ロック対象 `_LOCK_NAME` は git common dir 直下で
  worktree非依存) が実際の唯一の正しさの砦であり、D239 leaseとは独立に機能する** — lease無しでも
  D128だけで並行landは安全に直列化される。ただしD128の待ち上限は180秒
  (`_LAND_LOCK_WAIT_SECONDS`, `:60`) で公平性(FIFO)を持たない非公平な排他 (指数backoff+jitterのみ)。
  **leaseを縮小・撤去する場合、多数waveが同時に「claim→即land」へ殺到したときD128単体で
  livelock/starvationを起こさないかが攻撃対象。**
- D254 (`docs/decisions.md:11672`, `DW-O25`): 既に**land内部**に同型パターンが実在する —
  `land()`(`dev_wave_land.py:3127-3218`)は`locked_main != tested_tip`のときだけ、D128 lockを
  解放してから全史provenance監査 (480秒枠、`_audit_provenance_history`) をlock外で実行し、
  lock再取得後に`tip_sha`/`checker_blob_sha`/`executed_bytes_sha`/`returncode`を束縛した
  `_ProvenanceReceipt`(`:270-276`)を再照合する。**本waveの核心は、この既存パターンを
  「監査480秒」から「merge+受入テスト全体」へ一般化できるかの検討。**
- 受入receipt (26 field, schema `dev-wave-acceptance-receipt/v5`, 検証は
  `dev_wave_land.py:79-107`+`_verify_acceptance_receipt()`(`:716-947`)) の`tested_tip`は
  「merge直後・テスト実行前」の値に固定され、実行前後でwave自身のtree不変
  (`pre_fingerprint`==`post_fingerprint`)を要求する (`dev_wave_wait.py:4123-4133, 4209-4210`)。
  実際のテスト起動は`tools/acceptance_launcher.py`が`tested_tip`のblobから`tools/run_tests.py`を
  subprocess実行し、そこにcompute dispatch queue待ちを含む (launcher自体はlease機構に無関係、
  今回grep確認)。呼び出し元(`dev_wave_wait.py`)はこの完了を無タイムアウトで待つだけ
  (`:4145-4148`「timeout=none, long-running acceptance is intentional」)。
- 受入成功時、leaseは意図的にRETAINEDのまま保持され (`dev_wave_wait.py:3881`)、land成功後に
  親が明示`release`する設計 (`docs/pegasus-runbook.md:931-932`)。**「テスト成功とlease所有権の
  一体化」を解くのが再設計の中心課題。**

## 不変条件
- 正しさゲート・受入テストの内容 (件数・assert・検証ロジック) は一切変更しない (規律2、リワード
  ハック禁止)。`dev_wave_land.py`の全量再検証 (caller入力を信用しない設計、docstring `:4-7`が
  明言) を省略・弱体化する提案は却下する。
- 「tested_tip×tested_mainの組がテスト済み」という受入receiptの意味論を変えない。claim/lock取得
  タイミングを変えても、束縛検証の強度を落とさない。
- race検出 (前提再確認でtested_mainが現mainと不一致) 時の再測り直しは、常に**クロスwaveの排他
  資源を保持しない状態**で行う (D254の「監査はlock外」原則の一般化)。部分的・差分的な再検証
  (変更範囲だけ再テスト等) で済ませる提案は規律2により却下する。
- D239が受容した既知の限界 (fencing tokenなし) を悪化させない。claim/lockのタイミングを変える
  ことでこの既存の穴がどこへ・どう移動するかを明示する。

## 成果物の形・並列分割方針
単一の設計検討 (分割不要)。段2 codex plan (read-only) には上記アンカーの独立裏取りに加え、以下を
明示的に依頼する: (a) `_verify_acceptance_receipt()`(`dev_wave_land.py:716-947`)が`lease_holder`
fieldに対して何を検査しているか (leaseの扱いを変えたときこの検査が壊れないか)、(b) `renew()`
(`wave_land_window.py:784-847`、CLI未配線) がこの再設計で使えるか、(c) D128の180秒待ち上限
(`_LAND_LOCK_WAIT_SECONDS`)を維持したまま「claim→即land」殺到シナリオが安全か、必要なら
どう調整するか、(d) 具体的な再設計案 (最低2案: 「leaseを短縮するだけ」案と「leaseを廃しD128+
D254パターンの一般化だけに一本化する」案) をfile:line粒度で対比。

## (P1)〜(P4) 親のprovisional裁定 (段3攻撃対象)
- (P1) 排他leaseの「claim前に重い処理(merge・受入テスト)を済ませ、claim後は前提再確認+
  fast-forward+foldだけ」への再設計は成立する — D254が同型パターンをland内部で既に実証済みのため。
- (P2) D239のlease機構 (ticket FIFO含む) は「短時間化した後も」存続させる方が安全 — D128単体
  (180秒上限、FIFO無し) だけに委ねると多数wave同時到達時にlivelock/starvationのリスクがある。
- (P3) race検出時の再測り直しは、claim前の段階まで完全に巻き戻す (差分・部分再検証は行わない)。
- (P4) 受入receiptのschema (26 field) 自体は変更不要 — `tested_main`/`tested_tip`の記録タイミング
  (「merge直後・テスト前」) は現状のままでよく、claim/lockタイミングの変更はreceipt構造そのもの
  には影響しない。
