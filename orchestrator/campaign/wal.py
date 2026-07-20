# -*- coding: utf-8 -*-
"""WAL (write-ahead log) と クラッシュリカバリ (orchestrator-design.md D/A)。

探索は一晩回しっぱなしでクラッシュ前提。各 variant の評価を**ログ先行書き込み**で
進め (`build_start → build_done → verify_done → bench_done → commit`)、再起動時に
リプレイして「どこまで評価済みか」を復元し途中再開する。

- **D (durability):** 追記ごとに flush+fsync。クラッシュで追記済みレコードを失わない。
- **A (atomicity):** commit レコードがある variant だけ採用。なければ破棄して再評価
  (half-evaluated を population に混ぜない)。
- **末尾切れトレラント:** 追記中のクラッシュで最終行が壊れていても、その 1 行だけ
  捨ててリプレイを続ける (WAL の定石)。

各行は duplicate key と record の基本形を構造検査する。hash chain はなく、任意の
変更に対する真正性を保証するものではない。
"""
from __future__ import annotations

import json
import math
import os
import time
from typing import Dict, Iterator, List, Optional

from .layout import CampaignLayout
from .model import (STAGE_ABORT, STAGE_COMMIT, EvalState, WalRecord)


# ---- シリアライズ ----

class WalLineError(ValueError):
    """WAL 1 行が record 契約を満たさない。"""


class WalDuplicateKeyError(WalLineError):
    """WAL の JSON object に duplicate key がある。"""


def _reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise WalDuplicateKeyError("duplicate key in WAL JSON object: %r" % key)
        value[key] = item
    return value


def parse_line(line: str) -> WalRecord:
    """WAL 1 行を duplicate-aware に parse し、基本 record 契約を検査する。

    stage の白名簿・event topology・payload object 内の個別 schema は consumer 側の責務。
    空行は writer が生成しないため、record として受理しない。
    """
    if not line.strip():
        raise WalLineError("WAL line must not be empty")
    value = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
    if not isinstance(value, dict):
        raise WalLineError("WAL record must be a JSON object")
    required = {"variant", "stage", "env_tag", "ts", "payload"}
    if set(value) != required:
        missing = sorted(required - set(value))
        unknown = sorted(set(value) - required)
        raise WalLineError(
            "WAL record keys must be exactly %r (missing=%r, unknown=%r)"
            % (sorted(required), missing, unknown)
        )
    if not isinstance(value["variant"], str):
        raise WalLineError("WAL variant must be a string")
    if not isinstance(value["stage"], str):
        raise WalLineError("WAL stage must be a string")
    if not isinstance(value["env_tag"], str):
        raise WalLineError("WAL env_tag must be a string")
    ts = value["ts"]
    if (isinstance(ts, bool) or not isinstance(ts, (int, float))
            or (isinstance(ts, float) and not math.isfinite(ts))):
        raise WalLineError("WAL ts must be a finite number other than bool")
    if not isinstance(value["payload"], dict):
        raise WalLineError("WAL payload must be a JSON object")
    return WalRecord(
        variant=value["variant"], stage=value["stage"], env_tag=value["env_tag"],
        ts=ts, payload=value["payload"],
    )


def _record_to_line(r: WalRecord) -> str:
    obj = {"variant": r.variant, "stage": r.stage, "env_tag": r.env_tag,
           "ts": r.ts, "payload": r.payload}
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _line_to_record(line: str) -> WalRecord:
    return parse_line(line)


def iter_lines(path: str | os.PathLike[str]) -> Iterator[tuple[int, str, bool]]:
    """WAL の全物理行を ``(行番号, text, 最終物理行か)`` として返す。

    空行を含めて一行も省略しない。各 consumer は :func:`parse_line` を通すことで
    同じ空行・record 契約を適用する。
    """
    with open(path, "r", encoding="utf-8") as stream:
        lines = stream.readlines()
    for index, line in enumerate(lines):
        yield index + 1, line, index == len(lines) - 1


