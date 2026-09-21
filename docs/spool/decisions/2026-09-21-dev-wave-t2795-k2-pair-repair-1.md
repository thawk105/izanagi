---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-t2795-k2-pair-repair
seq: 1
---

## {{D:k2-pair-authorization-session}}. 同 job pair は 1 process の認可 session で claim を共有し、claim leaf と one-shot 性は不変のままにする

**決定:** D2187 の修復方向 ((ii')「1 回の認可・claim の所有期間で候補と stock の両評価を行う driver 設計」) を次の形で実装した。

- `orchestrator/campaign/loop.py` に `authorization_session()` (context manager) と opaque な session 型を足し、`run_campaign` と `_authorize_measurement` が
  keyword-only で受け取る。module-private の台帳が**発行個体の object identity** と発行 pid を保持し、close は不可逆、同型コピーと pickle は拒否する。
- 未束縛の session を渡した最初の呼出しは現行どおり認可し `campaign_claim.acquire_claim` を通ったうえで、**認可成功の直後** (perf preflight・layout・campaign lock・
  evaluate より前) に束縛する。初回取得の例外は包まず透過させる (`ClaimError` は `ClaimError` のまま)。
- 束縛済みの session を渡した呼出しは、現在の入力から契約 (`require_certified_writer_authorization` の再実行と契約 sha)・campaign identity・
  `sha256(canonical_preimage(bound_cfg))`・declared_use_class・解決済み output root・claim root (実在・非 symlink・write capability)・claim path・
  claim file の record 全体・reservation binding (`read_binding` + `check_reservation` の再実行)・required 契約の receipt (verified calibration 再ロード + `receipt_matches_contract`)・
  pre-write validator を**すべて再計算して照合**し、`acquire_claim` だけを省く。不一致は layout / campaign lock / WAL / evaluate より前に `ExecutionGuardError` で拒否し、
  救済の再取得や新しい session への認可情報の移植はしない。
- session 無しの `run_campaign` は呼出し順・receipt の object 同一性とも不変。`campaign_claim.py` は bytes 不変 (sha256 `2e9c0932…`)。identity preimage・admission・verifier の
  受理集合も不変。
- driver 側は `--run-iteration <proposal> --stock-control` を pair mode とし (`--isolate-worktree` 必須)、1 process で候補→stock を評価する。候補は従来の build context
  (coder authority 付き)、stock は authority 無しの別 context・STOCK 専用 resolver・別の pinned-clean checkout を使い、両 context の admission policy 一致を測定前に要求する。
  候補が reject / abort / duplicate-skip / 通常例外でも stock を試行し、rc は候補非零優先 (候補 0 なら stock rc、0 は `certified-stock` のときだけ)。
  `--stock-control` 単独 (B-5 の slot 起動) は argv・挙動とも不変。
- job body は `IZANAGI_S4_STOCK_CONTROL=1` を driver 1 起動にし、shell 側の 2 段集約を削除して driver の rc を返す。`=1` かつ proposal 無し (fixture) は prebuild / trap より前に
  rc=2 で拒否する。これは `tools/pegasus/README.md` §7 が認めていた fixture 併用契約の**縮小**であり、理由は「今回修復する production 入力は proposal で、fixture pair の
  新規対応は広げない」。未設定 / `0` の argv は bytes 不変。

**理由:**
- D464 / D553 の one-shot claim leaf は release も stale 回収も持たず、同 identity path を所有者の生死に関わらず拒否する。2 process 設計 (D2183) はこの leaf と構造的に
  両立しないが、leaf を変えることは排他防壁の受理集合を変えることになる。認可を 1 度取り、その所有期間の内側で両評価を行う形にすれば、leaf を不変のまま同 campaign・
  同 WAL の対照が取れる。
- 「同 process にまとめるだけ」では成立しない — `run_campaign` は呼出しごとに認可するため、2 回目も同 path を `O_EXCL` で取りに行く。認可済みであることを sink が
  再確認して取得だけを省く形まで具体化して初めて成立する。
- 束縛の再照合を sink に置くのは、driver に所有判定を置くと「claim を持たない process が測定へ到達する」経路を driver 側の誤りで作れてしまうためである。
- 候補と stock を別 checkout・別 build context にするのは、stock の source が STOCK であること (BUILD_START の `src_token`) と coder authority の不使用を、
  名前ではなく実体で保つためである。

**却下した選択肢:**
- loop.py を変えず 1 回の `run_campaign([候補 genome, stock genome])` にまとめる — 先例 (A-1 paired、sweep 系) はあるが、通常経路は `ccbench_dir`・`build_context`・
  capability resolver を各 1 本しか取らないため、stock の隔離・admission・結果処理を作り直す必要がある。候補が検疫 reject で sink に到達しない経路も別に組み直しになる。
- 同 identity path の DEAD 所有者を再取得可能にする / claim の rename・退避 / 別 out_root / stock 未測定を判定で置換 — いずれも D2187 が却下済み。
- 発行台帳を持たず型だけで session を判定する — 同型のコピーや close 後の個体を受理する。段 6 レビューの must-fix。
- session 転送を字面 pin だけで守る — 代入の後に `campaign_options.pop(...)` を挟む実装でも緑になる。実効性は結合検査に帰属させる。

**再訪条件:** 実機 (Pegasus) の pair 1 走は本決定の時点で未実施であり、予算の再提示はユーザー手番である。実走で新しい不整合が出た場合は、
結合検査の stub 境界 (build / trace / bench / attestation 観測 / condition gate / patch 適用 / checkout / SourceEvidence / perf preflight) のどれが機序を隠したかを先に切り分ける。
