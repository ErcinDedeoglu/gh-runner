repomix --no-file-summary --no-security-check --include "src/**,.github/**" --output "repopack.yml"

repomix --no-file-summary --no-security-check --include ".github/**" --output "repopack.yml"

repomix --no-file-summary --no-security-check --include "src/**" --output "repopack.yml"


docker build -f src/Dockerfile -t test src && docker run --rm -it test

docker run -it --rm \
  --entrypoint sh \
  test