# ---- 追記 (D) ----

def append(layout: CampaignLayout, record: WalRecord) -> None:
    """WAL に 1 レコードを追記。flush+fsync で耐久化。"""
    line = _record_to_line(record) + "\n"
    # writer 自身が strict reader で読めない行を生成しないことを、open 前に検査する。
    parse_line(line)
    os.makedirs(layout.runs_dir, exist_ok=True)
    new_file = not os.path.exists(layout.wal_file)
    # 'a' は O_APPEND 相当でレコード境界がアトミックに近い。fsync でディスクまで。
    fd = os.open(layout.wal_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    if new_file:
        # 初回作成時はディレクトリエントリも fsync し、WAL ファイルの存在自体を耐久化
        # する (D)。これが無いとファイル作成直後のクラッシュで WAL ごと失われうる。
        dfd = os.open(layout.runs_dir, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)


def log(layout: CampaignLayout, variant: str, stage: str, env_tag: str,
        payload: Optional[Dict] = None, ts: Optional[float] = None) -> WalRecord:
    """WalRecord を組んで追記する糖衣。ts 省略時は現在時刻。"""
    rec = WalRecord(variant=variant, stage=stage, env_tag=env_tag,
                    ts=ts if ts is not None else time.time(),
                    payload=payload or {})
    append(layout, rec)
    return rec


# ---- リプレイ / リカバリ (D, A) ----

def read_records_collected(
        layout: CampaignLayout,
) -> tuple[list[WalRecord], list[tuple[int, str]], bool]:
    """WAL の有効行と行単位 issue、末尾切断の有無を返す。

    ``line_issues`` は ``(物理行番号, 理由)``。途中の不正行を除外して後続の
    有効 record も集める。JSON として途中で切れた最終行だけは従来の crash
    prefix として ``truncated_tail`` へ分離する。
    """
    if not os.path.exists(layout.wal_file):
        return [], [], False
    records: list[WalRecord] = []
    line_issues: list[tuple[int, str]] = []
    truncated_tail = False
    for line_number, line, is_last in iter_lines(layout.wal_file):
        try:
            records.append(_line_to_record(line))
        except json.JSONDecodeError as exc:
            if is_last:
                truncated_tail = True
            else:
                line_issues.append((
                    line_number, f"{type(exc).__name__}: {exc}",
                ))
        except WalLineError as exc:
            line_issues.append((
                line_number, f"{type(exc).__name__}: {exc}",
            ))
    return records, line_issues, truncated_tail


def read_records_checked(layout: CampaignLayout) -> tuple[list[WalRecord], bool]:
    """WAL を読み、``(records, truncated_tail)`` を返す。

    JSON として途中で切れた最終行だけを crash prefix として許容する。構文的に完全な
    record 契約違反は、最終行でも :class:`WalLineError` として伝播する。
    """
    if not os.path.exists(layout.wal_file):
        return [], False
    out: list[WalRecord] = []
    truncated_tail = False
    for _line_number, line, is_last in iter_lines(layout.wal_file):
        try:
            out.append(_line_to_record(line))
        except json.JSONDecodeError:
            # 末尾の切れた 1 行だけは許容 (クラッシュ)。途中行の破損は異常。
            if is_last:
                truncated_tail = True
                break
            raise
    return out, truncated_tail


def read_records(layout: CampaignLayout) -> List[WalRecord]:
    """WAL を全レコード読む。最終行の crash prefix は従来どおり捨てる。"""
    records, _ = read_records_checked(layout)
    return records


def replay(layout: CampaignLayout) -> Dict[str, EvalState]:
    """WAL をリプレイし variant ごとの評価状態を復元する。"""
    states: Dict[str, EvalState] = {}
    for r in read_records(layout):
        st = states.get(r.variant)
        if st is None:
            st = EvalState(variant=r.variant)
            states[r.variant] = st
        st.stages_seen.append(r.stage)
        st.env_tag = r.env_tag
        st.last = r
        if r.stage == STAGE_COMMIT:
            st.committed = True
            st.last_terminal = r
        elif r.stage == STAGE_ABORT:
            st.aborted = True
            st.last_terminal = r
    return states


def records_by_stage(layout: CampaignLayout, variant: str) -> Dict[str, Dict]:
    """variant の stage→payload (最後勝ち)。判定は宣言でなく WAL レコードで行う。

    p3_kickoff.py / p3_s4_red.py / p3_s4_loop.py が各々独立に持っていた同一実装を
    統合 (D36 決定4-2)。**注意 (敵対レビュー 2026-07-09 で確認):** STAGE_VERIFY_DONE
    は S2 有効時 (evaluate() の extra_correctness、search_config['verify']=='legacy+s2')
    に variant ごと legacy→S2 の順で複数回書かれる。本関数は stage 単位の最後勝ちの
    ため、この場合は最後のパス (S2) の payload だけが残り、先行パスの verdict/commits/
    aborts は見えなくなる。全パスを見る・スケールを揃えて比較する必要がある consumer
    (例 critic.digest.load_verify_abort_signals) は wal.read_records() を直接使い、
    workload タグ (payload["workload"]["tag"]) で読み分けること。"""
    out: Dict[str, Dict] = {}
    for r in read_records(layout):
        if r.variant == variant:
            out[r.stage] = r.payload
    return out


def terminal_variants(states: Dict[str, EvalState]) -> set:
    """評価が終わっている (commit=採用 / abort=不採用) variant 集合 = スキップ対象。"""
    return {v for v, st in states.items() if st.terminal}


def resumable_variants(states: Dict[str, EvalState]) -> set:
    """未終端 = リカバリで破棄して再評価すべき variant (in-flight クラッシュ)。"""
    return {v for v, st in states.items() if st.resumable}


# ---- campaign.lock (同一性の正準 pre-image) ----

def write_lock(layout: CampaignLayout, preimage: str) -> None:
    os.makedirs(layout.root, exist_ok=True)
    # 初回のみ書く (既存があれば上書きしない = identity は不変)。
    if not os.path.exists(layout.lock_file):
        with open(layout.lock_file, "w", encoding="utf-8") as f:
            f.write(preimage)


def read_lock(layout: CampaignLayout) -> Optional[str]:
    if not os.path.exists(layout.lock_file):
        return None
    with open(layout.lock_file, "r", encoding="utf-8") as f:
        return f.read()


# ---- 原子的 one-shot lock / WAL 存在判定 (R6 resume 拒否の強化) ----

def acquire_lock_atomic(layout: CampaignLayout, preimage: str) -> bool:
    """`O_CREAT|O_EXCL` で campaign.lock を原子的に獲得する。既存なら False。

    write_lock (exists 確認後の非原子書き込み) の resume-safe 版。並行起動では一方だけが
    True を得る。WAL 空確認から最初の campaign-start append までを覆う排他区間の起点。
    True 時は preimage を書き込み、ファイル本体と親ディレクトリを fsync して存在を
    耐久化する (作成直後の crash でも lock が残る)。
    """
    os.makedirs(layout.root, exist_ok=True)
    try:
        fd = os.open(layout.lock_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return False
    try:
        os.write(fd, preimage.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(layout.root, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return True


def wal_bytes_present(layout: CampaignLayout) -> bool:
    """WAL ファイルに byte が存在するか (parse 可否は問わない)。

    read_records は末尾切れの 1 行を捨てるため、campaign-start 1 行だけの途中切断 WAL
    では [] を返しうる。resume 拒否は「parse 可能 record の有無」でなく「byte の存在」で
    判定する必要がある (truncated/汚染 WAL 迂回の閉鎖、fail-closed)。
    """
    try:
        return os.path.getsize(layout.wal_file) > 0
    except OSError:
        return False
