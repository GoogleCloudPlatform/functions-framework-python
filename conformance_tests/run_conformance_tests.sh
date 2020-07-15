cd ..
dockerFile=conformance_tests/Dockerfile

if [ ! -f "$dockerFile" ]; then
    echo "$dockerFile not in expected location"
    exit 1
fi

docker build -t conformance -f conformance_tests/Dockerfile .
docker run -p 8080:8080 -t conformance
