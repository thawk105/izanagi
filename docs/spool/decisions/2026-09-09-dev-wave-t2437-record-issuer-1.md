---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2437-record-issuer
seq: 1
---

## {{D:result-evidence-production-issuer}}. result-evidence の発行は per-result で行い、受領証は解決済み契約から読んだ値で権威検証器に掛ける

**決定:** D1809 が core API として閉じた producer を、`run_campaign()` の実行結果から呼ぶ形へ配線する。
形は次に閉じる。

- `run_campaign()` へ keyword-only の `result_evidence_context` を足す。既定 `None` で既存 caller は無変更。
- **発火点は per-result** (`s.results.append(r)` の直前) とする。campaign 末尾では複数 genome のとき
  「どの評価の証拠か」が一意に決まらない。
- context 非 `None` のとき、最初の durable write より前に exact 型・単一 genome・balanced 非併用・
  evidence root の実在と layout 包含を要求する。
- identity-skip / identity-error / terminal-skip / eval-exception の 4 経路も発行の判断を通し、
  terminal はあるが typed 結果が無い場合と attempt が一意でない場合は**明示的に拒否する。**
  既存 terminal の skip 2 経路は無条件に拒否する (過去 attempt の WAL と現在 run の受領証を
  混ぜた record を作らせない)。
- **公開 issuer は解決済みの `ExecutionEnvironmentContract` を必須入力として受け取る。**
  契約の digest が origin capability の束縛値と一致することを要求し、
  `env_tag` / `attestation_mode` / `contract_sha256` を**契約から読んで**
  `execution_guard.receipt_matches_contract()` へ渡す。呼び手の自己申告で検証の分岐を選べない。
  required 契約で較正の裏取りが欠ければ拒否する。
- source は terminal 時点の WAL prefix の immutable snapshot とし、live WAL を参照しない。
  projection の byte 区間は元 WAL の実 offset を保つ。
- `EvalResult` が typed `VerifyResult` を保持するのは local verifier 由来の rejected repetition だけとし、
  accepted と remote fan-out は `None` にする。自己申告の wire payload から typed 値を再構成しない。
- issuer の例外は abort へ変換せず伝播させ、`CampaignSummary` を返さない。

**名乗りの上限を決定に含める。** 本決定が閉じるのは production package 内の issuer 配線と、
fixture-origin scope での単一 member の発火可能性までである。
「8c origin を結線した」「本番の projection が端から端まで通る」
「producer が自由に生成した record を ledger 束縛 consumer が受理した」とは主張しない。

**理由:**
- 受理側は exact 33 record を要求し、1 campaign run は 1 件しか作らない。さらに ledger の
  evidence digest は seal 時に確定するのに、新しい record は attempt ID・nonce・timestamp という
  毎回変わる値を含む。したがって「先に答えを知っている fixture」でしか通らず、
  自由生成 record の受理は原理的に示せない。この循環は敵対相談の 2 レンズが独立に指摘し、
  親が現物で裏取りした。
- 受領証は「あるか」ではなく「本物か」で見なければ関門にならない。repo には権威検証器が
  既にあったのに参照が 0 件で、条件に合う任意の dict が通っていた。さらにそれを直した後も、
  検証の分岐を呼び手が自己申告できた。**契約実体を渡す以外に、呼び手の申告と実際の認証強度を
  一致させる手段が無い。**
- 発行を使わない既定経路の意味を変えないためには、helper 内の早期 return では足りない。
  Python は呼び出しの前に引数を評価するため、call site を囲む必要がある。
- 既存 terminal の skip で generic な発行判断へ落とすと、過去 attempt の WAL と現在 run の受領証を
  混ぜた record を新規発行できてしまう。

**却下した選択肢:**
- **campaign 末尾を発火点にする** — 複数 genome のとき証拠と評価の対応が一意でない。
- **accepted でも typed 結果を保持する** — 任意 1 pass の値を残すことは「全 pass 通過」という
  事実の誤縮約になる。accepted の成立条件は terminal の `commit` と検証構成の exact 一致で閉じている。
- **live WAL を source ref に指す** — 後続 append で whole-file digest が壊れ、解決不能になる。
- **producer 用の共有 module を新設する** — 受理側の source 検査が production source を
  exact 15 file の閉集合に固定しており、新 module はその外へ出る。
- **`attestation_mode` が none の site でも自己申告の digest で provenance を埋める** — 規律 3 に反する。
  発行は認証済み受領証がある site に限る。
- **`run_origin_trial` の production 呼び手を同じ wave で置く** — 公開呼び手を置いても issuer へ
  到達する経路が 1 本も無いことを実測した。発火しない機構を置くのは実装したふりである (DW-G04)。

**限界:**
- 受理側の completeness の origin 分岐と材料レポート renderer は未着手であり、
  設計 §12 の「この 2 層に触れずに結線したと名乗ってはならない」に従って名乗らない。
- terminal 後に issuer が失敗すると terminal WAL と部分 artifact が残り record が無い。
  受理側は fail-closed で拒否するが、自動で ledger tombstone へ接続する経路は無い。
- **enforcement source closure に載る file は変異検査で帰属できない** ({{F:mutation-blocked-by-source-closure}})。
  本決定のうち `loop.py` と `pipeline.py` に置いた関門の実効性は、変異ではなく負例そのものが担保する。
