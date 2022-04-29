# prerun.sh sets up the test function to use the functions framework commit
# specified by generating a `requirements.txt`. This makes the function `pack` buildable
# with GCF buildpacks.
#
# `pack` command example:
# pack build python-test --builder us.gcr.io/fn-img/buildpacks/python310/builder:python310_20220320_3_10_2_RC00 --env GOOGLE_RUNTIME=python310 --env GOOGLE_FUNCTION_TARGET=write_http_declarative
set -e

FRAMEWORK_VERSION=$1
if [ -z "${FRAMEWORK_VERSION}" ]
    then
        echo "Functions Framework version required as first parameter"
        exit 1
fi

SCRIPT_DIR=$(realpath $(dirname $0))

cd $SCRIPT_DIR

echo "git+https://github.com/GoogleCloudPlatform/functions-framework-python@$FRAMEWORK_VERSION#egg=functions-framework" > requirements.txt
cat requirements.txt