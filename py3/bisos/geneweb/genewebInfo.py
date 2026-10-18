# -*- coding: utf-8 -*-

""" #+begin_org
* ~[Summary]~ :: =CS-Lib= The single source of the facts of this host's GeneWeb installation.
#+end_org """

""" #+begin_org
* [[elisp:(org-cycle)][| ~Description~ |]] :: Facts shared by geneweb-sbom.pcs, genewebUsage-sbom.pcs,
genewebAdmin.cs, quickGeneweb.cs, geneweb-sysd.pcs, geneweb-here-dns.pcs and geneweb-wvd.pcs: the
account, the pinned upstream release and its checksum, the paths, the EnvironmentFile, the fqdn, the
banna port, the wizard password and the out-of-the-box base.
** Pure: importing this module has no side effects and touches no host state.
** GeneWeb is genealogy software (OCaml). Its web server, gwd, serves the bases in a directory;
command-line tools (gwc, ged2gwb, gwb2ged, gwu) create bases and convert GEDCOM. gwsetup, its setup
web UI, is not run: it cannot bind an address (it listens on every interface).
** Login (rawBisos convention, insecure by design): the wizard password is geneweb; no friend
password; public pages need no login.
** Status: Starting point.
** /[[elisp:(org-cycle)][| Planned Improvements |]]/ :
*** TODO The "secure it" layer: real passwords, HTTPS, listening beyond loopback.
*** TODO Architectures other than amd64.
#+end_org """

####+BEGIN: b:prog:file/proclamations :outLevel 1
""" #+begin_org
* *[[elisp:(org-cycle)][| Proclamations |]]* :: Libre-Halaal Software --- Part Of BISOS ---  Poly-COMEEGA Format.
** This is Libre-Halaal Software. © Neda Communications, Inc. Subject to AGPL.
** It is part of BISOS (ByStar Internet Services OS)
** Best read and edited  with Blee in Poly-COMEEGA (Polymode Colaborative Org-Mode Enhance Emacs Generalized Authorship)
#+end_org """
####+END:

####+BEGIN: b:prog:file/particulars :authors ("./inserts/authors-mb.org")
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars |]]* :: Authors, version
** This File: /bisos/git/bxRepos/bisos-pip/geneweb/py3/bisos/geneweb/genewebInfo.py
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

import dataclasses
import difflib
import pathlib

from bisos.banna import tcpPorts as bannaTcpPorts


def _bannaPortNu(portName: str) -> int:
    """The registry, bisos.banna, is authoritative: never hardcode these ports."""
    return bannaTcpPorts.tcpPortsAssignedList.tcpPortsList[portName].portNu


@dataclasses.dataclass(frozen=True)
class GenewebInfo:
    """The facts of this host's GeneWeb installation. Built once, as genewebInfo below."""

    acctName: str = "geneweb"

    # Debian 13 does not package GeneWeb. The upstream Linux zip is pinned with the SHA-256 GitHub
    # records for the release asset. v7.1.0-beta2 (2025-12-25) is the newest release and the only one
    # with a published digest; it is named a beta (GitHub does not mark it a prerelease).
    # The binaries need libgmp (apt: libgmp10) beyond libc.
    version: str = "7.1.0-beta2"
    distSha256: tuple = (("amd64", "84b29e6fd1370cae81ea5f812d7fefe127396f294a949692a958556531905734"),)

    installBase: pathlib.Path = pathlib.Path("/opt/geneweb")

    # The bases (one .gwb directory and .gwf file per base) and gwd's working directory.
    dataDir: pathlib.Path = pathlib.Path("/var/lib/geneweb")

    # Read by systemd as root before the unit drops to User=. root:acctName 640.
    envFile: pathlib.Path = pathlib.Path("/etc/default/geneweb")

    listenIp: str = "127.0.0.1"
    fqdn: str = "geneweb.here"
    workers: int = 2
    lang: str = "en"

    # rawBisos convention: the password is the service's name. GeneWeb has no user names: a wizard
    # password (may edit) and a friend password (may see private data). No friend password is set.
    wizardPassword: str = "geneweb"

    # The out-of-the-box base: empty, created once, so http://geneweb.here/demo works at once.
    demoBase: str = "demo"

    portNu: int = dataclasses.field(default_factory=lambda: _bannaPortNu('geneweb'))

    @property
    def distName(self) -> str:
        """The zip has no top directory; it is unpacked into installBase/<distName>."""
        return f"geneweb-{self.version}"

    def distUrl(self, arch: str = "amd64") -> str:
        # The release ships one Linux zip (x86-64); arch selects the pinned checksum only.
        return (f"https://github.com/geneweb/geneweb/releases/download/v{self.version}/"
                f"geneweb-{self.version}-linux.zip")

    @property
    def distDir(self) -> pathlib.Path:
        return self.installBase / self.distName

    @property
    def homeLink(self) -> pathlib.Path:
        """installBase/current -> distDir. The unit and the tools go through it."""
        return self.installBase / "current"

    @property
    def gwDir(self) -> pathlib.Path:
        """gwd's -hd: the etc, images and lang directories, and the binaries."""
        return self.homeLink / "gw"

    def tool(self, name: str) -> pathlib.Path:
        """E.g. tool("gwd"), tool("ged2gwb")."""
        return self.gwDir / name

    @property
    def basesDir(self) -> pathlib.Path:
        return self.dataDir / "bases"

    @property
    def workDir(self) -> pathlib.Path:
        """gwd's -wd: access counts and the like."""
        return self.dataDir / "wd"

    @property
    def demoBaseDir(self) -> pathlib.Path:
        return self.basesDir / f"{self.demoBase}.gwb"

    @property
    def listenAddr(self) -> str:
        return f"{self.listenIp}:{self.portNu}"

    @property
    def baseUrl(self) -> str:
        return f"http://{self.fqdn}"

    @property
    def localUrl(self) -> str:
        return f"http://{self.listenAddr}"

    @property
    def demoUrl(self) -> str:
        return f"{self.baseUrl}/{self.demoBase}"


