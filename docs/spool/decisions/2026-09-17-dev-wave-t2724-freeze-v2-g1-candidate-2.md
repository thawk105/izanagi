---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2724-freeze-v2-g1-candidate
seq: 2
---

## {{D:v2-candidate-producer-resolves-protocol-via-index-authority}}. freeze v2 g1 candidate producer は floor protocol を index authority で解決し、固定 path の literal read をやめる

**決定:** `s8b_holdout_freeze.py generate-v2-candidate` の `_validate_floor_inputs` は、固定
`output/s8b-freeze/floor_protocol.json` を直接読む代わりに、campaign 側・admission 側と同じ
`s8b_floor_campaign.resolve_current_floor_protocol` (D460 型: caller に選ばせず index authority で解決)
で現行 protocol を解決する。解決 record の commit OID が captured HEAD と一致すること、解決 path の
worktree bytes が HEAD blob と一致することを要求し、candidate の `floor_protocol` には解決 path と
raw sha256 を記録する。固定 path は index の anchor として残し、`FLOOR_PROTOCOL_REL` 定数は変えない。
走査除外・allowlist・admission・批准側・既存 test の期待値は変えない。

受理集合: 旧「固定 protocol と一致する result」→ 新「index authority が解決した現行 protocol と一致する
result」。本番相当 (anchor + 同一契約の版付き 1 件、HEAD の ccbench gitlink が版付きを選ぶ) では、旧実装は
早期の hash 比較で版付き result を拒否し、固定 protocol 対応の result も後段の admission
(`_authority` が解決 record と producer の protocol 文書の一致を要求) で拒否していたため、受理集合は
空だった。新実装は版付き result だけを受理する。

**理由:**
- 2026-09-16 完走の official 床値 result (`protocol_sha256 = 2c8cf9be…`) を producer が
  `protocol_sha256 不一致` で fail-closed した (2026-09-17 実測)。固定 protocol (ccbench pin `d706650c…`)
  と official 走行が解決した版付き protocol (pin `511c9538…`) の差は pin 1 行で、producer が
  2026-08-12 の pin 前進に追随していなかった。
- D589 がこの箇所を「current の literal read で D460 型変換の対象になり得るが、承認 artifact・pin ratify・
  official result の 3 条件が揃わず到達不能」と deferred していた。3 条件は 2026-09-16 にすべて揃った。
- 批准側 (`_verify_generation_semantics` V1d、`assert_g1_floor_selection_identity`) は generation
  document の `floor_protocol.path` を読むので、版付き path の記録と整合する (段 6 レビューで確認)。

**却下した選択肢:**
- 固定 `floor_protocol.json` の pin を書き換える — `output/s8b-freeze/` の凍結 bytes であり、historical
  anchor として literal を pin する test (`test_floor_protocol_historical_anchors_remain_legacy`) と
  hook の誤操作抑止に反する (規律 2)。
- result 側を書き換える — 測定成果物の改変。
- 解決 record の raw bytes と worktree bytes の比較を producer に足す — 同じ commit の HEAD blob 同士の
  比較で恒真になる (段 6 レビュー RA-1)。実装後に削除した。

## {{D:freeze-g1-candidate-chain-isolation}}. g1 候補の入力 chain は保存 branch に置き、docs の land 集合から分離する

**決定:** official 床値 result の再配置 commit・budget 入力・候補 commit (X1' / X2) は、base main から
分岐した保存 branch `freeze-g1-chain-t2724` に置き、本 wave が local main へ land するのは producer の
修正・docs・一次資料・fragment だけとする。chain を main へ取り込むか (= D2077 step 4 の「当該 holdout
集合の official 走行を打ち切る」決定) は人間裁定に委ね、裁定パッケージで返す。

**本 wave は D2077 step 4 の打ち切り決定を下していない。** 依頼が候補生成を明示し、候補生成は D2077
step 5〜6 (restore → commit → generate) 無しに機構上不可能なため、restore 以降を保存 branch に隔離して
実施した。これは D2077 の例外を新設するものではなく、step 7 の帰結 (成果物を持つ checkout では
official 床値の起動証明が赤になる) を main に及ぼさない実施形である。「D2077 を満たした」とは記録しない。

**理由:**
- X1' を含む checkout では official 床値の clean scan が赤になる (D2077 step 7)。main に載せる判断は
  以後の official 床値 wave を止める判断と同じであり、依頼は「人間承認の受領証発行まで進めるかを裁定
  パッケージで返す」としている。
- 批准 topology は X1' が保存されていれば後から満たせる: 世代導入 commit G は非 merge・親 == X1'
  (`frozen_at_head`)・AI trailer 付き、approval A / pointer X は人間 commit。通常 merge で G の
  ancestry と入力 bytes を保持すれば `_immutable_introductions` も成立する (段 3 レンズ A で確認)。
- 固定退避先の bundle は restore 後も残るので、chain を捨てても入力は再取得できる (可逆性は data の
  話であり、判断の取消しの根拠ではない)。

**却下した選択肢:**
- chain を docs と同時に main へ導入する — 未裁定の打ち切りを先取りする。
- 停止して裁定へ返す — 隔離実施は main に不可逆な影響を残さず、ユーザーの常設指示 (裁定へ返さず決める、
  可逆で低影響の判断は諮らない) に反する。

## {{D:oracle-manifest-caller-is-operator-cli}}. oracle manifest の呼び手は operator で、入口は既存の build-approved CLI とする

**決定:** runbook W-4 の「production 配線」は `s8b_oracle_manifest.py build-approved --output <path>` CLI
(実装済み、[T-750] 単位 B) を入口とし、実行主体は operator とする。wrapper script は新設しない。

**理由:**
- CLI は `build_approved_manifest` を呼ぶ production の入口であり、呼び手が test だけという runbook の
  記述は stale だった。
- 発火できる artifact が無い: active ratified freeze が無く `no-active-ratified-freeze`、
  `s8b_oracle_spec.APPROVED_SPEC_SHA256 = None` で `no-approved-spec` の 2 段で fail-closed する。
  発火条件を満たす artifact を書けない条件付き機能は実装しない (dev-wave `DW-G04`)。

**却下した選択肢:**
- 最小 wrapper script の新設 — 現在の不足 (spec 承認) を解消せず、承認済み入力も無い。
