---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2195-policy-binding
seq: 2
---

## {{D:mocc-policy-binding-five-party-sha}}. mocc trace policy の束縛は投入時 raw SHA を 5 者で照合し、読み口は non-blocking かつ strict JSON にする

**決定:** D1541 の三者照合 (job 側 raw bytes・shell 変数・最終受領証) を次の形で実装する。

- 投入側 (`submit_mocc_trace.sh`) は policy を O_NOFOLLOW + regular file 検査で 1 回だけ読み、同じ bytes から
  raw SHA-256・`expected_compiler_version_body_sha256` mapping・`mocc_trace` 射影を導く。clean-tree gate 通過後に
  再 hash して初回と一致することを要求し、pre-submit / submit receipt の `policy` 節へ `raw_sha256` と mapping を
  記録し、qsub の `-v` で `IZANAGI_MOCC_POLICY_RAW_SHA256` を job 環境へも渡す。
- job 側 (`mocc_trace_pilot.sh`) は早期 parser も同じ bytes から raw SHA を出し、source clean capture の**後**・
  T1718 compiler gate の**前**に独立 marked block (`T2195 POLICY BINDING GATE`) を置く。gate は post-clean で読み直した
  policy raw bytes・早期 parse 由来の shell 変数・pinned submit receipt・qsub 環境変数・receipt に記録された qsub argv の
  `-v` 項の **5 者の raw SHA 全一致**と、live policy・shell 変数・receipt の **3 者の mapping 全一致**、および
  policy の repo 相対 path が正準値であることを要求し、不一致・欠落・型不正・symlink・非 regular file・duplicate key を
  `policy_binding` stage で fail-closed にする。finalization では独立 block で同じ値を再確認し、最終受領証の
  top-level `policy` に `repo_path` / `raw_sha256` / mapping を記録する。
- policy と pinned receipt を読む全 open に `O_NONBLOCK` を加え (fd 直後の `fstat` で非 regular を拒否する順序は不変)、
  権威的な全 `json.loads` に `NaN` / `Infinity` / `-Infinity` を `ValueError` にする `parse_constant` を渡す。
- 負例は production の shell fragment (parse → policy 復元 → receipt pin → clean capture → binding gate) を 1 つの
  bash wrapper で実走し、「書き換え → 読ませる → 復元」経路が clean capture を通っても `policy_binding` で拒否される
  ことを示す。schema version (pre-submit v1 / submit-receipt v2 / pilot-receipt v4)・既存 gate の述語と順序・
  consumer・履歴 receipt は変えない。

**理由:**
- 受領証だけに raw SHA を持たせると、receipt の自己 pin と同じ主体が書く値になる。qsub `-v` は scheduler が保持する
  投入時の値であり、receipt と独立した第 5 の証人になる (段 3 相談 A の must-fix)。
- 早期 parser が raw SHA を出さないと、shell 変数側の期待値がどの bytes 由来かを job 内で言えない。late read を残すのは
  clean capture 後の実体を読む必要があるからで、両方が要る。
- 書き手のいない FIFO は O_NOFOLLOW だけの open で `fstat` の前に block し、失敗記録も最終受領証も残らないまま walltime
  まで停滞する (段 6 レビュー A1 / B1)。`json.loads` は既定で非有限定数を受理するため、未参照 field に置いて SHA を合わせれば
  gate を通れる (A2)。どちらも受理集合を狭めるだけの修正である。
- 三者照合の実装であって、版ずれ検出の拡張 (D1542 の射程) や他 policy field の一般化は含めない (ユーザー指示の scope)。

**却下した選択肢:**
- 既存 checks dict へ policy 比較を混ぜる — gate の順序と marker の一意性が test で固定できず、既存述語の変更と区別しにくい。
- receipt の自己 pin だけで済ませる — 投入権威の独立した証人にならない。
- 早期 parser を廃して late read だけにする — shell 変数側の期待値の出所を失う。
- gate 順序 (M12) を実行時変異で所有する — 170 行 block の移動は置換で表せず、marker 削除は診断文字列だけの赤になるため、
  静的 test で所有する。
