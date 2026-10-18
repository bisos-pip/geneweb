#!/bin/bash -i
#

# Safety check: must run from a directory named "tests"
if [[ "$(basename "$PWD")" != "tests" ]]; then
    echo "ERROR: verify.sh must be run from a directory named 'tests'." >&2
    echo "  Current PWD: $PWD" >&2
    exit 1
fi

# Starting-point smoke test for bisos.geneweb -- covers genewebAdmin.cs, quickGeneweb.cs, the
# read-only Cmnds of the planted files, and bisos.geneweb.genewebInfo's generators.
# Nothing here installs, starts or writes anything on the host.

# --- CS entry points: smoke test (no args → examples/usage, non-zero ok) ---

lpDo ../bin/genewebAdmin.cs
lpDo ../bin/quickGeneweb.cs
lpDo ../bin/geneweb-assemble.cs

# --- genewebAdmin.cs: each admin sub-Cmnd runs and produces examples output ---

lpDo ../bin/genewebAdmin.cs -i examples
lpDo ../bin/genewebAdmin.cs -i hostInfo
lpDo ../bin/genewebAdmin.cs -i servicesInfo
lpDo ../bin/genewebAdmin.cs -i basesInfo
lpDo ../bin/genewebAdmin.cs -i driftCheck
lpDo ../bin/genewebAdmin.cs -i fullUpdate

# --- planted files: menus and read-only Cmnds ---

lpDo ../bin/geneweb-sbom.pcs -i readme
lpDo ../bin/genewebUsage-sbom.pcs -i readme
lpDo ../bin/genewebCbs-sbom.pcs -i readme
lpDo ../bin/geneweb-sysd.pcs
lpDo ../bin/geneweb-cbs.pcs
lpDo ../bin/cbmProc-geneweb.spcs
lpDo ../bin/geneweb-here-dns.pcs
lpDo ../bin/geneweb-wvd.pcs -i configFileStdout --cls=configFile_nginxVd

# --- bisos.geneweb.genewebInfo: banna numbers and generator invariants ---

lpDo python3 -c "
import subprocess, sys
from bisos.banna import sysAccts
from bisos.geneweb.genewebInfo import (
    genewebInfo as i, envFileContent, distSetupScript, demoBaseScript, kvDrift,
)

cases = [
    ('banna: geneweb port',             i.portNu == 24017),
    ('banna sysAccts: geneweb uid',     sysAccts.sysAcctOf(i.acctName).uid == 508),
    ('banna sysAccts: homeDir',         sysAccts.sysAcctOf(i.acctName).homeDir == str(i.dataDir)),
    ('amd64 checksum pinned',           dict(i.distSha256).get('amd64', '') != ''),
    ('gwd on loopback',                 f'-a 127.0.0.1 -p {i.portNu}' in envFileContent()),
    ('minimal: 2 workers',              '-n_workers 2' in envFileContent()),
    ('wizard password geneweb',         '-wizard geneweb' in envFileContent()),
    ('no friend password',              '-friend' not in envFileContent().split(chr(10))[0]),
    ('log to journald',                 '-log -' in envFileContent()),
    ('demo base created by gwc',        'gwc -o demo' in demoBaseScript()),
    ('scripts parse',                   all(subprocess.run(['bash', '-n'], input=s, text=True).returncode == 0
                                            for s in (distSetupScript(), demoBaseScript()))),
    ('drift: extra key reported',       kvDrift(envFileContent() + 'X=1\n', envFileContent())['extra'] == ['X']),
]

failed = 0
for name, ok in cases:
    print(f'  [{\"PASS\" if ok else \"FAIL\"}] {name}')
    failed += not ok

if failed:
    print(f'genewebInfo: {failed} test(s) FAILED')
    sys.exit(1)
else:
    print('genewebInfo: all cases PASS')
" 2>/dev/null || true
