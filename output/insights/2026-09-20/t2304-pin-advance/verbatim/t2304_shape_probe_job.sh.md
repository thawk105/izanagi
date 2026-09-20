#!/bin/bash
# T-2304: build shape and compile liveness only; no performance measurement.
set -u

tag=${1:-}
mode=${2:-}
case "$tag" in login|compute) ;; *) exit 2 ;; esac
case "$mode" in configure|build) ;; *) exit 2 ;; esac
[[ $# -eq 2 ]] || exit 2
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2304-pin-advance
SRC=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/external/ccbench
REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance
R="$J/shape-probe/$tag"
CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache
PREFIX=/work/1/SFC/tanab/izanagi-a2-deps
mkdir -p "$J/shape-probe" || exit 10
exec > "$J/shape-probe/$tag.out" 2>&1
trap 'rc=$?; date -Is; printf "%s\n" "$rc" > "$J/shape-probe/$tag.done"' EXIT
rm -f "$J/shape-probe/$tag.done"

hostname
date -Is
nproc
uptime
ps -eo user,pid,pcpu,comm --sort=-pcpu | awk -v owner="$(id -un)" 'NR == 1 || $1 != owner' | head -15
CMAKE=/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin/cmake
[[ -f "$CMAKE" ]] || CMAKE=/usr/bin/cmake
[[ -z "${T2304_CMAKE:-}" ]] || CMAKE="$T2304_CMAKE"
"$CMAKE" --version
/usr/bin/g++ --version
/bin/python3.10 -V
head_oid=$(git -C "$SRC" rev-parse HEAD) || exit 13
printf 'SOURCE_HEAD=%s\n' "$head_oid"
[[ "$head_oid" == e9e477ca1b55348ab4530de0b1cf663ce4555290 ]] || exit 13

SNAP="$R/snapshot"
BASE="$R/fetchcontent"
SHIM="$R/shim"
rm -rf "$R" || exit 10
mkdir -p "$SNAP" "$BASE" "$SHIM" || exit 10
printf '#!/bin/bash\nexec /bin/python3.10 "$@"\n' > "$SHIM/python3"
chmod +x "$SHIM/python3"
export PATH="$SHIM:$PATH"
# archive would omit cc/oze via export-ignore.
cp -a "$SRC/." "$SNAP/" || exit 11
rm -f "$SNAP/.git" "$SNAP/third_party/shirakami/.git" || exit 11
test -f "$SNAP/cc/oze/CMakeLists.txt" || exit 15
for dependency in masstree mimalloc googletest; do
    cp -a "$CACHE/$dependency" "$BASE/$dependency-src" || exit 12
done

overall_rc=0
for trace in 0 1; do
    [[ "$trace" == 0 || "$mode" == build ]] || break
    BUILD="$R/build$trace"
    "$CMAKE" -S "$SNAP" -B "$BUILD" \
        -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF \
        -DCMAKE_C_COMPILER=/usr/bin/gcc -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
        -DCMAKE_PREFIX_PATH="$PREFIX" -DFETCHCONTENT_BASE_DIR="$BASE" \
        -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DCCBENCH_TRACE="$trace"
    cfg_rc=$?
    echo "CONFIGURE${trace}_RC=$cfg_rc"
    grep -n -E '^(CMAKE_GENERATOR:|FETCHCONTENT_SOURCE_DIR_MASSTREE|FETCHCONTENT_BASE_DIR)' "$BUILD/CMakeCache.txt"
    echo 'FETCHCONTENT_SOURCE_DIR_MASSTREE occurrence count:'
    grep -c 'FETCHCONTENT_SOURCE_DIR_MASSTREE' "$BUILD/CMakeCache.txt"
    cat "$BUILD/CMakeFiles/masstree_build.dir/DependInfo.cmake"
    /bin/python3.10 "$J/shape-probe/t2304_masstree_shape_probe.py" \
        "$REPO" "$BUILD" "$J/shape-probe/$tag-build$trace.json"
    probe_rc=$?
    echo "PROBE${trace}_RC=$probe_rc"
    [[ "$probe_rc" -eq 0 ]] || overall_rc=3
    if [[ "$cfg_rc" -ne 0 ]]; then
        overall_rc=20
        continue
    fi
    if [[ "$mode" == build ]]; then
        "$CMAKE" --build "$BUILD" --target ycsb_mocc.exe -j "$(nproc)"
        build_rc=$?
        echo "BUILD${trace}_RC=$build_rc"
        ls -la "$BUILD/cc/mocc/ycsb_mocc.exe"
        [[ "$build_rc" -eq 0 ]] || overall_rc=21
    fi
done
exit "$overall_rc"
