#!/bin/bash

set -e

if [ $# -ne 3 ]
then
	echo "Usage: $0 <kernel commit> <remote name> <remote url>"
	echo
	echo "Setup machine for running the performance test agains the"
	echo "linux kernel of <kernel commit>, which can be fetched from"
	echo "<remote name> remote repo of url <remote url>"
	echo
	echo "e.g., $0 985236144211 gh.damon https://github.com/damonitor/linux.git"
	exit 1
fi

commit=$1
remote=$2
url=$3

bindir=$(dirname "$0")
repos_dir=$(realpath "$bindir/../../")

# rsync is required for remote results fetching
sudo apt install -y rsync
# pstree is required by lazybox
sudo apt install -y psmisc

# Setup test machine for corr test run
cont_local_setup_sh=$(realpath "$bindir/../cont/_local_setup.sh")
"$cont_local_setup_sh" "$repos_dir" upstream/next-customize upstream/next \
	"$commit" "$remote" "$url"

# Install PARSEC3/SPLASH-2X
cd "$repos_dir"
if [ ! -d parsec-benchmark ]
then
	git clone https://github.com/damonitor/parsec-benchmark
else
	git -C parsec-benchmark fetch origin
	git -C parsec-benchmark checkout origin/master
fi
cd parsec-benchmark
./configure
./get-inputs -n

dirs=("pkgs/libs/gsl/src")
for d in "${dirs[@]}"; do
  wget -O "$d/config.guess" "https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD"
  wget -O "$d/config.sub" "https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD"
  chmod +x "$d/config.guess"
  chmod +x "$d/config.sub"
done

# autoreconf need libtool to regenerate the build scripts
sudo apt install -y libtool

for dir in "${dirs[@]}"; do
  echo ">>> Entering: $dir"
  pushd "$dir" > /dev/null

  echo ">>> Running autoupdate"
  autoupdate || echo "Warning: autoupdate failed, continuing."

  echo ">>> Running autoreconf -fi"
  autoreconf -fi

  popd > /dev/null
done

echo "=== All subprojects processed ==="

# apply patch to parsec
parsec_patch_file=$repos_dir/damon-tests/perf/parsec-debian13-fix.diff

git apply -p1 --3way $parsec_patch_file || {
	echo "[Error] applying ${parsec_patch_file} failed"
	exit 1
}

# texinfo is required to build parsec
sudo apt install -y texinfo

bash -c '
	source env.sh &&
	env \
		CFLAGS="$CFLAGS -Wno-error=incompatible-pointer-types -Wno-implicit-function-declaration -Wno-error=int-conversion -Wno-error=implicit-int" \
		CXXFLAGS="$CXXFLAGS -Wno-error=incompatible-pointer-types" \
		parsecmgmt -a build
'

# Install SPLASH-3
sudo apt install -y m4 ivtools-dev
cd "$repos_dir"
if [ ! -d splash-3 ]
then
	git clone https://github.com/SakalisC/Splash-3.git splash-3
else
	git -C splash-3 fetch origin
	git -C splash-3 checkout origin/main
fi

pushd splash-3/codes
make clean 
make -j $(($(nproc) / 2))
popd

