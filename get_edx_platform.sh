#!/bin/bash

ROOT=$(pwd)

# the edx-platform Git repository to clone for testing
REPO="${OPENEDX_REPO:-https://github.com/edx/edx-platform}"

# if a copy is already available locally, allow it to be used with "git
# clone --reference"
if [ -d "${OPENEDX_REFERENCE_REPO}" ]
then
    REFERENCE=" --reference ${OPENEDX_REFERENCE_REPO} "
else
    echo "Ignoring invalid reference repo \"$OPENEDX_REFERENCE_REPO\""
fi

# the branch to work on
BRANCH="${OPENEDX_RELEASE:-master}"

# and the location of the working copy
WORKING_COPY="${ROOT}/.tox/edx-platform"

function check_repo_remote() {
    (cd "$WORKING_COPY" && git remote -v | grep "$REPO")
}

function clone() {
    echo -ne "Cloning edx-platform from $REPO, branch $BRANCH "
    if [ "$REFERENCE" ]
    then
        echo "using reference copy in $OPENEDX_REFERENCE_REPO"
    else
        echo ""
    fi
    rm -rf "$WORKING_COPY"
    git clone $REFERENCE -b "$BRANCH" "$REPO" "$WORKING_COPY"
}

function checkout() {
    cd "$WORKING_COPY" && git checkout "$BRANCH"
}

mkdir -p "${ROOT}/.tox"

if test -d .tox/edx-platform
then
    echo "Making sure edx-platform is checked out at branch $BRANCH"
    check_repo_remote || clone
    checkout
else
    clone
fi