# A Singleton
genewebInfo = GenewebInfo()


def zipSetupScript(url: str, sha256: tuple, dirName: str, link: pathlib.Path,
                   base: pathlib.Path) -> str:
    """Bash: fetch a pinned release zip for this host's architecture, verify, unpack, link.

    The zip variant of tarballSetupScript (bisos.grafana/prometheus): unpacked once per version into
    base/<dirName> (the zip has no top directory), root-owned; link then points at it. A zip whose
    SHA-256 does not match is discarded and nothing is unpacked.
    """
    cases = "\n".join(f'    {arch}) sha={sha} ;;' for arch, sha in sha256)
    return f"""
set -e
arch=$(dpkg --print-architecture)
case "$arch" in
{cases}
    *) echo "no pinned checksum for architecture $arch" >&2 ; exit 1 ;;
esac
dir={base}/{dirName}
sudo mkdir -p {base}
if [ ! -d "$dir" ] ; then
    tmpDir=$(mktemp -d)
    trap 'rm -rf "$tmpDir"' EXIT
    curl -fsSL -o "$tmpDir/dist.zip" {url}
    echo "$sha  $tmpDir/dist.zip" | sha256sum -c --quiet -
    sudo mkdir -p "$dir"
    sudo unzip -q "$tmpDir/dist.zip" -d "$dir"
    sudo chown -R root:root "$dir"
fi
sudo ln -sfn "$dir" {link}
"""


def distSetupScript(info: GenewebInfo = genewebInfo) -> str:
    """The GeneWeb zip (gwd and the tools). Used by both the server and the usage sbom."""
    return zipSetupScript(info.distUrl(), info.distSha256, info.distName, info.homeLink,
                          info.installBase)


def demoBaseScript(info: GenewebInfo = genewebInfo) -> str:
    """Bash: the empty out-of-the-box base, created once by gwc, as the account."""
    return f"""
if ! sudo test -d {info.demoBaseDir} ; then
    sudo -u {info.acctName} sh -c 'cd {info.basesDir} && {info.tool("gwc")} -o {info.demoBase}'
fi
"""


def envFileContent(info: GenewebInfo = genewebInfo) -> str:
    """The content /etc/default/geneweb is generated with. Written only when absent.

    ARGS is expanded by the unit's ExecStart as separate words ($ARGS). -log - sends gwd's log to
    stdout, so to journald. The wizard password is on gwd's command line (visible in ps) --- rawBisos.
    """
    return (
        f'ARGS="-hd {info.gwDir} -bd {info.basesDir} -wd {info.workDir}'
        f' -a {info.listenIp} -p {info.portNu} -n_workers {info.workers} -lang {info.lang}'
        f' -wizard {info.wizardPassword} -log -"\n'
        "# Add gwd flags (e.g. -friend <passwd>, -robot_xcl 10,60) to ARGS above\n"
    )


def sysdServiceLines(envFile: pathlib.Path, info: GenewebInfo = genewebInfo) -> str:
    """The identity lines the geneweb unit has in its [Service] section."""
    return (
        f"User={info.acctName}\n"
        f"Group={info.acctName}\n"
        f"EnvironmentFile={envFile}\n"
    )


def _kvMap(text: str) -> dict[str, str]:
    """KEY=VALUE lines of an EnvironmentFile; comments and blank lines are skipped."""
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


def kvDrift(liveText: str, generatedText: str) -> dict[str, list]:
    """Compare a live KEY=VALUE file with its generator: missing, differs, extra."""
    expected = _kvMap(generatedText)
    live = _kvMap(liveText)
    return {
        "missing": [k for k in expected if k not in live],
        "differs": [(k, expected[k], live[k]) for k in expected if k in live and live[k] != expected[k]],
        "extra": [k for k in live if k not in expected],
    }


def textDrift(liveText: str, generatedText: str) -> list[str]:
    """A unified diff of a structured file against its generator; empty when they agree."""
    return list(difflib.unified_diff(generatedText.splitlines(), liveText.splitlines(),
                                     "generator", "live", lineterm=""))


def unitDrift(unitText: str, envFile: pathlib.Path, info: GenewebInfo = genewebInfo) -> list[str]:
    """The identity lines (sysdServiceLines) that an installed unit file lacks."""
    present = {line.strip() for line in unitText.splitlines()}
    return [line for line in sysdServiceLines(envFile, info).splitlines() if line not in present]


####+BEGIN: b:py3:cs:framework/endOfFile :basedOn "classification"
""" #+begin_org
* [[elisp:(org-cycle)][| *End-Of-Editable-Text* |]] :: emacs and org variables and control parameters
#+end_org """

#+STARTUP: showall

### local variables:
### no-byte-compile: t
### end:
####+END:
